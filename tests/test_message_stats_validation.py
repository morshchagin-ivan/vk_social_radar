"""U13A: real service/import writes on temporary SQLite; no application startup."""
from __future__ import annotations

import csv
import io
import json
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app import db, importers, main, seed, services
from app.message_stats import MessageStatsValidationError, normalize_message_stats
from test_ai_provider import NetworkBlockedTests


class MessageStatsValidationTests(NetworkBlockedTests):
    def setUp(self):
        super().setUp()
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.enterContext(patch.multiple(
            db, DB_PATH=self.root / 'test.db', DATA_DIR=self.root,
            IMPORT_DIR=self.root / 'imports', BACKUP_DIR=self.root / 'backups',
        ))
        self.enterContext(patch.object(importers, 'IMPORT_DIR', self.root / 'imports'))
        db.init_db()
        self.row = dict(
            vk_id=990001, full_name='Synthetic validation person',
            period_start='2026-01-01', period_end='2026-12-31',
            incoming_count=1, outgoing_count=2, active_days=1,
            initiated_by_person=1, initiated_by_me=0,
        )

    def domain_state(self):
        with db.get_connection() as conn:
            return {table: [tuple(row) for row in conn.execute(f'SELECT * FROM {table} ORDER BY id')]
                    for table in ('people', 'message_stats')}

    def assert_rejected(self, field, value):
        before = self.domain_state()
        row = dict(self.row, **{field: value})
        for write in (
            lambda: services.import_message_stats([row]),
            lambda: importers._dispatch([row], 'message_stats', None, None),
        ):
            with self.assertRaisesRegex(MessageStatsValidationError, field):
                write()
            self.assertEqual(self.domain_state(), before)

    def test_val_001_malformed_periods_rejected_at_both_boundaries(self):
        for field in ('period_start', 'period_end'):
            for value in ('not-a-date', '2026-01', '20260101', '2026-1-01',
                          '2026-01-01T00:00:00', '2026-W01-1', ''):
                with self.subTest(field=field, value=value):
                    self.assert_rejected(field, value)

    def test_val_002_real_calendar_validation(self):
        for field in ('period_start', 'period_end'):
            for value in ('2026-00-01', '2026-13-01', '2026-02-29', '2026-04-31',
                          '2026-01-00', '0000-01-01'):
                with self.subTest(field=field, value=value):
                    self.assert_rejected(field, value)

    def test_val_003_negative_incoming_rejected(self):
        for value in (-1, '-1', ' -7 '):
            self.assert_rejected('incoming_count', value)

    def test_val_004_negative_outgoing_rejected(self):
        for value in (-1, '-1', ' -7 '):
            self.assert_rejected('outgoing_count', value)

    # VAL-005: no independent total input/column exists; exercise derived total.
    def test_val_005_total_is_derived_and_auxiliary_counts_nonnegative(self):
        for field in ('active_days', 'initiated_by_person', 'initiated_by_me'):
            self.assert_rejected(field, -1)
        services.import_message_stats([self.row])
        self.assertEqual(services.message_leaderboard()[0]['total_messages'], 3)
        with db.get_connection() as conn:
            self.assertNotIn('total_count', {row[1] for row in conn.execute('PRAGMA table_info(message_stats)')})

    def test_val_006_zero_counts_and_same_day_accepted(self):
        row = dict(self.row, period_end=self.row['period_start'])
        for field in ('incoming_count', 'outgoing_count', 'active_days', 'initiated_by_person', 'initiated_by_me'):
            row[field] = 0
        services.import_message_stats([row])
        result = services.message_leaderboard()[0]
        self.assertEqual(result['total_messages'], 0)
        self.assertEqual(result['person_initiative_pct'], 0)

    def test_val_007_valid_boundaries_and_leap_day_accepted(self):
        for start, end in (('2026-01-01', '2026-12-31'), ('2028-02-29', '2028-02-29'),
                           ('2026-06-01', '2026-06-30'), ('2026-07-01', '2026-07-31')):
            services.import_message_stats([dict(self.row, period_start=start, period_end=end)])
        self.assertEqual(len(self.domain_state()['message_stats']), 4)

    def test_val_008_invalid_upsert_cannot_modify_existing_person_or_stats(self):
        services.import_message_stats([self.row])
        before = self.domain_state()
        self.row['full_name'] = 'Synthetic replacement must not persist'
        self.assert_rejected('incoming_count', -1)
        self.assertEqual(self.domain_state(), before)

    def test_val_009_direct_service_batch_remains_atomic(self):
        invalid = dict(self.row, vk_id=990002, outgoing_count=-1)
        with self.assertRaisesRegex(MessageStatsValidationError, 'outgoing_count'):
            services.import_message_stats([self.row, invalid])
        self.assertEqual(self.domain_state(), {'people': [], 'message_stats': []})

    def test_val_010_invalid_upload_has_only_existing_failed_attempt_bookkeeping(self):
        invalid = dict(self.row, vk_id=990002, period_end='synthetic invalid date')
        with self.assertRaisesRegex(MessageStatsValidationError, 'period_end'):
            importers.import_uploaded_file('synthetic.json', json.dumps([self.row, invalid]).encode(), 'message_stats')
        self.assertEqual(self.domain_state(), {'people': [], 'message_stats': []})
        with db.get_connection() as conn:
            jobs = [tuple(row) for row in conn.execute('SELECT status, imported_rows, error_text FROM import_jobs')]
        self.assertEqual(jobs, [('error', 0, 'Import failed')])
        self.assertEqual(len(list((self.root / 'imports').iterdir())), 1)

    def test_val_011_existing_csv_fixture_and_valid_upsert(self):
        fixture = Path(__file__).resolve().parents[1] / 'sample_import/message_stats.csv'
        result = importers.import_uploaded_file('synthetic.csv', fixture.read_bytes(), 'message_stats')
        self.assertEqual(result['imported'], 2)
        self.assertEqual(sorted(row['total_messages'] for row in services.message_leaderboard()), [59, 217])
        services.import_message_stats([self.row])
        services.import_message_stats([dict(self.row, incoming_count=10)])
        match = [row for row in services.message_leaderboard() if row['full_name'] == self.row['full_name']]
        self.assertEqual(len(match), 1)
        self.assertEqual(match[0]['total_messages'], 12)

    def test_val_012_api_preserves_safe_400_and_valid_success(self):
        # No context manager: TestClient does not invoke production lifespan.
        client = TestClient(main.app, base_url='http://127.0.0.1:8765')
        self.addCleanup(client.close)
        for change in ({'period_start': 'synthetic private malformed date'}, {'incoming_count': -1}):
            response = client.post('/api/import/file', data={'import_type': 'message_stats'},
                                   files={'file': ('synthetic.json', json.dumps([dict(self.row, **change)]), 'application/json')})
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.json(), {'detail': 'Invalid input or operation failed'})
            self.assertEqual(self.domain_state(), {'people': [], 'message_stats': []})
        response = client.post('/api/import/file', data={'import_type': 'message_stats'},
                               files={'file': ('synthetic.json', json.dumps([self.row]), 'application/json')})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['imported'], 1)

    def test_wrong_types_rejected_without_lossy_coercion(self):
        for field in ('incoming_count', 'outgoing_count', 'active_days', 'initiated_by_person', 'initiated_by_me'):
            for value in (True, False, 1.9, -0.5, 1.0, None, [], {}, '1.5', '1e3', '', ' '):
                with self.subTest(field=field, value=value):
                    self.assert_rejected(field, value)
        for field in ('period_start', 'period_end'):
            for value in (None, 20260101, True, [], {}):
                self.assert_rejected(field, value)

    def test_whitespace_integer_normalization_and_large_count(self):
        for field in ('period_start', 'period_end'):
            self.assert_rejected(field, ' 2026-06-01 ')
        row = dict(self.row, incoming_count=' +1000000000000 ', outgoing_count=' 0 ')
        original = dict(row)
        services.import_message_stats([row])
        self.assertEqual(row, original)
        self.assertEqual(services.message_leaderboard()[0]['total_messages'], 10**12)

    def test_missing_dates_and_reversed_range_rejected(self):
        for field in ('period_start', 'period_end'):
            row = dict(self.row)
            del row[field]
            with self.assertRaisesRegex(MessageStatsValidationError, field):
                services.import_message_stats([row])
            with self.assertRaisesRegex(MessageStatsValidationError, field):
                importers._dispatch([row], 'message_stats', None, None)
        self.assert_rejected('period_start', '2027-01-01')

    def test_csv_and_tsv_invalid_counts_rejected(self):
        for suffix, delimiter in (('csv', ','), ('tsv', '\t')):
            content = io.StringIO()
            writer = csv.DictWriter(content, fieldnames=list(self.row), delimiter=delimiter)
            writer.writeheader()
            writer.writerow(dict(self.row, incoming_count=-1))
            with self.assertRaisesRegex(MessageStatsValidationError, 'incoming_count'):
                importers.import_uploaded_file('synthetic.' + suffix, content.getvalue().encode(), 'message_stats')
            self.assertEqual(self.domain_state(), {'people': [], 'message_stats': []})

    def test_archive_preserves_independent_member_commits(self):
        content = io.BytesIO()
        with zipfile.ZipFile(content, 'w') as archive:
            archive.writestr('valid.json', json.dumps([self.row]))
            archive.writestr('invalid.json', json.dumps([dict(self.row, vk_id=990002, outgoing_count=-1)]))
        with self.assertRaisesRegex(MessageStatsValidationError, 'outgoing_count'):
            importers.import_uploaded_file('synthetic.zip', content.getvalue(), 'message_stats')
        self.assertEqual(len(self.domain_state()['people']), 1)
        self.assertEqual(len(self.domain_state()['message_stats']), 1)

    def test_seed_writer_uses_shared_validator_and_rolls_back_on_rejection(self):
        with patch.object(seed, 'normalize_message_stats', side_effect=MessageStatsValidationError('incoming_count: synthetic refusal')):
            with self.assertRaisesRegex(MessageStatsValidationError, 'incoming_count'):
                seed.seed_demo_data()
        self.assertEqual(self.domain_state(), {'people': [], 'message_stats': []})
        with patch.object(seed, 'normalize_message_stats', wraps=normalize_message_stats) as validator:
            seed.seed_demo_data()
        self.assertEqual(validator.call_count, 6)
        self.assertEqual(len(self.domain_state()['message_stats']), 6)
