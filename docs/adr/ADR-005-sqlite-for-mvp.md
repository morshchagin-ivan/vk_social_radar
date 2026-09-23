# ADR-005 — SQLite for MVP

**Status:** ACCEPTED. **Implementation:** SQLite IMPLEMENTED; migration discipline PLANNED. **Date:** 2026-09-23.
**Decision owners:** владелец VK Social Radar и architecture maintainer (роли).
**Related backlog:** [U02 migration, U03 data model, U12 persistence boundaries](../certification/05_UPGRADE_BACKLOG.md).

## Context

Текущий продукт — local single-user app с восемью таблицами, raw SQL и одним backend. Нет измеренного требования к distributed writes, HA или multi-tenancy. [db.py](../../app/db.py) уже использует sqlite3/FK/transactions.

## Decision

Сохранить SQLite для MVP и следующего certification upgrade. Добавить безопасную версионированную schema migration U02, затем менять source model U03. PostgreSQL сейчас не нужен: нет соответствующего concurrency/operational requirement, а отдельный server усложнит локальную установку. Это решение по scope, не утверждение о максимальной производительности СУБД.

## Current implementation status

IMPLEMENTED SQLite. `get_connection` открывает локальную БД и включает FK; services/LM/importers выполняют SQL напрямую. **KNOWN P0 DEBT:** installed collector_dialogs имеет 6 columns, fresh DDL — 13; CREATE TABLE IF NOT EXISTS не мигрирует существующую схему.

## Alternatives considered

PostgreSQL; document/files-only storage; другой embedded store. PostgreSQL стоит пересмотреть при измеренной конкуренции writers/remote access. Files-only усложнит уже используемые relational queries/constraints. Замена embedded DB сейчас не устраняет отсутствие migration policy.

## Consequences

- Positive: простое local deployment, транзакции/constraints, удобные isolated fixture databases.
- Negative: schema upgrades/backup/locking требуют дисциплины; raw SQL coupling пока остаётся.
- Risks: installed schema drift, runtime corruption/recovery, рост истории. Fresh-DB tests не покрывают upgrade существующих файлов.

## Security/Privacy impact

Local DB не означает автоматическое шифрование или безопасный Git package. DB/sidecars/backups должны попадать под U06; копирование/restore должно сохранять приватность. Каталог backups в коде не является работающей backup policy.

## Validation/Evidence

[Data status](../certification/DATA_MODEL_STATUS.md), [audit](../certification/00_REPOSITORY_AS_IS.md): 8 actual tables, read-only FK check 0 violations, service tests с temporary SQLite. Target: old→new migration fixture, repeat startup, rollback on failure, preserved data. Рабочая БД в baseline не открывалась на запись.

## Evolution path

Следующая implementation iteration — U02 на synthetic legacy schema; затем U03. U11 измерит growth/recovery/concurrency. PostgreSQL рассматривается только после изменения requirements/measurement evidence.
