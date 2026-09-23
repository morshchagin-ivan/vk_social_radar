from __future__ import annotations

import ast
import json
import socket
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import httpx
from fastapi.testclient import TestClient

from app import db, importers, main
from app.ai import composition
from app.ai.contracts import (
    GenerationRequest, GenerationResult, Message, ModelInfo, ProviderError,
    ProviderProtocolError, ProviderResponseError, ProviderTimeoutError,
    ProviderUnavailableError, StructuredOutput,
)
from app.ai.providers.lmstudio import LMStudioProvider
from app.ai.resilience import ResilientLLMProvider
from app.ai.service import AIInsightService, InsightValidationError, store_insight
from app.ai.settings import save_settings
from app.services import person_detail


VALID = {"status": "stable", "confidence": 0.7, "summary": "Synthetic summary",
         "evidence": ["Synthetic metric"], "cautions": []}
MODEL = {"id": "model-a", "object": "model", "owned_by": "synthetic", "custom": {"size": 1}}
REQUEST = GenerationRequest("model-a", (Message("user", "Synthetic prompt"),), 0.2)


class FakeProvider:
    """Structural implementation: deliberately does not inherit a provider class."""
    def __init__(self, content=None, error=None):
        self.content = json.dumps(VALID) if content is None else content
        self.error = error
        self.models = [ModelInfo("model-a", {key: value for key, value in MODEL.items() if key != "id"})]
        self.requests = []
        self.list_calls = 0

    def list_models(self):
        self.list_calls += 1
        if self.error:
            raise self.error
        return self.models

    def generate(self, request):
        self.requests.append(request)
        if self.error:
            raise self.error
        return GenerationResult(self.content, request.model, "fake")


class NetworkBlockedTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch.object(time, "sleep", side_effect=AssertionError("Real sleep forbidden")))
        self.enterContext(patch.object(socket, "create_connection", side_effect=AssertionError("Network forbidden")))
        self.enterContext(patch.object(httpx.HTTPTransport, "handle_request", side_effect=AssertionError("HTTP network forbidden")))


class ProviderContract:
    """Reusable contract: implement make_provider(unavailable=False) for another adapter.

    The factory supplies deterministic discovery/completion and failure fixtures.
    Assertions below use only the vendor-neutral port, with no transport details.
    """
    def test_contract_models(self):
        models = self.make_provider().list_models()
        self.assertTrue(models)
        self.assertTrue(all(isinstance(model, ModelInfo) and model.id for model in models))

    def test_contract_generation(self):
        result = self.make_provider().generate(REQUEST)
        self.assertIsInstance(result, GenerationResult)
        self.assertEqual(result.model, REQUEST.model)
        self.assertIsInstance(result.content, str)
        self.assertTrue(result.provider)

    def test_contract_failure(self):
        for operation in (lambda p: p.list_models(), lambda p: p.generate(REQUEST)):
            with self.assertRaises(ProviderUnavailableError):
                operation(self.make_provider(unavailable=True))


class FakeProviderContractTests(ProviderContract, NetworkBlockedTests):
    def make_provider(self, unavailable=False):
        return FakeProvider(error=ProviderUnavailableError("Provider is unavailable") if unavailable else None)


class LMStudioContractTests(ProviderContract, NetworkBlockedTests):
    def make_provider(self, unavailable=False):
        def handler(request):
            if unavailable:
                return httpx.Response(503)
            if request.method == "GET":
                return httpx.Response(200, json={"data": [MODEL]})
            return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps(VALID)}}]})
        return LMStudioProvider("http://provider.invalid/v1", transport=httpx.MockTransport(handler))


