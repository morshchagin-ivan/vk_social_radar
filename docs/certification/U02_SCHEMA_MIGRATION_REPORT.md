# U02 — SQLite Schema Migration Report

Date: 2026-09-23. **Implementation / validation: PASS.** Branch: `certification/u02-schema-migration`.
Start SHA and protected baseline tag `v0.4.2-certification-baseline`: `e34624462fa8ef3cdf56e29ce64cab24aac61411`.
The initial worktree was clean. This change is intended as one atomic commit, `feat(db): add versioned SQLite schema migration`; its SHA is provided in the final console report (not embedded recursively in this commit). No push or merge.

## Problem and previous state

The [audit](01_ARCHITECTURE_INVENTORY.md) identified an installed six-column `collector_dialogs` while [runtime persistence](../../app/services.py) writes thirteen columns. `CREATE TABLE IF NOT EXISTS` left existing tables unchanged. There was no schema version or executable migration. Fresh-only tests missed the upgrade failure.

Old fields: `id`, `dialog_key`, `peer_id`, `full_name`, `dialog_url`, `collected_at`.
Required additions: `preview`, `date_label`, `unread`, `unread_count`, `outgoing`, `avatar_url`, `verified`.

## Implemented design and version strategy

[app/migrations.py](../../app/migrations.py) provides one small SQLite-native migration, schema detection, validation and backup. [db.init_db](../../app/db.py) retains existing DDL/default settings and orchestrates initialization; no external package, ORM, API, collector or service refactor.

`CURRENT_SCHEMA_VERSION = 1`; `PRAGMA user_version` is the sole canonical marker. Version 0 means unversioned, **not necessarily empty**. Detection inspects SQLite schema objects and dialog column metadata.

| Detected state | Action | Migration backup |
|---|---|---|
| Version 0, no application schema objects | Create all eight existing tables; validate; set version 1; initialize defaults | None |
| Version 0, recognized six-column dialogs | Backup; add seven columns; create any missing current tables; validate; set version 1; initialize defaults | One per attempted upgrade |
| Version 0, recognized thirteen-column dialogs | Backup; create any missing current tables; validate; adopt version 1; initialize defaults | Required before version adoption on existing DB |
| Version 1 | Validate existing schema; initialize missing default settings with INSERT OR IGNORE | None |
| Version greater than 1 | Raise `Database schema version X is newer than supported 1` before mutation | None |
| Unknown unversioned shape or negative version | Refuse startup; no guessing or destructive repair | None |

Versioned-current drift also fails validation instead of silently recreating missing tables. Extra application tables are preserved; required tables must all exist. Detection under the writer reservation is repeated so two startup callers cannot both act on stale unversioned detection.

## Migration path and validation

Supported path: **0 → 1**, using seven ordered `ALTER TABLE collector_dialogs ADD COLUMN` statements. No table rebuild, DELETE, data UPDATE or ID remapping. Static fresh DDL executes statement by statement, avoiding `executescript`'s implicit pre-commit.

Before committing, validation requires all eight expected tables, exactly thirteen dialog fields with current types/defaults/nullability/primary key, the non-partial unique key `(dialog_key, collected_at)`, current schema version and no `PRAGMA foreign_key_check` violations. Hidden/generated unexpected dialog fields are rejected. Physical column order differs between additive and fresh schemas; runtime inserts use named fields and selects are read by field name.

## Backup and recovery boundaries

Existing recognized version-0 databases are copied **before the first mutation** with SQLite `Connection.backup()`, including committed WAL content. The main connection holds `BEGIN IMMEDIATE`; a separate `mode=ro` source connection supplies the committed pre-migration image without attempting backup from an active write transaction. The reservation excludes competing writers during copy/migration.

