# Pattern Inventory

Дата: 2026-09-23. Проверены все прикладные `.py`, `.js`, requirements и Python-тесты; зависимости из `.venv` не считаются реализацией паттернов приложения. Отрицательные выводы относятся к предоставленной рабочей копии, не к неизвестным веткам/коммитам.

## ADR candidates: фактическая реализация

Идентификаторы ADR-001…006 ниже — кандидаты из задания. Их нельзя смешивать с AD-001…006 в конце `08_SYSTEM_ARCHITECTURE.md`: там другая нумерация решений. Отдельных ADR-файлов с этими шестью идентификаторами нет; rationale частично находится в `specs/001-vk-profile-analysis/research.md`.

| Candidate | Verdict | Evidence и граница |
|---|---|---|
| ADR-001 Local-first Architecture | PARTIAL | локальные SQLite/files и bind `127.0.0.1` (`db:8`, `run_server:6`); optional localhost LLM. Настраиваемый endpoint без local-only validation (`lmstudio:17,36`) не гарантирует privacy invariant |
| ADR-002 Playwright instead of VK API | IMPLEMENTED | `collector.start:186` → `async_playwright` + persistent context; `collect:617` → DOM extractors; main routes 143/182/195. Direct VK API client не найден; live browser не запускался |
| ADR-003 Immutable Snapshot as Source of Truth | CONTRADICTED_BY_CODE | mutable people/message_stats, daily relation rows, отсутствие snapshot aggregate; `services:165,194,201,235,250`; синтетические probes подтверждают несогласованность |
| ADR-004 Local LLM + Provider Abstraction | PARTIAL | concrete LM Studio integration wired (`main:132` → `lmstudio:57`); abstraction, selection, Ollama implementation отсутствуют |
| ADR-005 SQLite for MVP | IMPLEMENTED | `db.get_connection:21`, 8 CREATE TABLE; schema прочитана в существующей БД; это не свидетельство готовности migrations |
| ADR-006 RAG Architecture | DOCUMENTED_ONLY | C4/AI diagrams и spec FR-8/9; `generate_person_insight` формирует prompt непосредственно из person_data, без query retrieval |

## LLM Provider verdict

**Status: NOT_IMPLEMENTED — provider abstraction. Concrete LM Studio integration: IMPLEMENTED по коду и wiring; успешный live inference в аудите не проверялся.** Предварительное утверждение «Provider/Adapter уже работает» подтверждается только в смысле конкретной HTTP-интеграции, не vendor abstraction.

**Evidence:** `app/lmstudio.py:40` `list_models`, `:57` `generate_person_insight`, `:131` прямой `httpx.Client.post`; `app/main.py:13` imports конкретного модуля; `:132` `create_insight`.

**Interface:** Protocol/ABC/abstract method/структурный provider contract не найден. Нет injection/factory/registry, принимающего provider реализацию.

**Implementations:** только набор функций `app/lmstudio.py` с OpenAI-compatible `/models`, `/chat/completions`. Ollama adapter отсутствует. Возможность вручную указать совместимый URL не доказывает Ollama implementation и не тестировалась.

**Configuration:** SQLite `app_settings`, allowlist `lmstudio_base_url`, `lmstudio_model`, `lmstudio_temperature`; default endpoint `127.0.0.1:1234/v1`, model empty → first listed model, temperature 0.2. UI `static/app.js:40,41,58`, `static/index.html:145`. Guide `llm_provider` не поддерживается и игнорируется. Автовыбор первой модели — выбор model, не provider.

**Call sites:** GET `/api/lmstudio/models` → list_models; POST `/api/lmstudio/test` → test_connection → list_models; POST `/api/people/{person_id}/insight` → person_detail → generate_person_insight → store_insight. UI runInsight (`static/app.js:38`), loadModels (`:41`); кнопка проверки UI вызывает GET models, не POST test.

