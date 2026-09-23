# Data Model Status

Baseline 1.0 + U02 · 2026-09-23. Current physical model comes from [audit read-only schema](01_ARCHITECTURE_INVENTORY.md), [db.py](../../app/db.py) and [migrations.py](../../app/migrations.py). U02 tested only temporary databases; the working user DB remains unchanged (read-only preflight: version 0, six dialog columns).

## Current physical model — eight tables

| Table | Actual responsibility | Important limit |
|---|---|---|
| people | mutable person identity/name/URLs | no historical attribute version |
| relation_snapshots | person/type/date membership | no snapshot header; only friend/follower; empty state cannot be represented |
| relation_events | relation changes journal | no snapshot FK; duplicate/mutable event semantics |
| message_stats | per-person period aggregates | mutable upsert, no snapshot scope |
| app_settings | key/value LM configuration | three editable LM keys, no provider selector |
| ai_insights | per-person model output/evidence strings | no snapshot/prompt provenance, not RAG citations |
| collector_dialogs | collected dialog summaries | version 1 supports 13 fields; legacy metadata cannot be recovered |
| import_jobs | filename/status/count/error | no aggregate/run lineage |

## RESOLVED in code — collector_dialogs schema drift (U02)

Installed columns at audit: `id, dialog_key, peer_id, full_name, dialog_url, collected_at` (6). Version 1 adds `preview, date_label, unread, unread_count, outgoing, avatar_url, verified` (13 total) with additive ALTERs. `services.save_collector_preview` now succeeds after migration on synthetic legacy data. [U02 tests/report](U02_SCHEMA_MIGRATION_REPORT.md) prove old row/ID preservation, backup, rollback and repeated startup. This resolves the implementation defect; migration was **not applied to the user DB** during this build.

`PRAGMA user_version` is the sole version mechanism: 0 = unversioned, 1 = current. Introspection distinguishes empty, legacy six-column, unversioned thirteen-column, current and unsupported databases. Both recognized existing unversioned shapes receive a SQLite backup before the first mutation (including version adoption); fresh/current databases do not. Version 1 is validated on every startup, future versions fail without mutation.

New optional metadata is NULL. `unread`, `outgoing`, `verified` use the existing runtime DDL's NOT NULL DEFAULT 0 as compatibility sentinels; these zeros **do not prove observed false values** for legacy records. No invented metadata or historical reconstruction. ALTER appends columns after `collected_at`; runtime uses named fields, so physical order need not match fresh DDL.

Audit FK check reported zero violations; this does not certify Snapshot/Run/Graph relations, which do not exist. Generic org operations live in memory with result JSON, not durable CollectorRun/Community tables.

## Target logical model

[ADR-003](../adr/ADR-003-immutable-snapshot-source-of-truth.md): CollectionRun → Immutable Snapshot with source items/completeness/schema version; separate source-linked Diff/Timeline/Analytics. [ADR-004](../adr/ADR-004-local-llm-provider-abstraction.md)/[ADR-006](../adr/ADR-006-rag-architecture.md): provider config and source-linked AI results/retrieval index. Graph/Export models follow only with U15/U16.

[Root ER](../../10_DATA_MODEL.md) and [feature model](../../specs/001-vk-profile-analysis/data-model.md) are historical logical proposals, not SQLite DDL. UUID IDs, Embedding entity and all listed tables are not thereby approved physical schema. U03/U08 choose the minimum model necessary to satisfy the accepted ADRs.

## Migration path

1. **U02 — IMPLEMENTED:** version 0→1, backup before mutation, all DDL/version/defaults in one transaction, required-table/exact-dialog-schema/version/FK validation; 14 new behavior tests PASS.
2. **U03:** immutable source aggregate and identity/completeness semantics; explicit transformation of legacy relation rows with documented provenance limits. Do not invent missing historical state.
3. **Subsequent models:** U05 settings contract; U08 local source index/results; U12 persistence seams; U14–U17 only accepted roadmap increments.

Next recommended implementation step is U03. U02 does not make the whole Data Architecture READY and does not implement Snapshot. [Backlog](05_UPGRADE_BACKLOG.md), [debt register](TECHNICAL_DEBT_REGISTER.md).
