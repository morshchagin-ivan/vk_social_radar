from __future__ import annotations

import ast
import json
import sqlite3
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient

from app import db, importers, main, migrations, services, snapshot_schema, snapshots
from test_ai_provider import NetworkBlockedTests


def person(number, name=None):
    return {"vk_id": number, "full_name": name or f"Synthetic {number}",
            "profile_url": f"https://example.invalid/{number}", "avatar_url": "old-avatar"}


class SnapshotFixture(NetworkBlockedTests):
    def setUp(self):
        super().setUp()
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        self.enterContext(patch.multiple(db, DB_PATH=self.root / "test.db", DATA_DIR=self.root,
                                        IMPORT_DIR=self.root / "imports", BACKUP_DIR=self.root / "backups"))
        self.enterContext(patch.object(importers, "IMPORT_DIR", self.root / "imports"))

    def capture(self, numbers, at="2099-01-01T10:00:00+00:00", relation="friend", **extras):
        return services.import_snapshot({"people": [person(n) for n in numbers], "captured_at": at,
                                         "relation_type": relation, **extras})["snapshot_id"]

    def events(self):
        with db.get_connection() as conn:
            return [dict(r) for r in conn.execute("SELECT * FROM snapshot_events ORDER BY id")]

    def current(self, relation="friend"):
        with db.get_connection() as conn:
            return snapshots.latest(conn, relation)[0]["id"]


