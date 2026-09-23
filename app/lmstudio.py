"""Compatibility imports for legacy callers; production API uses app.ai directly."""
from typing import Any

from .ai.composition import get_insight_service, get_provider
from .ai.service import store_insight
from .ai.settings import get_settings, save_settings


def list_models() -> list[dict[str, Any]]:
    return [model.as_dict() for model in get_provider().list_models()]


def test_connection() -> dict[str, Any]:
    models = get_provider().list_models()
    return {"ok": True, "models_count": len(models), "models": [model.id for model in models]}


def generate_person_insight(person_data: dict[str, Any]) -> dict[str, Any]:
    return get_insight_service().generate(person_data)
