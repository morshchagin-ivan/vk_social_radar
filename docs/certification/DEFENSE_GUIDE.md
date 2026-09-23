# Defense Guide

Baseline 1.0 · 2026-09-23. Основание — [readiness audit](04_CERTIFICATION_READINESS.md), без новых live VK/LLM запусков. Презентуем работающий ограниченный MVP и контролируемую эволюцию, не полную реализацию прежнего SDD.

## 90-second project pitch

VK Social Radar — локальное приложение для сбора доступных пользователю данных VK и анализа истории контактов. В MVP уже есть FastAPI, HTML/JavaScript интерфейс, SQLite, Playwright с отдельным профилем Chromium, сбор друзей, подписчиков и диалогов, public organization source, импорты, журнал изменений и агрегаты сообщений. Результат обычного сбора сначала показывается в preview и затем сохраняется по явному действию. Для AI реализован прямой HTTP-вызов LM Studio по метрикам человека.

Архитектурный аудит отделил эти возможности от прежних проектных обещаний. Immutable Snapshot aggregate, LLM Provider abstraction и RAG пока не реализованы. Нашлись конкретные дефекты истории и несовместимость установленной схемы БД с новым кодом. OpenAPI тоже описывает целевой, а не текущий API.

Поэтому подготовлены отдельные CURRENT/TARGET C4, шесть ADR, реестр долга, traceability и приоритетный backlog. Следующая итерация начинается с безопасной миграции данных, затем формирует корректный Snapshot, контракты и provider port, после чего вводит проверяемый локальный retrieval. Distributed infrastructure не добавляем без нагрузки или требования. Evidence — код и wiring, 18 unittest и 8 отдельно выполненных существующих функций из аудита; это не доказательство live E2E или полного выполнения SDD.

## 5-minute architecture walkthrough

| Time | Показываем | Главная мысль |
|---|---|---|
| 0:00–0:45 | [Landing](README.md), [status](ARCHITECTURE_STATUS.md) | различаем implemented, partial, planned |
| 0:45–1:45 | [CURRENT C4](C4_CURRENT.md) | UI→API→SQL; Collector→browser/preview; отдельный LM HTTP flow |
| 1:45–2:30 | [Data debt](DATA_MODEL_STATUS.md), [API status](API_STATUS.md) | installed schema drift и snapshot semantics — конкретные P0 |
| 2:30–3:30 | [ADR register](../adr/README.md), [TARGET C4](C4_TARGET.md) | accepted direction ≠ implementation; local monolith сохраняется |
| 3:30–4:15 | [Traceability](TRACEABILITY_MATRIX.md), [NFR](NFR_BASELINE.md) | существующие tests узкие; неизвестные метрики не придуманы |
| 4:15–5:00 | [Evolution](ARCHITECTURE_EVOLUTION.md), [backlog](05_UPGRADE_BACKLOG.md) | U02 first, затем integrity/contracts/provider/RAG; privacy/quality поперёк этапов |

## Strongest implemented decisions

Local bind/SQLite и отдельный persistent browser profile; preview-before-save для поддерживаемых kinds; аналитика читает сохранённые данные без VK; multiformat imports и normalization; concrete LM Studio HTTP integration. Ссылки на код и границы тестирования: [traceability](TRACEABILITY_MATRIX.md). Эти преимущества не доказывают immutable history, provider abstraction или strict local-only policy.

## Planned architecture and why

U02 migration предотвращает несовместимость схем; U03 immutable source делает историю повторяемой; U04 API contract исключает расхождение consumers; U05 port отделяет AI от transport; U08 retrieval даёт проверяемое source evidence. U09 bounded retry/Circuit Breaker принимаются только после U11 deadlines/failure requirements. U10/U12 вводят небольшие parser/persistence boundaries. Graph/Scheduler/Export остаются roadmap.

## 20 likely examiner questions and evidence-based answers