class SnapshotTests(SnapshotFixture):
    def setUp(self):
        super().setUp()
        db.init_db()

    def test_snp_001_same_day_distinct_and_snp_007_tie_order(self):
        a, b = self.capture([1]), self.capture([2])
        self.assertNotEqual(a, b)
        self.assertEqual(self.current(), b)
        self.assertEqual(snapshots.derive_events(b)["from_snapshot_id"], a)

    def test_snp_002_projection_immutable_and_evt_003_historical_display(self):
        a = self.capture([1])
        before = snapshots.read_snapshot(a)
        b = self.capture([], "2099-01-02")
        pid = before["people"][0]["person_id"]
        with db.get_connection() as conn:
            conn.execute("UPDATE people SET full_name='Changed',avatar_url='new' WHERE id=?", (pid,))
        self.assertEqual(snapshots.read_snapshot(a), before)
        self.assertEqual(services.list_changes()[0]["full_name"], "Synthetic 1")
        self.assertEqual(services.person_detail(pid)["events"][0]["from_snapshot_id"], a)
        self.assertEqual(services.person_detail(pid)["events"][0]["to_snapshot_id"], b)

    def test_snp_003_exact_membership_and_no_daily_union(self):
        self.capture([1, 2])
        b = self.capture([1], "2099-01-01T15:00:00Z")
        self.assertEqual([p["vk_id"] for p in snapshots.read_snapshot(b)["people"]], [1])
        self.assertEqual(services.dashboard()["friends"], {"current": 1, "added": 0, "removed": 1})

    def test_snp_004_empty_complete_and_evt_005_replay(self):
        a = self.capture([1, 2])
        b = self.capture([], "2099-01-02")
        row = snapshots.read_snapshot(b)
        self.assertEqual((row["status"], row["item_count"], row["people"]), ("COMPLETE", 0, []))
        for _ in range(3):
            self.assertEqual(len(snapshots.derive_events(b)["removed"]), 2)
        self.assertEqual(len(self.events()), 2)
        self.assertEqual(services.dashboard()["friends"], {"current": 0, "added": 0, "removed": 2})
        self.assertFalse(any(p["is_friend"] for p in services.list_people()))

    def test_snp_005_incomplete_failed_creating_do_not_replace_current(self):
        a = self.capture([1])
        for status, completeness in (("FAILED", "PARTIAL"), ("CREATING", "UNKNOWN"), ("INCOMPLETE", "UNKNOWN")):
            with self.subTest(status=status):
                sid = self.capture([2], "2099-02-01", status=status, completeness=completeness)
                self.assertEqual(snapshots.read_snapshot(sid)["status"], status)
                self.assertEqual(self.current(), a)
                self.assertEqual(services.dashboard()["friends"]["current"], 1)
        self.assertEqual(len(services.list_people()), 1)
        self.assertEqual(self.events(), [])

    def test_snp_006_provenance_and_date_precision(self):
        sid = self.capture([], "2099-01-01", source="file_import", source_reference="import_job:9:synthetic.csv")
        row = snapshots.read_snapshot(sid)
        self.assertEqual(row["captured_at"], "2099-01-01")
        self.assertEqual(row["capture_precision"], "date")
        self.assertEqual(row["source_reference"], "import_job:9:synthetic.csv")
        self.assertEqual((row["source"], row["domain_version"]), ("file_import", 1))
        self.assertTrue(row["created_at"])

    def test_diff_001_002_003_004_005_membership_cases(self):
        for old, new, added, removed in (([1], [1, 2], [2], []), ([1, 2], [1], [], [2]),
                                        ([1, 2], [], [], [1, 2]), ([], [1, 2], [1, 2], []),
                                        ([1, 2], [1, 2], [], [])):
            with self.subTest(old=old, new=new):
                a, b = self.capture(old), self.capture(new)
                delta = snapshots.diff_snapshots(a, b)
                self.assertEqual([p["vk_id"] for p in delta["added"]], added)
                self.assertEqual([p["vk_id"] for p in delta["removed"]], removed)
                with db.get_connection() as conn:
                    count = conn.execute("SELECT COUNT(*) FROM snapshot_events WHERE to_snapshot_id=?", (b,)).fetchone()[0]
                self.assertEqual(count, len(added) + len(removed))

    def test_diff_006_three_same_day_captures(self):
        a = self.capture([1], "2099-01-01T10:00:00Z")
        b = self.capture([1, 2], "2099-01-01T15:00:00Z")
        c = self.capture([2], "2099-01-01T22:00:00Z")
        self.assertEqual(snapshots.derive_events(b)["from_snapshot_id"], a)
        self.assertEqual(snapshots.derive_events(c)["from_snapshot_id"], b)
        self.assertEqual(services.dashboard()["friends"], {"current": 1, "added": 0, "removed": 1})

    def test_diff_007_stream_isolation(self):
        a = self.capture([1])
        self.capture([2], relation="follower")
        b = self.capture([], "2099-01-02")
        f = self.capture([], "2099-01-02", relation="follower")
        self.assertEqual(snapshots.derive_events(b)["from_snapshot_id"], a)
        with self.assertRaises(ValueError):
            snapshots.diff_snapshots(a, f)
        self.assertEqual({e["event_type"] for e in self.events()}, {"friend_removed", "follower_removed"})

    def test_diff_008_pure_pair_and_evt_001_reprocess_three_times(self):
        a, b = self.capture([1]), self.capture([1, 2], "2099-01-02")
        expected, events = snapshots.diff_snapshots(a, b), self.events()
        for _ in range(3):
            self.assertEqual(snapshots.derive_events(b), expected)
            self.assertEqual(self.events(), events)
        self.capture([3], "2099-01-03")
        self.assertEqual(snapshots.diff_snapshots(a, b), expected)

    def test_diff_009_predecessor_ignores_failed_creating(self):
        a = self.capture([1], "2099-01-01")
        for state in ("FAILED", "CREATING", "INCOMPLETE"):
            self.capture([2], "2099-01-02", status=state, completeness="PARTIAL")
        b = self.capture([3], "2099-01-03")
        self.assertEqual(snapshots.derive_events(b)["from_snapshot_id"], a)

    def test_evt_002_provenance_and_db_unique(self):
        a, b = self.capture([1]), self.capture([], "2099-01-02")
        event = self.events()[0]
        self.assertEqual((event["from_snapshot_id"], event["to_snapshot_id"], event["projection_snapshot_id"]), (a, b, a))
        with db.get_connection() as conn, self.assertRaises(sqlite3.IntegrityError):
            conn.execute("""INSERT INTO snapshot_events
                (from_snapshot_id,to_snapshot_id,projection_snapshot_id,external_key,event_type)
                SELECT from_snapshot_id,to_snapshot_id,projection_snapshot_id,external_key,event_type FROM snapshot_events""")

    def test_evt_004_backdated_rebuilds_only_affected_edges(self):
        a = self.capture([1], "2099-01-01")
        c = self.capture([1, 3], "2099-01-03")
        original_a, original_c = snapshots.read_snapshot(a), snapshots.read_snapshot(c)
        b = self.capture([1, 2], "2099-01-02")
        self.assertEqual(snapshots.read_snapshot(a), original_a)
        self.assertEqual(snapshots.read_snapshot(c), original_c)
        self.assertEqual(snapshots.derive_events(b)["from_snapshot_id"], a)
        self.assertEqual(snapshots.derive_events(c)["from_snapshot_id"], b)
        self.assertEqual({(r["from_snapshot_id"], r["to_snapshot_id"]) for r in self.events()}, {(a, b), (b, c)})
        self.assertEqual(len(self.events()), 3)
        self.assertEqual(self.current(), c)

    def test_backdated_insertion_before_first_and_projection_not_regressed(self):
        c = self.capture([1], "2099-01-03", people=[person(1, "Newest")])
        a = self.capture([], "2099-01-01")
        self.capture([1], "2099-01-02", people=[person(1, "Old")])
        self.assertEqual(services.list_people()[0]["full_name"], "Newest")
        self.assertEqual(len(self.events()), 1)
        self.assertEqual(self.current(), c)
        self.assertEqual(self.events()[0]["from_snapshot_id"], a)

    def test_snapshot_id_exact_replay_and_conflict(self):
        payload = {"snapshot_id": str(uuid4()), "relation_type": "friend", "people": [person(1)]}
        first = services.import_snapshot(payload)
        self.assertEqual(services.import_snapshot(payload), first)
        with self.assertRaises(ValueError):
            services.import_snapshot({**payload, "people": [person(2)]})
        with db.get_connection() as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM snapshots").fetchone()[0], 1)

    def test_complete_source_sql_mutations_rejected(self):
        sid = self.capture([1])
        statements = [
            ("UPDATE snapshots SET source='changed' WHERE id=?", (sid,)),
            ("DELETE FROM snapshots WHERE id=?", (sid,)),
            ("UPDATE snapshot_people SET full_name='changed' WHERE snapshot_id=?", (sid,)),
            ("DELETE FROM snapshot_people WHERE snapshot_id=?", (sid,)),
            ("INSERT OR REPLACE INTO snapshot_people SELECT * FROM snapshot_people WHERE snapshot_id=?", (sid,)),
            ("""INSERT OR REPLACE INTO snapshots(sequence,id,relation_type,captured_at,capture_precision,source,status,completeness,item_count,created_at)
                SELECT sequence,id,relation_type,captured_at,capture_precision,source,'CREATING',completeness,item_count,created_at FROM snapshots WHERE id=?""", (sid,)),
        ]
        original = snapshots.read_snapshot(sid)
        for sql, params in statements:
            with self.subTest(sql=sql), db.get_connection() as conn, self.assertRaises(sqlite3.IntegrityError):
                conn.execute(sql, params)
        self.assertEqual(snapshots.read_snapshot(sid), original)

    def test_atomic_failure_in_event_derivation_rolls_back_everything(self):
        self.capture([1])
        with db.get_connection() as conn:
            before = list(conn.iterdump())
        with patch.object(snapshots, "_derive", side_effect=RuntimeError("Synthetic failure")):
            with self.assertRaises(RuntimeError):
                self.capture([2], "2099-01-02")
        with db.get_connection() as conn:
            self.assertEqual(list(conn.iterdump()), before)

    def test_bad_capture_rejected_without_partial_data(self):
        for extra in ({"completeness": "UNKNOWN", "status": "COMPLETE"}, {"people": [person(1), person(1)]},
                      {"people": [person(0)]}, {"people": [person(1, " ")]}, {"captured_at": "invalid"}, {"people": None}):
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                services.import_snapshot({"relation_type": "friend", "people": [], **extra})
        with db.get_connection() as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM snapshots").fetchone()[0], 0)

    def test_namespaced_screen_identity_no_numeric_hash(self):
        with self.assertRaises(ValueError):
            services.import_snapshot({"relation_type": "friend"})
        row = {"screen_name": "Example.user", "full_name": "Synthetic screen"}
        a = self.capture([], people=[row])
        b = self.capture([], "2099-01-02", people=[row])
        p = snapshots.read_snapshot(a)["people"][0]
        self.assertEqual(p["external_key"], "screen:example.user")
        self.assertIsNone(p["vk_id"])
        self.assertEqual(p["person_id"], snapshots.read_snapshot(b)["people"][0]["person_id"])
        self.assertEqual(len(services.list_people()), 1)

    def test_legacy_precedence_until_first_complete_per_stream(self):
        with db.get_connection() as conn:
            pid = conn.execute("INSERT INTO people(vk_id,full_name) VALUES (1,'Legacy')").lastrowid
            conn.executemany("INSERT INTO relation_snapshots(person_id,relation_type,snapshot_date) VALUES (?,?,?)",
                             [(pid, "friend", "2099-01-01"), (pid, "follower", "2099-01-01")])
            conn.execute("INSERT INTO relation_events(person_id,event_type,event_date) VALUES (?,'friend_added','2099-01-01')", (pid,))
        self.capture([], "2099-01-02", status="INCOMPLETE", completeness="UNKNOWN")
        self.assertEqual(services.dashboard()["friends"]["current"], 1)
        self.capture([], "2099-01-03")
        self.assertEqual(services.dashboard()["friends"]["current"], 0)
        self.assertEqual(services.dashboard()["followers"]["current"], 1)
        self.assertEqual(services.list_changes()[0]["provenance"], "legacy_unknown")
        self.assertIsNone(services.list_changes()[0]["from_snapshot_id"])

    def test_preview_friends_followers_unknown_replay_dialogs_unchanged(self):
        a = self.capture([1])
        for kind in ("friends", "followers"):
            preview = {"kind": kind, "collected_at": "2099-01-02T00:00:00Z", "items": [person(2)],
                       "source_url": "https://example.invalid/source", "completeness": "DECLARED_COMPLETE"}
            result = services.save_collector_preview(preview)
            self.assertEqual(result["status"], "INCOMPLETE")
            self.assertEqual(services.save_collector_preview(preview), result)
            self.assertEqual(snapshots.read_snapshot(result["snapshot_id"])["source_reference"], preview["source_url"])
        self.assertEqual(self.current(), a)
        result = services.save_collector_preview({"kind": "dialogs", "collected_at": "2099-01-02", "items": [
            {"dialog_key": "synthetic", "full_name": "Synthetic dialog"}]})
        self.assertEqual(result["saved"], 1)
        self.assertEqual(len(services.list_collected_dialogs()), 1)

    def test_file_empty_json_and_partial_metadata(self):
        self.capture([1])
        result = importers.import_uploaded_file("synthetic.json", b'{"people":[]}', "relations", "friend", "2099-01-02")
        self.assertEqual(result["count"], 0)
        row = snapshots.read_snapshot(result["snapshot_id"])
        self.assertEqual(row["source_reference"], "import_job:1:synthetic.json")
        self.assertEqual(services.dashboard()["friends"]["current"], 0)
        result = importers.import_uploaded_file("partial.json", json.dumps({"people": [person(2)], "status": "FAILED"}).encode(), "relations", "friend")
        self.assertEqual(result["status"], "FAILED")
        self.assertEqual(services.dashboard()["friends"]["current"], 0)

    def test_html_partial_extract_never_claims_complete(self):
        a = self.capture([1])
        result = importers.import_uploaded_file("synthetic.html", b'<a href="https://vk.com/id2">Synthetic 2</a>',
                                               "relations", "friend", "2099-01-02")
        self.assertEqual((result["status"], result["completeness"]), ("INCOMPLETE", "UNKNOWN"))
        self.assertEqual(self.current(), a)

    def test_seed_does_not_replace_valid_empty_user_history(self):
        from app.seed import seed_demo_data
        a = self.capture([])
        seed_demo_data()
        self.assertEqual(self.current(), a)
        self.assertEqual(services.list_people(), [])
        self.assertEqual(services.dashboard()['friends']['current'], 0)

    def test_actual_api_import_dashboard_timeline_person(self):
        with closing(TestClient(main.app, base_url="http://127.0.0.1")) as client:  # No production startup/lifespan.
            a = client.post('/api/import/snapshot', json={"relation_type": "friend", "snapshot_date": "2099-01-01", "people": [person(1)]})
            self.assertEqual(a.status_code, 200)
            b = client.post('/api/import/snapshot', json={"relation_type": "friend", "snapshot_date": "2099-01-02", "people": []})
            self.assertEqual(b.status_code, 200)
            self.assertEqual(client.get('/api/dashboard').json()["friends"]["current"], 0)
            event = client.get('/api/changes').json()[0]
            self.assertEqual(event["to_snapshot_id"], b.json()["snapshot_id"])
            self.assertEqual(client.get(f'/api/people/{event["person_id"]}').status_code, 200)

    def test_concurrent_same_id_serialized_replay(self):
        payload = {"snapshot_id": str(uuid4()), "captured_at": "2099-01-01", "relation_type": "friend", "people": [person(1)]}
        with ThreadPoolExecutor(max_workers=3) as pool:
            results = list(pool.map(lambda _: services.import_snapshot(payload), range(3)))
        self.assertTrue(all(row == results[0] for row in results))
        with db.get_connection() as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM snapshots").fetchone()[0], 1)

    def test_architecture_source_and_message_scope(self):
        source = Path('app/snapshots.py').read_text(encoding='utf-8')
        imports = [node.module for node in ast.walk(ast.parse(source)) if isinstance(node, ast.ImportFrom)]
        self.assertFalse(any(name and ('ai' in name or 'httpx' in name or 'collector' in name) for name in imports))
        self.capture([1])
        with db.get_connection() as conn:
            columns = {r[1] for r in conn.execute('PRAGMA table_info(message_stats)')}
            self.assertNotIn('snapshot_id', columns)
            self.assertEqual(conn.execute('PRAGMA foreign_key_check').fetchall(), [])

    def test_performance_sanity_1000_memberships(self):
        start = time.perf_counter()
        a = self.capture(list(range(1, 1001)))
        b = self.capture(list(range(501, 1501)), "2099-01-02")
        delta = snapshots.diff_snapshots(a, b)
        elapsed = time.perf_counter() - start
        self.assertEqual((len(delta["added"]), len(delta["removed"])), (500, 500))
        self.assertEqual(services.dashboard()["friends"]["current"], 1000)
        print(f'\nU03 SANITY: 2 x 1000 memberships + diff, {elapsed:.4f}s; no SLA assertion')


