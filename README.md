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
- Person insight через LLMProvider → ResilientLLMProvider → LMStudioProvider, выбор model/temperature/endpoint; typed request/result/errors, validation до SQLite save. Person Insight сохраняет fixed context; отдельный U08 RAG service реализован ниже. Ollama adapter/fallback не реализованы.

Code/wiring подтверждены [аудитом](docs/certification/00_REPOSITORY_AS_IS.md) и U02/U03/U05/U09 tests; live VK/LLM не запускались. Dialog persistence после legacy migration подтверждена U02 на временных БД. Рабочая БД во время сборок не изменялась — [data status](docs/certification/DATA_MODEL_STATUS.md).

## Architecture at a glance

[CURRENT C4](docs/certification/C4_CURRENT.md): Static UI → FastAPI → services/raw SQL → SQLite; отдельный browser collector с preview. AI: endpoint → AIInsightService → LLMProvider → ResilientLLMProvider → LMStudioProvider → HTTP. Composition сохраняет одну active endpoint binding на процесс, чтобы breaker работал между requests; existing lmstudio_* settings и UI сохранены. Models/health проходят отдельно без retry и не меняют generation circuit. Analytics читает локальные records без прямого VK access.

## Target architecture

[TARGET C4](docs/certification/C4_TARGET.md): immutable Snapshot, typed API, persistence ports, replaceable parsers и evaluated local retrieval. Migration, Provider и Retry/Exponential Backoff/Jitter/Circuit Breaker реализованы в U02/U05/U09. Immutable friend/follower Snapshot foundation — **IMPLEMENTED U03**; full message/dialog corpus — **PLANNED**; U08 runtime RAG = **STRUCTURED_RAG—LEXICAL**, internal service only. Global DIP остаётся PARTIAL. Social Graph/Scheduler/Export — roadmap, не current features.

## Architecture decisions — ADR-001…006

[ADR register](docs/adr/README.md): [001 Local-first](docs/adr/ADR-001-local-first-architecture.md), [002 Playwright](docs/adr/ADR-002-playwright-instead-of-vk-api.md), [003 Snapshot](docs/adr/ADR-003-immutable-snapshot-source-of-truth.md), [004 Provider](docs/adr/ADR-004-local-llm-provider-abstraction.md), [005 SQLite](docs/adr/ADR-005-sqlite-for-mvp.md), [006 RAG](docs/adr/ADR-006-rag-architecture.md). ACCEPTED — статус решения; implementation status указан отдельно.

## Known limitations

U03 resolves same-day/repeated/empty/backdated defects for new relation snapshots. Legacy history is retained without fabricated capture identity/completeness; message_stats and AI remain outside snapshot reproducibility. U02 исправляет schema drift при startup, но не восстанавливает отсутствующие исторические metadata. U04 canonical OpenAPI now matches current `/api`; old `/api/v1` proposal is archived/non-canonical. Repository/Strategy отсутствуют; DIP ограничен AI/provider boundary. U06 enforces loopback-only LLM, local Host/Origin, fail-closed collector routing and minimized diagnostics/retention. Overall privacy remains bounded: no application auth/encryption, no complete historical/binary secret or third-party debug audit. [Debt register](docs/certification/TECHNICAL_DEBT_REGISTER.md), [API status](docs/certification/API_STATUS.md), [privacy](docs/certification/SECURITY_PRIVACY_STATUS.md).

U09 сохраняет HTTP timeouts 8/120s: retries не гарантируют hard total latency. Circuit state живёт только в процессе и сбрасывается при restart/смене endpoint. При auto-model selection discovery может выполняться даже при OPEN generation; уже допущенные calls могут завершить retry loop. [Точные границы и NFR](docs/certification/NFR_BASELINE.md).

## Verification

[Audit results](docs/certification/00_REPOSITORY_AS_IS.md), [traceability](docs/certification/TRACEABILITY_MATRIX.md) и [baseline validation report](docs/certification/BASELINE_UPGRADE_REPORT.md). Старые test specifications/SDD описывают ожидаемые проверки/target design, а не completed evidence. Quantitative NFR ещё не измерены: [NFR baseline](docs/certification/NFR_BASELINE.md).

## Architecture evolution / backlog

[Evolution stages](docs/certification/ARCHITECTURE_EVOLUTION.md) и [U01–U17 backlog](docs/certification/05_UPGRADE_BACKLOG.md). U02/U03/U04/U05/U09 завершены в заявленном scope; U07 unified runner/fitness IMPLEMENTED, workflow CONFIGURED LOCALLY; U08 internal lexical retrieval IMPLEMENTED; следующий рекомендуемый increment — U10. Вся Data Architecture не объявляется READY.

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

Canonical command: **`python scripts/run_quality_gates.py`** (or `.venv\Scripts\python.exe scripts/run_quality_gates.py`). First install `requirements-dev.txt` in the test environment; Node.js 22.14.0 is required for the existing UI helper test. Validated Python: 3.13.2 on Windows. BAT delegates to the same runner and returns its exit code.

