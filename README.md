# VK Social Radar

Локальное приложение для сбора доступных пользователю данных VK, просмотра истории связей, агрегатов сообщений и AI-интерпретации метрик через LM Studio. Текущий runtime: Python/FastAPI, static HTML/CSS/vanilla JavaScript, SQLite и Playwright.

## Certification Architecture Baseline

Baseline 1.0 · 2026-09-23 · runtime 0.4.2. Защищённый tag `v0.4.2-certification-baseline` указывает на `e34624462fa8ef3cdf56e29ce64cab24aac61411`. Последующее изменение **U02 IMPLEMENTED** добавляет безопасную миграцию SQLite; [отчёт](docs/certification/U02_SCHEMA_MIGRATION_REPORT.md). Исторические audit reports сохранены.

**U05 IMPLEMENTED** поверх U02: LLMProvider port, LM Studio adapter, отдельный AIInsightService и локальная валидация output — [отчёт](docs/certification/U05_LLM_PROVIDER_REPORT.md). DIP реализован только на AI/provider boundary.

**U09 IMPLEMENTED** поверх U05: generation retry, exponential backoff, full jitter и CLOSED/OPEN/HALF_OPEN Circuit Breaker — [отчёт](docs/certification/U09_LLM_RESILIENCE_REPORT.md). Max 3 attempts, max retry sleep 1.5s, threshold 3 exhausted logical calls, recovery 30s и один probe. Total deadline НЕ enforced; это internal policy, не измеренный latency SLO.

This repository contains a working MVP and a documented target architecture. Target components are never presented as implemented unless confirmed by code and tests.

**U03 IMPLEMENTED**: immutable friend/follower snapshots, explicit empty states, stable same-day identity, deterministic diffs/events and safe v1→v2 migration — [report](docs/certification/U03_IMMUTABLE_SNAPSHOT_REPORT.md). Collector observations remain incomplete until completeness can be established; message analytics/AI are outside snapshot reproducibility.

Начните с [certification landing](docs/certification/README.md), [Architecture Status](docs/certification/ARCHITECTURE_STATUS.md) и [Defense Guide](docs/certification/DEFENSE_GUIDE.md).

## What works today — AS-IS

- Локальные API/UI/SQLite, loopback bind по умолчанию.
- Schema version 2 (`PRAGMA user_version`): immutable relation foundation plus preserved legacy dialogs 6→13 columns, backup перед upgrade, транзакционный откат, повторяемый startup и отказ от future schema.
- Отдельный persistent Chromium profile и collection friends/followers/dialogs; public organization source API/jobs.
- Preview перед явным save поддерживаемых friends/followers/dialog kinds. Organization preview пока сохраняется в RAM/JSON и не совместим с общим save-preview.
- Импорты JSON/CSV/TSV/HTML/ZIP, relation history/diff-like processing, журнал изменений и message aggregates.
- Person insight через LLMProvider → ResilientLLMProvider → LMStudioProvider, выбор model/temperature/endpoint; typed request/result/errors, validation до SQLite save. RAG отсутствует; Ollama adapter/fallback не реализованы.

Code/wiring подтверждены [аудитом](docs/certification/00_REPOSITORY_AS_IS.md) и U02/U03/U05/U09 tests; live VK/LLM не запускались. Dialog persistence после legacy migration подтверждена U02 на временных БД. Рабочая БД во время сборок не изменялась — [data status](docs/certification/DATA_MODEL_STATUS.md).

## Architecture at a glance

[CURRENT C4](docs/certification/C4_CURRENT.md): Static UI → FastAPI → services/raw SQL → SQLite; отдельный browser collector с preview. AI: endpoint → AIInsightService → LLMProvider → ResilientLLMProvider → LMStudioProvider → HTTP. Composition сохраняет одну active endpoint binding на процесс, чтобы breaker работал между requests; existing lmstudio_* settings и UI сохранены. Models/health проходят отдельно без retry и не меняют generation circuit. Analytics читает локальные records без прямого VK access.

## Target architecture

[TARGET C4](docs/certification/C4_TARGET.md): immutable Snapshot, typed API, persistence ports, replaceable parsers и evaluated local retrieval. Migration, Provider и Retry/Exponential Backoff/Jitter/Circuit Breaker реализованы в U02/U05/U09. Immutable friend/follower Snapshot foundation — **IMPLEMENTED U03**; full message/dialog corpus and RAG — **PLANNED**, runtime RAG = **NO_RAG**. Global DIP остаётся PARTIAL. Social Graph/Scheduler/Export — roadmap, не current features.

## Architecture decisions — ADR-001…006

[ADR register](docs/adr/README.md): [001 Local-first](docs/adr/ADR-001-local-first-architecture.md), [002 Playwright](docs/adr/ADR-002-playwright-instead-of-vk-api.md), [003 Snapshot](docs/adr/ADR-003-immutable-snapshot-source-of-truth.md), [004 Provider](docs/adr/ADR-004-local-llm-provider-abstraction.md), [005 SQLite](docs/adr/ADR-005-sqlite-for-mvp.md), [006 RAG](docs/adr/ADR-006-rag-architecture.md). ACCEPTED — статус решения; implementation status указан отдельно.

## Known limitations

U03 resolves same-day/repeated/empty/backdated defects for new relation snapshots. Legacy history is retained without fabricated capture identity/completeness; message_stats and AI remain outside snapshot reproducibility. U02 исправляет schema drift при startup, но не восстанавливает отсутствующие исторические metadata. OpenAPI target `/api/v1` не соответствует current `/api`. Repository/Strategy отсутствуют; DIP ограничен AI/provider boundary. Arbitrary LLM endpoint/raw diagnostics/fail-open whitelist мешают строгой privacy guarantee; полный privacy audit Git history остаётся U06. [Debt register](docs/certification/TECHNICAL_DEBT_REGISTER.md), [API status](docs/certification/API_STATUS.md), [privacy](docs/certification/SECURITY_PRIVACY_STATUS.md).

