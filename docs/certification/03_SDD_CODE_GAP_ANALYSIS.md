# SDD ↔ Code Gap Analysis

Дата: 2026-09-23. Overall: **FAIL для заявленной полной архитектуры**, работающий функциональный прототип с частичной реализацией. FAIL означает несоответствие проверяемому обещанию; WARNING — неполноту evidence/scope; PASS — подтверждённый ограниченный факт. Рекомендации в этом файле не выполнялись.

## Документарный inventory

Обозначения копий: **R** = файл в корне; **S** = одноимённый файл в `specs/001-vk-profile-analysis/`; **Z** = entry в `specs/001-vk-profile-analysis/Artefacts.zip`. Для `spec.md` и всех перечисленных SDD 08–18 (без отсутствующего 13) сравнение SHA-256 R/S/Z подтвердило идентичность. Это три экземпляра одного текста, не три независимых доказательства.

| Требуемый документ | Найденные версии/пути | Status | Оценка |
|---|---|---|---|
| PROJECT_PASSPORT | только ссылка `01_PROJECT_PASSPORT.md` из System Architecture | NOT_FOUND | отдельного паспорта нет, включая Z |
| SPECIFICATION | `spec.md` R/S/Z; `specs/001-testing-feature/spec.md` — другой feature | FOUND, DUPLICATE, CONTRADICTS_CODE | snapshot/RAG/graph scope существенно шире runtime |
| SYSTEM_ARCHITECTURE | `08_SYSTEM_ARCHITECTURE.md` R/S/Z, Draft 1.0 | FOUND, DUPLICATE, CONTRADICTS_CODE | React, scheduler, RAG-exclusive AI, snapshot-only storage не AS-IS |
| C4_MODEL | `09_C4_MODEL.md` R/S/Z | FOUND, DUPLICATE, CONTRADICTS_CODE | intended decomposition не совпадает с module graph |
| DATA_MODEL | `10_DATA_MODEL.md` R/S/Z; `specs/001-vk-profile-analysis/data-model.md`; `specs/001-testing-feature/data-model.md` | FOUND, DUPLICATE, CONTRADICTS_CODE | root ER/feature model разные; обе target-модели не DDL |
| OPENAPI | `11_OPENAPI.yaml` R/S/Z; runtime-generated app.openapi() | FOUND, DUPLICATE, CONTRADICTS_CODE | YAML 18 operations, runtime 29, разные prefix/security/schemas |
| API_GUIDE | `12_API_GUIDE.md` R/S/Z; два `specs/*/contracts/local-api.md` | FOUND, DUPLICATE, CONTRADICTS_CODE | несколько целевых контрактов, пути и поля расходятся |
| BUSINESS_PROCESSES | `14_BUSINESS_PROCESSES.md` R/S/Z | FOUND, DUPLICATE, CONTRADICTS_CODE | BP-02 complete snapshot; BP-06/07 RAG; all-process idempotency не выполняются |
| SEQUENCE_DIAGRAMS | `15_SEQUENCE_DIAGRAMS.md` R/S/Z | FOUND, DUPLICATE, CONTRADICTS_CODE | automatic snapshot pipeline и все длительные операции async — не текущий flow |
| CLASS_DIAGRAM | `16_CLASS_DIAGRAM.md` R/S/Z | FOUND, DUPLICATE, CONTRADICTS_CODE | Snapshot/Repository/RAGService/AIWorker только UML |
| IMPLEMENTATION_PLAN | `17_IMPLEMENTATION_PLAN.md` R/S/Z; оба `specs/*/plan.md` | FOUND, DUPLICATE | планы, не выполненные milestones; feature plan ближе к actual static UI/SQLite |
| IMPLEMENTATION_BACKLOG | `18_IMPLEMENTATION_BACKLOG.md` R/S/Z; оба `specs/*/tasks.md` | FOUND, DUPLICATE | vk-profile-analysis 62 unchecked; testing-feature 46 unchecked; не считать done |
| TEST_PLAN | `tests/01_TEST_PLAN.md` v1.0 Approved | FOUND, OUTDATED относительно actual coverage | покрытие всего target scope декларируется, executable suite намного уже |
| TEST_CASES | `tests/02_TEST_CASES.md` | FOUND | спецификации, не результаты запусков |
| API_TESTS | `tests/03_API_TESTS.md` | FOUND, CONTRADICTS_CODE | contract-first expectations для отсутствующих endpoints; автоматических API tests нет |
| INTEGRATION_TESTS | `tests/04_INTEGRATION_TESTS.md` | FOUND | преимущественно target integration scenarios, не исполняемый suite |
| SMOKE_TESTS | `tests/05_SMOKE_TESTS.md` | FOUND | PASS labels/ожидания не execution evidence; нет runner для описанной полной suite |
| TEST_DATA | `tests/06_TEST_DATA.md`; `sample_import/`; seed fixtures | FOUND, PARTIAL fulfillment | large/history/AI/graph datasets заданы описанием; несколько малых fixtures реализованы |
| ACCEPTANCE_CHECKLIST | `tests/07_ACCEPTANCE_CHECKLIST.md` | FOUND | незаполненные PASS/FAIL boxes, не certificate |
| ROADMAP | отдельного файла нет; этапы `17_IMPLEMENTATION_PLAN.md` | NOT_FOUND standalone | roadmap-подобные планы есть; не дублировать новый документ ради названия |
| ADR | standalone ADR отсутствуют; AD-001…006 в System Architecture; decisions в `specs/001-vk-profile-analysis/research.md` | FOUND inline / NOT_FOUND formal | есть rationale/alternatives, нет registry шести ADR candidates с runtime evidence |

