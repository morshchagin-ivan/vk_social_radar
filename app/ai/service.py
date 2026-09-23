from __future__ import annotations

import json
import math
from typing import Any

from ..db import get_connection
from .contracts import GenerationRequest, Message, ProviderUnavailableError, StructuredOutput
from .provider import LLMProvider


class InsightValidationError(ValueError):
    pass


class AIConfigurationError(ValueError):
    pass


def validate_insight(value: Any) -> dict[str, Any]:
    fields = {"status", "confidence", "summary", "evidence", "cautions"}
    if not isinstance(value, dict) or set(value) != fields:
        raise InsightValidationError("Insight must contain exactly the required fields")
    if not isinstance(value["status"], str) or value["status"] not in {
        "strengthening", "stable", "weakening", "insufficient_data",
    }:
        raise InsightValidationError("Invalid insight status")
    confidence = value["confidence"]
    if type(confidence) not in (int, float) or not 0 <= confidence <= 1:
        raise InsightValidationError("Insight confidence must be a number between 0 and 1")
    if not isinstance(value["summary"], str):
        raise InsightValidationError("Insight summary must be a string")
    for field in ("evidence", "cautions"):
        if not isinstance(value[field], list) or any(not isinstance(item, str) for item in value[field]):
            raise InsightValidationError("Insight evidence and cautions must be arrays of strings")
    return value


class AIInsightService:
    def __init__(self, provider: LLMProvider, *, model: str = "", temperature: str = "0.2"):
        self.provider = provider
        self.model = model.strip()
        try:
            self.temperature = float(temperature)
        except (TypeError, ValueError):
            raise AIConfigurationError("Invalid AI temperature setting") from None
        if not math.isfinite(self.temperature):
            raise AIConfigurationError("Invalid AI temperature setting")

    def create(self, person_id: int, person_data: dict[str, Any]) -> dict[str, Any]:
        return store_insight(person_id, self.generate(person_data))

    def generate(self, person_data: dict[str, Any]) -> dict[str, Any]:
        model = self.model
        if not model:
            models = self.provider.list_models()
            if not models:
                raise ProviderUnavailableError("No models available from provider")
            model = models[0].id
        stats = (person_data.get("message_stats") or [{}])[0]
        events = person_data.get("events") or []
        person = person_data["person"]
        source = {
            "person": person["full_name"],
            "period_start": stats.get("period_start"),
            "period_end": stats.get("period_end"),
            "incoming_count": stats.get("incoming_count", 0),
            "outgoing_count": stats.get("outgoing_count", 0),
            "active_days": stats.get("active_days", 0),
            "initiated_by_person": stats.get("initiated_by_person", 0),
            "initiated_by_me": stats.get("initiated_by_me", 0),
            "median_reply_minutes": stats.get("median_reply_minutes"),
            "relationship_events": events[:10],
        }
        schema = {
            "type": "object",
            "properties": {
                "status": {"type": "string", "enum": [
                    "strengthening", "stable", "weakening", "insufficient_data",
                ]},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                "summary": {"type": "string"},
                "evidence": {"type": "array", "items": {"type": "string"}},
                "cautions": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["status", "confidence", "summary", "evidence", "cautions"],
            "additionalProperties": False,
        }
        request = GenerationRequest(
            model=model,
            messages=(
                Message("system", (
                    "Ты аналитик социальных взаимодействий. Анализируй только предоставленные "
                    "метрики. Не приписывай человеку эмоции, намерения, романтический интерес, "
                    "слежку или психологические состояния. Пиши по-русски, кратко и доказательно."
                )),
                Message("user", (
                    "Интерпретируй наблюдаемую динамику общения. Если данных недостаточно, "
                    "скажи это прямо. Данные:\n" + json.dumps(source, ensure_ascii=False)
                )),
            ),
            temperature=self.temperature,
            structured_output=StructuredOutput("social_interaction_insight", schema),
        )
        result = self.provider.generate(request)
        try:
            value = json.loads(result.content)
        except (ValueError, TypeError, RecursionError):
            raise InsightValidationError("Provider output is not valid insight JSON") from None
        insight = validate_insight(value)
        # Preserve the existing API/persistence convention: selected model id.
        return {**insight, "model": model}


def store_insight(person_id: int, insight: dict[str, Any]) -> dict[str, Any]:
    validate_insight({key: value for key, value in insight.items() if key != "model"})
    if not isinstance(insight.get("model"), str) or not insight["model"].strip():
        raise InsightValidationError("Invalid insight model")
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO ai_insights(
                person_id, model, status, confidence, summary, evidence_json, cautions_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                person_id,
                insight["model"],
                insight["status"],
                float(insight["confidence"]),
                insight["summary"],
                json.dumps(insight["evidence"], ensure_ascii=False),
                json.dumps(insight["cautions"], ensure_ascii=False),
            ),
        )
    return {"id": cursor.lastrowid, **insight}