Destination: existing `BACKUP_DIR` (`data/backups` in normal operation), filename `schema-v0-to-v1-<UTC timestamp>-<UUID>.db`. Exclusive creation prevents overwrite. SQLite `quick_check` must pass on the copy. Backup errors propagate as `SchemaMigrationError` and block all schema/version/default changes. No automatic deletion or retention; retry after an unsuccessful migration creates a distinct copy and retains the previous one. Existing `.gitignore` covers `data/backups/*`.

A failed copy can leave an incomplete backup file; its mere presence is not success evidence. Before any manual recovery, stop application/writers, verify the chosen copy with SQLite integrity/schema checks and preserve the failed original plus relevant sidecars. Use a separate recovery destination first; never restore a copy over a running database. Automatic restore, backup encryption, retention, disk-space budgets and measured recovery time are outside U02. A migration exception normally needs no restore: its transaction rolls back, leaving the pre-upgrade DB available for diagnosis/retry.

## Transaction / rollback

`init_db` checks for unsupported versions before reserving a writer, then begins an explicit transaction and re-detects. DDL, schema/FK validation, version assignment, version check and default settings initialization share that transaction. `get_connection` explicitly rolls back on exceptions and re-raises. `main.startup` already calls `init_db` without swallowing exceptions; failure prevents seed/startup continuation.

Tests induce failure after all seven ALTERs but before version advancement, and another failure at default insertion **after** version assignment. Both restore the original schema, version and legacy rows. The pre-upgrade backup remains. Current/fresh failures are also surfaced; no automatic downgrade or empty replacement database.

## Preservation guarantees

The migration only adds columns. Synthetic fixture: three rows with non-contiguous IDs 3/17/42, NULLs, empty strings, whitespace, Unicode and signed peer IDs. All six legacy values and row count compare equal before/after; original uniqueness, a custom index and AUTOINCREMENT continuation are verified. The backup's full SQL dump matches the pre-upgrade state.

`preview`, `date_label`, `unread_count`, `avatar_url` remain NULL for legacy rows. Existing DDL requires `unread`, `outgoing`, `verified` as INTEGER NOT NULL DEFAULT 0; zeros are **compatibility sentinels, not evidence that a historical flag was observed false**. No fabricated preview, date, count, URL or verification fact. U02 does not change UI interpretation or recover absent history.

Migration code emits no row data/logs. Validation errors describe schema/version/integrity status, not dialog previews/names/IDs/URLs.

## Idempotency and future versions

Three consecutive initializations on the migrated fixture preserve its dump, count, version and defaults. SQL tracing confirms no ALTER on subsequent calls; backup is invoked once. Fresh initialization repeated three times preserves an edited setting and creates no backup. Future-version rejection preserves the database bytes and creates no backup.

## Tests

Environment: existing Windows `.venv`, Python 3.13.2, standard-library unittest/SQLite. No dependency installation. All DB tests use temporary paths; four existing test modules received only storage/backup isolation changes, with CSV import's separately imported path patched too. No production startup, browser collection, profile writes, LLM or network calls.

| Test / contract | Evidence | Result |
|---|---|---|
| MIG-001 fresh | Eight required tables, exact dialog schema, version 1, unchanged defaults, no backup | PASS |
| MIG-002 legacy | 3 rows → 3, 6 columns → 13, exact old values/IDs, NULL/defaults, unique/custom index, readable pre-state backup | PASS |
| MIG-003 runtime write | Real save_collector_preview/list_collected_dialogs, all metadata, next ID, duplicate prevention; 3 old + 1 new row | PASS |
| MIG-004 idempotency | Three init calls, unchanged dump/version/count, no repeat ALTER, exactly one backup | PASS |
| MIG-005 rollback | Mocked validation error after ALTERs; original schema/version/data restored; retry retains previous backup | PASS |
| MIG-006 future | Version 99 rejected by supported version 1; byte-identical DB, no backup | PASS |
| MIG-007 current fresh repeat | Three startups, edited model setting preserved, no backup | PASS |
| Backup failure | Permission error creating backup prevents all DB mutation | PASS |
| Unversioned-current adoption | Existing thirteen-column schema backed up before version assignment; next startup no backup | PASS |
| Unknown unversioned schema | Nonempty unknown schema rejected, not mistaken for fresh | PASS |
| Current schema drift | Missing required table fails without silent repair | PASS |
| FK failure | Orphan causes rollback and unchanged version/data | PASS |
| Late defaults failure | SQL trigger aborts default insertion after version assignment; DDL/version/data rollback | PASS |
| WAL backup | Committed, uncheckpointed WAL row included in backup and preserved after migration | PASS |
| MIG-008 existing regression | 18 pre-existing unittest cases including CSV import, relation changes, message stats, fresh dialog save | PASS |
| Additional existing functions | 8 v043 functions run separately (4 classifiers, 4 source checks) | PASS |

