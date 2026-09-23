from __future__ import annotations

from typing import Any

from ..db import get_connection


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