**Violations:** business prompt/schema, provider transport, configuration и persistence смешаны в одном модуле; main напрямую зависит от LM Studio functions; SQL вызывается и для settings, и для AI result. Нет vendor-neutral request/response contract, error translation, injection seam или client unit tests. Указанный JSON Schema передаётся серверу, но ответ локально только `json.loads` и index access: enum/required/range не валидируются независимо от server enforcement.

## LLM resilience — отдельная проверка

| Capability | Verdict | Evidence |
|---|---|---|
| Timeout | IMPLEMENTED | `httpx.Client(timeout=8.0)` для models (`lmstudio:41`), 120.0 для completions (`:131`); не общий deadline бизнес-операции |
| Retry | NO | один GET/POST, нет loop/policy/transport retries/max_attempts; exceptions выходят в main |
| Exponential Backoff | NO | отсутствует в LLM path |
| Jitter | NO | отсутствует в LLM path |
| Circuit Breaker | NO | нет fail counter, CLOSED/OPEN/HALF_OPEN, threshold/recovery/probe gating |
| Fallback | PARTIAL | non-AI endpoints независимы, UI показывает unavailable/error (`main:115–140`, `static/app.js:38,41`); нет смены модели/provider, cached-result fallback или rule-based replacement |
| Tests | NO | тест settings default в `test_v02.py` не проверяет timeout/retry/inference/failure recovery |

Retryable exception classification: **NO**. Max attempts policy: **NO** (фактически один HTTP вызов на endpoint; выбор model может вызвать отдельный GET перед POST). Failure threshold/recovery timeout: **NO**. Health check: **PARTIAL**, `/api/lmstudio/test` проверяет только доступность `/models`; не inference capability. `/api/health` — константный liveness, не dependency readiness.

Поиск включал `retry, backoff, jitter, tenacity, circuit, breaker, timeout, max_attempts, attempt, fallback, health, connection_error, httpx, requests, aiohttp`. Найденные attempts/readiness polling (`collector._wait_for_member_list_container:1219`), dialog scroll fallbacks и operation states относятся к DOM collection. Они не являются LLM retry или breaker. `try/except` в main только преобразует исключение в HTTP 503. Любое исключение, включая ошибку JSON, преобразуется одинаково — retryable/non-retryable classification нет.

## Реестр паттернов

### 1. Immutable Snapshot

- **Status:** PARTIAL для хранения истории relations; invariant immutable aggregate **CONTRADICTED_BY_CODE**.
- **Problem solved:** сравнение текущих friend/follower membership sets с предыдущей датой.
- **Implementation:** `relation_snapshots(person_id,relation_type,snapshot_date)`; `INSERT OR IGNORE`; новые даты добавляют membership rows. Collector friends/followers через save-preview вызывает import_snapshot. Аналитика читает эти rows, но также mutable people/message_stats/import_jobs без snapshot scope.
- **Evidence:** `app/db.py:45`; `app/services.py:_latest_snapshot_dates:9`, `_snapshot_ids:21`, `import_snapshot:165`, `save_collector_preview:289`.
- **Tests:** `test_services.py:test_import_snapshot_detects_change`, `test_v03.py:test_save_friend_preview`; audit synthetic probes.
- **Gaps:** нет Snapshot object/id, completeness/status/version/hash/source_run; пустая коллекция не создаёт запись. Один календарный день объединяет прогоны. Same-day subset оставляет старые membership rows, тогда как diff использует только входной current_ids. Повтор imports дублирует события; people upsert меняет отображение исторических данных; friend→follower меняет/удаляет события. Backdated import выбирает одну из двух последних дат, а не гарантированно ближайшего хронологического предшественника. Полная история профилей и единый source of truth не обеспечены.

### 2. Repository