class AdapterTests(NetworkBlockedTests):
    def test_llm_port_002_request_mapping_and_timeout(self):
        calls = []
        def handler(request):
            calls.append(request)
            return httpx.Response(200, json={"model": "resolved-model", "choices": [{"message": {"content": "{}"}}]})
        schema = {"type": "object", "properties": {}}
        request = GenerationRequest("chosen", (Message("system", "Rule"), Message("user", "Input")),
                                    0.4, StructuredOutput("synthetic_schema", schema))
        provider = LMStudioProvider("http://provider.invalid/v1/", transport=httpx.MockTransport(handler))
        result = provider.generate(request)
        self.assertEqual(result, GenerationResult("{}", "resolved-model", "lmstudio"))
        self.assertEqual(len(calls), 1)
        self.assertEqual(str(calls[0].url), "http://provider.invalid/v1/chat/completions")
        self.assertEqual(calls[0].method, "POST")
        self.assertEqual(json.loads(calls[0].content), {
            "model": "chosen", "temperature": 0.4, "stream": False,
            "messages": [{"role": "system", "content": "Rule"}, {"role": "user", "content": "Input"}],
            "response_format": {"type": "json_schema", "json_schema": {
                "name": "synthetic_schema", "strict": True, "schema": schema}},
        })
        self.assertEqual(set(calls[0].extensions["timeout"].values()), {120.0})

    def test_llm_port_003_models_mapping(self):
        calls = []
        def handler(request):
            calls.append(request)
            return httpx.Response(200, json={"data": [MODEL], "object": "list"})
        models = LMStudioProvider("http://provider.invalid/v1", transport=httpx.MockTransport(handler)).list_models()
        self.assertEqual(models[0].id, "model-a")
        self.assertEqual(models[0].as_dict(), MODEL)
        self.assertEqual(calls[0].method, "GET")
        self.assertEqual(str(calls[0].url), "http://provider.invalid/v1/models")
        self.assertEqual(set(calls[0].extensions["timeout"].values()), {8.0})

    def assert_transport_failure(self, error_class, expected):
        for operation in (lambda p: p.list_models(), lambda p: p.generate(REQUEST)):
            calls = []
            def handler(request):
                calls.append(request)
                raise error_class("PRIVATE transport diagnostic", request=request)
            provider = LMStudioProvider("http://provider.invalid/v1", transport=httpx.MockTransport(handler))
            with self.assertRaises(expected) as caught:
                operation(provider)
            self.assertEqual(len(calls), 1)  # No retry for either operation.
            self.assertNotIn("PRIVATE", str(caught.exception))
            self.assertIsNone(caught.exception.__cause__)

    def test_llm_port_004_connection_failure(self):
        self.assert_transport_failure(httpx.ConnectError, ProviderUnavailableError)

    def test_llm_port_005_timeout_no_retry(self):
        self.assert_transport_failure(httpx.ReadTimeout, ProviderTimeoutError)

    def test_protocol_and_http_errors(self):
        self.assert_transport_failure(httpx.RemoteProtocolError, ProviderProtocolError)
        for status, expected in ((400, ProviderProtocolError), (401, ProviderProtocolError),
                                 (429, ProviderUnavailableError), (500, ProviderUnavailableError)):
            for operation in (lambda p: p.list_models(), lambda p: p.generate(REQUEST)):
                with self.subTest(status=status, operation=operation):
                    calls = []
                    def handler(request):
                        calls.append(request)
                        return httpx.Response(status, text="PRIVATE provider response")
                    provider = LMStudioProvider("http://provider.invalid/v1", transport=httpx.MockTransport(handler))
                    with self.assertRaises(expected) as caught:
                        operation(provider)
                    self.assertEqual(len(calls), 1)
                    self.assertNotIn("PRIVATE", str(caught.exception))

    def test_llm_port_006_malformed_envelopes(self):
        cases = [[], {}, {"choices": []}, {"choices": {}}, {"choices": [None]},
                 {"choices": [{"message": {"content": None}}]},
                 {"choices": [{"message": {"content": []}}]},
                 {"model": 123, "choices": [{"message": {"content": "{}"}}]}]
        for payload in cases:
            with self.subTest(payload=payload):
                provider = LMStudioProvider("http://provider.invalid/v1", transport=httpx.MockTransport(
                    lambda request: httpx.Response(200, json=payload)))
                with self.assertRaises(ProviderResponseError):
                    provider.generate(REQUEST)
        for payload in ({}, {"data": None}, {"data": {}}, {"data": [None]},
                        {"data": [{}]}, {"data": [{"id": 3}]}, {"data": [{"id": " "}]}):
            with self.subTest(payload=payload):
                provider = LMStudioProvider("http://provider.invalid/v1", transport=httpx.MockTransport(
                    lambda request: httpx.Response(200, json=payload)))
                with self.assertRaises(ProviderResponseError):
                    provider.list_models()
        for operation in (lambda p: p.list_models(), lambda p: p.generate(REQUEST)):
            provider = LMStudioProvider("http://provider.invalid/v1", transport=httpx.MockTransport(
                lambda request: httpx.Response(200, content=b"not JSON")))
            with self.assertRaises(ProviderResponseError):
                operation(provider)


class InsightFixture(NetworkBlockedTests):
    def setUp(self):
        super().setUp()
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        self.enterContext(patch.multiple(db, DB_PATH=root / "test.db", DATA_DIR=root,
                                        IMPORT_DIR=root / "imports", BACKUP_DIR=root / "backups"))
        self.enterContext(patch.object(importers, "IMPORT_DIR", root / "imports"))
        self.enterContext(patch.object(composition, "_active_provider", None))
        db.init_db()
        with db.get_connection() as conn:
            self.person_id = conn.execute("INSERT INTO people(vk_id, full_name) VALUES (101, 'Synthetic person')").lastrowid
        self.data = person_detail(self.person_id)
        self.fake = FakeProvider()

    def count(self):
        with db.get_connection() as conn:
            return conn.execute("SELECT COUNT(*) FROM ai_insights").fetchone()[0]


