# Certification Readiness

Дата: 2026-09-23. Repository: `C:\Developments\Javascript\VK`; branch/commit UNAVAILABLE — `.git` не предоставлен.

## Executive Summary

**PARTIAL / не готово к защите как реализация полного SDD.** Есть предметный локальный прототип: FastAPI/static UI, отдельный Chromium profile, сбор friends/followers/dialogs и public organization member index, preview/save workflow, SQLite, простые diff/events/aggregates и прямой вызов LM Studio. Код и wiring существуют; успешный live VK/LLM run этим аудитом не подтверждается.

Главные разрывы: immutable Snapshot source of truth опровергнут кодом и синтетическими probes; рабочая DB schema отстаёт от DDL; OpenAPI относится к другой системе интерфейсов; Provider abstraction, Retry, Circuit Breaker и RAG отсутствуют. Green tests в основном подтверждают service happy paths и source markers. Отдельный security блокер evidence — отсутствие Git index/history при наличии чувствительных runtime артефактов.

Для следующей итерации нужен ограниченный вертикальный сценарий с проверяемыми гарантиями, актуальными контрактами и воспроизводимыми тестами. Ни количество диаграмм, ни добавление инфраструктурных технологий сами по себе эти разрывы не закрывают. Политика оценки: READY требует согласованных implementation + wiring + validation evidence, PARTIAL — часть уже есть, MISSING — ключевой механизм/evidence отсутствует. Это инженерная оценка по запрошенным областям, не официальная рубрика курса.

## Evidence matrix

| Area | Status | Evidence | What is missing |
|---|---|---|---|
| 1 Requirements/Scope | PARTIAL | `spec.md` FR/scope/alternatives; 62 unchecked feature tasks | выбранный certification MVP и traceability к реально выполненным сценариям |
| 2 C4 HLD | PARTIAL | 08/09 docs; actual graph в report 01 | current vs target labels; vanilla UI/monolith/preview semantics |
| 3 LLD/Sequence | PARTIAL | 15/16 docs; actual calls `main:132,248` | UML реальных модулей/contracts, failure/cancel/restart sequences |
| 4 Contract-First/OpenAPI | PARTIAL | target YAML + generated 29-operation schema | единый typed contract, auth/error policy, API compatibility gate |
| 5 Data Architecture | PARTIAL | 8 SQLite tables/FK, service integration | installed-schema migration, immutable snapshot scope/version/provenance |
| 6 Architectural Patterns | PARTIAL | concrete wrappers, input mapping, relation history, procedural stages | Repository/DIP/Strategy не реализованы; чёткие границы minimal ports и tests |
| 7 RAG | MISSING | diagrams/spec only | ingestion/retrieval/index/source citations/evaluation; runtime NO_RAG |
| 8 Local LLM integration | PARTIAL | `lmstudio:40,57,131`, UI/API wiring | mock contract tests, output validation, local endpoint policy, synthetic demo evidence |
| 9 Vendor abstraction | MISSING | direct `main` imports `lmstudio`; no provider port | provider interface/selection and tested implementations |
| 10 Security/privacy | PARTIAL | loopback/storage/profile, ignore, source constraints | diagnostics minimization, endpoint restriction, real Git tracked/history proof |
| 11 Testing/Quality Gates | PARTIAL | 18 unittest + 8 direct calls passed | runner collects all tests; contract/migration/edge/failure tests; CI gate |
| 12 ADR/trade-offs | PARTIAL | AD inline, `research.md` decisions/alternatives | approved candidates 001–006, consequences/status and concrete evidence |
| 13 Observability | PARTIAL | collector diagnostics/progress/status | safe structured events, correlation, latency/errors; no sensitive DOM default |
| 14 CI/CD | MISSING | only local bat launch/test scripts | reproducible pipeline and release packaging gate; no deployment cluster needed |
| 15 NFR | MISSING | `spec.md:352` explicitly no quantitative requirements | selected hardware/data scale, deadlines/resource/privacy bounds and measurements |
| 16 Architecture Verification / CTO challenge | PARTIAL | this audit, synthetic defect reproduction, limited tests | automated invariants and demonstration tied to known commit/build |

Итого: **READY 0 / PARTIAL 12 / MISSING 4**. «Нет READY» относится к полным certification areas и не отменяет implemented components в report 01.

## Приоритет защиты

P0 (8 backlog entries): согласовать заявленный scope/AS-IS; обеспечить migration installed DB; устранить snapshot integrity gap; привести API contract к code; подтвердить vendor port, если его заявляем; закрыть privacy/distribution evidence; воспроизводимые тесты; минимальный RAG, если сохраняем его в certification scope. Исключение RAG/provider из scope должно быть явным решением, а не переименованием существующего кода.

