from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass(frozen=True)
class Message:
    role: Literal["system", "user", "assistant"]
    content: str


@dataclass(frozen=True)
class StructuredOutput:
    name: str
    schema: dict[str, Any]


@dataclass(frozen=True)
class GenerationRequest:
    model: str
    messages: tuple[Message, ...]
    temperature: float
    structured_output: StructuredOutput | None = None


@dataclass(frozen=True)
class GenerationResult:
    content: str
    model: str
    provider: str


@dataclass(frozen=True)
class ModelInfo:
    id: str
    # Optional descriptive attributes preserve the existing models API. The
    # use case selects by id only; no HTTP envelope crosses the port.
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {**self.metadata, "id": self.id}


class ProviderError(RuntimeError):
    """Provider failures expose only safe, vendor-neutral messages."""


class ProviderUnavailableError(ProviderError):
    pass


class ProviderTimeoutError(ProviderError):
    pass


class ProviderProtocolError(ProviderError):
    pass


class ProviderResponseError(ProviderError):
    pass


class LLMCircuitOpenError(ProviderError):
    """Generation is temporarily rejected without calling the transport."""
