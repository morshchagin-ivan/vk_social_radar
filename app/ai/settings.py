from __future__ import annotations

from typing import Any

from ..db import get_connection
from ..privacy import PrivacyPolicyError, local_llm_url


def get_settings() -> dict[str, str]:
    with get_connection() as conn:
        rows = conn.execute("SELECT key, value FROM app_settings").fetchall()
    settings = {row["key"]: row["value"] for row in rows}
    if "lmstudio_base_url" in settings:
        try:
            settings["lmstudio_base_url"] = local_llm_url(settings["lmstudio_base_url"])
        except PrivacyPolicyError:
            # Do not expose legacy URL credentials; do not silently rewrite the DB
            # or fall back to another provider. Empty configuration fails closed.
            settings["lmstudio_base_url"] = ""
    return settings


def save_settings(settings: dict[str, Any]) -> dict[str, str]:
    allowed = {"lmstudio_base_url", "lmstudio_model", "lmstudio_temperature"}
    settings = dict(settings)
    if "lmstudio_base_url" in settings:
        settings["lmstudio_base_url"] = local_llm_url(settings["lmstudio_base_url"])
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