class InsightTests(InsightFixture):
    def test_llm_port_001_fake_substitution_and_context_scope(self):
        self.data["person"]["profile_url"] = "PRIVATE not needed"
        self.data["insights"] = ["PRIVATE old output"]
        self.data["message_stats"] = [{"incoming_count": 3}, {"incoming_count": 999}]
        self.data["events"] = [{"event_type": "synthetic", "event_date": str(i), "details": "fixture"} for i in range(12)]
        result = AIInsightService(self.fake).generate(self.data)
        self.assertEqual(result, {**VALID, "model": "model-a"})
        self.assertEqual(self.fake.list_calls, 1)
        request = self.fake.requests[0]
        self.assertEqual(request.temperature, 0.2)
        self.assertEqual(request.messages[0].role, "system")
        self.assertNotIn("PRIVATE", request.messages[1].content)
        source = json.loads(request.messages[1].content.split("Данные:\n", 1)[1])
        self.assertEqual(source, {
            "person": "Synthetic person", "period_start": None, "period_end": None,
            "incoming_count": 3, "outgoing_count": 0, "active_days": 0,
            "initiated_by_person": 0, "initiated_by_me": 0, "median_reply_minutes": None,
            "relationship_events": self.data["events"][:10],
        })
        self.assertEqual(self.count(), 0)

    def test_llm_port_007_valid_insight_persisted(self):
        result = AIInsightService(self.fake, model=" selected ", temperature="0.4").create(self.person_id, self.data)
        self.assertEqual(result, {"id": 1, **VALID, "model": "selected"})
        self.assertEqual(self.fake.list_calls, 0)
        self.assertEqual(self.fake.requests[0].temperature, 0.4)
        with db.get_connection() as conn:
            row = conn.execute("SELECT * FROM ai_insights").fetchone()
        self.assertEqual(row["person_id"], self.person_id)
        self.assertEqual(row["status"], VALID["status"])
        self.assertEqual(json.loads(row["evidence_json"]), VALID["evidence"])
        self.assertEqual(json.loads(row["cautions_json"]), [])
        self.assertEqual(self.count(), 1)

    def reject(self, content):
        self.fake.content = content
        before = self.count()
        with self.assertRaises(InsightValidationError):
            AIInsightService(self.fake).create(self.person_id, self.data)
        self.assertEqual(self.count(), before)

    def test_llm_port_008_invalid_json_not_persisted(self):
        self.reject("PRIVATE not JSON")
        self.reject("[]")
        self.reject("null")

    def test_llm_port_009_required_fields_not_persisted(self):
        for missing in VALID:
            with self.subTest(missing=missing):
                self.reject(json.dumps({key: value for key, value in VALID.items() if key != missing}))

    def test_llm_port_010_enums_ranges_types_and_extra_fields(self):
        cases = [("status", "invented"), ("status", []), ("confidence", -0.1), ("confidence", 1.1),
                 ("confidence", True), ("confidence", "0.5"), ("confidence", float("nan")),
                 ("confidence", float("inf")), ("summary", 1), ("evidence", "text"),
                 ("evidence", [1]), ("cautions", [None]), ("cautions", {}), ("extra", "value")]
        for key, value in cases:
            with self.subTest(key=key, value=value):
                self.reject(json.dumps({**VALID, key: value}))
        for status in ("strengthening", "stable", "weakening", "insufficient_data"):
            for confidence in (0, 1):
                self.fake.content = json.dumps({**VALID, "status": status, "confidence": confidence})
                AIInsightService(self.fake).create(self.person_id, self.data)
        self.assertEqual(self.count(), 8)

    def test_no_models_or_provider_error_does_not_persist(self):
        self.fake.models = []
        with self.assertRaises(ProviderUnavailableError):
            AIInsightService(self.fake).create(self.person_id, self.data)
        self.assertEqual(self.fake.requests, [])
        self.fake.error = ProviderTimeoutError("Provider request timed out")
        with self.assertRaises(ProviderTimeoutError):
            AIInsightService(self.fake, model="chosen").create(self.person_id, self.data)
        self.assertEqual(len(self.fake.requests), 1)
        self.assertEqual(self.count(), 0)

    def test_compatibility_store_also_validates_before_sql(self):
        with self.assertRaises(InsightValidationError):
            store_insight(self.person_id, {**VALID, "confidence": 4, "model": "chosen"})
        self.assertEqual(self.count(), 0)

    def test_composition_uses_existing_settings(self):
        save_settings({"lmstudio_base_url": "http://provider.invalid/v1/", "lmstudio_model": "chosen", "lmstudio_temperature": "0.6"})
        provider = composition.get_provider()
        self.assertIsInstance(provider, ResilientLLMProvider)
        self.assertIsInstance(provider.provider, LMStudioProvider)
        self.assertEqual(provider.provider.base_url, "http://provider.invalid/v1")
        with patch.object(composition, "get_provider", return_value=self.fake):
            composition.get_insight_service().create(self.person_id, self.data)
        self.assertEqual(self.fake.requests[0].model, "chosen")
        self.assertEqual(self.fake.requests[0].temperature, 0.6)


