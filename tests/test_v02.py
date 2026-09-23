from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class V02Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        from app import db
        self.patch = patch.object(db, "DB_PATH", Path(self.tmp.name) / "test.db")
        self.patch.start()
        from app.db import init_db
        from app.seed import seed_demo_data
        init_db()
        seed_demo_data()

    def tearDown(self):
        self.patch.stop()
        self.tmp.cleanup()

    def test_settings_defaults(self):
        from app.lmstudio import get_settings
        settings = get_settings()
        self.assertIn("lmstudio_base_url", settings)

    def test_message_stats_upsert(self):
        from app.services import import_message_stats, message_leaderboard
        row = {
            "vk_id": 999, "full_name": "Тестовый Пользователь",
            "profile_url": "https://vk.com/id999", "avatar_url": "",
            "period_start": "2026-07-01", "period_end": "2026-07-31",
            "incoming_count": 10, "outgoing_count": 20, "active_days": 4,
            "initiated_by_person": 2, "initiated_by_me": 1,
            "median_reply_minutes": 15.0,
        }
        self.assertEqual(import_message_stats([row])["imported"], 1)
        match = [x for x in message_leaderboard() if x["full_name"] == "Тестовый Пользователь"]
        self.assertEqual(match[0]["total_messages"], 30)

    def test_csv_file_import(self):
        from app.importers import import_uploaded_file
        content = (
            "vk_id,full_name,profile_url\n"
            "701,Первый Контакт,https://vk.com/id701\n"
            "702,Второй Контакт,https://vk.com/id702\n"
        ).encode("utf-8")
        result = import_uploaded_file("friends.csv", content, "relations", "friend", "2099-02-01")
        self.assertEqual(result["count"], 2)


if __name__ == "__main__":
    unittest.main()
