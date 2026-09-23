# Data Model Status

Baseline 1.0 · 2026-09-23. Current physical model comes from [audit read-only schema](01_ARCHITECTURE_INVENTORY.md) and [db.py](../../app/db.py). This iteration does not change/open the DB for application startup or migrations.

## Current physical model — eight tables

| Table | Actual responsibility | Important limit |
|---|---|---|
| people | mutable person identity/name/URLs | no historical attribute version |
| relation_snapshots | person/type/date membership | no snapshot header; only friend/follower; empty state cannot be represented |
| relation_events | relation changes journal | no snapshot FK; duplicate/mutable event semantics |
| message_stats | per-person period aggregates | mutable upsert, no snapshot scope |
| app_settings | key/value LM configuration | three editable LM keys, no provider selector |
| ai_insights | per-person model output/evidence strings | no snapshot/prompt provenance, not RAG citations |
| collector_dialogs | collected dialog summaries | installed schema differs from code DDL |
| import_jobs | filename/status/count/error | no aggregate/run lineage |

## KNOWN P0 DEBT — installed collector_dialogs schema drift

Installed columns at audit: `id, dialog_key, peer_id, full_name, dialog_url, collected_at` (6). Fresh DDL additionally expects `preview, date_label, unread, unread_count, outgoing, avatar_url, verified` (13 total). `services.save_collector_preview` inserts these fields. `CREATE TABLE IF NOT EXISTS` does not add them to an existing table. Fresh temporary DB tests miss this case. U02 remains unimplemented.

Audit FK check reported zero violations; this does not certify Snapshot/Run/Graph relations, which do not exist. Generic org operations live in memory with result JSON, not durable CollectorRun/Community tables.

## Target logical model

[ADR-003](../adr/ADR-003-immutable-snapshot-source-of-truth.md): CollectionRun → Immutable Snapshot with source items/completeness/schema version; separate source-linked Diff/Timeline/Analytics. [ADR-004](../adr/ADR-004-local-llm-provider-abstraction.md)/[ADR-006](../adr/ADR-006-rag-architecture.md): provider config and source-linked AI results/retrieval index. Graph/Export models follow only with U15/U16.

[Root ER](../../10_DATA_MODEL.md) and [feature model](../../specs/001-vk-profile-analysis/data-model.md) are historical logical proposals, not SQLite DDL. UUID IDs, Embedding entity and all listed tables are not thereby approved physical schema. U03/U08 choose the minimum model necessary to satisfy the accepted ADRs.

## Migration path

1. **U02:** schema versioning and compatible dialogs migration; test preservation, repeatability and failure safety on synthetic legacy data.
2. **U03:** immutable source aggregate and identity/completeness semantics; explicit transformation of legacy relation rows with documented provenance limits. Do not invent missing historical state.
3. **Subsequent models:** U05 settings contract; U08 local source index/results; U12 persistence seams; U14–U17 only accepted roadmap increments.

Exact next implementation step is U02. No migration or Snapshot implementation occurred in baseline. [Backlog](05_UPGRADE_BACKLOG.md), [debt register](TECHNICAL_DEBT_REGISTER.md).
