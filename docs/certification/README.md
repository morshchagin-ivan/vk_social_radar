# VK Social Radar — Certification Architecture Baseline

**Baseline:** 1.0 · **Date:** 2026-09-23 · **Repository:** `C:\Developments\Javascript\VK` · **Runtime version:** 0.4.2. **Branch / commit:** UNAVAILABLE: предоставленная копия не содержит Git metadata. Название ветки в старом feature plan не считается текущей веткой.

This repository contains a working MVP and a documented target architecture. Target components are never presented as implemented unless confirmed by code and tests.

Это документарная baseline-итерация U01 после аудита. Production-код заморожен; U02–U17 не реализовывались. Принятие ADR означает принятие направления, а не готовность кода. Документарная часть U01 подготовлена; Git revision evidence остаётся открытым.

## What is implemented

Python/FastAPI и static HTML/CSS/vanilla JS; SQLite; Playwright с отдельным persistent Chromium profile; friends/followers/dialog collection и public organization source collection; preview перед явным сохранением friends/followers/dialogs; локальные импорты; история связей и diff-like processing; message aggregates; прямой LM Studio HTTP client; loopback bind по умолчанию. Organization source имеет API jobs и JSON preview, но не поддерживается общим save-preview service. Код/wiring подтверждены аудитом; live VK/LLM в нём не запускались.

- [Current C4](C4_CURRENT.md) — только фактические зависимости.
- [Architecture Status](ARCHITECTURE_STATUS.md) — статус каждой capability и Uxx.
- [Traceability](TRACEABILITY_MATRIX.md) — реальные требования, API, тесты, ADR.

## Target architecture

[Target C4](C4_TARGET.md): immutable source snapshots, migration discipline, contracts, ограниченные persistence/provider ports, заменяемые DOM parsers, локальный retrieval с citations/eval. [Patterns](ARCHITECTURAL_PATTERNS.md) отделяет частичные механизмы от отсутствующих паттернов. Runtime RAG = **NO_RAG**; LLM Provider abstraction, immutable Snapshot aggregate, Retry/Circuit Breaker — **PLANNED**.

Graph, Scheduler, Export — более поздний roadmap U14–U16; vector DB/hybrid/RRF/reranker не являются обязательствами baseline. Существующие target SDD сохранены с banner. [Архив прежнего SDD](../../specs/001-vk-profile-analysis/Artefacts.zip) — неизменённый исторический target bundle; его текст не является implementation evidence. [Feature index](../../specs/001-vk-profile-analysis/README.md) объясняет статус копий и старых задач.

## Known gaps

[Technical Debt Register](TECHNICAL_DEBT_REGISTER.md) разделяет дефекты и roadmap. Критичны installed DB schema drift, same-day/empty/repeat snapshot semantics, API/OpenAPI mismatch, raw diagnostics и отсутствие проверяемой Git history. Документирование этих проблем не устраняет их.

- [API status](API_STATUS.md): current `/api`, target `/api/v1`, U04.
- [Data model status](DATA_MODEL_STATUS.md): восемь таблиц и migration U02.
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

[Evolution](ARCHITECTURE_EVOLUTION.md) связывает U01–U13 с acceptance evidence. Следующий рекомендуемый implementation step — **U02: безопасная migration collector_dialogs**, сначала на синтетической копии старой схемы. Он не начат. Для защиты: [Defense Guide](DEFENSE_GUIDE.md), для запуска: [root README](../../README.md).
