from __future__ import annotations

import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from app import db, importers, migrations
from app.services import list_collected_dialogs, save_collector_preview


LEGACY_DDL = """
CREATE TABLE collector_dialogs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dialog_key TEXT NOT NULL,
    peer_id INTEGER,
    full_name TEXT NOT NULL,
    dialog_url TEXT,
    collected_at TEXT NOT NULL,
    UNIQUE(dialog_key, collected_at)
)
"""
LEGACY_FIELDS = "id, dialog_key, peer_id, full_name, dialog_url, collected_at"
LEGACY_ROWS = [
    (3, "synthetic-a", 101, "Синтетический А", "https://example.invalid/a", "2099-01-01T00:00:00"),
    (17, "synthetic-b", None, "  Synthetic B  ", None, "2099-01-01T00:00:00"),
    (42, "synthetic-a", -7, "", "", "2099-01-02T00:00:00"),
]
EXPECTED_FIELDS = {
    "id", "dialog_key", "peer_id", "full_name", "dialog_url", "collected_at",
    "preview", "date_label", "unread", "unread_count", "outgoing", "avatar_url", "verified",
}


class MigrationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.path = self.root / "test.db"
        self.backups = self.root / "backups"
        self.enterContext(patch.multiple(
            db, DB_PATH=self.path, DATA_DIR=self.root,
            IMPORT_DIR=self.root / "imports", BACKUP_DIR=self.backups,
        ))
        self.enterContext(patch.object(importers, "IMPORT_DIR", self.root / "imports"))

    def create_legacy(self):
        with closing(sqlite3.connect(self.path)) as conn, conn:
            conn.execute(LEGACY_DDL)
            conn.executemany("INSERT INTO collector_dialogs VALUES (?, ?, ?, ?, ?, ?)", LEGACY_ROWS)
            conn.execute("CREATE INDEX retained_name_index ON collector_dialogs(full_name)")

    def rows(self, path=None):
        with closing(sqlite3.connect(path or self.path)) as conn:
            return conn.execute(f"SELECT {LEGACY_FIELDS} FROM collector_dialogs ORDER BY id").fetchall()

    def snapshot(self):
        with closing(sqlite3.connect(self.path)) as conn:
            return (conn.execute("PRAGMA user_version").fetchone()[0], list(conn.iterdump()))

    def backup_files(self):
        return list(self.backups.glob("*.db"))

    def assert_current(self):
        with closing(sqlite3.connect(self.path)) as conn:
            self.assertEqual(conn.execute("PRAGMA user_version").fetchone()[0], migrations.CURRENT_SCHEMA_VERSION)
            columns = {row[1]: row for row in conn.execute("PRAGMA table_info(collector_dialogs)")}
            self.assertEqual(set(columns), EXPECTED_FIELDS)
            for field in ("unread", "outgoing", "verified"):
                self.assertEqual(columns[field][2:6], ("INTEGER", 1, "0", 0))
            for field in ("preview", "date_label", "avatar_url"):
                self.assertEqual(columns[field][2:6], ("TEXT", 0, None, 0))
            self.assertEqual(columns["unread_count"][2:6], ("INTEGER", 0, None, 0))
            self.assertEqual(conn.execute("PRAGMA foreign_key_check").fetchall(), [])
            tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            self.assertTrue({"people", "relation_snapshots", "relation_events", "message_stats",
                             "app_settings", "ai_insights", "collector_dialogs", "import_jobs"} <= tables)
            self.assertEqual(dict(conn.execute("SELECT key, value FROM app_settings")), {
                "lmstudio_base_url": "http://127.0.0.1:1234/v1",
                "lmstudio_model": "", "lmstudio_temperature": "0.2",
            })

    def test_mig_001_fresh_database(self):
        self.assertFalse(self.path.exists())
        db.init_db()
        self.assert_current()
        self.assertEqual(self.backup_files(), [])

    def test_mig_002_legacy_preservation_and_backup(self):
        self.create_legacy()
        before = self.snapshot()
        db.init_db()
        self.assert_current()
        self.assertEqual(self.rows(), LEGACY_ROWS)
        backups = self.backup_files()
        self.assertEqual(len(backups), 1)
        self.assertTrue(backups[0].name.startswith("schema-v0-to-v2-"))
        self.assertEqual(self.rows(backups[0]), LEGACY_ROWS)
        with closing(sqlite3.connect(backups[0])) as conn:
            self.assertEqual((conn.execute("PRAGMA user_version").fetchone()[0], list(conn.iterdump())), before)
            self.assertEqual(len(conn.execute("PRAGMA table_info(collector_dialogs)").fetchall()), 6)
        with closing(sqlite3.connect(self.path)) as conn:
            values = conn.execute("SELECT preview, date_label, unread, unread_count, outgoing, avatar_url, verified FROM collector_dialogs").fetchall()
            self.assertEqual(values, [(None, None, 0, None, 0, None, 0)] * 3)
            self.assertIsNotNone(conn.execute("SELECT 1 FROM sqlite_master WHERE name='retained_name_index'").fetchone())
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute("INSERT INTO collector_dialogs(dialog_key, full_name, collected_at) VALUES (?, ?, ?)",
                             (LEGACY_ROWS[0][1], "Duplicate", LEGACY_ROWS[0][5]))

    def test_mig_003_real_runtime_write_after_migration(self):
        self.create_legacy()
        db.init_db()
        item = {"dialog_key": "synthetic-new", "peer_id": 103, "full_name": "Synthetic new",
                "dialog_url": "https://example.invalid/new", "preview": "Synthetic preview",
                "date_label": "2h", "unread": True, "unread_count": 4, "outgoing": True,
                "avatar_url": "https://example.invalid/avatar", "verified": True}
        payload = {"kind": "dialogs", "collected_at": "2099-02-01T00:00:00", "items": [item]}
        self.assertEqual(save_collector_preview(payload)["saved"], 1)
        save_collector_preview(payload)  # Unique key still prevents duplicates.
        records = list_collected_dialogs()
        self.assertEqual(len(records), 1)
        for key, value in item.items():
            self.assertEqual(records[0][key], value)
        self.assertGreater(records[0]["id"], 42)
        self.assertEqual(records[0]["collected_at"], payload["collected_at"])
        self.assertEqual(self.rows()[:3], LEGACY_ROWS)
        self.assertEqual(len(self.rows()), 4)

    def test_mig_004_three_initializations_are_idempotent(self):
        self.create_legacy()
        with patch.object(migrations, "backup_database", wraps=migrations.backup_database) as backup:
            db.init_db()
            state = self.snapshot()
            statements = []
            real_connect = sqlite3.connect

            def traced_connect(*args, **kwargs):
                conn = real_connect(*args, **kwargs)
                conn.set_trace_callback(statements.append)
                return conn

            with patch.object(sqlite3, "connect", side_effect=traced_connect):
                db.init_db()
                db.init_db()
            self.assertFalse(any(sql.lstrip().upper().startswith("ALTER") for sql in statements))
            self.assertEqual(backup.call_count, 1)
        # iterdump contains unchanged sqlite_sequence, schema, settings and rows.
        self.assertEqual(self.snapshot(), state)
        self.assertEqual(len(self.backup_files()), 1)
        self.assertEqual(self.rows(), LEGACY_ROWS)

    def test_mig_005_ddl_failure_rolls_back_and_surfaces(self):
        self.create_legacy()
        before = self.snapshot()

        def fail_validation(conn):
            self.assertEqual(len(conn.execute("PRAGMA table_info(collector_dialogs)").fetchall()), 13)
            self.assertEqual(conn.execute("PRAGMA user_version").fetchone()[0], 0)
            raise migrations.SchemaMigrationError("Synthetic validation failure")

        with patch.object(migrations, "validate_schema", side_effect=fail_validation):
            with self.assertRaisesRegex(migrations.SchemaMigrationError, "Synthetic validation failure"):
                db.init_db()
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.rows(), LEGACY_ROWS)
        self.assertEqual(len(self.backup_files()), 1)
        first_backup = self.backup_files()[0]
        contents = first_backup.read_bytes()
        db.init_db()  # Retry is safe, retains previous recovery copy.
        self.assertEqual(len(self.backup_files()), 2)
        self.assertEqual(first_backup.read_bytes(), contents)
        self.assert_current()

    def test_mig_006_future_version_no_mutation(self):
        self.create_legacy()
        with closing(sqlite3.connect(self.path)) as conn:
            conn.execute("PRAGMA user_version = 99")
        before = self.path.read_bytes()
        with self.assertRaisesRegex(migrations.SchemaMigrationError, "version 99 is newer than supported 2"):
            db.init_db()
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(self.backup_files(), [])

    def test_mig_007_fresh_repeat_startup_preserves_settings(self):
        db.init_db()
        with db.get_connection() as conn:
            conn.execute("UPDATE app_settings SET value='custom-model' WHERE key='lmstudio_model'")
        before = self.snapshot()
        db.init_db()
        db.init_db()
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.backup_files(), [])

    def test_backup_failure_blocks_all_schema_mutation(self):
        self.create_legacy()
        before = self.path.read_bytes()
        with patch.object(Path, "open", side_effect=PermissionError("Synthetic backup permission failure")):
            with self.assertRaisesRegex(migrations.SchemaMigrationError, "backup failed; database unchanged"):
                db.init_db()
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(self.backup_files(), [])

    def test_unversioned_current_is_backed_up_before_version_adoption(self):
        db.init_db()
        with closing(sqlite3.connect(self.path)) as conn:
            conn.execute("PRAGMA user_version = 0")
        db.init_db()
        db.init_db()
        self.assert_current()
        self.assertEqual(len(self.backup_files()), 1)
        with closing(sqlite3.connect(self.backup_files()[0])) as conn:
            self.assertEqual(conn.execute("PRAGMA user_version").fetchone()[0], 0)
            self.assertEqual(len(conn.execute("PRAGMA table_info(collector_dialogs)").fetchall()), 13)

    def test_unknown_unversioned_schema_is_not_fresh(self):
        with closing(sqlite3.connect(self.path)) as conn:
            conn.execute("CREATE TABLE sqliteX_unknown_data (id INTEGER)")
        before = self.path.read_bytes()
        with self.assertRaisesRegex(migrations.SchemaMigrationError, "Unsupported unversioned"):
            db.init_db()
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(self.backup_files(), [])

    def test_current_schema_drift_is_not_silently_repaired(self):
        db.init_db()
        with closing(sqlite3.connect(self.path)) as conn:
            conn.execute("DROP TABLE import_jobs")
        before = self.snapshot()
        with self.assertRaisesRegex(migrations.SchemaMigrationError, "missing required tables"):
            db.init_db()
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.backup_files(), [])

    def test_foreign_key_failure_rolls_back_upgrade(self):
        db.init_db()
        with closing(sqlite3.connect(self.path)) as conn, conn:
            conn.execute("PRAGMA user_version = 0")
            conn.execute("INSERT INTO relation_events(person_id, event_type, event_date) VALUES (999, 'synthetic', '2099-01-01')")
        before = self.snapshot()
        with self.assertRaisesRegex(migrations.SchemaMigrationError, "foreign key validation failed"):
            db.init_db()
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(len(self.backup_files()), 1)

    def test_default_settings_failure_rolls_back_version_and_ddl(self):
        self.create_legacy()
        with closing(sqlite3.connect(self.path)) as conn:
            conn.execute("CREATE TABLE app_settings(key TEXT PRIMARY KEY, value TEXT NOT NULL, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)")
            conn.execute("CREATE TRIGGER reject_settings BEFORE INSERT ON app_settings BEGIN SELECT RAISE(ABORT, 'Synthetic defaults failure'); END")
        before = self.snapshot()
        with self.assertRaisesRegex(sqlite3.IntegrityError, "Synthetic defaults failure"):
            db.init_db()
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.rows(), LEGACY_ROWS)

    def test_backup_contains_committed_wal_rows(self):
        self.create_legacy()
        with closing(sqlite3.connect(self.path)) as writer:
            self.assertEqual(writer.execute("PRAGMA journal_mode=WAL").fetchone()[0], "wal")
            writer.execute("PRAGMA wal_autocheckpoint=0")
            writer.execute("UPDATE collector_dialogs SET full_name='Synthetic WAL row' WHERE id=3")
            writer.commit()
            self.assertGreater(Path(str(self.path) + "-wal").stat().st_size, 0)
            before = self.rows()
            db.init_db()
            self.assertEqual(self.rows(self.backup_files()[0]), before)
            self.assertEqual(self.rows(), before)
        self.assert_current()


if __name__ == "__main__":
    unittest.main()