Commands executed from repository root:

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p test_migrations.py -v
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -B -c "import runpy; namespace = runpy.run_path('tests/test_v043_organization_source.py'); tests = [(name, test) for name, test in namespace.items() if name.startswith('test_') and callable(test)]; [test() for name, test in tests]; print('Additional existing tests:', len(tests), 'PASS')"
```

**Counts:** 14 new migration tests PASS; standard discovery **32 = 14 + 18 PASS**; additional **8 PASS**; failures/errors **0**. Additional functions are not claimed as standard discovery. Two existing `ResourceWarning` messages from unclosed source-reading files in `test_v031.py` remain; they are not failures. U07 runner/CI and broader behavioral coverage remain planned.

## Working database / regression safety

The working `data/social_radar.db` was never opened in write mode or migrated. After the full PASS gate, a metadata-only `mode=ro` preflight classified it as `legacy_dialogs`, version 0, six columns. No row values were printed. SHA-256 before the build and after testing/preflight matched:
`0c20c00abed8fae1d154db1c0f04a45ba2512dfdd6f6c3d5e440422e5d459652`.

All real persistence/import regression calls ran against temporary data. Normal application startup on this branch will apply U02 after backup; it was deliberately not invoked against user data during this build.

## Files changed

- Runtime: [app/db.py](../../app/db.py), new [app/migrations.py](../../app/migrations.py).
- New discoverable behavior tests: [tests/test_migrations.py](../../tests/test_migrations.py).
- Existing test storage isolation only: [test_services.py](../../tests/test_services.py), [test_v02.py](../../tests/test_v02.py), [test_v03.py](../../tests/test_v03.py), [test_v04.py](../../tests/test_v04.py).
- Seven required documentation updates: [Architecture Status](ARCHITECTURE_STATUS.md), [Data Model](DATA_MODEL_STATUS.md), [Technical Debt](TECHNICAL_DEBT_REGISTER.md), [Traceability](TRACEABILITY_MATRIX.md), [Upgrade Backlog](05_UPGRADE_BACKLOG.md), [ADR-005](../adr/ADR-005-sqlite-for-mvp.md), [README](../../README.md).
- This new report. No user DB/backups/imports/profile/previews/logs/secrets or unrelated refactors belong in the commit.

## Known limitations / architecture impact / certification value

U02 adds an executable, versioned startup boundary and resolves D01 in code. It demonstrates a legacy-data upgrade, safe backup and failure rollback with behavioral evidence, without changing the existing eight-table domain model. Other tables are checked for presence and FK integrity, not exhaustively compared column by column. Unknown schemas require explicit diagnosis; only version 0→1 is supported. Backup locking and copying can delay startup; concurrent-writer stress, power-loss simulation and performance/recovery measurements are not claimed.

This does **not** certify the entire Data Architecture as READY or implement immutable Snapshot, new API/provider contracts, Retry/Breaker, RAG, Repository/Strategy, Graph, Scheduler or Export. Those statuses remain unchanged. Historical audit reports remain historical evidence.

## Next recommended upgrade

**U03 — immutable Snapshot source of truth**, starting with regression fixtures for empty/repeated/same-day/backdated collection semantics. U03 is recommended only; no U03 implementation is included here.
