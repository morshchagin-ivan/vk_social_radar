# ADR-005 — SQLite for MVP

**Status:** ACCEPTED. **Implementation:** SQLite IMPLEMENTED; U02 schema migration IMPLEMENTED. **Date:** 2026-09-23.
**Decision owners:** владелец VK Social Radar и architecture maintainer (роли).
**Related backlog:** [U02 migration, U03 data model, U12 persistence boundaries](../certification/05_UPGRADE_BACKLOG.md).

## Context

Текущий продукт — local single-user app с восемью таблицами, raw SQL и одним backend. Нет измеренного требования к distributed writes, HA или multi-tenancy. [db.py](../../app/db.py) уже использует sqlite3/FK/transactions.

## Decision

Сохранить SQLite для MVP и следующего certification upgrade. U02 использует один native version marker `PRAGMA user_version` (0 unversioned → 1 current) и additive ALTER без ORM/framework; далее source model U03. PostgreSQL сейчас не нужен: нет соответствующего concurrency/operational requirement, а отдельный server усложнит локальную установку. Это решение по scope, не утверждение о максимальной производительности СУБД.

## Current implementation status

IMPLEMENTED SQLite и [U02](../certification/U02_SCHEMA_MIGRATION_REPORT.md). `init_db` различает fresh/legacy/unversioned-current/current/future, резервирует writer через BEGIN IMMEDIATE и повторяет detection под lock. До изменения existing unversioned DB выполняется SQLite Connection.backup из отдельного read-only соединения. Семь ALTER, validation, version update и defaults входят в одну transaction; ошибка откатывается и прерывает startup. Current schema проверяется без repair; future version отклоняется без mutation. Services/LM/importers по-прежнему выполняют SQL напрямую.

**D01 RESOLVED in code:** legacy 6→13 подтверждено synthetic fixtures; рабочая пользовательская БД в этой сборке не мигрировалась. NULL сохраняет неизвестные новые metadata; flag defaults 0 обязательны для существующего runtime и не являются наблюдением false. Unversioned 13-column DB также получает backup перед version adoption; fresh/versioned-current — без backup.

## Alternatives considered

PostgreSQL; document/files-only storage; другой embedded store. PostgreSQL стоит пересмотреть при измеренной конкуренции writers/remote access. Files-only усложнит уже используемые relational queries/constraints. Замена embedded DB сейчас не устраняет отсутствие migration policy.

## Consequences

- Positive: простое local deployment, транзакции/constraints, удобные isolated fixture databases.
- Negative: schema upgrades/backup/locking требуют дисциплины; raw SQL coupling пока остаётся.
- Risks: неизвестные schema shapes отклоняются; backup требует места и writer lock; рост истории и recovery time ещё не измерены. Проверки U02 покрывают fresh/legacy/WAL/rollback, но не заменяют эксплуатационную recovery policy.

## Security/Privacy impact

Local DB не означает автоматическое шифрование или безопасный Git package. Migration backups находятся в gitignored `data/backups`, имеют UTC/version/unique filename, не перезаписываются и не удаляются автоматически. Они содержат полную БД; failed copy может оставить неполный файл. Полная retention/restore/privacy policy и SQLite sidecar review остаются U06/U11; U02 не пишет содержимое строк в logs.

## Validation/Evidence

[Data status](../certification/DATA_MODEL_STATUS.md), [U02 report](../certification/U02_SCHEMA_MIGRATION_REPORT.md), [behavior tests](../../tests/test_migrations.py): 14 migration tests, 18 existing unittest и 8 additional functions PASS; exact dialog schema, expected tables/version/FK checks. Legacy row values/IDs/count preserved; real metadata write, three init calls, backup refusal, failure rollback, future guard, WAL backup verified. Рабочая БД открывалась только read-only для preflight; hash unchanged.

## Evolution path

Следующая рекомендуемая implementation iteration — U03; U02 завершена. U11 измерит growth/recovery/concurrency. PostgreSQL рассматривается только после изменения requirements/measurement evidence.
