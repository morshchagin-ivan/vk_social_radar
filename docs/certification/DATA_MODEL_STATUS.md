# Data Model Status

2026-09-24 · U02/U03 current physical schema **v2**. [U03 evidence](U03_IMMUTABLE_SNAPSHOT_REPORT.md), [DDL](../../app/snapshot_schema.py), [migration](../../app/migrations.py). Tests used temporary databases; the working user database was not migrated.

## Physical model — eleven tables

| Table | Responsibility | Boundary |
|---|---|---|
| snapshots | UUID identity, sequence tie-break, captured_at/precision, relation stream, source/reference, status/completeness, item_count, domain_version, created_at | immutable after finalization; COMPLETE requires declared completeness and exact membership count |
| snapshot_people | frozen external identity, numeric VK ID if known, name/profile/avatar, optional current person reference | historical reads do not join mutable people for attributes; membership immutable after finalization |
| snapshot_events | derived membership changes with from/to IDs and historical projection reference | UNIQUE pair/type/identity; rebuild affected edges on backdated insertion; not Event Sourcing |
| people | mutable convenience/person/message projection; nullable UNIQUE snapshot_key added | namespaced vk:/screen: linkage for new captures; not historical truth |
| relation_snapshots | preserved legacy person/type/date membership | no invented run ID/completeness; fallback only before first COMPLETE v2 capture per stream |
| relation_events | preserved legacy journal | labelled legacy_unknown; original historical name/completeness cannot be reconstructed |
| message_stats | mutable per-person period aggregates | no snapshot scope |
| app_settings | existing key/value LM configuration | unchanged |
| ai_insights | existing per-person output | existing fixed-context insights lack snapshot/prompt provenance; U08 returns separate cited results without persistence |
| collector_dialogs | existing 13-field dialog summaries | U02 compatibility preserved; outside immutable relation aggregate |
| import_jobs | existing import status/files/count | real job/file reference may be recorded; not a fabricated CollectorRun |

UUID identity is independent of date. Sequence is a stable database insertion tie-break. Date-only input remains a date string with date precision and sorts before timestamped captures on that date. Timestamp input normalizes to UTC; old offset-free preview timestamps follow the application local-time convention. Missing upstream time defaults to import acceptance time, not a claimed VK observation time. Streams are friend/follower; no account/tenant dimension is invented.

Lifecycle: CREATING → COMPLETE / INCOMPLETE / FAILED. Drafts never become current. Finalized rows cannot be promoted or modified; corrected captures get new IDs. Manual/CSV/JSON imports declare replacement sets, including explicit []. Missing people is rejected. Collector and HTML extraction cannot prove full coverage and remain UNKNOWN/INCOMPLETE. Unexpected persistence/derivation failure rolls back the whole operation.

## Migration and legacy policy

PRAGMA user_version remains the sole marker. v1→v2 adds three tables, indexes, immutability triggers and nullable people.snapshot_key. All existing rows/IDs/values are preserved; no legacy backfill. Recognized v0 receives the U02 dialog columns and v2 foundation in one transaction. Fresh initialization finishes at v2. Future versions fail closed; current schema drift is not silently repaired.

Existing supported upgrades first create SQLite backups, including committed WAL: `schema-v<from>-to-v2-<UTC>-<UUID>.db`. Backup refusal prevents mutation. DDL, validation, version and defaults share the transaction. Three repeat v2 initializations produce no changes/extra backups. Snapshot schema objects and FK integrity are checked; U02 exact dialog-column/unique-key checks remain.

Legacy tables remain compatibility history and are never declared COMPLETE v2. The first COMPLETE establishes a new baseline; no legacy→v2 removal events are invented. Thereafter current counts use latest COMPLETE v2, including empty, regardless of legacy dates. New events render frozen source fields; legacy events retain unknown provenance and mutable presentation limitations.

## Derived data and reads

Order: (captured_at, sequence) within friend/follower, excluding non-COMPLETE. A backdated B between A/C atomically derives A→B and replaces obsolete A→C with B→C. Source membership/projection never changes. Pair replay uses DB uniqueness and retains unchanged event IDs. Explicit pair diff reads only those two immutable sets.

Dashboard relation counts, list_people flags and new timeline/person-detail events use v2 truth. People remain mutable convenience records; messages and AI retain existing period/current semantics. Full FR-2 corpus/lifecycle, attribute/activity diff, snapshot browser/export/retention and durable source-linked AI reports remain target. [Logical target](../../10_DATA_MODEL.md) is not current SQLite DDL.

## Evidence

34 new U03 + 14 U02 + 26 U05 + 25 U09 + 18 existing = **117 unittest PASS**; 8 additional functions PASS. Fresh/migrated FK checks, preservation/backup/refusal/rollback, drift rejection, immutability, replay/concurrency, same-day/empty/backdated cases and incomplete exclusion use synthetic data. No network or user database writes. [Report](U03_IMMUTABLE_SNAPSHOT_REPORT.md).

U08 reads COMPLETE snapshot headers, frozen memberships and derived compatible events through a readonly corpus builder. No table/migration is added. Event document IDs use stable pair/type/person identity, not the rebuildable autoincrement row ID. The index lives only in memory and is rebuilt after source changes. Message_stats, ai_insights and mutable people are excluded. [U08 evidence](U08_LOCAL_RAG_REPORT.md).
