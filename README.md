# VK Social Radar

Локальное приложение для сбора доступных пользователю данных VK, просмотра истории связей, агрегатов сообщений и AI-интерпретации метрик через LM Studio. Текущий runtime: Python/FastAPI, static HTML/CSS/vanilla JavaScript, SQLite и Playwright.

## Certification Architecture Baseline

Baseline 1.0 · 2026-09-23 · runtime 0.4.2. Git branch/commit недоступны в предоставленной копии. В этой итерации изменена только документация; audit reports сохранены, production-код заморожен.

This repository contains a working MVP and a documented target architecture. Target components are never presented as implemented unless confirmed by code and tests.

Начните с [certification landing](docs/certification/README.md), [Architecture Status](docs/certification/ARCHITECTURE_STATUS.md) и [Defense Guide](docs/certification/DEFENSE_GUIDE.md).

## What works today — AS-IS

- Локальные API/UI/SQLite, loopback bind по умолчанию.
- Отдельный persistent Chromium profile и collection friends/followers/dialogs; public organization source API/jobs.
- Preview перед явным save поддерживаемых friends/followers/dialog kinds. Organization preview пока сохраняется в RAM/JSON и не совместим с общим save-preview.
- Импорты JSON/CSV/TSV/HTML/ZIP, relation history/diff-like processing, журнал изменений и message aggregates.
- Прямой LM Studio HTTP client, выбор model/temperature/endpoint и person insight. Это не provider abstraction и не RAG.

Code/wiring подтверждены [аудитом](docs/certification/00_REPOSITORY_AS_IS.md); live VK/LLM не запускались при аудите/baseline. Dialog persistence на установленной БД ограничена known schema drift — [data status](docs/certification/DATA_MODEL_STATUS.md).

## Architecture at a glance

[CURRENT C4](docs/certification/C4_CURRENT.md): Static UI → FastAPI → services/raw SQL → SQLite; отдельный browser collector с preview и отдельный LM Studio HTTP flow. Analytics читает локальные records без прямого VK access.

## Target architecture

[TARGET C4](docs/certification/C4_TARGET.md): migration/integrity, immutable Snapshot, typed API, provider/persistence ports, replaceable parsers и evaluated local retrieval. Snapshot aggregate, Provider, Retry/Circuit Breaker и RAG — **PLANNED**, runtime RAG = **NO_RAG**. Social Graph/Scheduler/Export — roadmap, не current features.

## Architecture decisions — ADR-001…006

[ADR register](docs/adr/README.md): [001 Local-first](docs/adr/ADR-001-local-first-architecture.md), [002 Playwright](docs/adr/ADR-002-playwright-instead-of-vk-api.md), [003 Snapshot](docs/adr/ADR-003-immutable-snapshot-source-of-truth.md), [004 Provider](docs/adr/ADR-004-local-llm-provider-abstraction.md), [005 SQLite](docs/adr/ADR-005-sqlite-for-mvp.md), [006 RAG](docs/adr/ADR-006-rag-architecture.md). ACCEPTED — статус решения; implementation status указан отдельно.

## Known limitations

Snapshot semantics имеют same-day/repeated/empty defects; installed collector_dialogs schema отстаёт от DDL. OpenAPI target `/api/v1` не соответствует current `/api`. Repository/DIP/Strategy отсутствуют. Arbitrary LLM endpoint/raw diagnostics/fail-open whitelist мешают строгой privacy guarantee; Git tracked/history проверить нельзя. [Debt register](docs/certification/TECHNICAL_DEBT_REGISTER.md), [API status](docs/certification/API_STATUS.md), [privacy](docs/certification/SECURITY_PRIVACY_STATUS.md).

## Verification

[Audit results](docs/certification/00_REPOSITORY_AS_IS.md), [traceability](docs/certification/TRACEABILITY_MATRIX.md) и [baseline validation report](docs/certification/BASELINE_UPGRADE_REPORT.md). Старые test specifications/SDD описывают ожидаемые проверки/target design, а не completed evidence. Quantitative NFR ещё не измерены: [NFR baseline](docs/certification/NFR_BASELINE.md).

## Architecture evolution / backlog

[Evolution stages](docs/certification/ARCHITECTURE_EVOLUTION.md) и [U01–U17 backlog](docs/certification/05_UPGRADE_BACKLOG.md). Следующий рекомендуемый implementation step — U02 migration на синтетической старой схеме. Baseline не начинает migration/Snapshot/API/provider реализацию.

## Running locally

Для обычной эксплуатации в Windows с установленным Python:

```powershell
.\start.bat
```

Скрипт создаёт `.venv` при необходимости, устанавливает зависимости/Chromium и запускает сервер/UI. При уже подготовленном окружении:

```powershell
.\.venv\Scripts\python.exe run_server.py
```

Адрес: `http://127.0.0.1:8765`, API prefix `/api`. Startup выполняет init_db и demo seed при пустой people; это не read-only команда. В frozen baseline запуск не выполнялся. Не используйте рабочую БД для демонстрации migration/новых функций; текущий drift должен быть закрыт U02. [Dependency-free defense path](docs/certification/DEFENSE_GUIDE.md) не требует запуска приложения.

## Tests

```powershell
.\run_tests.bat
```

Эквивалент: `.venv\Scripts\python.exe -m unittest discover -s tests -v`. Standard runner — **18 unittest**; prior audit отдельно подтвердил **8 existing plain functions** из `tests/test_v043_organization_source.py`. Это не 26 tests стандартного runner. Unified runner/CI — U07; **CI отсутствует**.

Текущий CSV import test без path isolation может писать `data/imports/friends.csv`; audit использовал temporary DB/storage paths. Baseline не перезапускал tests и не устанавливал pytest/dependencies. [Coverage limits](docs/certification/03_SDD_CODE_GAP_ANALYSIS.md).

## Existing v0.4.2 notes — Exact Messenger Scroll Container Fix

Ниже сохранены прежние диагностические инструкции. Это описание реализации, не новый live test result; live VK steps не выполнялись в certification baseline. Diagnostics могут содержать персональные данные — не публикуйте реальные HTML/PNG/JSON.

v0.4.1 по-прежнему видела только 15 диалогов, потому что wheel попадал не в фактический scroll-owner списка.

## Исправлено

- поиск ближайшего scrollable ancestor от реальной строки `convo_*`;
- сохранение цепочки родителей в диагностический JSON;
- наведение мыши прямо на последнюю видимую строку;
- восемь небольших wheel-событий;
- fallback через `scrollTo`, `WheelEvent`, `scroll`;
- fallback через `ArrowDown` и `PageDown`;
- проверка смены первого и последнего `convo_*`, а не только `scrollTop`;
- диагностика после каждого запуска.

## Новый extractor

`vk_reforged_exact_scroll_ancestor_v4`

## Проверка

1. `start.bat`
2. Открыть Chromium.
3. Проверить вход.
4. Нажать «Собрать диалоги».
5. Список должен визуально двигаться.
6. Проверить свежий JSON:
   - `scroll_target_kind`
   - `scroll_target_tag`
   - `scroll_target_class`
   - `scroll_target_height`
   - `scroll_target_client_height`
   - `scroll_target_ancestor_chain`
   - `last_scroll_before`
   - `last_scroll_after`
   - `unique_dialogs`

## Логи

`logs\collector\dialogs_success_*.html`
`logs\collector\dialogs_success_*.png`
`logs\collector\dialogs_success_*.json`