Дополнительно: `README.md` и `FILE_MANIFEST.md` описывают v0.4.2 dialog scroll fix; `app/collector.py` и v043 tests включают более поздний organization-source flow, отсутствующий в README/API docs. Manifest содержит старый размер collector (36013 bytes) и не является доказательством состава Git. Ссылки System Architecture на `13_DATABASE_SCHEMA.md`, специализированные Collector/AI/RAG/Graph документы не разрешаются в предоставленном дереве. `specs/001-testing-feature` — запланированная функция управления тестовыми запусками пользователем, не доказательство существующего QA automation.

## Проверенные расхождения

| ID / Verdict | Document / Section | Code location | Description | Impact | Recommendation |
|---|---|---|---|---|---|
| G01 FAIL | spec FR-2; Data Model Snapshot | `services.import_snapshot:165`, `db:45` | вместо full immutable snapshot — membership по дню; people mutable | история неповторяема, snapshot first нельзя защищать | определить минимальный immutable aggregate с completeness/version/run identity |
| G02 FAIL | Business Processes, idempotency | `services:194–245` | same-day input/result расходится с stored set; повтор событий; empty snapshot теряется | недостоверные diff/dashboard | зафиксировать semantics повторов/empty/backdated; regression cases до upgrade |
| G03 FAIL | Implementation Plan stabilization; Data Architecture | `db.init_db:33`, `services:307` | installed collector_dialogs старее DDL, нет миграции | сохранение dialog metadata несовместимо с существующей БД | versioned migration + проверка old→new с сохранением данных |
| G04 FAIL | OpenAPI servers/paths/security; API Guide | `main:27–258`, `run_server:6` | `/api/v1` vs `/api`, 18 vs 29, auth отсутствует | документация не пригодна как контракт | canonical AS-IS/target contract и contract gate; scope decision для auth |
| G05 FAIL | API Guide Settings; Architecture Local LLM | `lmstudio:17,40,57`, `main:13` | llm_provider ignored; нет provider abstraction/Ollama | vendor abstraction не доказана | маленький provider port/factory, contract tests; не заявлять Ollama до adapter test |
| G06 WARNING | spec AF-3; Reliability | `lmstudio:41,131`, `main:123,132` | timeout есть, retry/backoff/jitter/breaker нет; все exceptions → 503 | каждый request может долго ждать неисправный LLM | обоснованная bounded policy и breaker при принятом NFR, deterministic tests |
| G07 FAIL | System Architecture AD-004; spec FR-8/9 | `lmstudio.generate_person_insight:57` | прямой fixed context; нет RAG/chat | центральная AI-architecture часть только на бумаге | минимальный локальный retrieval с source IDs/eval либо явное исключение из scope |
| G08 FAIL | C4 Frontend, Graph/RAG/Scheduler | `static/app.js`, `collector:2178` | vanilla UI, нет graph/chat/snapshot browser/scheduler | C4 смешивает AS-IS и target | AS-IS диаграммы и отмеченный target; не добавлять React ради диаграммы |
| G09 FAIL | Class Diagram Repository/DIP | `services:6,31`, `lmstudio:8` | SQL в services; concrete imports без ports | нарисованные классы/паттерны не существуют | ограничить ports реально нужными seams, обновить LLD |
| G10 WARNING | Collector components / Normalizer | `collector:617,714,1772`; `importers:16` | отдельные методы/mapper есть, заменяемых strategies/domain schemas нет | изменения DOM затрагивают большую class | parser contract + fixtures для существующих surfaces, не universal framework |
| G11 FAIL | ER Snapshot/Person/Dialog/Run | `db:35–124`, `collector:117` | UUID graph превращён в 8 int-key tables; run в RAM; dialog без FK | traceability/run provenance отсутствует | canonical physical model и обоснование связей; миграции |
| G12 FAIL | spec FR-7/8; BP-05/06 | `services.dashboard:31`, `lmstudio:66` | dashboard смешивает текущие relations и все message periods; AI берёт latest period | нет согласованного snapshot/time scope | определить period/snapshot semantics и provenance |
| G13 WARNING | spec Privacy; Architecture Local First | `lmstudio.save_settings:17`, `_base_url:36` | arbitrary configured endpoint может получить имя/метрики | local-only обещание не enforced | loopback policy/default + явно согласованный remote mode при необходимости |
| G14 FAIL | Privacy First / Logging | `collector._save_diagnostics:2650` | raw HTML, screenshot, page.url без общей редактуры | diagnostics могут сохранять персональные данные/session-bearing URLs | минимизация/redaction/retention, fixtures без реальных данных |
| G15 WARNING | Security / distribution | `.gitignore`, Git unavailable | sensitive runtime artifacts присутствуют; tracked status проверить нельзя | нельзя заверить безопасный Git/package release | повторный index/history/package audit на настоящем repo без вывода секретов |
| G16 WARNING | Browser isolation | `collector._route_request:224` | exception handling продолжает запрос | whitelist fail-open | fail-closed policy и test exceptions в network guard |
| G17 FAIL | Test Plan / API / Integration / Smoke | `tests/test_*.py`, `run_tests.bat` | 18 unittest; 8 plain tests пропускаются; многие marker assertions | green suite не доказывает архитектуру | единый runner, behavioral tests, API/schema/migration/inference mocks |
| G18 WARNING | NFR Performance / stabilization | `spec.md:352`, `17_IMPLEMENTATION_PLAN.md` | spec не задаёт численные NFR; нет benchmark/quality pipeline | нет измеримой fitness baseline | минимальные локальные latency/timeout/volume limits и reproducible gates |
| G19 FAIL | Sequence diagrams, AIWorker/jobs | `main.create_insight:132`, `collector.operations:183` | blocking LLM request; org job volatile; generic collect in-request | async/durable semantics завышены | описать actual concurrency/cancel/restart semantics; worker только при требовании |
| G20 FAIL | Search/Export BP-08/09; YAML | `static/app.js:29,147`, отсутствуют routes | client filters вместо global search; export отсутствует | acceptance сценарии не выполняются | отделить in-scope MVP от roadmap; реализация только принятого scope |
| G21 WARNING | Data collection organization source | `collector:2172`, `services.save_collector_preview:289` | org preview сохраняется в state, service принимает лишь friends/followers/dialogs | generic save-preview отклонит org result | отдельный явный контракт persistence или документированный preview-only scope |
| G22 WARNING | Init / real data provenance | `main.startup:31`, `seed.seed_demo_data:8` | пустая people автоматически запускает demo seed | смешение демонстрационного и пользовательского режима | явный demo mode перед защитой на чистой БД |
| G23 WARNING | Identity/validation | `services:182–188`, `importers:90,134` | screen_name → bounded numeric surrogate; ZIP without expanded size bound; raw validation dicts | collision/integrity и memory resource risks | сохранить external namespace/id, ограничить unpack budget и typed validation |
| G24 PASS | Architecture: Analytics not VK | `services.py` imports + raw SQL | аналитика не обращается к VK | независимость read-side от доступности VK | сохранить границу, покрыть architecture test |
| G25 PASS | Collector separate profile | `collector.start:186` | persistent context в отдельном local directory | изоляция пользовательской browser session по каталогу | сохранить, добавить fixtures/операционный сценарий |
| G26 PASS | Local persistence | `db.get_connection:21`, `run_server:6` | SQLite и loopback; нет cloud sync клиента | подходит single-user local MVP | не вводить distributed stack без требования |

