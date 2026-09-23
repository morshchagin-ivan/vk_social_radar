from __future__ import annotations

import ast
import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path
from threading import Event
from unittest.mock import patch

import httpx
from fastapi.testclient import TestClient

from app import main
from app.ai import composition
from app.ai.contracts import (
    GenerationResult, LLMCircuitOpenError, ProviderProtocolError,
    ProviderResponseError, ProviderTimeoutError, ProviderUnavailableError,
)
from app.ai.providers.lmstudio import LMStudioProvider
from app.ai.resilience import CircuitState, ResiliencePolicy, ResilientLLMProvider
from app.ai.service import AIInsightService, InsightValidationError
from app.ai.settings import save_settings
from test_ai_provider import FakeProvider, InsightFixture, NetworkBlockedTests, REQUEST, VALID


RESULT = GenerationResult(json.dumps(VALID), REQUEST.model, "fake")


class FakeTime:
    def __init__(self):
        self.now = 0.0
        self.delays = []

    def clock(self):
        return self.now

    def sleep(self, delay):
        self.delays.append(delay)
        self.now += delay


class ScriptedProvider(FakeProvider):
    def __init__(self, outcomes=()):
        super().__init__()
        self.outcomes = list(outcomes)

    def generate(self, request):
        self.requests.append(request)
        outcome = self.outcomes.pop(0) if self.outcomes else RESULT
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome


def unavailable():
    return ProviderUnavailableError("Provider is unavailable")


