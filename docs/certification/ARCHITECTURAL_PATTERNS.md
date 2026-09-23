# Architectural Pattern Catalog

Baseline 1.0 + U05/U09 · 2026-09-23. Status starts from the historical [audit verdict](02_PATTERN_INVENTORY.md), with AI-boundary changes proven by [U05 tests/report](U05_LLM_PROVIDER_REPORT.md) and [U09 resilience evidence](U09_LLM_RESILIENCE_REPORT.md). PLANNED in Target is an accepted direction, not implementation evidence. Pattern names are not inferred from class names alone.

| Pattern | Status | Problem | Current implementation | Target | Evidence / Backlog |
|---|---|---|---|---|---|
| Local-first | PARTIAL | local control/privacy | local bind/files/SQLite; arbitrary LLM URL | enforced local inference/privacy | [ADR-001](../adr/ADR-001-local-first-architecture.md); U06 |
| Adapter | IMPLEMENTED for LM Studio; PARTIAL elsewhere | isolate external protocols | LMStudioProvider implements LLMProvider, owns HTTP/extraction/errors; browser/file wrappers remain concrete | browser/persistence adapters still planned | [LM adapter](../../app/ai/providers/lmstudio.py), [contract tests](../../tests/test_ai_provider.py); U05 completed / U10/U12 planned |
| ACL | PARTIAL | external DOM/raw→internal data | cleaners and dict normalization | typed identity/result boundary | [importers](../../app/importers.py); U10/U13 |
| Pipeline | PARTIAL | staged transformation | collect→preview→manual save; import→normalize→SQL/diff; AI separate | validated run→snapshot→derived data→retrieval | [services](../../app/services.py); U03/U08 |
| Immutable Snapshot | PARTIAL history; immutability CONTRADICTED_BY_CODE | reproducible history | daily memberships and mutable people | PLANNED immutable aggregate | [ADR-003](../adr/ADR-003-immutable-snapshot-source-of-truth.md); U03 |
| Repository | NOT_IMPLEMENTED | persistence boundary | direct SQL, connection helper is not repository | PLANNED selected persistence ports | [services](../../app/services.py); U12 |
| DIP | IMPLEMENTED at AI provider boundary only | business independence from vendor transport | AIInsightService accepts LLMProvider; structural fake works without adapter inheritance; composition binds LM Studio | persistence ports PLANNED; no global DIP claim | [service](../../app/ai/service.py), [composition](../../app/ai/composition.py); U05 completed / U12 planned |
| Strategy | NOT_IMPLEMENTED | replace parser independently | hardcoded kind branch and methods | PLANNED parser contract/registry or injection | [collector.collect](../../app/collector.py); U10 |
| RAG | DOCUMENTED_ONLY; runtime NO_RAG | question-relevant context/evidence | fixed person metrics/events prompt | PLANNED evaluated local retrieval | [ADR-006](../adr/ADR-006-rag-architecture.md); U08 |
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
