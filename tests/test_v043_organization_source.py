from __future__ import annotations

from pathlib import Path
import unittest

from app.collector import classify_public_vk_source


ROOT = Path(__file__).resolve().parents[1]
COLLECTOR_TEXT = (ROOT / "app/collector.py").read_text(encoding="utf-8")
MAIN_TEXT = (ROOT / "app/main.py").read_text(encoding="utf-8")


class OrganizationSourceTests(unittest.TestCase):
    def test_classifies_vk_com_public_as_organization_community(self) -> None:
        row = classify_public_vk_source("https://vk.com/public123")
        self.assertEqual(row["source_type"], "ORGANIZATION_COMMUNITY")
        self.assertIs(row["eligible_for_collection"], True)


    def test_classifies_vk_ru_club_and_normalizes_host(self) -> None:
        row = classify_public_vk_source("https://vk.ru/club123")
        self.assertEqual(row["source_type"], "ORGANIZATION_COMMUNITY")
        self.assertEqual(row["normalized_url"], "https://vk.com/club123")


    def test_person_profile_is_not_eligible_for_organization_collection(self) -> None:
        row = classify_public_vk_source("https://vk.com/id123")
        self.assertEqual(row["source_type"], "PERSON_PROFILE")
        self.assertIs(row["eligible_for_collection"], False)


    def test_post_is_not_eligible_for_organization_collection(self) -> None:
        row = classify_public_vk_source("https://vk.com/wall-1_2")
        self.assertEqual(row["source_type"], "POST")
        self.assertIs(row["eligible_for_collection"], False)


    def test_existing_safe_collector_owns_contract(self) -> None:
        self.assertIn("class SafeVKCollector", COLLECTOR_TEXT)
        self.assertIn("collect_public_organization_source", COLLECTOR_TEXT)
        self.assertIn("launch_persistent_context", COLLECTOR_TEXT)


    def test_organization_source_api_is_exposed(self) -> None:
        self.assertIn("/api/collector/organization-source", MAIN_TEXT)
        self.assertIn("collector.collect_public_organization_source", MAIN_TEXT)


    def test_contract_excludes_dialogs_and_private_messages(self) -> None:
        self.assertIn('"dialogs_excluded": True', COLLECTOR_TEXT)
        self.assertIn('"private_messages_excluded": True', COLLECTOR_TEXT)


    def test_contract_preserves_membership_not_employment_policy(self) -> None:
        self.assertIn('"membership_is_employment_proof": False', COLLECTOR_TEXT)
