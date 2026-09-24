# VK Social Radar — Certification Architecture Baseline

**Baseline:** 1.0 · **Updated:** 2026-09-24 · **Repository:** VK Social Radar · **Runtime version:** 0.4.2. U07 build uses `certification/architecture-upgrade` on U06; protected revisions/tags are retained in the build reports.

This repository contains a working MVP and a documented target architecture. Target components are never presented as implemented unless confirmed by code and tests.

После documentary U01 реализованы U02 migration, U05 provider, U09 resilience, U03 immutable relation foundation и U04 runtime contract governance. Принятие остальных ADR не означает готовность кода. Historical audit reports retain their original findings; current status is maintained in the linked status/data/report pages.

## What is implemented

Python/FastAPI и static HTML/CSS/vanilla JS; SQLite; Playwright с отдельным persistent Chromium profile; friends/followers/dialog collection и public organization source collection; preview перед явным сохранением friends/followers/dialogs; локальные импорты; immutable relation snapshots и derived diff/events; message aggregates; U05 provider port с LM Studio adapter и U09 resilience; loopback bind по умолчанию. Organization source имеет API jobs и JSON preview, но не поддерживается общим save-preview service. Код/wiring подтверждены аудитом и implementation tests; live VK/LLM не запускались.

- [Current C4](C4_CURRENT.md) — только фактические зависимости.
- [Architecture Status](ARCHITECTURE_STATUS.md) — статус каждой capability и Uxx.
- [Traceability](TRACEABILITY_MATRIX.md) — реальные требования, API, тесты, ADR.

## Target architecture

[Target C4](C4_TARGET.md): broader source corpus, contracts, persistence ports, replaceable parsers and evaluated retrieval remain target. [Patterns](ARCHITECTURAL_PATTERNS.md): Provider, immutable relation Snapshot and Retry/Backoff/Jitter/Circuit Breaker are IMPLEMENTED in their tested scope. Message analytics/AI are not snapshot-reproducible; runtime RAG = **NO_RAG**.

Graph, Scheduler, Export — более поздний roadmap U14–U16; vector DB/hybrid/RRF/reranker не являются обязательствами baseline. Существующие target SDD сохранены с banner. [Архив прежнего SDD](../../specs/001-vk-profile-analysis/Artefacts.zip) — неизменённый исторический target bundle; его текст не является implementation evidence. [Feature index](../../specs/001-vk-profile-analysis/README.md) объясняет статус копий и старых задач.

## Known gaps

[Technical Debt Register](TECHNICAL_DEBT_REGISTER.md) разделяет дефекты и roadmap. U02/U03 resolve schema upgrade and new relation same-day/empty/replay/backdated defects in code. User DB remains unmigrated; legacy history cannot be reconstructed. U04 resolves current API/OpenAPI drift; U06 implements bounded privacy controls. Full erasure, encryption, exhaustive log review, collector completeness and broader message/AI scope remain open.

- [API status](API_STATUS.md): canonical current `/api`, archived `/api/v1` proposal, U04 implemented.
- [Data model status](DATA_MODEL_STATUS.md): eleven tables, schema v2, immutable relation foundation and preserved legacy history.
- [Security/privacy](SECURITY_PRIVACY_STATUS.md): local defaults есть, strict guarantees частичны.
- [NFR baseline](NFR_BASELINE.md): подтверждённые свойства отдельно от предложенных метрик; неизвестные значения TBD.

## Architecture decisions

[Formal ADR register](../adr/README.md): [001 Local-first](../adr/ADR-001-local-first-architecture.md), [002 Playwright](../adr/ADR-002-playwright-instead-of-vk-api.md), [003 Snapshot](../adr/ADR-003-immutable-snapshot-source-of-truth.md), [004 Provider](../adr/ADR-004-local-llm-provider-abstraction.md), [005 SQLite](../adr/ADR-005-sqlite-for-mvp.md), [006 RAG](../adr/ADR-006-rag-architecture.md). Старые AD-001…006 имеют другую нумерацию; canonical decisions теперь находятся в этом ADR register.

## Verification evidence

Audit от 2026-09-23: **18 unittest passed + 8 existing plain functions passed отдельно**. Это не 26 tests стандартного runner и не live E2E. В baseline-итерации tests не перезапускались; выполнялась только статическая validation. Исходные шесть audit reports сохранены без изменений, включая выявленные FAIL и исходные номера строк старых SDD до banners:

1. [Repository AS-IS](00_REPOSITORY_AS_IS.md).
2. [Architecture inventory](01_ARCHITECTURE_INVENTORY.md).
3. [Pattern inventory](02_PATTERN_INVENTORY.md).
4. [SDD/code gaps](03_SDD_CODE_GAP_ANALYSIS.md).
5. [Readiness audit](04_CERTIFICATION_READINESS.md).
6. [Prioritized U01–U17 backlog](05_UPGRADE_BACKLOG.md).

Текущая документарная готовность отражена в [Checklist](CERTIFICATION_CHECKLIST.md) и [Baseline upgrade report](BASELINE_UPGRADE_REPORT.md); историческая readiness-оценка не переписана задним числом.

## Upgrade roadmap

Working MVP → Architecture Audit → Known Gaps → ADR → Target Architecture → Prioritized Upgrade Backlog → Controlled Evolution.

[Evolution](ARCHITECTURE_EVOLUTION.md) связывает U01–U13 с acceptance evidence. Historical U06 gate: **171 unittest + 8 additional functions PASS**, no network/user DB writes; [report](U06_PRIVACY_ACCESS_HARDENING_REPORT.md). U07 now unifies those gates. For operation use [root README](../../README.md); the [Defense Guide](DEFENSE_GUIDE.md) retains baseline-era context.

U06 supplies bounded privacy/access controls: [security status](SECURITY_PRIVACY_STATUS.md), [threat model](THREAT_MODEL.md), [classification](DATA_CLASSIFICATION.md), [report](U06_PRIVACY_ACCESS_HARDENING_REPORT.md). Its historical gate was **171 unittest + 8 additional PASS**; no network/real DB/profile modification.

## Current quality evidence — U07

**191 automated tests PASS**, all seven gates and twelve architecture fitness invariants PASS. The former 171+8 split is closed. Canonical command: `python scripts/run_quality_gates.py`; [reference](QUALITY_GATE_REFERENCE.md), [U07 report](U07_QUALITY_GATES_CI_REPORT.md). Workflow CONFIGURED LOCALLY, remote GitHub Actions NOT YET VERIFIED, branch protection NOT CONFIGURED. Historical build counts/recommendations above retain their milestone context; current next recommendation only is U08 if RAG remains in scope.