P1: обоснованная LLM resilience, replaceable parsers и DOM fixtures, минимальная persistence boundary, safe observability/NFR, demo/user data isolation. Retry и Circuit Breaker нельзя объявлять реализованными до появления механизма и тестов; при низкой частоте локальных вызовов усложнение должно иметь измеримый смысл.

## Технологии, не необходимые этой версии

| Technology | Архитектурное обоснование |
|---|---|
| Kubernetes | один local-user процесс + SQLite/Chromium; нет cluster scheduling/deployment requirement |
| Kafka | нет независимых distributed consumers или streaming throughput; local transaction/job state достаточно |
| Redis | нет измеренной cache bottleneck, shared multi-process session или queue requirement; добавляет local service lifecycle |
| Full CQRS | текущие read/write functions могут жить в одном модуле/БД; immutable source и derived tables не требуют отдельного bus/read service |
| Microservices | deployment и trust boundary локальные; дробление усложнит транзакции и отладку без нагрузки-компенсации |
| MAS | fixed collection/analytics/retrieval steps не требуют переговоров autonomous agents; deterministic use cases проверяемее |
| MCP | runtime не имеет требования предоставлять инструменты внешним AI-клиентам; наличие developer tooling не обосновывает protocol в продукте |
| Feature Store | отсутствует train/serve ML feature lifecycle; SQL aggregates покрывают текущую задачу |
| MLflow | нет training/experiment registry; prompt/model version + небольшой evaluation dataset достаточно для текущей LLM-интеграции |
| Multi-tenancy | один локальный пользователь и отдельный browser profile; tenant isolation требует отдельного продукта/требования |
| HA/DR platform | кластерная доступность не заявлена; нужны простые local backup/restore и atomic operations, а не multi-region failover |
| Federated Learning | модель не обучается на пользовательских данных, нет federated peers/aggregation problem |

Также не нужен React rewrite только ради старой C4-диаграммы; vanilla UI уже wired. Для минимального RAG не обязательны vector service, hybrid/RRF/reranker: выбрать простой retrieval под corpus и подтвердить relevance tests.

## Strongest points for defense

1. **Локальный runtime и простая эксплуатация:** loopback Uvicorn + SQLite; `run_server.py:6`, `app/db.py:8,21`. Можно объяснить trade-off single-user vs distributed infrastructure.
2. **Отдельный persistent Chromium profile:** `SafeVKCollector.start:186` задаёт собственный user_data_dir; авторизация остаётся в browser session, логин через API не реализован.
3. **Разделение collection preview и DB save:** `collector.collect:617`, `main.collector_save_preview:248`; пользователь видит результат до сохранения membership/dialogs. Это реально существующий workflow, не immutable snapshot guarantee.
4. **Локальная аналитика без VK calls:** `services.dashboard:31`, `message_leaderboard:146` используют persisted SQL data; не зависят от browser для чтения.
5. **Нормализация импортов нескольких форматов:** `importers._rows_from_file:79`, `_normalize_person:16`, `_dispatch:158`; CSV behavior подтверждён тестом.
6. **SQL transactions/FK и уникальность:** `db.get_connection:21`, relation/message unique constraints; FK integrity read-only проверена. Ограничения snapshot semantics честно раскрыты.
7. **Конкретная локальная AI-интеграция с ограничивающим prompt:** `lmstudio:57` передаёт metrics/events, требует evidence/cautions и запрещает домыслы о чувствах; transport wired. Evidence strings пока не source citations.
8. **Organization-source collection policy и progress:** `collector._normalize_public_org_profile:1772`, `CollectorOperation:117`, jobs:2178; membership не выдаётся за трудоустройство, есть cancellation/terminal statuses. Jobs volatile, live flow не проверялся.
9. **Пройденные локальные service tests:** 18 unittest и 8 existing function tests; небольшой, но воспроизводимый фундамент. Типы проверок и пробелы известны.

## Likely examiner questions — evidence-based answers

