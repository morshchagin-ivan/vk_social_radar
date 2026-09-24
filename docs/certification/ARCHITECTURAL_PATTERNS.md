# Architectural Pattern Catalog

Baseline 1.0 + U05/U09 · 2026-09-23. Status starts from the historical [audit verdict](02_PATTERN_INVENTORY.md), with AI-boundary changes proven by [U05 tests/report](U05_LLM_PROVIDER_REPORT.md) and [U09 resilience evidence](U09_LLM_RESILIENCE_REPORT.md). PLANNED in Target is an accepted direction, not implementation evidence. Pattern names are not inferred from class names alone.

| Pattern | Status | Problem | Current implementation | Target | Evidence / Backlog |
|---|---|---|---|---|---|
| Local-first | IMPLEMENTED bounded U06 controls; overall assurance PARTIAL | local control/privacy | loopback/Host/Origin, local-only LLM, minimized diagnostics and safe paths | broader operator/history/erasure assurance remains open | [ADR-001](../adr/ADR-001-local-first-architecture.md), [U06](U06_PRIVACY_ACCESS_HARDENING_REPORT.md) |
| Adapter | IMPLEMENTED for LM Studio; PARTIAL elsewhere | isolate external protocols | LMStudioProvider implements LLMProvider, owns HTTP/extraction/errors; browser/file wrappers remain concrete | browser/persistence adapters still planned | [LM adapter](../../app/ai/providers/lmstudio.py), [contract tests](../../tests/test_ai_provider.py); U05 completed / U10/U12 planned |
| ACL | PARTIAL | external DOM/raw→internal data | cleaners and dict normalization | typed identity/result boundary | [importers](../../app/importers.py); U10/U13 |
| Pipeline | PARTIAL | staged transformation | collect→preview→INCOMPLETE observation; declared import→atomic COMPLETE source→derived pair events; AI separate | validated run→snapshot→derived data→retrieval | [services](../../app/services.py); U03/U08 |
| Immutable Snapshot | IMPLEMENTED for relations | reproducible friend/follower history | UUID header + immutable snapshot_people projection; SQLite guards; COMPLETE-only current | broader corpus remains planned | [ADR-003](../adr/ADR-003-immutable-snapshot-source-of-truth.md), [U03 evidence](U03_IMMUTABLE_SNAPSHOT_REPORT.md); U03 completed |
| Repository | NOT_IMPLEMENTED | persistence boundary | direct SQL, connection helper is not repository | PLANNED selected persistence ports | [services](../../app/services.py); U12 |
| DIP | IMPLEMENTED at AI/RAG boundaries | use cases independent of transport/ranking implementation | AIInsightService uses LLMProvider; RAGService uses Retriever/LLMProvider | persistence ports planned; global DIP partial | [service](../../app/rag/service.py), [composition](../../app/ai/composition.py); U05/U08 complete |
| Strategy | NOT_IMPLEMENTED | replace parser independently | hardcoded kind branch and methods | PLANNED parser contract/registry or injection | [collector.collect](../../app/collector.py); U10 |
| RAG | IMPLEMENTED — STRUCTURED_RAG—LEXICAL | query-relevant evidence | COMPLETE snapshot corpus, derived RAM index, filtered BM25, bounded context, validated citations, offline eval | embeddings/hybrid/reranker and chat remain planned | [ADR-006](../adr/ADR-006-rag-architecture.md), [U08](U08_LOCAL_RAG_REPORT.md) |
| Retry | IMPLEMENTED | bounded transient recovery | wrapper retries only normalized unavailable/timeout; at most 3 generation attempts; logical failure counted once | U11 measured latency/deadline remains planned | [wrapper](../../app/ai/resilience.py), RES-001/002/003/006/007; U09 completed |
| Exponential Backoff | IMPLEMENTED | space transient retries | ceiling min(2s, 0.5s × 2^k), k starts at 0 | no hard total latency claim | RES-004; U09 completed |
| Jitter | IMPLEMENTED | spread retry timing | full jitter U(0, ceiling), injectable random and sleeper; default max total sleep 1.5s | empirical tuning remains U11 | RES-005; U09 completed |
| Circuit Breaker | IMPLEMENTED | fail-fast and controlled recovery | generation-only CLOSED/OPEN/HALF_OPEN; threshold 3 exhausted logical calls; 30s cooldown; locked single probe | per-process state only; no remote fallback | [behavior/API tests](../../tests/test_llm_resilience.py), CB-001…010; U09 completed |

