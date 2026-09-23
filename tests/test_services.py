from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class ServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test.db"

        from app import db

        root = Path(self.temp_dir.name)
        self.db_patch = patch.multiple(
            db, DB_PATH=self.db_path, DATA_DIR=root,
            IMPORT_DIR=root / "imports", BACKUP_DIR=root / "backups",
        )
        self.db_patch.start()

        from app.db import init_db
        from app.seed import seed_demo_data

        init_db()
        seed_demo_data()

    def tearDown(self) -> None:
        self.db_patch.stop()
        self.temp_dir.cleanup()

    def test_dashboard_has_seeded_data(self) -> None:
        from app.services import dashboard

        data = dashboard()
        self.assertGreaterEqual(data["friends"]["current"], 1)
        self.assertGreater(data["message_total"], 0)
        self.assertTrue(data["changes"])

    def test_people_have_message_totals(self) -> None:
        from app.services import list_people

        people = list_people()
        self.assertTrue(people)
        self.assertIn("total_messages", people[0])

    def test_import_snapshot_detects_change(self) -> None:
        from app.services import import_snapshot

        result = import_snapshot(
            {
                "relation_type": "friend",
                "snapshot_date": "2099-01-01",
                "people": [
                    {
                        "vk_id": 101,
                        "full_name": "Анна Петрова",
                        "profile_url": "https://vk.com/id101",
                    }
                ],
            }
        )
        self.assertEqual(result["count"], 1)
        self.assertGreaterEqual(result["removed"], 1)


if __name__ == "__main__":
    unittest.main()
