# Architecture Decision Records

Baseline 1.0 · 2026-09-23. Решения формализованы по поручению владельца проекта для certification baseline. **ACCEPTED относится к архитектурному выбору, не к завершённой реализации.** Именованные ответственные не назначены; roles указаны в ADR. Audit verdicts сохранены в [pattern inventory](../certification/02_PATTERN_INVENTORY.md).

| ADR | Decision status | Implementation status | Backlog |
|---|---|---|---|
| [001 Local-first](ADR-001-local-first-architecture.md) | ACCEPTED | IMPLEMENTED U06 bounded controls; overall privacy assurance PARTIAL | U06 completed; U07/U11/U13 residuals |
| [002 Playwright instead of VK API](ADR-002-playwright-instead-of-vk-api.md) | ACCEPTED | IMPLEMENTED; DOM fragility remains | U10/U06 |
| [003 Immutable Snapshot source of truth](ADR-003-immutable-snapshot-source-of-truth.md) | ACCEPTED | IMPLEMENTED relation foundation; messages excluded | U03 completed |
| [004 Local LLM provider abstraction](ADR-004-local-llm-provider-abstraction.md) | ACCEPTED | IMPLEMENTED provider/AI DIP; U09 resilience implemented | U05/U09 completed |
| [005 SQLite for MVP](ADR-005-sqlite-for-mvp.md) | ACCEPTED | IMPLEMENTED SQLite, U02 migration and U03 schema v2 | U02/U03 completed |
| [006 RAG architecture](ADR-006-rag-architecture.md) | ACCEPTED | IMPLEMENTED: STRUCTURED_RAG—LEXICAL, internal service | U08 completed / U17 evolution |

Canonical numbering — этот register. AD-001…006 в legacy System Architecture обозначают другой набор принципов и не являются прежними версиями этих ADR. В случае расхождения new ADR определяет target baseline, [CURRENT C4](../certification/C4_CURRENT.md) и [audit](../certification/00_REPOSITORY_AS_IS.md) определяют AS-IS. Старые документы остаются историческим evolutionary design.

[Status matrix](../certification/ARCHITECTURE_STATUS.md) · [Backlog Uxx](../certification/05_UPGRADE_BACKLOG.md) · [Certification landing](../certification/README.md).