- **Status:** NOT_IMPLEMENTED.
- **Problem solved (цель):** отделение persistence от business services.
- **Implementation:** connection context manager, без repository interfaces/implementations.
- **Evidence:** `services.py:6,31,104,165`, `lmstudio.py:8,11,142`, `importers.py:12,105` содержат SQL напрямую. Классы SnapshotRepository/PersonRepository/TimelineRepository существуют только в `16_CLASS_DIAGRAM.md:143`.
- **Tests:** service integration с временной SQLite есть; repository contract tests нет.
- **Gaps:** get_connection — resource management helper, не Repository. Business code зависит от SQL/schema; memory fake нельзя подставить через domain interface.

### 3. Dependency Inversion

- **Status:** NOT_IMPLEMENTED.
- **Problem solved (цель):** независимость high-level use cases от IO.
- **Implementation:** обычные модульные imports и конкретные вызовы; interface layer отсутствует.
- **Evidence:** `main.py:11,13,22`, `services.py:6`, `collector.py:15,193`, `lmstudio.py:6,8,131`.
- **Tests:** patch DB_PATH подтверждает тестируемость через monkeypatch, не DIP.
- **Gaps:** API → concrete functions/singleton; services → SQLite helper; AI module создаёт httpx client. Прямого создания Playwright внутри analytics services нет: это выполняет collector infrastructure. Не следует выдумывать нарушение Domain→Playwright, отдельного domain layer нет.

### 4. Adapter

- **Status:** PARTIAL.
- **Problem solved:** привести внешние данные/HTTP к формату приложения.
- **Implementation:** concrete browser wrapper и LM Studio HTTP module; file parsers преобразуют форматы в dicts.
- **Evidence:** `SafeVKCollector:176`, `_extract_visible_profiles:714`, `lmstudio.generate_person_insight:57`, `importers._rows_from_file:79`.
- **Tests:** CSV import и public source classification; нет LLM adapter tests.
- **Gaps:** LLM port отсутствует; browser wrapper тесно смешивает navigation/extraction/policy/state. Persistence adapter interface и export adapters отсутствуют. Adapter-подобная граница не подтверждает взаимозаменяемость vendors.

### 5. Strategy in Collector

- **Status:** NOT_IMPLEMENTED как заменяемый Strategy pattern.
- **Problem solved (частично):** разные DOM surfaces имеют разные extractors.
- **Implementation:** `collect(kind)` hardcoded if/elif: friends/followers используют `_collect_profiles`, dialogs — `_collect_dialogs`. Organization source — отдельный метод той же большой class.
- **Evidence:** `collector.py:617,804,1801,2539`.
- **Tests:** source-marker assertions в v031/v04/v041/v042, source classification v043; не substitution tests.
- **Gaps:** нет contract/registry/injected parser; замена или добавление стратегии требует изменения collector. subscriptions и общий community collector отсутствуют; public organization member scan не эквивалентен им. Наличие `strategy` строки в result metadata — не Strategy pattern.

### 6. Pipeline

- **Status:** PARTIAL.
- **Problem solved:** преобразование collected/imported data в persisted records и аналитику.
- **Implementation:** Collect → DOM parse/clean/dedup → preview → manual save → relation import/diff либо dialogs save. Import: file → parse → normalize → ограниченная validation → upsert → events. AI запускается отдельно по пользователю.
- **Evidence:** `collector.collect:617`, `importers._dispatch:158`, `services.save_collector_preview:289/import_snapshot:165`, `main.create_insight:132`.
- **Tests:** import/save/service integration, не end-to-end stage contract.
- **Gaps:** нет единого Collect→Parse→Normalize→Validate→Snapshot→Diff→Analytics→RAG→AI orchestration. Snapshot aggregate/RAG отсутствуют; stages не имеют явных contracts/completeness checks; AI не запускается автоматически после snapshot. Не каждый последовательный вызов — полноценный pipeline framework.

### 7. Anti-Corruption Layer (ACL)

