from pathlib import Path
import tempfile, unittest
from unittest.mock import patch
class V04Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        from app import db
        root = Path(self.tmp.name)
        self.p = patch.multiple(db, DB_PATH=root / "t.db", DATA_DIR=root,
                                IMPORT_DIR=root / "imports", BACKUP_DIR=root / "backups")
        self.p.start()
        from app.db import init_db;init_db()
    def tearDown(self):self.p.stop();self.tmp.cleanup()
    def test_dialog_metadata(self):
        from app.services import save_collector_preview,list_collected_dialogs
        save_collector_preview({"kind":"dialogs","collected_at":"2099-04-01T10:00:00","items":[{"dialog_key":"convo_123","peer_id":123,"full_name":"Тест","dialog_url":"https://vk.com/im?sel=123","preview":"Привет","date_label":"2ч","unread":True,"unread_count":3,"outgoing":False,"avatar_url":"","verified":True}]})
        r=list_collected_dialogs()[0];self.assertEqual(r["preview"],"Привет");self.assertEqual(r["unread_count"],3)
    def test_marker(self):
        from app import collector
        self.assertIn("vk_reforged_exact_scroll_ancestor_v4",Path(collector.__file__).read_text("utf-8"))
