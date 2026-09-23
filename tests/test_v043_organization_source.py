from __future__ import annotations

from pathlib import Path

from app.collector import classify_public_vk_source


COLLECTOR_TEXT = Path("app/collector.py").read_text(encoding="utf-8")
MAIN_TEXT = Path("app/main.py").read_text(encoding="utf-8")


def test_classifies_vk_com_public_as_organization_community() -> None:
    row = classify_public_vk_source("https://vk.com/public123")
    assert row["source_type"] == "ORGANIZATION_COMMUNITY"
    assert row["eligible_for_collection"] is True


def test_classifies_vk_ru_club_and_normalizes_host() -> None:
    row = classify_public_vk_source("https://vk.ru/club123")
    assert row["source_type"] == "ORGANIZATION_COMMUNITY"
    assert row["normalized_url"] == "https://vk.com/club123"


def test_person_profile_is_not_eligible_for_organization_collection() -> None:
    row = classify_public_vk_source("https://vk.com/id123")
    assert row["source_type"] == "PERSON_PROFILE"
    assert row["eligible_for_collection"] is False


def test_post_is_not_eligible_for_organization_collection() -> None:
    row = classify_public_vk_source("https://vk.com/wall-1_2")
    assert row["source_type"] == "POST"
    assert row["eligible_for_collection"] is False


def test_existing_safe_collector_owns_contract() -> None:
    assert "class SafeVKCollector" in COLLECTOR_TEXT
    assert "collect_public_organization_source" in COLLECTOR_TEXT
    assert "launch_persistent_context" in COLLECTOR_TEXT


def test_organization_source_api_is_exposed() -> None:
    assert "/api/collector/organization-source" in MAIN_TEXT
    assert "collector.collect_public_organization_source" in MAIN_TEXT


def test_contract_excludes_dialogs_and_private_messages() -> None:
    assert '"dialogs_excluded": True' in COLLECTOR_TEXT
    assert '"private_messages_excluded": True' in COLLECTOR_TEXT


def test_contract_preserves_membership_not_employment_policy() -> None:
    assert '"membership_is_employment_proof": False' in COLLECTOR_TEXT