- **Status:** PARTIAL.
- **Problem solved:** очистка/нормализация VK DOM и файлов на входе.
- **Implementation:** `_normalize_person` нормализует aliases id/name; DOM cleaners/validators; public organization mapper добавляет source_context/observed_at и не трактует membership как employment.
- **Evidence:** `importers.py:16,53,158`, `collector.py:714,1772,2303,2644`.
- **Tests:** CSV import, 4 behavior classification tests; normalization edge cases не покрыты.
- **Gaps:** domain models/типизированных границ нет, raw dict structures проходят до services/UI; synthetic screen_name ID в `services:185` смешивает external identity и storage key, ограниченный modulo допускает collisions. Organization profile dict несовместим с friend preview persistence. ACL неполный, не отдельный слой.

### 8. RAG

- **Status:** NOT_IMPLEMENTED runtime / DOCUMENTED_ONLY architecture. **Level: NO_RAG.**
- **Problem solved (цель):** grounded ответы на вопросы по истории с найденным релевантным контекстом.
- **Implementation:** обычный context-enriched prompt по person ID, последнему message_stats и первым 10 events. Это фиксированная выборка, а не query-dependent retrieval.
- **Evidence:** `services.person_detail:104`, `lmstudio.generate_person_insight:57–139`; `db:33` не создаёт индекс/embeddings, `main` не имеет chat route.
- **Tests:** retrieval tests отсутствуют.
- **Gaps:** ingestion/indexing/chunking/embedding/index/search/retrieval chain отсутствует; подробная матрица ниже.

| RAG stage/feature | State | Evidence |
|---|---|---|
| Ingestion в knowledge corpus | NO | бизнес-импорт данных не ingestion retrieval index |
| Chunking | NO | нет chunks/source document IDs |
| Embeddings / dense | NO | нет embeddings HTTP call/model/vector column |
| Storage/index | NO | SQLite application tables, не retrieval index |
| BM25/sparse | NO | нет FTS/query rank |
| Hybrid / RRF / reranker | NO / NO / NO | код отсутствует |
| Query retrieval / metadata filtering | NO | person_id SQL lookup не retriever с source metadata filters |
| Context assembly | YES, limited non-RAG | latest stats + events[:10], `lmstudio:66–82` |
| Prompt construction / LLM call | YES | `lmstudio:101,131`; это не доказательство RAG |
| Citations / evidence | PARTIAL text evidence only | LLM генерирует array strings; нет проверяемых chunk/snapshot/event citations |
| Retrieval tests/evaluation | NO | тестов retrieval relevance/faithfulness нет |

### 9. Retry

- **Status:** NOT_IMPLEMENTED для LLM.
- **Problem solved (цель):** ограниченное восстановление после временной транспортной ошибки.
- **Implementation:** отсутствует; один request per endpoint.
- **Evidence:** `lmstudio.list_models:40`, `generate_person_insight:131`, `requirements.txt`.
- **Tests:** NO.
- **Gaps:** classifier, budget, max attempts, backoff, jitter отсутствуют. Browser polling не компенсирует LLM failure.

### 10. Circuit Breaker

- **Status:** NOT_IMPLEMENTED.
- **Problem solved (цель):** прекратить повторные долгие обращения к неисправной зависимости и контролировать восстановление.
- **Implementation:** отсутствует; exception handling в API только 503.
- **Evidence:** `main.py:115–140`, `lmstudio.py:40,131`; поиск всех runtime файлов не нашёл counter/state/recovery gate.
- **Tests:** NO.
- **Gaps:** CLOSED/OPEN/HALF_OPEN либо эквивалент, failure threshold, recovery timeout, single recovery probe и concurrency semantics отсутствуют. CollectorOperation states не Circuit Breaker.

Итого по **10** обязательным паттернам: **IMPLEMENTED 0 / PARTIAL 4 / Missing (NOT_IMPLEMENTED) 6**. Это строгая оценка паттернов: не отрицание работающих HTTP, SQL, DOM и aggregate функций. Snapshot PARTIAL относится к истории membership; заявленная immutability отдельно опровергнута.