class APITests(InsightFixture):
    def setUp(self):
        super().setUp()
        # No TestClient context manager: do not run production startup/seed.
        self.client = TestClient(main.app)
        self.addCleanup(self.client.close)

    def test_llm_port_011_models_api_through_composition(self):
        # Real composition/adapter, fake HTTP only.
        original = composition.LMStudioProvider
        transport = httpx.MockTransport(lambda request: httpx.Response(200, json={"data": [MODEL]}))
        with patch.object(composition, "LMStudioProvider", side_effect=lambda url: original(url, transport=transport)):
            response = self.client.get("/api/lmstudio/models")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [MODEL])

    def test_connection_test_api_success_and_failure(self):
        with patch.object(main, "get_provider", return_value=self.fake):
            response = self.client.post("/api/lmstudio/test")
            self.assertEqual(response.json(), {"ok": True, "models_count": 1, "models": ["model-a"]})
            self.fake.error = ProviderUnavailableError("Provider is unavailable")
            for method, url in (("GET", "/api/lmstudio/models"), ("POST", "/api/lmstudio/test")):
                response = self.client.request(method, url)
                self.assertEqual(response.status_code, 503)
                self.assertEqual(set(response.json()), {"detail"})

    def test_llm_port_012_insight_api_through_fake_composition(self):
        with patch.object(composition, "get_provider", return_value=self.fake):
            response = self.client.post(f"/api/people/{self.person_id}/insight")
            missing = self.client.post("/api/people/99999/insight")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"id": 1, **VALID, "model": "model-a"})
        self.assertEqual(self.count(), 1)
        self.assertEqual(missing.status_code, 404)
        self.assertEqual(missing.json(), {"detail": "Person not found"})
        self.assertEqual(len(self.fake.requests), 1)

    def test_invalid_output_and_settings_return_controlled_503(self):
        self.fake.content = "PRIVATE invalid model response"
        with patch.object(composition, "get_provider", return_value=self.fake):
            response = self.client.post(f"/api/people/{self.person_id}/insight")
            self.assertEqual(response.status_code, 503)
            self.assertNotIn("PRIVATE", response.text)
            save_settings({"lmstudio_temperature": "PRIVATE invalid setting"})
            response = self.client.post(f"/api/people/{self.person_id}/insight")
            self.assertEqual(response.status_code, 503)
            self.assertNotIn("PRIVATE", response.text)
        self.assertEqual(self.count(), 0)

    def test_llm_port_013_settings_regression(self):
        response = self.client.get("/api/settings")
        self.assertEqual(response.json(), {"lmstudio_base_url": "http://127.0.0.1:1234/v1",
                                          "lmstudio_model": "", "lmstudio_temperature": "0.2"})
        response = self.client.put("/api/settings", json={"lmstudio_model": "chosen", "lmstudio_temperature": 0.5,
                                                        "llm_provider": "ignored", "unknown": "ignored"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"lmstudio_base_url": "http://127.0.0.1:1234/v1",
                                          "lmstudio_model": "chosen", "lmstudio_temperature": "0.5"})


class ArchitectureTests(NetworkBlockedTests):
    def test_llm_port_014_dependency_fitness(self):
        root = Path(__file__).resolve().parents[1]
        for name, forbidden in (
            ("app/ai/service.py", {"httpx", "providers", "composition", "lmstudio", "fastapi"}),
            ("app/ai/providers/lmstudio.py", {"fastapi", "services", "service", "db", "settings"}),
            ("app/ai/provider.py", {"httpx", "providers", "lmstudio", "fastapi"}),
            ("app/main.py", {"lmstudio", "httpx"}),
        ):
            tree = ast.parse((root / name).read_text(encoding="utf-8"))
            modules = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    modules.extend(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom):
                    modules.append(node.module or "")
            self.assertFalse(forbidden & set(".".join(modules).split(".")), (name, modules))
        self.assertNotIn("LMStudioProvider", (root / "app/ai/service.py").read_text(encoding="utf-8"))