`try/except` translates an error; it does not track failures or deny requests while OPEN. DOM readiness polling is not LLM retry. Fixed context assembly is not query retrieval. `get_connection` manages connections, not a domain collection interface.

Composition now retains `ResilientLLMProvider(LMStudioProvider)` across requests. Models/health bypass generation resilience and cannot trip/reset its circuit. Global DIP remains PARTIAL; Ollama and fallback are absent. U09 does not enforce a total deadline or add response caching.

## Patterns deliberately NOT introduced

The requested list contains infrastructure technologies as well as architectural approaches. NOT_PLANNED applies to current certification scope, not a negative assessment of those technologies.

| Technology / approach | Why no current requirement or load justifies it |
|---|---|
| Kubernetes | no multi-node deployment/scheduling requirement for one local application |
| Kafka | no independent distributed consumers or measured streaming throughput need |
| Redis | no demonstrated shared-cache/queue/session bottleneck |
| Full CQRS | source/derived tables can be separated within one application/transaction model |
| Microservices | no independent deployment/team/scaling boundary; local transactions remain simpler |
| MAS | fixed collection/analysis/retrieval workflows do not require autonomous-agent coordination |
| MCP | no runtime requirement to expose tools to external AI clients; developer tooling is separate |
| Feature Store | no train/serve feature lifecycle; current SQL aggregates suffice |
| MLflow | no model-training registry requirement; versioned prompt/eval artifacts cover near-term need |
| Multi-tenancy | single local user/profile, no tenant-isolation product requirement |
| HA/DR platform | no cluster/regional availability requirement; local backup/restore still needed |
| Federated Learning | no model training over distributed user datasets |

[ADR rationale](../adr/README.md), [NFR](NFR_BASELINE.md), [U01–U17](05_UPGRADE_BACKLOG.md). Reconsider these choices only on changed requirements or measured constraints.

U03 uses immutable state snapshots with derived, rebuildable membership diffs/events. It is **not Event Sourcing**. Mutable people remain convenience/current records; message_stats, AI inputs and legacy event names remain outside immutable reproduction. 34 U03 behavior/migration tests PASS.

U04 implements **Contract Governance** for the current runtime: generated canonical OpenAPI plus semantic route/schema/security/frontend checks and synthetic response fixtures. [Evidence](U04_API_CONTRACT_REPORT.md). U04 did not implement global DIP, authentication or target API resources. U07 now supplies local quality governance and the shared CI configuration.

## U07 executable architecture fitness

**IMPLEMENTED:** [runner](../../scripts/run_quality_gates.py) derives 18 invariant verdicts, including six RAG checks from successful tests actually executed in one discovery. DB version/idempotency, immutable/complete snapshot rules, provider DIP/transport boundary, resilience wiring/determinism, API drift, privacy and UI checks have stable FITNESS IDs. [Reference](QUALITY_GATE_REFERENCE.md) maps each to concrete evidence. This is executable governance, not a new runtime design pattern or proof of all target architecture. Prior U07 remote Actions success is owner-reported; this U08 revision is locally verified only and has not been pushed. Branch settings are unchanged.

**U08 current evidence:** STRUCTURED_RAG—LEXICAL, internal service only; 31 RAG tests, 222 total tests, seven gates and 18 fitness invariants PASS. [Report](U08_LOCAL_RAG_REPORT.md) · [Evaluation](RAG_EVALUATION.md). Prior U07 remote Actions success is owner-reported; this U08 revision is locally verified only and has not been pushed. Branch settings are unchanged.