class ResilienceTests(NetworkBlockedTests):
    def setUp(self):
        super().setUp()
        self.time = FakeTime()
        self.provider = ScriptedProvider()

    def wrap(self, **overrides):
        return ResilientLLMProvider(self.provider, ResiliencePolicy(**overrides),
                                    clock=self.time.clock, sleep=self.time.sleep, random_value=lambda: 1.0)

    def fail(self, wrapper):
        self.provider.outcomes = [unavailable()] * wrapper.policy.max_attempts
        with self.assertRaises(ProviderUnavailableError):
            wrapper.generate(REQUEST)

    def open(self, wrapper):
        for _ in range(wrapper.policy.failure_threshold):
            self.fail(wrapper)
        self.assertEqual(wrapper.state, CircuitState.OPEN)

    def test_res_001_transient_then_success_and_cb_008_no_failure(self):
        wrapper = self.wrap()
        self.provider.outcomes = [unavailable(), RESULT]
        self.assertEqual(wrapper.generate(REQUEST), RESULT)
        self.assertEqual(len(self.provider.requests), 2)
        self.assertEqual(self.time.delays, [0.5])
        self.assertEqual(wrapper.failure_count, 0)
        self.assertEqual(wrapper.state, CircuitState.CLOSED)

    def test_res_002_exhaustion_and_cb_009_counts_one(self):
        wrapper = self.wrap()
        final = unavailable()
        self.provider.outcomes = [unavailable(), unavailable(), final]
        with self.assertRaises(ProviderUnavailableError) as caught:
            wrapper.generate(REQUEST)
        self.assertIs(caught.exception, final)
        self.assertEqual(len(self.provider.requests), 3)
        self.assertEqual(self.time.delays, [0.5, 1.0])
        self.assertEqual(wrapper.failure_count, 1)

    def test_res_003_nonretryable_single_attempt(self):
        for error in (ProviderProtocolError("Rejected"), ProviderResponseError("Malformed"),
                      InsightValidationError("Invalid"), ValueError("Invalid config"), LLMCircuitOpenError("Open")):
            with self.subTest(error=type(error)):
                wrapper = self.wrap()
                before = len(self.provider.requests)
                self.provider.outcomes = [error]
                with self.assertRaises(type(error)):
                    wrapper.generate(REQUEST)
                self.assertEqual(len(self.provider.requests) - before, 1)
                self.assertEqual(self.time.delays, [])
                self.assertEqual(wrapper.failure_count, 0)

    def test_res_004_exact_capped_exponential_delays(self):
        wrapper = self.wrap(max_attempts=6)
        self.fail(wrapper)
        self.assertEqual(self.time.delays, [0.5, 1.0, 2.0, 2.0, 2.0])
        self.assertEqual(len(self.provider.requests), 6)

    def test_res_005_full_jitter_bounds(self):
        for sample in (0, 0.25, 0.5, 1):
            with self.subTest(sample=sample):
                self.time = FakeTime()
                wrapper = ResilientLLMProvider(self.provider, clock=self.time.clock,
                                              sleep=self.time.sleep, random_value=lambda: sample)
                self.fail(wrapper)
                self.assertEqual(self.time.delays, [] if sample == 0 else [0.5 * sample, sample])
                self.assertLessEqual(sum(self.time.delays), 1.5)

    def test_res_006_timeout_retries(self):
        wrapper = self.wrap()
        self.provider.outcomes = [ProviderTimeoutError("Timeout"), RESULT]
        self.assertEqual(wrapper.generate(REQUEST), RESULT)
        self.assertEqual(len(self.provider.requests), 2)
        self.assertEqual(wrapper.failure_count, 0)

    def test_cb_001_logical_failure_threshold(self):
        wrapper = self.wrap(failure_threshold=2)
        self.fail(wrapper)
        self.assertEqual(wrapper.state, CircuitState.CLOSED)
        self.assertEqual(wrapper.failure_count, 1)
        self.fail(wrapper)
        self.assertEqual(wrapper.state, CircuitState.OPEN)
        self.assertEqual(wrapper.failure_count, 2)
        self.assertEqual(len(self.provider.requests), 6)

    def test_cb_002_open_rejects_without_calls_retries_or_sleep(self):
        wrapper = self.wrap(failure_threshold=1)
        self.open(wrapper)
        before = (len(self.provider.requests), list(self.time.delays))
        for _ in range(3):
            with self.assertRaises(LLMCircuitOpenError):
                wrapper.generate(REQUEST)
        self.assertEqual((len(self.provider.requests), self.time.delays), before)

    def test_cb_003_recovery_boundary_and_cb_004_success(self):
        wrapper = self.wrap(failure_threshold=1)
        self.open(wrapper)
        self.time.now += 29.99
        with self.assertRaises(LLMCircuitOpenError):
            wrapper.generate(REQUEST)
        self.time.now += 0.01
        calls = len(self.provider.requests)
        sleeps = list(self.time.delays)
        self.assertEqual(wrapper.generate(REQUEST), RESULT)
        self.assertEqual(len(self.provider.requests) - calls, 1)
        self.assertEqual(self.time.delays, sleeps)
        self.assertEqual(wrapper.state, CircuitState.CLOSED)
        self.assertEqual(wrapper.failure_count, 0)

    def test_cb_005_failed_probe_is_single_attempt_and_restarts_timer(self):
        wrapper = self.wrap(failure_threshold=1)
        self.open(wrapper)
        self.time.now += 30
        self.provider.outcomes = [unavailable(), RESULT]
        calls = len(self.provider.requests)
        sleeps = list(self.time.delays)
        with self.assertRaises(ProviderUnavailableError):
            wrapper.generate(REQUEST)
        self.assertEqual(len(self.provider.requests) - calls, 1)
        self.assertEqual(wrapper.state, CircuitState.OPEN)
        self.time.now += 29
        with self.assertRaises(LLMCircuitOpenError):
            wrapper.generate(REQUEST)
        self.time.now += 1
        self.assertEqual(wrapper.generate(REQUEST), RESULT)
        self.assertEqual(self.time.delays, sleeps)

    def test_cb_006_closed_success_resets_consecutive_failures(self):
        wrapper = self.wrap(failure_threshold=2)
        self.fail(wrapper)
        wrapper.generate(REQUEST)
        self.assertEqual(wrapper.failure_count, 0)
        self.fail(wrapper)
        self.assertEqual(wrapper.state, CircuitState.CLOSED)
        self.assertEqual(wrapper.failure_count, 1)

    def test_cb_007_nonretryable_is_neutral_closed_and_closes_probe(self):
        wrapper = self.wrap(failure_threshold=2)
        self.fail(wrapper)
        self.provider.outcomes = [ProviderProtocolError("Rejected")]
        with self.assertRaises(ProviderProtocolError):
            wrapper.generate(REQUEST)
        self.assertEqual(wrapper.failure_count, 1)
        self.assertEqual(wrapper.state, CircuitState.CLOSED)
        self.fail(wrapper)
        self.time.now += 30
        self.provider.outcomes = [ProviderResponseError("Malformed")]
        with self.assertRaises(ProviderResponseError):
            wrapper.generate(REQUEST)
        self.assertEqual(wrapper.state, CircuitState.CLOSED)
        self.assertEqual(wrapper.failure_count, 0)

    def test_cb_010_half_open_concurrent_single_probe(self):
        wrapper = self.wrap(failure_threshold=1)
        self.open(wrapper)
        self.time.now += 30
        entered, release = Event(), Event()
        original = self.provider.generate
        def blocked(request):
            entered.set()
            if not release.wait(5):
                raise AssertionError("Test probe was not released")
            return original(request)
        with patch.object(self.provider, "generate", side_effect=blocked) as generate:
            with ThreadPoolExecutor(max_workers=2) as pool:
                future = pool.submit(wrapper.generate, REQUEST)
                try:
                    self.assertTrue(entered.wait(5))
                    self.assertEqual(wrapper.state, CircuitState.HALF_OPEN)
                    with self.assertRaises(LLMCircuitOpenError):
                        pool.submit(wrapper.generate, REQUEST).result(timeout=5)
                    self.assertEqual(generate.call_count, 1)
                finally:
                    release.set()
                self.assertEqual(future.result(timeout=5), RESULT)
        self.assertEqual(wrapper.state, CircuitState.CLOSED)

    def test_stale_closed_success_cannot_close_newly_open_circuit(self):
        wrapper = self.wrap(failure_threshold=1, max_attempts=1)
        entered, release = Event(), Event()
        def first_call(request):
            entered.set()
            if not release.wait(5):
                raise AssertionError("Test call was not released")
            return RESULT
        with ThreadPoolExecutor(max_workers=1) as pool:
            with patch.object(self.provider, "generate", side_effect=first_call):
                future = pool.submit(wrapper.generate, REQUEST)
                self.assertTrue(entered.wait(5))
            try:
                self.fail(wrapper)
            finally:
                release.set()
            self.assertEqual(future.result(timeout=5), RESULT)
        self.assertEqual(wrapper.state, CircuitState.OPEN)

    def test_models_neither_trip_nor_reset_generation_circuit(self):
        wrapper = self.wrap(failure_threshold=1)
        self.provider.error = unavailable()
        with self.assertRaises(ProviderUnavailableError):
            wrapper.list_models()
        self.assertEqual(self.provider.list_calls, 1)
        self.assertEqual(wrapper.failure_count, 0)
        self.open(wrapper)
        self.provider.error = None
        self.assertTrue(wrapper.list_models())
        self.assertEqual(wrapper.state, CircuitState.OPEN)
        self.assertEqual(self.provider.list_calls, 2)

    def test_policy_rejects_invalid_values(self):
        for changes in ({"max_attempts": 0}, {"max_attempts": True}, {"failure_threshold": 0},
                        {"base_delay": -1}, {"max_delay": 0.1}, {"recovery_timeout": 0},
                        {"recovery_timeout": float("inf")}, {"jitter": "unbounded"}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                ResiliencePolicy(**changes)

    def test_selected_http_statuses_only(self):
        for status in (400, 401, 404, 422, 429, 500, 501, 502, 503, 504, 505):
            with self.subTest(status=status):
                calls = []
                def handler(request):
                    calls.append(request)
                    return httpx.Response(status, text="Synthetic response")
                adapter = LMStudioProvider("http://provider.invalid/v1", transport=httpx.MockTransport(handler))
                self.provider = adapter
                wrapper = self.wrap()
                transient = status in {429, 500, 502, 503, 504}
                with self.assertRaises(ProviderUnavailableError if transient else ProviderProtocolError):
                    wrapper.generate(REQUEST)
                self.assertEqual(len(calls), 3 if transient else 1)
                self.assertEqual(wrapper.failure_count, 1 if transient else 0)

    def test_architecture_import_fitness(self):
        root = Path(__file__).resolve().parents[1]
        for file, forbidden in (
            ("app/ai/service.py", {"httpx", "resilience", "composition", "providers", "lmstudio"}),
            ("app/ai/resilience.py", {"httpx", "fastapi", "service", "services", "db", "lmstudio"}),
            ("app/ai/providers/lmstudio.py", {"resilience", "service", "services", "fastapi", "db"}),
        ):
            tree = ast.parse((root / file).read_text(encoding="utf-8"))
            names = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    names.update((node.module or "").split("."))
                    names.update(alias.name for alias in node.names)
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        names.update(alias.name.split("."))
            self.assertFalse(names & forbidden, file)


class ResilienceAPITests(InsightFixture):
    def setUp(self):
        super().setUp()
        self.time = FakeTime()
        self.scripted = ScriptedProvider()
        self.policy = ResiliencePolicy(failure_threshold=1)
        self.wrapper = ResilientLLMProvider(self.scripted, self.policy, clock=self.time.clock,
                                           sleep=self.time.sleep, random_value=lambda: 1)
        # Real composition binding is retained across separate API requests.
        self.enterContext(patch.object(composition, "LMStudioProvider", return_value=self.scripted))
        self.enterContext(patch.object(composition, "ResilientLLMProvider", return_value=self.wrapper))
        save_settings({"lmstudio_model": REQUEST.model})
        self.client = TestClient(main.app)  # No production startup/lifespan.
        self.addCleanup(self.client.close)

    def request(self):
        return self.client.post(f"/api/people/{self.person_id}/insight")

    def trip(self):
        self.scripted.outcomes = [unavailable()] * 3
        self.assertEqual(self.request().status_code, 503)
        self.assertEqual(self.wrapper.state, CircuitState.OPEN)

    def test_res_api_001_recovers_and_persists_once(self):
        self.scripted.outcomes = [unavailable(), RESULT]
        response = self.request()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"id": 1, **VALID, "model": REQUEST.model})
        self.assertEqual(len(self.scripted.requests), 2)
        self.assertEqual(self.wrapper.failure_count, 0)
        self.assertEqual(self.count(), 1)

    def test_res_api_002_open_503_without_provider_call(self):
        self.trip()
        before = (len(self.scripted.requests), self.scripted.list_calls, list(self.time.delays))
        response = self.request()
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {"detail": "Не удалось получить анализ: LLM generation temporarily unavailable"})
        self.assertEqual((len(self.scripted.requests), self.scripted.list_calls, self.time.delays), before)
        self.assertEqual(self.count(), 0)

    def test_res_api_003_recovery_restores_following_requests(self):
        self.trip()
        self.time.now += 30
        self.assertEqual(self.request().status_code, 200)
        self.assertEqual(self.wrapper.state, CircuitState.CLOSED)
        self.assertEqual(self.request().status_code, 200)
        self.assertEqual(len(self.scripted.requests), 5)
        self.assertEqual(self.count(), 2)

    def test_res_api_004_models_test_and_settings_compatible_while_open(self):
        self.trip()
        models = self.client.get("/api/lmstudio/models")
        self.assertEqual(models.status_code, 200)
        self.assertEqual(models.json()[0]["id"], REQUEST.model)
        self.assertEqual(self.client.post("/api/lmstudio/test").json(),
                         {"ok": True, "models_count": 1, "models": [REQUEST.model]})
        self.assertEqual(self.client.get("/api/settings").json()["lmstudio_model"], REQUEST.model)
        response = self.client.put("/api/settings", json={"lmstudio_temperature": "0.4", "retry": "ignored"})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("retry", response.json())
        self.assertEqual(self.request().status_code, 503)
        self.assertEqual(self.wrapper.state, CircuitState.OPEN)

    def test_res_007_invalid_generated_output_is_not_retried_or_persisted(self):
        for content in ("not JSON", json.dumps({**VALID, "confidence": 2})):
            self.scripted.outcomes = [replace(RESULT, content=content)]
            before = len(self.scripted.requests)
            self.assertEqual(self.request().status_code, 503)
            self.assertEqual(len(self.scripted.requests) - before, 1)
            self.assertEqual(self.wrapper.failure_count, 0)
        self.assertEqual(self.time.delays, [])
        self.assertEqual(self.count(), 0)

    def test_auto_model_discovery_still_runs_when_generation_open(self):
        self.trip()
        save_settings({"lmstudio_model": ""})
        self.assertEqual(self.request().status_code, 503)
        self.assertEqual(self.scripted.list_calls, 1)
        self.assertEqual(len(self.scripted.requests), 3)


class CompositionTests(InsightFixture):
    def test_shared_binding_endpoint_change_and_concurrent_creation(self):
        with ThreadPoolExecutor(max_workers=4) as pool:
            bindings = list(pool.map(lambda _: composition.get_provider(), range(8)))
        first = bindings[0]
        self.assertIsInstance(first, ResilientLLMProvider)
        self.assertIsInstance(first.provider, LMStudioProvider)
        self.assertTrue(all(binding is first for binding in bindings))
        save_settings({"lmstudio_model": "different", "lmstudio_temperature": "0.3"})
        self.assertIs(composition.get_provider(), first)
        save_settings({"lmstudio_base_url": "http://other.invalid/v1"})
        second = composition.get_provider()
        self.assertIsNot(first, second)
        self.assertEqual(second.state, CircuitState.CLOSED)
