# C4 TARGET — accepted evolutionary design

Baseline 1.0 · 2026-09-23. **TARGET / PLANNED**, не runtime inventory. Сохраняется локальный модульный монолит: boxes ниже — логические ответственности, не microservices. Принятые [ADR](../adr/README.md) не означают завершённую реализацию.

Legend: IMPLEMENTED = существующая technology/component boundary; PARTIAL = существующая capability требует изменений; PLANNED = новый contract/mechanism. Статус указан текстом и цветом. Даже IMPLEMENTED box не доказывает готовность всех целевых стрелок.

```mermaid
flowchart TD
  UI["IMPLEMENTED: Static UI"] --> API["PARTIAL: Backend API - U04"]
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
  Snapshot --> Index["PLANNED: Local ingestion and index - U08"]
  Analytics --> Index
  App --> AI["PARTIAL: AI Use Cases"]
  AI --> Retrieval["PLANNED: Retrieval - U08"]
  Index --> Retrieval
  Retrieval --> Context["PLANNED: Context Builder and citations"]
  Context --> Provider["IMPLEMENTED: LLM Provider Port - U05"]
  AI -->|"current person insight"| Provider
  Provider --> Resilience["IMPLEMENTED: Generation retry and Circuit Breaker - U09"]
  Resilience --> LMAdapter["IMPLEMENTED: LM Studio Adapter - U05"]
  LMAdapter --> LM["IMPLEMENTED: LM Studio HTTP integration"]
  Gates["PLANNED: Quality Gates - U07"] --> ContractGate["PARTIAL: U02 migration and U05/U09 AI behavior tests"]
  Gates --> TestGate["PARTIAL: Behavior tests"]
  Gates --> Eval["PLANNED: AI retrieval evaluation"]
  classDef implemented fill:#dcfce7,stroke:#166534,color:#111827
  classDef partial fill:#fef3c7,stroke:#92400e,color:#111827
  classDef planned fill:#e0e7ff,stroke:#4338ca,color:#111827
  class UI,DB,LM,Provider,LMAdapter,Resilience,Snapshot,Diff implemented
  class API,App,Orchestrator,VKAdapter,ACL,Analytics,AI,TestGate,ContractGate partial
  class Ports,SQLAdapter,Strategies,Run,Index,Retrieval,Context,Gates,Eval planned
```

U02 уже реализует безопасную schema migration; U03 реализует relation Snapshot и derived membership events; persisted CollectorRun, полный message corpus и application persistence ports остаются target. На схеме не развёрнуты все CRUD стрелки. В target source snapshots неизменяемы, derived metrics/index/reports версионируются отдельно. Валидное полностью наблюдённое пустое состояние отличается от неудачного/неполного сбора; ADR-003/U03 заменяет blanket empty rejection из legacy task T018 поддержкой явно подтверждённого пустого состояния.

LLM port уже отделяет current person insight use case от concrete HTTP — [U05 report](U05_LLM_PROVIDER_REPORT.md). Будущая retrieval цепочка ещё отсутствует: runtime NO_RAG; Ollama NOT IMPLEMENTED. [U09](U09_LLM_RESILIENCE_REPORT.md) реализует generation retry/backoff/jitter и stateful breaker: 3 attempts, max sleep 1.5s, threshold 3 logical failures, recovery 30s и single probe. Это internal defaults, не измеренный SLO: total deadline НЕ enforced; U11 measurement/tuning остаётся целью. Models/health независимы от generation breaker. Hidden remote fallback отсутствует. Vector DB, dense/hybrid/RRF/reranker не выбраны; U08 начинает с измеримого retrieval baseline.

U06 privacy действует поперёк всей схемы: endpoint policy, safe diagnostics, local storage/package audit. U07 gates планируются; присутствующие tests не дают оснований объявлять CI реализованной. Graph/Export/Scheduler остаются P2 U14–U16 и не обязательны для этого ядра. [Evolution and acceptance](ARCHITECTURE_EVOLUTION.md), [CURRENT](C4_CURRENT.md).

U03 implementation is narrower than the full target chain: relation imports can declare complete sets; the current DOM collector cannot prove completeness and produces INCOMPLETE observations. No automatic index/AI pipeline, retrieval, Graph or immutable messages were added. [U03 evidence](U03_IMMUTABLE_SNAPSHOT_REPORT.md).