| № | Вопрос | Честный ответ и reference |
|---|---|---|
| 1 | Где immutable Snapshot? | Сейчас только relation_snapshots по дню; гарантия не реализована. `db:45`, `services.import_snapshot:165`; same-day/empty probes report 03 |
| 2 | Можно повторить исторический AI-анализ? | Полностью нет: people и period metrics изменяемы, ai_insights не связаны с snapshot/prompt hash. `services:194,250`, `db:84` |
| 3 | Provider abstraction уже есть? | Нет. Есть concrete HTTP module LM Studio; main импортирует его функции. `main:13`, `lmstudio:57` |
| 4 | Что нужно для Ollama? | Текущая возможность сменить URL — не протестированный adapter. Нужны port/selection/contract tests; Ollama code в копии не найден |
| 5 | Есть retry/backoff/jitter? | Нет; один GET/POST с timeout 8/120 s. `lmstudio:40,131` |
| 6 | Почему try/except не breaker? | Не хранит failures/state и не блокирует обращения до recovery. `main:123,132`; report 02 resilience matrix |
| 7 | Что происходит при недоступной LLM? | AI endpoints возвращают 503, UI показывает ошибку; non-AI SQL endpoints не требуют LLM. Нет cached/provider fallback. `main:115–140`, `static/app.js:38,41` |
| 8 | Где RAG? | В SDD. Runtime использует fixed context последнего period + 10 events, без index/query retrieval. Уровень NO_RAG. `lmstudio:66–82` |
| 9 | Evidence в AI — это цитаты? | Нет, это сгенерированные строки; нет verified source IDs/chunks. `lmstudio:85–99,136–139`, `store_insight:142` |
| 10 | Почему Playwright? | Реализовано чтение доступного пользовательской сессии DOM и persistent Chromium, нет direct VK API client. Trade-off — зависимость от DOM/virtual scrolling. `collector:186,714,2539` |
| 11 | Можно заменить parser без orchestration? | Сейчас отдельные methods, но hardcoded branch в collect. Полного Strategy contract нет. `collector:617` |
| 12 | Чем Repository отличается от get_connection? | get_connection управляет connection/commit; services сами знают SQL/schema. Repository abstractions из UML отсутствуют. `db:21`, `services:31`, `16_CLASS_DIAGRAM.md:143` |
| 13 | Почему OpenAPI-клиент не работает? | Документ задаёт `/api/v1` и 18 target operations; код `/api` и 29 других. Health probe v1=404, actual=200. `11_OPENAPI.yaml:25`, `main:42` |
| 14 | Все endpoints требуют Bearer Token? | Нет. YAML требует, guide исключает health, runtime вообще не внедряет auth. `11_OPENAPI.yaml:51`, `main.py` |
| 15 | Что показало сравнение установленной БД? | Dialog table имеет 6 старых columns, fresh DDL 13; CREATE IF NOT EXISTS не мигрирует. `db:98`, `services:307`; read-only schema inventory report 01 |
| 16 | Почему tests зелёные при этом дефекте? | Tests создают свежую temp DB; migrations не тестируются. `test_v04.py:setUp`, `test_v03.py:setUp` |
| 17 | Все 26 tests запускает bat? | Нет, unittest запускает 18; восемь plain v043 functions пришлось вызвать отдельно. `run_tests.bat`, `test_v043_organization_source.py` |
| 18 | Как доказать local-first? | Defaults/storage/bind локальные; строгая гарантия пока неполна из-за arbitrary LLM URL. `db:128`, `lmstudio:17,36`, `run_server:6` |
| 19 | Cookies и private data не попали в Git? | В этой копии нельзя подтвердить: нет Git metadata. Profile/previews/diagnostics присутствуют; ignore не доказывает отсутствие tracked/history. Report 00 security |
| 20 | Логи безопасны? | Trace sanitizer есть, но raw DOM/screenshots/URL сохраняются без общей редактуры. Нужна минимизация; реальные logs аудит не выводил. `collector:163,2650` |
| 21 | Scheduler и worker где работают? | Scheduler отсутствует; org jobs — asyncio tasks/RAM, AI — synchronous function в FastAPI threadpool. `collector:2178`, `main:132` |
| 22 | Что произойдёт при restart job? | Operations/result state в RAM потеряется; отдельный preview JSON может сохраниться, resume из него не реализован. `collector:183,2175,2205` |
| 23 | Почему не Kubernetes/Kafka? | Нет distributed scale/availability requirement; они не решат snapshot/contract/schema gaps. `run_server.py`, `db.py`, NFR `spec.md:352` |
| 24 | Что именно доказывает этот аудит? | Code/wiring/schema и изолированные tests; не live VK/LLM readiness, не Git history, не 100% coverage. Границы и результаты report 00 |

Следующая итерация: [05_UPGRADE_BACKLOG.md](05_UPGRADE_BACKLOG.md). Production upgrade в рамках этого аудита не выполнялся.
