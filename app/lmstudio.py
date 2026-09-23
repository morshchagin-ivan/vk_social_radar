from __future__ import annotations

import json
from typing import Any

import httpx

from .db import get_connection


def get_settings() -> dict[str, str]:
    with get_connection() as conn:
        rows = conn.execute("SELECT key, value FROM app_settings").fetchall()
    return {row["key"]: row["value"] for row in rows}


def save_settings(settings: dict[str, Any]) -> dict[str, str]:
    allowed = {"lmstudio_base_url", "lmstudio_model", "lmstudio_temperature"}
    with get_connection() as conn:
        for key, value in settings.items():
            if key not in allowed:
                continue
            conn.execute(
                """
                INSERT INTO app_settings(key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET
                    value=excluded.value,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (key, str(value)),
            )
    return get_settings()


def _base_url() -> str:
    return get_settings().get("lmstudio_base_url", "http://127.0.0.1:1234/v1").rstrip("/")


def list_models() -> list[dict[str, Any]]:
    with httpx.Client(timeout=8.0) as client:
        response = client.get(f"{_base_url()}/models")
        response.raise_for_status()
        payload = response.json()
    return payload.get("data", [])


def test_connection() -> dict[str, Any]:
    models = list_models()
    return {
        "ok": True,
        "models_count": len(models),
        "models": [model.get("id") for model in models],
    }


def generate_person_insight(person_data: dict[str, Any]) -> dict[str, Any]:
    settings = get_settings()
    model = settings.get("lmstudio_model", "").strip()
    if not model:
        models = list_models()
        if not models:
            raise RuntimeError("В LM Studio нет доступных моделей")
        model = models[0]["id"]

    temperature = float(settings.get("lmstudio_temperature", "0.2"))
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
            "status": {
                "type": "string",
                "enum": ["strengthening", "stable", "weakening", "insufficient_data"],
            },
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "summary": {"type": "string"},
            "evidence": {"type": "array", "items": {"type": "string"}},
            "cautions": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["status", "confidence", "summary", "evidence", "cautions"],
        "additionalProperties": False,
    }

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Ты аналитик социальных взаимодействий. Анализируй только предоставленные "
                    "метрики. Не приписывай человеку эмоции, намерения, романтический интерес, "
                    "слежку или психологические состояния. Пиши по-русски, кратко и доказательно."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Интерпретируй наблюдаемую динамику общения. Если данных недостаточно, "
                    "скажи это прямо. Данные:\n" + json.dumps(source, ensure_ascii=False)
                ),
            },
        ],
        "temperature": temperature,
        "stream": False,
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "social_interaction_insight",
                "strict": True,
                "schema": schema,
            },
        },
    }

    with httpx.Client(timeout=120.0) as client:
        response = client.post(f"{_base_url()}/chat/completions", json=payload)
        response.raise_for_status()
        raw = response.json()

    content = raw["choices"][0]["message"]["content"]
    result = json.loads(content)
    result["model"] = model
    return result


def store_insight(person_id: int, insight: dict[str, Any]) -> dict[str, Any]:
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