U09 сохраняет HTTP timeouts 8/120s: retries не гарантируют hard total latency. Circuit state живёт только в процессе и сбрасывается при restart/смене endpoint. При auto-model selection discovery может выполняться даже при OPEN generation; уже допущенные calls могут завершить retry loop. [Точные границы и NFR](docs/certification/NFR_BASELINE.md).

## Verification

[Audit results](docs/certification/00_REPOSITORY_AS_IS.md), [traceability](docs/certification/TRACEABILITY_MATRIX.md) и [baseline validation report](docs/certification/BASELINE_UPGRADE_REPORT.md). Старые test specifications/SDD описывают ожидаемые проверки/target design, а не completed evidence. Quantitative NFR ещё не измерены: [NFR baseline](docs/certification/NFR_BASELINE.md).

## Architecture evolution / backlog

[Evolution stages](docs/certification/ARCHITECTURE_EVOLUTION.md) и [U01–U17 backlog](docs/certification/05_UPGRADE_BACKLOG.md). U02/U03/U05/U09 завершены в заявленном scope; следующий рекомендуемый implementation step — U04 actual API contract, пока PLANNED. Вся Data Architecture не объявляется READY.

## Running locally

Для обычной эксплуатации в Windows с установленным Python:

```powershell
.\start.bat
```

Скрипт создаёт `.venv` при необходимости, устанавливает зависимости/Chromium и запускает сервер/UI. При уже подготовленном окружении:

```powershell
.\.venv\Scripts\python.exe run_server.py
```

Адрес: `http://127.0.0.1:8765`, API prefix `/api`. Startup выполняет init_db (теперь с migration) и demo seed при пустой people; это не read-only команда. U02 build не запускал production startup. Existing unversioned schema сначала получает SQLite backup в `data/backups/schema-v<from>-to-v2-<UTC>-<unique>.db`, затем upgrade. Backup failure/unsupported schema/future version останавливают startup; данные не заменяются пустой БД. Fresh/current version 2 не создают migration backup. Файлы backup не перезаписываются и не удаляются автоматически; recovery details — [U02 report](docs/certification/U02_SCHEMA_MIGRATION_REPORT.md). [Dependency-free defense path](docs/certification/DEFENSE_GUIDE.md) не требует запуска приложения.

## Tests

```powershell
.\run_tests.bat
```

Эквивалент: `.venv\Scripts\python.exe -m unittest discover -s tests -v`. U03 standard runner — **117 unittest PASS**: 34 U03 + 25 U09 + 26 U05 AI + 14 U02 migration + 18 existing. Отдельно выполнены **8 existing plain functions PASS** из `tests/test_v043_organization_source.py`; стандартный runner по-прежнему их не обнаруживает. Unified runner/CI — U07; **CI отсутствует**.

U02 изолирует DB/storage/backup paths новых и существующих DB tests; CSV test также подменяет импортированный `IMPORT_DIR`. Тесты используют temporary directories, не рабочие БД/imports/profile и не VK/LLM/network. Две прежние ResourceWarning в marker tests `test_v031.py` не являются failures и остаются вне U02. Команды и результаты — [U02 report](docs/certification/U02_SCHEMA_MIGRATION_REPORT.md); [historical coverage limits](docs/certification/03_SDD_CODE_GAP_ANALYSIS.md).

U05 добавляет fake provider, httpx.MockTransport и in-process API tests с запретом сетевого HTTP; reusable provider contract запускается для fake и LM Studio adapter. [U05 report](docs/certification/U05_LLM_PROVIDER_REPORT.md) содержит mapping/error/validation/API/import-fitness evidence. Успешный live inference этими тестами не заявляется.

U09 добавляет scripted provider, fake monotonic clock/sleeper/random, synchronised concurrency и resilience API tests; network и настоящий `time.sleep` запрещены test guards. [U09 report](docs/certification/U09_LLM_RESILIENCE_REPORT.md) содержит RES/CB/API mapping и команды всех regression gates.

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

## U03 immutable relation foundation

**IMPLEMENTED**: UUID snapshots with frozen person projection, declared completeness, lifecycle, explicit empty sets, deterministic predecessor/diff and idempotent pair events. Backdated imports repair the new and successor edges in one transaction. [Report and evidence](docs/certification/U03_IMMUTABLE_SNAPSHOT_REPORT.md).

Manual/CSV/JSON relation import is a declaration of a complete replacement set, including `people: []`. Missing people is rejected. Partial/unknown input cannot replace current truth. Current DOM collector and HTML anchor extraction cannot prove completeness: saves retain INCOMPLETE observations and the UI explains that current relations were not changed. Re-saving the same preview reuses its ID. Dialog saves remain independent.

Legacy membership supplies current counts only until the first COMPLETE v2 snapshot for that relation stream; legacy events remain labelled `legacy_unknown`. New events render frozen historical names/URLs. The old same-day friend→follower inference is not emitted for new captures: friends/followers have independent evidence. Message analytics/AI are not snapshot-reproducible; RAG remains NO_RAG. No Event Sourcing or automatic AI pipeline was introduced.

The startup migration supports v1→v2 and recognized v0→v2 with a pre-change SQLite backup. No migration was applied to the user database during this build. Empty v2 user history prevents automatic demo seeding; broader demo-mode work remains U13.
