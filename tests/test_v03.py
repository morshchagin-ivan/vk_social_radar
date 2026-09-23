from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class V03Tests(unittest.TestCase):
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

    def test_collector_profile_dir_is_outside_package_payload(self):
        from app.collector import PROFILE_DIR
        self.assertEqual(PROFILE_DIR.name, "vk_browser_profile")
        self.assertIn("data", PROFILE_DIR.parts)

    def test_save_friend_preview(self):
        from app.services import save_collector_preview
        result = save_collector_preview({
            "kind": "friends",
            "collected_at": "2099-03-01T12:00:00",
            "items": [
                {
                    "vk_id": 88001,
                    "screen_name": None,
                    "full_name": "Тест Коллектор",
                    "profile_url": "https://vk.com/id88001",
                }
            ],
        })
        self.assertEqual(result["count"], 1)

    def test_save_dialog_preview(self):
        from app.services import save_collector_preview
        result = save_collector_preview({
            "kind": "dialogs",
            "collected_at": "2099-03-01T12:00:00",
            "items": [
                {
                    "dialog_key": "88001",
                    "peer_id": 88001,
                    "full_name": "Тестовый Диалог",
                    "dialog_url": "https://vk.com/im?sel=88001",
                }
            ],
        })
        self.assertEqual(result["saved"], 1)


if __name__ == "__main__":
    unittest.main()
