# C4 TARGET — accepted evolutionary design

Baseline 1.0 · 2026-09-23. **TARGET / PLANNED**, не runtime inventory. Сохраняется локальный модульный монолит: boxes ниже — логические ответственности, не microservices. Принятые [ADR](../adr/README.md) не означают завершённую реализацию.

Legend: IMPLEMENTED = существующая technology/component boundary; PARTIAL = существующая capability требует изменений; PLANNED = новый contract/mechanism. Статус указан текстом и цветом. Даже IMPLEMENTED box не доказывает готовность всех целевых стрелок.

```mermaid
flowchart TD
  UI["IMPLEMENTED: Static UI"] --> API["IMPLEMENTED: Current API contract - U04"]
  API --> App["PARTIAL: Application Services"]
  App --> Ports["PLANNED: Persistence Ports - U12"]
  Ports --> SQLAdapter["PLANNED: SQLite Adapter boundary - U12"]
  SQLAdapter --> DB[("IMPLEMENTED: SQLite technology")]
  App --> Orchestrator["PARTIAL: Collector Orchestrator"]
  Orchestrator --> Strategies["PLANNED: Collector Strategies - U10"]
  Strategies --> VKAdapter["PARTIAL: VK and Playwright Adapter"]
  VKAdapter --> ACL["PARTIAL: Normalizer and ACL - U13"]
  ACL --> Run["PLANNED: Persisted Collection Run"]
  Run --> Snapshot["IMPLEMENTED: Immutable relation Snapshot - U03"]
  Snapshot --> Diff["IMPLEMENTED: Relation membership diff - U03"]
  Diff --> Analytics["PARTIAL: Timeline and Analytics"]
  Snapshot --> Index["IMPLEMENTED: Relation corpus and RAM index - U08"]
  Analytics --> Index
  App --> AI["PARTIAL: AI Use Cases"]
  AI --> Retrieval["IMPLEMENTED: Lexical retrieval - U08"]
  Index --> Retrieval
  Retrieval --> Context["IMPLEMENTED: Bounded context and citations - U08"]
  Context --> Provider["IMPLEMENTED: LLM Provider Port - U05"]
  AI -->|"current person insight"| Provider
  Provider --> Resilience["IMPLEMENTED: Generation retry and Circuit Breaker - U09"]
  Resilience --> LMAdapter["IMPLEMENTED: LM Studio Adapter - U05"]
  LMAdapter --> LM["IMPLEMENTED: LM Studio HTTP integration"]
  Gates["IMPLEMENTED: Local Quality Gates - U07"] --> ContractGate["IMPLEMENTED: Runtime contract drift gate - U04"]
  Gates --> TestGate["PARTIAL: Behavior tests"]
  Gates --> Eval["IMPLEMENTED: Synthetic retrieval evaluation - U08"]
  classDef implemented fill:#dcfce7,stroke:#166534,color:#111827
  classDef partial fill:#fef3c7,stroke:#92400e,color:#111827
  classDef planned fill:#e0e7ff,stroke:#4338ca,color:#111827
  class UI,API,ContractGate,DB,LM,Provider,LMAdapter,Resilience,Snapshot,Diff,Gates,Index,Retrieval,Context,Eval implemented
  class App,Orchestrator,VKAdapter,ACL,Analytics,AI,TestGate partial
  class Ports,SQLAdapter,Strategies,Run planned
```

U02 уже реализует безопасную schema migration; U03 реализует relation Snapshot и derived membership events; persisted CollectorRun, полный message corpus и application persistence ports остаются target. На схеме не развёрнуты все CRUD стрелки. В target source snapshots неизменяемы, derived metrics/index/reports версионируются отдельно. Валидное полностью наблюдённое пустое состояние отличается от неудачного/неполного сбора; ADR-003/U03 заменяет blanket empty rejection из legacy task T018 поддержкой явно подтверждённого пустого состояния.

LLM port уже отделяет current person insight use case от concrete HTTP — [U05 report](U05_LLM_PROVIDER_REPORT.md). U08 implements the relation-only internal STRUCTURED_RAG—LEXICAL chain. API/UI chat and automatic orchestration arrows remain target; Ollama NOT IMPLEMENTED. [U09](U09_LLM_RESILIENCE_REPORT.md) реализует generation retry/backoff/jitter и stateful breaker: 3 attempts, max sleep 1.5s, threshold 3 logical failures, recovery 30s и single probe. Это internal defaults, не измеренный SLO: total deadline НЕ enforced; U11 measurement/tuning остаётся целью. Models/health независимы от generation breaker. Hidden remote fallback отсутствует. Vector DB, dense/hybrid/RRF/reranker не выбраны; U08 supplies an evaluated lexical baseline, with no improvement over term-frequency measured on its small fixture.

U06 now implements bounded controls across the diagram: loopback endpoint policy, Host/Origin, minimized diagnostics/retention and tracked disclosure guard; broader privacy assurance remains partial. U07 local gates are implemented and U08 adds six retrieval fitness checks. Graph/Export/Scheduler остаются P2 U14–U16 и не обязательны для этого ядра. [Evolution and acceptance](ARCHITECTURE_EVOLUTION.md), [CURRENT](C4_CURRENT.md).

U03 implementation is narrower than the full target chain: relation imports can declare complete sets; the current DOM collector cannot prove completeness and produces INCOMPLETE observations. No automatic index/AI pipeline, retrieval, Graph or immutable messages were added. [U03 evidence](U03_IMMUTABLE_SNAPSHOT_REPORT.md).

U04 implemented current contract governance only: canonical `/api`, no fictitious auth or target endpoints. Future API resources remain planned; full CI/unified runner remains U07. [U04 evidence](U04_API_CONTRACT_REPORT.md).

Local application authentication and encryption are not implemented by U06. Its tested local controls do not promote RAG, Graph, Export or multi-user capabilities. [Security status](SECURITY_PRIVACY_STATUS.md).

**U08 current evidence:** STRUCTURED_RAG—LEXICAL, internal service only; 31 RAG tests, 222 total tests, seven gates and 18 fitness invariants PASS. [Report](U08_LOCAL_RAG_REPORT.md) · [Evaluation](RAG_EVALUATION.md). Prior U07 remote Actions success is owner-reported; this U08 revision is locally verified only and has not been pushed. Branch settings are unchanged.

The implemented Index/Retrieval/Context boxes cover only the bounded internal U08 service. The broader source corpus and API/AI workflow are still target. [Current dependencies](C4_CURRENT.md).
