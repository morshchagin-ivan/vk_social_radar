# Architectural Pattern Catalog

Baseline 1.0 · 2026-09-23. The Status column preserves [audit verdict](02_PATTERN_INVENTORY.md); PLANNED in Target is an accepted direction, not implementation evidence. Pattern names are not inferred from class names alone.

| Pattern | Status | Problem | Current implementation | Target | Evidence / Backlog |
|---|---|---|---|---|---|
| Local-first | PARTIAL | local control/privacy | local bind/files/SQLite; arbitrary LLM URL | enforced local inference/privacy | [ADR-001](../adr/ADR-001-local-first-architecture.md); U06 |
| Adapter | PARTIAL | isolate external protocols | concrete browser wrapper, LM HTTP, file mappers; no common port | narrow vendor/browser/persistence adapters | [collector](../../app/collector.py), [lmstudio](../../app/lmstudio.py); U05/U10/U12 |
| ACL | PARTIAL | external DOM/raw→internal data | cleaners and dict normalization | typed identity/result boundary | [importers](../../app/importers.py); U10/U13 |
| Pipeline | PARTIAL | staged transformation | collect→preview→manual save; import→normalize→SQL/diff; AI separate | validated run→snapshot→derived data→retrieval | [services](../../app/services.py); U03/U08 |
| Immutable Snapshot | PARTIAL history; immutability CONTRADICTED_BY_CODE | reproducible history | daily memberships and mutable people | PLANNED immutable aggregate | [ADR-003](../adr/ADR-003-immutable-snapshot-source-of-truth.md); U03 |
| Repository | NOT_IMPLEMENTED | persistence boundary | direct SQL, connection helper is not repository | PLANNED selected persistence ports | [services](../../app/services.py); U12 |
| DIP | NOT_IMPLEMENTED | business independence from IO | concrete module/singleton imports | PLANNED provider/persistence ports | [main](../../app/main.py); U05/U12 |
| Strategy | NOT_IMPLEMENTED | replace parser independently | hardcoded kind branch and methods | PLANNED parser contract/registry or injection | [collector.collect](../../app/collector.py); U10 |
| RAG | DOCUMENTED_ONLY; runtime NO_RAG | question-relevant context/evidence | fixed person metrics/events prompt | PLANNED evaluated local retrieval | [ADR-006](../adr/ADR-006-rag-architecture.md); U08 |
| Retry | NOT_IMPLEMENTED | bounded transient recovery | single requests, timeout settings only | PLANNED classifier/attempt budget/backoff/jitter | [lmstudio](../../app/lmstudio.py); U09/U11 |
| Circuit Breaker | NOT_IMPLEMENTED | fail-fast and controlled recovery | try/except→503, no state/counter | PLANNED CLOSED/OPEN/HALF_OPEN subject to NFR | [main](../../app/main.py); U09/U11 |

`try/except` translates an error; it does not track failures or deny requests while OPEN. DOM readiness polling is not LLM retry. Fixed context assembly is not query retrieval. `get_connection` manages connections, not a domain collection interface.

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
