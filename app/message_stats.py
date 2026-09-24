"""Validation shared by message-stat import and synthetic seed writers.

Periods use the existing YYYY-MM-DD format, without whitespace trimming.
Count strings retain CSV's integer/whitespace normalization; floats and bools
are not counts. Totals are derived, not a separately stored input field.
"""
from __future__ import annotations

import re
from datetime import date
from typing import Any


class MessageStatsValidationError(ValueError):
    """Safe field/category error: never includes the supplied row or value."""


def normalize_message_stats(raw: dict[str, Any]) -> dict[str, Any]:
    result = dict(raw)
    for field in ("period_start", "period_end"):
        value = raw.get(field)
        if not isinstance(value, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
            raise MessageStatsValidationError(f"{field}: expected calendar date YYYY-MM-DD")
        try:
            date.fromisoformat(value)
        except ValueError:
            raise MessageStatsValidationError(f"{field}: invalid calendar date") from None
    if result["period_end"] < result["period_start"]:
        raise MessageStatsValidationError("period_end: precedes period_start")

    for field in ("incoming_count", "outgoing_count", "active_days", "initiated_by_person", "initiated_by_me"):
        value = raw.get(field, 0)
        if isinstance(value, str) and re.fullmatch(r"[+-]?[0-9]+", value.strip()):
            try:
                value = int(value)
            except ValueError:
                raise MessageStatsValidationError(f"{field}: invalid integer representation") from None
        if type(value) is not int or value < 0:
            raise MessageStatsValidationError(f"{field}: expected non-negative integer")
        result[field] = value
    return result