Current U08 local gate: **222 automated tests PASS**, seven gates and **18 architecture fitness invariants PASS**, including 31 RAG tests and six RAG invariants. [Quality reference](docs/certification/QUALITY_GATE_REFERENCE.md). Prior U07 remote Actions success is owner-reported; this U08 revision is locally verified only and has not been pushed. Branch settings are unchanged.

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

Legacy membership supplies current counts only until the first COMPLETE v2 snapshot for that relation stream; legacy events remain labelled `legacy_unknown`. New events render frozen historical names/URLs. The old same-day friend→follower inference is not emitted for new captures: friends/followers have independent evidence. Message analytics/AI are not snapshot-reproducible; RAG was NO_RAG at U03; U08 now adds a separate lexical service. No Event Sourcing or automatic AI pipeline was introduced.

The startup migration supports v1→v2 and recognized v0→v2 with a pre-change SQLite backup. No migration was applied to the user database during this build. Empty v2 user history prevents automatic demo seeding; broader demo-mode work remains U13.

## U04 runtime API contract governance

**IMPLEMENTED**: [canonical OpenAPI 3.1](11_OPENAPI.yaml) generated from FastAPI, [runtime guide](12_API_GUIDE.md), [inventory](docs/certification/U04_RUNTIME_API_INVENTORY.md), [report](docs/certification/U04_API_CONTRACT_REPORT.md). `/api` preserved; 29 public operations + HTML shell, 21 frontend call sites, explicit operationIds, typed responses and accurate errors. Auth is absent; Chat API/Graph/Export remain planned; U08 RAG is internal-only.

Run `.venv\Scripts\python.exe -B scripts/export_openapi.py --check` for artifact drift and `.venv\Scripts\python.exe -B -m unittest discover -s tests -p test_api_contract.py -v` for semantic/UI/behavior coverage. Edit route metadata/models then regenerate with the same exporter without `--check`. JSON-form YAML 1.2 needs no new dependency. Formal OpenAPI validator/client generation was not available/run. No frontend changes.


## U06 privacy and access controls

**IMPLEMENTED in bounded local single-user scope**: [report](docs/certification/U06_PRIVACY_ACCESS_HARDENING_REPORT.md), [threat model](docs/certification/THREAT_MODEL.md), [data classification](docs/certification/DATA_CLASSIFICATION.md). Normal launcher binds 127.0.0.1 with access logging disabled. Only local Host/same-origin browser requests are accepted; there is no application login.

LM Studio URL must use HTTP(S) loopback (localhost normalizes to 127.0.0.1; ::1 supported), without credentials/query/fragment. Public/LAN URLs, environment proxies and redirects are rejected/disabled; there is no remote opt-in. Unsafe legacy URL settings are returned empty and cannot perform inference until explicitly corrected; the build never changes the real DB.

The Chromium profile is fixed at data/vk_browser_profile; former external profile override is ignored. Diagnostics now contain counters only. On collector start or diagnostic write, recognized direct diagnostic files older than 30 days are pruned; .gitkeep, links, subdirectories, DB, profile, imports and previews are excluded. No cleanup ran against real data during this build. Full erasure and broader retention remain separate work; storage is not encrypted.

Uploads use bounded reads, unique contained basenames and safe formats; ZIP expansion is capped at 100 MiB/1000 members, parsed without extraction. Ordinary API errors omit raw payloads, paths and SQL; UI text is escaped and links reject executable schemes. Run `.venv\Scripts\python.exe -B scripts/check_privacy.py` before committing and `.venv\Scripts\python.exe -B -m unittest discover -s tests -p test_privacy.py -v` for security fixtures. The guard reports file/category only and does not certify all historical or encoded secrets.

## U07 — Unified quality gates

[Report](docs/certification/U07_QUALITY_GATES_CI_REPORT.md) · [Command/gate reference](docs/certification/QUALITY_GATE_REFERENCE.md). One runner checks tracked sensitive artifacts/secrets, syntax/imports, canonical OpenAPI, documentation, the full test suite and measured architecture fitness. Tests use temporary data and mocks; no live VK/LM Studio/Chromium or user database is required. Markdown scenarios remain DOCUMENTED_ONLY; live walkthroughs remain MANUAL and unperformed by this gate. Recommendation only: require PRs and the Quality Gates status for main after observing the first remote run; no repository settings were changed.

## U08 — Evaluated local RAG

**IMPLEMENTED — STRUCTURED_RAG—LEXICAL**: COMPLETE persisted relation snapshots/frozen people/timeline events → stable document IDs → derived RAM index → filtered BM25 → bounded context → LLMProvider → validated evidence citations. [Report](docs/certification/U08_LOCAL_RAG_REPORT.md) · [Evaluation](docs/certification/RAG_EVALUATION.md). Internal `app.ai.composition.get_rag_service()` preserves existing API/UI and Person Insight; no RAG endpoint. Empty evidence bypasses model discovery/generation.

Synthetic evaluation: 18 cases, Recall@3/MRR/no-evidence accuracy all 1.0; term-frequency baseline ties BM25. No embeddings/hybrid/reranker, live-model quality claim or perfect prompt-injection protection. Names remain untrusted evidence. Corpus refresh requires a newly composed service; message history is excluded.
