# ADR-001 — Local-first Architecture

**Status:** ACCEPTED. **Implementation:** PARTIAL. **Date:** 2026-09-23.
**Decision owners:** владелец VK Social Radar и architecture maintainer (роли; персонально не назначены).
**Related backlog:** [U06 privacy, U11 NFR](../certification/05_UPGRADE_BACKLOG.md).

## Context

[Specification](../../spec.md), Product Principles/Privacy/Constraints: персональная локальная система без обязательной cloud synchronization. Сейчас local storage/bind уже есть, однако configurable LLM endpoint и diagnostics не обеспечивают строгую privacy guarantee.

## Decision

Сохранить local-first deployment: UI/backend, SQLite/files и inference на пользовательской машине. VK web — ожидаемый внешний источник для явного сбора. Non-AI чтение локальных данных не должно требовать VK/LLM. Strict local-only inference policy и минимизация diagnostics принимаются как target U06; remote provider не является скрытым fallback.

## Current implementation status

PARTIAL: [run_server.py](../../run_server.py) слушает 127.0.0.1:8765; [db.py](../../app/db.py) хранит локально. [lmstudio.py](../../app/lmstudio.py) имеет localhost default, но принимает arbitrary URL. Отсутствие обязательной cloud LLM подтверждено code review, а не полным network forensic test.

## Alternatives considered

Cloud-hosted analytics/inference; remote collector; hybrid sync. Не выбраны для текущего scope, поскольку добавляют передачу персональных данных и внешний operational dependency. Local-first не означает offline collection: сбор VK требует сети.

## Consequences

- Positive: локальный контроль storage, простое single-user deployment, чтение истории без VK.
- Negative: пользователь обслуживает local LLM/profile/backups; ресурсы ограничены одним компьютером.
- Risks: arbitrary endpoint, raw diagnostics, неустановленная retention policy; local storage сам по себе не является encryption/access control.

## Security/Privacy impact

U06 должен ограничить endpoints, закрыть fail-open browser guard и проверить реальный Git/package состав. Нельзя утверждать отсутствие cookies/private data в Git: metadata копии отсутствует. [Security status](../certification/SECURITY_PRIVACY_STATUS.md).

## Validation/Evidence

[Audit 00](../certification/00_REPOSITORY_AS_IS.md), `run_server` bind, `db.get_connection`, `lmstudio._base_url`; prior audit health probe. Target validation: negative endpoint tests, safe log fixtures, explicit packaging check. Эти target проверки ещё не выполнены.

## Evolution path

U06 → U11 measurable privacy/retention → U07 regression gates; provider U05 обязан сохранить local policy. Изменение на remote inference требует отдельного явного решения, не незаметной смены defaults.