## Test inventory и фактическое покрытие

Status TESTED означает наличие behavior test для конкретной области, не 100% coverage. Большие области ниже PARTIAL из-за узости проверок. Аудиторские одноразовые probes не добавлялись в репозиторий и не заменяют maintained suite.

| Area | Status | Реальные tests / пробел |
|---|---|---|
| Unit | PARTIAL | 4 classification functions v043 behavior; helpers/normalization/edge cases покрыты мало |
| API | NOT_TESTED в existing suite | main route strings v043 — не HTTP requests; audit health 200/target 404 только отдельный smoke |
| Integration | PARTIAL | SQLite services/seed, file import, preview persistence: test_services/v02/v03/v04 |
| Smoke | NOT_TESTED maintained suite | Markdown scenarios и audit health, без app startup/UI/LLM/collector E2E |
| Collector | PARTIAL | profile path/whitelist и source markers; нет DOM fixtures/live scenario доказательства |
| Snapshot | PARTIAL | basic import change/save_friend_preview; immutability/empty/repeat не проверялись suite |
| Diff | PARTIAL | removed >=1 assertion; нет full cases ordering/empty/repeat/transition |
| Timeline | PARTIAL | seeded dashboard changes nonempty; нет event chronology/idempotency tests |
| Graph | NOT_TESTED | code отсутствует |
| Analytics | PARTIAL | seeded totals, message_stats upsert; period consistency и duplicate joins не проверены |
| LLM provider | NOT_TESTED | settings default test не проверяет inference/adapter contract |
| LLM resilience | NOT_TESTED | нет mock transport timeout/recovery/breaker tests |
| RAG | NOT_TESTED | runtime отсутствует |
| Export | NOT_TESTED | runtime отсутствует |
| UI | NOT_TESTED | нет browser UI assertions |
| Migration / installed DB | NOT_TESTED | тесты создают свежую БД, поэтому пропускают обнаруженный schema drift |

