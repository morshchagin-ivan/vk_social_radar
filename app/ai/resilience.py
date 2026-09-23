"""In-process generation resilience. No HTTP, domain logic or total deadline."""
from __future__ import annotations

import math
import random
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from threading import Lock
from typing import Literal

from .contracts import (
    GenerationRequest, GenerationResult, LLMCircuitOpenError, ModelInfo,
    ProviderTimeoutError, ProviderUnavailableError,
)
from .provider import LLMProvider


@dataclass(frozen=True)
class ResiliencePolicy:
    max_attempts: int = 3
    base_delay: float = 0.5
    max_delay: float = 2.0
    jitter: Literal["full"] = "full"
    failure_threshold: int = 3
    recovery_timeout: float = 30.0

    def __post_init__(self) -> None:
        for value in (self.max_attempts, self.failure_threshold):
            if type(value) is not int or value < 1:
                raise ValueError("Attempts and failure threshold must be positive integers")
        for value in (self.base_delay, self.max_delay, self.recovery_timeout):
            if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
                raise ValueError("Resilience durations must be finite and nonnegative")
        if self.max_delay < self.base_delay or self.recovery_timeout == 0 or self.jitter != "full":
            raise ValueError("Invalid resilience delay, recovery timeout or jitter strategy")


class CircuitState(str, Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


def is_retryable(error: BaseException) -> bool:
    return isinstance(error, (ProviderUnavailableError, ProviderTimeoutError))


class ResilientLLMProvider:
    def __init__(
        self, provider: LLMProvider, policy: ResiliencePolicy = ResiliencePolicy(), *,
        clock: Callable[[], float] | None = None,
        sleep: Callable[[float], None] | None = None,
        random_value: Callable[[], float] | None = None,
    ):
        self.provider = provider
        self.policy = policy
        self._clock = clock if clock is not None else time.monotonic
        self._sleep = sleep if sleep is not None else time.sleep
        self._random = random_value if random_value is not None else random.random
        self._lock = Lock()
        self._state = CircuitState.CLOSED
        self._failures = 0
        self._opened_at = 0.0
        # Tickets from a previous state epoch cannot close/reopen a newer circuit.
        self._epoch = 0

    @property
    def state(self) -> CircuitState:
        with self._lock:
            return self._state

    @property
    def failure_count(self) -> int:
        with self._lock:
            return self._failures

    def list_models(self) -> list[ModelInfo]:
        # Discovery/health is deliberately independent: one call, no state changes.
        return self.provider.list_models()

    def _admit(self) -> tuple[int, bool]:
        with self._lock:
            if self._state == CircuitState.OPEN:
                if self._clock() - self._opened_at < self.policy.recovery_timeout:
                    raise LLMCircuitOpenError("LLM generation temporarily unavailable")
                self._state = CircuitState.HALF_OPEN
                self._epoch += 1
                return self._epoch, True
            if self._state == CircuitState.HALF_OPEN:
                raise LLMCircuitOpenError("LLM generation temporarily unavailable")
            return self._epoch, False

    def _open(self) -> None:
        # Called only with the state lock held.
        self._state = CircuitState.OPEN
        self._opened_at = self._clock()
        self._epoch += 1

    def _complete(self, ticket: tuple[int, bool], *, success: bool, transient: bool = False) -> None:
        epoch, probe = ticket
        with self._lock:
            if epoch != self._epoch:
                return  # A previously admitted operation completed after a transition.
            if probe:
                if transient:
                    self._open()
                else:
                    # Non-transient errors do not establish infrastructure outage.
                    # Release the probe, close/reset and propagate its original error.
                    self._state = CircuitState.CLOSED
                    self._failures = 0
                    self._epoch += 1
            elif success:
                self._failures = 0
            elif transient:
                self._failures += 1
                if self._failures >= self.policy.failure_threshold:
                    self._open()
            # Non-transient CLOSED failures are neutral, not resets or increments.

    def _generate(self, request: GenerationRequest, attempts: int) -> GenerationResult:
        ceiling = self.policy.base_delay
        for attempt in range(attempts):
            try:
                return self.provider.generate(request)
            except Exception as error:
                if not is_retryable(error) or attempt + 1 == attempts:
                    raise
                sample = self._random()
                if not math.isfinite(sample) or not 0 <= sample <= 1:
                    raise ValueError("Jitter source must return a value in [0, 1]") from None
                delay = ceiling * sample  # Full jitter: U(0, min(max, base * 2**k)).
                if delay > 0:
                    self._sleep(delay)
                ceiling = min(self.policy.max_delay, ceiling * 2)
        raise AssertionError("Validated policy must allow at least one attempt")

    def generate(self, request: GenerationRequest) -> GenerationResult:
        ticket = self._admit()
        try:
            # A HALF_OPEN probe has exactly one underlying attempt, no retries/sleep.
            result = self._generate(request, 1 if ticket[1] else self.policy.max_attempts)
        except BaseException as error:
            # Also release a probe on cancellation/unexpected exceptions.
            self._complete(ticket, success=False, transient=is_retryable(error))
            raise
        self._complete(ticket, success=True)
        return result
