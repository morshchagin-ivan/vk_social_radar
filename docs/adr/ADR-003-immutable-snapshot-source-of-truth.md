# ADR-003 — Immutable Snapshot as Source of Truth

**Status:** ACCEPTED / IMPLEMENTATION PLANNED. **Implementation:** PLANNED. **Date:** 2026-09-23.
**Decision owners:** владелец VK Social Radar и architecture maintainer (роли).
**Related backlog:** [U03 snapshots, prerequisite U02 migration, U07 tests](../certification/05_UPGRADE_BACKLOG.md).

## Context

[FR-2/FR-3/FR-7](../../spec.md) требуют исторически воспроизводимого состояния. Audit обнаружил mutable people/message_stats, relation rows по дню, same-day/repeat/empty defects. `relation_snapshots` **не является immutable Snapshot aggregate**.

## Decision

Target: сохранять завершённый collection/import run как immutable source aggregate с identity, timestamp, schema version, source run, completeness и items. Производные diff/events/analytics/index/reports хранить отдельно с source references и version. Исторический source read не меняется от обновления Person. Повтор импорта имеет явную idempotency policy.

Полностью проверенное пустое состояние допустимо; неудачный/неполный scan не представляется успешным пустым Snapshot. Legacy feature task T018 («reject empty») требует reconciliation в U03: нельзя смешивать confirmed-empty и failed collection. Конкретный DDL/ключи выбираются в U03, не в этой итерации.

## Current implementation status

PLANNED aggregate. [services.import_snapshot](../../app/services.py) сохраняет person/type/date rows и вычисляет set differences; [db.py](../../app/db.py) не содержит snapshot header/source_run/version. Audit pattern history PARTIAL, immutable-source invariant **CONTRADICTED_BY_CODE**. Здесь не переименовывается existing table в готовый pattern.

## Alternatives considered

Mutable current state + event log; daily membership rows (AS-IS); полное event sourcing. Первые два не сохраняют независимую историческую версию всех source attributes. Полное event sourcing не требуется для single-user snapshot-oriented scope.

## Consequences

- Positive: reproducible diff/analytics, source lineage, возможность local export позже.
- Negative: дополнительное хранение/versioning, migration и определение completeness.
- Risks: ошибочная отметка partial scan complete, identity collisions, storage growth; retention требует отдельной политики, не перезаписи snapshots.

## Security/Privacy impact

История увеличивает объём локальных персональных данных. U06/U11 должны задать retention/deletion/export rules; immutable source не отменяет явного удаления пользователем по согласованной политике.

## Validation/Evidence

[Audit defects](../certification/03_SDD_CODE_GAP_ANALYSIS.md): same-day 1 vs dashboard 2; repeat events 1→2; empty snapshot не становится current. Target tests: these regressions, backdated ordering, immutable old reads, atomic failure, completeness. Пока не реализованы.

## Evolution path

U02 safe migrations → U03 source model/invariants → U04 contract → U08 retrieval; U12 persistence boundary вводится по нужным seams, а не большим framework rewrite.