18 unittest methods распределены: services 3, v02 3, v03 3, v031 3, v04 2, v041 2, v042 2. Из них 8 — source-marker или whitelist checks (v031 3, v04 marker 1, v041 2, v042 2). Отдельно v043: 4 classification behavior + 4 assertions по source text. Результат аудита: 18/18 + 8/8 passed; это **не 26 pytest passes**. pytest отсутствует в окружении и requirements; 8 plain функций были вызваны напрямую. Coverage measurement/lint gate не найдены.

## Воспроизводимые audit observations

Только temporary SQLite, synthetic A/B, даты 2099-01-01…03; не реальные VK/person данные:

1. Импорт [A,B] на первую и вторую дату, затем [A] на вторую: returned count=1, removed=1, dashboard current=2.
2. Повтор последнего payload: events count 1 → 2.
3. Импорт [] на третью дату: dashboard current=2, поскольку дата пустого состояния не записана.
4. `GET /api/health` через in-process ASGI → 200; `GET /api/v1/health` → 404.
5. Read-only existing DB `collector_dialogs` имеет 6 columns против 13 в fresh DDL. `PRAGMA foreign_key_check` = 0. Это не проверка правильности аналитики.

Базовая команда — `run_tests.bat`; безопасная audit-обёртка патчила DB_PATH/DATA_DIR/IMPORT_DIR/BACKUP_DIR и импортированный `importers.IMPORT_DIR`. Production startup запрещён, потому что init/seed пишет БД. Дополнительные probes не сохранены как новые тесты в соответствии с analysis-only scope.
