# ADR-003 — Immutable Snapshot as Source of Truth

**Status:** ACCEPTED. **Implementation:** IMPLEMENTED for friend/follower relation foundation (U03); broader corpus remains target. **Updated:** 2026-09-24.
**Decision owners:** project owner and architecture maintainer.
**Related backlog:** [U02 migration, U03 snapshots, U04 contract, U07 tests](../certification/05_UPGRADE_BACKLOG.md).

## Context

FR-2/FR-3/FR-7 call for reproducible history. The audit found mutable people, daily membership unions, lost empty states, duplicate events and wrong backdated predecessors. Legacy relation_snapshots alone were not an immutable aggregate.

## Decision and implementation

Use immutable state snapshots plus derived membership diffs/events, **not Event Sourcing**. [snapshots.py](../../app/snapshots.py) and [schema/triggers](../../app/snapshot_schema.py) implement UUID headers, capture/precision, source/reference, lifecycle/completeness and frozen membership/person projection. No CollectorRun/account metadata is invented. Friend/follower streams are independent.

CREATING finalizes to COMPLETE only for a declared entire set with matching item_count, including zero. Partial/unknown observations finalize INCOMPLETE; supplied failures can be retained FAILED. Only COMPLETE participates in current selection/predecessors. SQLite blocks finalized header/membership mutations. Transaction failures roll back the whole source/event operation.

Manual/CSV/JSON imports declare replacement sets; missing people is invalid, explicit [] valid. Current collector/HTML extraction cannot prove completeness and remain UNKNOWN/INCOMPLETE without replacing current relations. Confirmed-empty import supersedes the old target's blanket empty rejection; failed collection cannot imply confirmed empty.

Order by captured_at then insertion sequence, not date identity. Date-only input retains date precision. Backdated policy A repairs edges for the inserted snapshot and immediate successor in the same transaction. Event uniqueness uses from/to IDs, event type and external identity. Historical rendering joins frozen membership. First COMPLETE is a baseline, without invented changes against legacy history.

## Migration and compatibility

U02 advances v1→v2 with pre-change backup, additive schema, rollback and FK/version checks. Legacy tables are retained unchanged without invented completeness. Legacy current membership is used only before first COMPLETE v2 in each stream; legacy events remain labelled unknown. New writes, including synthetic seed relations, use v2. Empty v2 history prevents demo reseeding.

Dashboard relation counts, timeline and person-detail events use new source evidence. People and message_stats remain mutable; AI still uses current person/period information and is not snapshot-reproducible. Attribute/activity diff, full corpus, export/deletion policy, snapshot browser and automatic AI/RAG are outside U03.

## Alternatives and consequences

Daily memberships and mutable current state cannot retain historical attributes/run identity. Full Event Sourcing is unnecessary. Deriving everything on read was considered; adjacent-edge repair preserves existing event-oriented reads while sources remain immutable.

Benefits: reproducible relations, empty/same-day/backdated correctness and replay-safe events. Costs: more storage, schema guards and short SQLite writer transactions. Completeness is a declaration, not independent verification of VK truth. Namespaced screen keys avoid new modulo collisions but do not solve legacy aliases or account switching.

## Security/privacy and evidence

History increases local personal-data storage. No contents are logged or sent to new external services. Retention/export/deliberate deletion remain separate; triggers are not a security boundary against a DB owner who can change schema. Backups retain existing sensitivity/retention limits.

[U03 report](../certification/U03_IMMUTABLE_SNAPSHOT_REPORT.md): 34 new tests; 117 unittest + 8 additional PASS, including SQL immutability, replay/concurrency, backdated repair, empty/current exclusion, migration preservation/backup/rollback and FK checks. User DB untouched. Next recommendation: U04 actual API contract; U07/U11 remain separate.