class SnapshotMigrationTests(SnapshotFixture):
    def make_v1(self):
        validate = migrations.validate_schema
        with patch.object(migrations, 'CURRENT_SCHEMA_VERSION', 1), patch.object(snapshot_schema, 'create_schema'), \
             patch.object(migrations, 'validate_schema', side_effect=lambda conn: validate(conn, snapshots=False)):
            db.init_db()
        with db.get_connection() as conn:
            self.assertEqual(conn.execute('PRAGMA user_version').fetchone()[0], 1)
            self.assertNotIn('snapshot_key', {r[1] for r in conn.execute('PRAGMA table_info(people)')})
            conn.execute("INSERT INTO people(id,vk_id,full_name) VALUES (7,101,'Legacy synthetic')")
            conn.execute("INSERT INTO relation_snapshots(person_id,relation_type,snapshot_date) VALUES (7,'friend','2099-01-01')")
            conn.execute("INSERT INTO relation_events(person_id,event_type,event_date) VALUES (7,'friend_added','2099-01-01')")
            conn.execute("INSERT INTO message_stats(person_id,period_start,period_end,incoming_count) VALUES (7,'2099-01-01','2099-01-31',12)")

    def test_mig_snp_001_v1_v2_preserves_all_data_backup_and_fk(self):
        self.make_v1()
        with db.get_connection() as conn:
            before = list(conn.iterdump())
            old = {t: [tuple(r) for r in conn.execute(f'SELECT * FROM {t}')] for t in migrations.EXPECTED_TABLES}
        db.init_db()
        with db.get_connection() as conn:
            for table, rows in old.items():
                actual = [tuple(r) for r in conn.execute(f'SELECT * FROM {table}')]
                if table == 'people':
                    actual = [r[:-1] for r in actual]
                self.assertEqual(actual, rows, table)
            self.assertEqual(conn.execute('PRAGMA user_version').fetchone()[0], 2)
            self.assertEqual(conn.execute('PRAGMA foreign_key_check').fetchall(), [])
        backups = list(db.BACKUP_DIR.glob('schema-v1-to-v2-*.db'))
        self.assertEqual(len(backups), 1)
        with closing(sqlite3.connect(backups[0])) as conn:
            self.assertEqual(list(conn.iterdump()), before)

    def test_mig_snp_002_backup_refusal_and_ddl_rollback(self):
        self.make_v1()
        before = db.DB_PATH.read_bytes()
        with patch.object(migrations, 'backup_database', side_effect=migrations.SchemaMigrationError('Synthetic refusal')):
            with self.assertRaises(migrations.SchemaMigrationError):
                db.init_db()
        self.assertEqual(db.DB_PATH.read_bytes(), before)
        create = snapshot_schema.create_schema
        def fail(conn):
            create(conn)
            raise RuntimeError('Synthetic after DDL')
        with patch.object(snapshot_schema, 'create_schema', side_effect=fail), self.assertRaises(RuntimeError):
            db.init_db()
        self.assertEqual(db.DB_PATH.read_bytes(), before)

    def test_mig_snp_003_three_initializations_unchanged(self):
        self.make_v1()
        db.init_db()
        with db.get_connection() as conn:
            before = list(conn.iterdump())
        for _ in range(3):
            db.init_db()
        with db.get_connection() as conn:
            self.assertEqual(list(conn.iterdump()), before)
        self.assertEqual(len(list(db.BACKUP_DIR.glob('*.db'))), 1)

    def test_mig_snp_004_legacy_retained_no_fabricated_snapshots(self):
        self.make_v1()
        db.init_db()
        with db.get_connection() as conn:
            self.assertEqual(conn.execute('SELECT COUNT(*) FROM snapshots').fetchone()[0], 0)
            self.assertEqual(conn.execute('SELECT COUNT(*) FROM relation_snapshots').fetchone()[0], 1)
        self.assertEqual(services.dashboard()['friends']['current'], 1)

    def test_mig_snp_005_fresh_v2_and_future_guard(self):
        db.init_db()
        with db.get_connection() as conn:
            self.assertEqual(conn.execute('PRAGMA user_version').fetchone()[0], 2)
            self.assertEqual(conn.execute('PRAGMA foreign_key_check').fetchall(), [])
            conn.execute('PRAGMA user_version=3')
        before = db.DB_PATH.read_bytes()
        with self.assertRaises(migrations.SchemaMigrationError):
            db.init_db()
        self.assertEqual(db.DB_PATH.read_bytes(), before)
        self.assertEqual(list(db.BACKUP_DIR.glob('*.db')), [])

    def test_v2_immutability_trigger_drift_refused(self):
        db.init_db()
        with db.get_connection() as conn:
            conn.execute('DROP TRIGGER snapshot_people_delete_guard')
        with self.assertRaises(migrations.SchemaMigrationError):
            db.init_db()