| № | Question | Answer / evidence |
|---|---|---|
| 1 | Почему Playwright? | выбран доступный пользовательской сессии web interface и отдельный профиль; код уже использует persistent Chromium. Цена — DOM fragility, нужны fixtures. Это не утверждение, что VK API вообще невозможен. [ADR-002](../adr/ADR-002-playwright-instead-of-vk-api.md) |
| 2 | Почему SQLite, а не PostgreSQL? | single-user local app, нет подтверждённой distributed/concurrent write потребности; важнее исправить migration discipline. [ADR-005](../adr/ADR-005-sqlite-for-mvp.md) |
| 3 | Почему нет microservices/Kafka/K8s? | нет соответствующих deployment/throughput/team boundaries. Они не устраняют snapshot/schema/contract defects. [deliberately not introduced](ARCHITECTURAL_PATTERNS.md) |
| 4 | Где Snapshot source of truth? | target U03. AS-IS — relation rows по дню, mutable people, confirmed defects. [ADR-003](../adr/ADR-003-immutable-snapshot-source-of-truth.md), [data status](DATA_MODEL_STATUS.md) |
| 5 | Что доказало нарушение snapshot semantics? | synthetic audit: returned count=1 при dashboard=2; повтор events 1→2; пустая дата не становится current. [audit probes](03_SDD_CODE_GAP_ANALYSIS.md) |
| 6 | Provider уже существует? | concrete LM HTTP существует, port/factory/selection нет. [ADR-004](../adr/ADR-004-local-llm-provider-abstraction.md) |
| 7 | Можно просто заменить URL на Ollama? | compatibility URL не подтверждает adapter/behavior contract. Ollama implementation не проверена и не объявлена existing. [LLM verdict](02_PATTERN_INVENTORY.md) |
| 8 | Почему RAG planned? | нет corpus indexing/query retrieval/citations; latest metrics + 10 events — fixed context. Runtime NO_RAG. [ADR-006](../adr/ADR-006-rag-architecture.md) |
| 9 | Нужна vector DB/hybrid/RRF? | не обещаем до corpus/query evaluation. Начинаем с минимального подхода и измеряем relevance/citation correctness. [ADR-006](../adr/ADR-006-rag-architecture.md) |
| 10 | Почему try/except не Circuit Breaker? | exception translation не хранит failures/CLOSED/OPEN/HALF_OPEN и не закрывает доступ к dependency. [patterns](ARCHITECTURAL_PATTERNS.md) |
| 11 | Как планируется resilience? | U11 задаёт deadline; U09 — bounded attempts/classifier/backoff/jitter и stateful breaker с recovery probe. Сейчас только httpx settings 8/120 s, не общий deadline. [NFR](NFR_BASELINE.md) |
| 12 | Что при недоступной LM Studio? | AI endpoint возвращает 503, UI показывает ошибку; non-AI services не вызывают LLM. Нет provider/cache fallback. [audit](02_PATTERN_INVENTORY.md), [main](../../app/main.py) |
| 13 | Чем CURRENT отличается от TARGET? | CURRENT отражает concrete modules/direct SQL/fixed prompt; TARGET добавляет source invariants/ports/retrieval/gates. [CURRENT](C4_CURRENT.md), [TARGET](C4_TARGET.md) |
| 14 | Какие patterns реально есть? | частичные adapter-like wrappers, ACL normalization, procedural pipeline/history; Repository/DIP/Strategy отсутствуют. [catalog](ARCHITECTURAL_PATTERNS.md) |
| 15 | Почему YAML нельзя использовать как runtime contract? | `/api/v1`/18 operations против `/api`/29; отличаются auth/errors/schemas и scope. Parsed YAML не значит consistent API. [API status](API_STATUS.md) |
| 16 | Что с установленной БД? | dialog table 6 columns против 13 fresh DDL; CREATE IF NOT EXISTS не миграция. Next step U02. [data status](DATA_MODEL_STATUS.md) |
| 17 | Что именно проверили tests? | prior audit 18 unittest + 8 plain functions отдельно; часть — source markers, no live collector/inference. Fresh-DB tests пропустили migration defect. [audit inventory](03_SDD_CODE_GAP_ANALYSIS.md) |
| 18 | Local-first полностью гарантирован? | нет: local defaults есть, arbitrary LLM URL/raw diagnostics/fail-open остаются. Git absence не позволяет утверждать, что session data не tracked. [privacy status](SECURITY_PRIVACY_STATUS.md) |
| 19 | Каковы performance/recovery NFR? | adopted measured baseline отсутствует; workload/hardware и targets TBD during U11. HTTP timeout config не измеренная latency. [NFR](NFR_BASELINE.md) |
| 20 | Как audit изменил roadmap и что дальше? | data integrity/migration/contracts получили приоритет перед Graph/Export/distributed stack. U01 documentary baseline готов, Git proof открыт; U02 next implementation, не начат. [evolution](ARCHITECTURE_EVOLUTION.md), [upgrade report](BASELINE_UPGRADE_REPORT.md) |

## What NOT to claim

- Не называть relation_snapshots готовым immutable aggregate или dashboard snapshot-consistent.
- Не утверждать наличие Provider/Ollama, Retry/Breaker/RAG, CI, Scheduler, Graph/Export.
- Не называть AI evidence strings проверенными citations и не приписывать LLM verified accuracy.
- Не представлять 18 + 8 prior passes как единый maintained runner, 100% coverage или live E2E.
- Не заявлять Git/history clean, отсутствие private data или strict local-only transfers без U06 evidence.
- Не представлять ACCEPTED ADR/target diagram, legacy PASS/checklist или YAML parse как реализацию.

## Demo path without external VK/LLM dependency

Безопасная baseline-демонстрация полностью статическая: открыть landing/CURRENT, показать [main.py](../../app/main.py) routes, [services.py](../../app/services.py) read-side и [test_services.py](../../tests/test_services.py) assertions, затем prior audit results/defects, TARGET/ADRs и U02 acceptance. Не открывать реальные profile/diagnostic/import files и не выводить содержимое БД.

При необходимости можно показать **только статический** подсчёт декораторов API, не импортируя приложение:

```powershell
.\.venv\Scripts\python.exe -B -c "import ast,pathlib; t=ast.parse(pathlib.Path('app/main.py').read_text(encoding='utf-8')); print(sum(1 for n in ast.walk(t) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id=='app' and n.args and isinstance(n.args[0],ast.Constant) and isinstance(n.args[0].value,str) and n.args[0].value.startswith('/api/')))"
```

Ожидаемое число по audit/static inventory — 29; команда не проверяет работоспособность endpoints. Стандартный app startup вызывает init/seed и UI запрашивает LM models, поэтому его не включаем в dependency-free/frozen baseline demo. `run_tests.bat` также пишет CSV в default imports, если не изолировать пути. Future functional demo U07 следует выполнять на disposable synthetic environment с temp storage, без пользовательской session. В этой итерации такие запуски не выполнялись.
