# Architecture, data, API, process, ADR and NFR consistency

Evidence scope: full certification audit at U08 (4ff2e09fe97e846d74c00977e3bb90a01ebfeb77), followed by focused post-U13A delta verification at 53a35014e75bedc4e69691d38f39c4752cd4bd68. Unchanged architecture findings and independent U08 probes are carried forward; the full canonical suite was rerun. This is not a full-from-zero re-audit.

Audited HEAD: `53a35014e75bedc4e69691d38f39c4752cd4bd68`. Code/wiring is the authority; [C4_CURRENT](../C4_CURRENT.md), [C4_TARGET](../C4_TARGET.md) and target SDD were compared against it. Main result: implemented component graph is supported, with bounded features and stale prose warnings rather than a full target completion claim.

U13A changes only a shared 41-line validation module, importer count normalization, calls in services/seed, tests and category registration. Current C4 needs no new deployment/component layer; GLOBAL_DIP_PARTIAL remains. Ordinary C4/ADR files were not edited. All independent schema/route/ADR reconstruction below originates in the U08 full audit; the focused delta reviewed the complete six-file diff and reran the existing evidence.

## Reconstructed current components

| Component | Actual dependency / entry point | Audit conclusion |
|---|---|---|
| Static HTML/CSS/vanilla JS | static/app.js fetches /api; main mounts static and HTML shell | Exists/wired; no React rewrite or graph/chat UI |
| FastAPI boundary | main → services/importers/collector; main → ai.composition/settings | 30 APIRoute operations; middleware protects browser boundary |
| SQLite/source model | db → migrations/snapshot_schema; services → snapshots | Direct SQL; relation sources and events persisted, no Repository |
| Collector | SafeVKCollector singleton → Playwright persistent context; concrete extractors | Preview then explicit save; organization jobs in RAM |
| Importers | Parse JSON/CSV/TSV/HTML/ZIP → services; local import_jobs | HTML/collector relation observations incomplete; ZIP members commit independently |
| Message-stat validation | importers → services.import_message_stats → normalize_message_stats before SQL; seed uses the same function | Exact valid date endpoints/order and non-negative counts; no separate total input; application boundary, no DB CHECK |
| Person Insight | main.create_insight → get_insight_service → AIInsightService → LLMProvider | Fixed context, local validation then store_insight |
| Provider/transport | composition → shared ResilientLLMProvider → LMStudioProvider → httpx | Only production adapter; no concrete transport imports in use cases |
| RAG corpus/index | get_rag_service opens existing DB mode=ro → build_corpus → LexicalIndex | Callable internal composition; not auto-started or HTTP-exposed |
| RAG use case | RAGService → Retriever; assemble_context; LLMProvider; output/citation checks | Real query-dependent lexical retrieval; no-evidence before provider calls |
| Quality infrastructure | BAT/workflow → scripts/run_quality_gates.py | Development-only, separate from application runtime |

Current C4's boxes exist and their conceptual data flow is credible. Its RAG branch denotes explicit internal composition, not a route from the browser. No route imports get_rag_service; the build explicitly permits this service-only capability. C4_TARGET's future pipeline/arrows, persisted CollectorRun, parser strategies and persistence ports remain target even when individual reused boxes are implemented. All U02/03/04/05/06/07/08/09 mechanisms are reflected in current evidence. The old startup/settings/compatibility descriptions are not additional deployment services.

## Architecture ↔ physical data: independent clean room

Fresh temporary init produced schema version **2**, eleven application tables, **seven triggers**, zero FK violations:

`people`, `relation_snapshots`, `relation_events`, `message_stats`, `app_settings`, `ai_insights`, `collector_dialogs`, `import_jobs`, `snapshots`, `snapshot_people`, `snapshot_events`.

| Invariant | Code and fresh evidence | Residual |
|---|---|---|
| Versioned migration | PRAGMA user_version; detect before/under BEGIN IMMEDIATE; supported v0/v1 paths converge to v2 | It does not literally pause at v1 during a v0→v2 upgrade; original U02 dialog transformation remains |
| Backup before mutation | Separate readonly source Connection.backup, unique exclusive target, quick_check | Backup retains personal data; no restore-time/retention guarantee |
| Atomicity/rollback/idempotency | db context rolls back BaseException; migration avoids executescript; defaults/version/schema in transaction | Unknown schema fails closed; exact SQL guards constrain manual schema customization |
| Historical migration reproduction | Protected U02 db.py DDL used to build a temporary v1 DB without mocking current DDL; sentinel preserved, backup dump matched pre-upgrade exactly, repeated init unchanged | User DB never migrated/opened |
| Snapshot identity/lifecycle | UUID independent of date; sequence tie-break; capture precision; source/reference; CREATING→final status; COMPLETE requires declared count | Completeness declared, not independently verified VK truth; account/run fields not invented |
| Immutable history | Finalized header and membership insert/update/delete guards; frozen name/URLs; historical reads avoid mutable people | CREATING is intentionally mutable; DB-owner schema modification is outside invariant |
| Empty/current/history | Empty COMPLETE header replaces current; same-day UUIDs coexist; only COMPLETE compatible streams selected | Legacy current fallback only before first complete v2 stream |
| Pair events | predecessor by capture+sequence; deterministic sorted set diff; unique pair/type/key; projection FK | Events derived/rebuildable; not Event Sourcing or exact social-action time |
| Backdated repair | New snapshot and immediate successor edges repaired in one transaction; obsolete edges removed | RAG instances must be rebuilt after source changes |
| Current vs historical person | Mutable people projection may change; historical snapshot_people does not | Message aggregates and old legacy events remain outside frozen source truth |
| Message-stat integrity | Shared validator runs before service person upsert; seed validates inside transaction | Zero/equal/leap/CSV/large counts allowed; no new migration, repair of historical invalid rows, owner-SQL guard or complete identity validation |
| RAG index | Only RAM, fingerprinted derived data; source IDs tied to UUID/composite keys | No schema/index file, automatic refresh, immutable AI report store or message corpus |

Independent probes rechecked same-day captures, empty state, incomplete exclusion, immutable header refusal, mutable-person noninterference, exact replay and obsolete-edge removal. Canonical tests additionally exercise migration rollback/default failure/WAL backups, conflicting replay, concurrent same-ID creation and event uniqueness. [DATA_MODEL_STATUS](../DATA_MODEL_STATUS.md) matches this physical scope; root/feature ER documents are labelled target.

## Architecture ↔ OpenAPI

Independently enumerated APIRoute method/path/operation IDs: **30**, of which **29 /api operations** and one internal shell. Root JSON-form YAML parses as OpenAPI **3.1.0** and equals app.openapi exactly. Unique IDs, no securitySchemes/global Bearer declaration, server origin `http://127.0.0.1:8765`; paths already include /api. No /api/v1, RAG/chat/export/graph/snapshot-browser phantom resource.

The 23 contract tests verify requests, responses, errors, required path parameters, mutation-detected drift, all 21 frontend call sites and fake in-process behavior. Structured metadata for dictionary bodies is deliberate current contract documentation; business validation still occurs in services. Health remains liveness. The feature YAML has an explicit archived/non-canonical banner and is not a client-generation source. Formal external OpenAPI validation/generated-client execution was not available and is not inferred from FastAPI/PyYAML checks.

## Business process ↔ sequence comparison

| Process | Verified current sequence | Target distinction / evidence |
|---|---|---|
| Collector preview/save | Browser extract → in-memory/local preview → explicit API save → UNKNOWN/INCOMPLETE relation source or separate dialogs | Root 14/15 automatic full COMPLETE pipeline is TARGET; U03 preview tests and U04 mocked routes |
| Snapshot import | Validate identities/time/completeness → BEGIN IMMEDIATE → source/members → finalize → derive/repair → commit | Explicit empty allowed; full-source CollectorRun not present; U03 failure/replay tests |
| Diff/events/timeline | Compatible COMPLETE predecessor → deterministic member differences → pair/projection event → frozen historical read | No synthetic friend→follower causal transition; no profile/activity change engine |
| Person Insight | person_detail → latest message period/ten events → provider → local validate → persist | Synchronous request/threadpool; fixed context, not snapshot AI report or RAG |
| Resilience | Shared endpoint binding → admission ticket → bounded attempts/jitter → one logical completion | OPEN fails generation fast; discovery may still run; no global deadline/worker |
| RAG | Readonly source build → retrieve/filter → bounded whole facts → no-evidence return OR provider → validate citations | Internal callable; no API/chat session/automatic post-import indexing |
| File import | Bounded unique upload → parse → dispatch → service validates all message rows before person/stat transaction → import_jobs outcome | Archive-wide rollback absent; earlier successful members may remain after later failure |
| Organization job | RAM operation → asynchronous task/status/result/cancel → local preview | Restart loses job state; no scheduler/durable queue |

[14 business processes](../../../14_BUSINESS_PROCESSES.md), [15 sequences](../../../15_SEQUENCE_DIAGRAMS.md), [16 classes](../../../16_CLASS_DIAGRAM.md) visibly mark target/evolutionary design. Their larger classes and automatic arrows are not accepted as current code. Current mechanisms are supported by tests; no live UI/browser/LLM walkthrough was performed.

## ADR-001…006 audit

| ADR | Decision / implemented state | Code/test evidence | Consistency and residual |
|---|---|---|---|
| [001 local-first](../../adr/ADR-001-local-first-architecture.md) | ACCEPTED; bounded U06 controls implemented | privacy/access/collector/LM adapter; 31 U06 tests | Honest overall PARTIAL; trusted OS, no auth/encryption |
| [002 Playwright](../../adr/ADR-002-playwright-instead-of-vk-api.md) | ACCEPTED; code/wiring implemented | SafeVKCollector.start/collect; classification/path/mock API tests | Security paragraph still says fail-open/raw diagnostics need U06; stale versus code. Live extraction not proven |
| [003 snapshot](../../adr/ADR-003-immutable-snapshot-source-of-truth.md) | ACCEPTED; relation foundation implemented | snapshots/schema; 34 tests + clean-room | Scope correct; next-U04/U07 text is old milestone guidance, full corpus still deferred |
| [004 provider](../../adr/ADR-004-local-llm-provider-abstraction.md) | ACCEPTED; provider/LM and AI DIP implemented | composition/provider/service/adapter/resilience; U05/U09 tests | Security says arbitrary remote URL open; evolution says U08 planned/NO_RAG. Both stale current assertions |
| [005 SQLite](../../adr/ADR-005-sqlite-for-mvp.md) | ACCEPTED; SQLite/migration implemented | db/migrations; U02/U03 + independent v1 backup probe | Initial v1/eight-table text is historical; evolution correctly names v2. No full restore/capacity claim |
| [006 RAG](../../adr/ADR-006-rag-architecture.md) | ACCEPTED; STRUCTURED_RAG—LEXICAL implemented | corpus/index/service; 31 tests/eval | Accurate internal scope, no embeddings/hybrid/entailment guarantee; small benchmark warning |

P2-01 is genuine maintenance debt: historical build reports may preserve old results, but maintained ADR-002/004 current security/evolution prose contradicts implemented controls. TECHNICAL_DEBT_REGISTER D14 still describes arbitrary URL/fail-open as debt despite its later resolution paragraph. Current C4/quality prose saying U08 has not been pushed is superseded by the owner's new report and local tracking ref; it is not evidence against that external observation. DEFENSE_GUIDE is linked as baseline-era context and must not be read as current answers. No ordinary document was fixed; only this final evidence package was refreshed.

## NFR classification

| NFR/property | Classification | Verified evidence / limit |
|---|---|---|
| Local default bind and request/inference policy | ENFORCED | Launcher, Host/Origin, parsed loopback-only settings/adapter; offline negative tests. Not local-process authentication |
| Every possible information transfer/log channel is private | UNSUPPORTED as absolute guarantee | No cloud inference found; VK collection is intentionally external; third-party debug/operator behavior not comprehensively audited |
| API latency p50/p95/p99 | PROPOSED-TBD | No workload/hardware-labeled API benchmark or accepted SLO |
| Collector end-to-end latency/completeness | PROPOSED-TBD | 12s default action/45s navigation settings and bounds exist; not total deadline or live completeness proof |
| LLM per-phase timeout | ENFORCED configuration | Discovery 8s / generation 120s httpx values; these are inactivity/phase settings |
| Retry attempts/sleep/breaker | ENFORCED | At most 3 CLOSED attempts; sleep ceilings 0.5+1.0=1.5s; threshold 3, recovery 30s, single HALF_OPEN attempt |
| Hard total LLM elapsed-time ceiling | UNSUPPORTED if claimed; current target PROPOSED-TBD | 3×120+1.5 is not a hard wall-clock limit; discovery/in-flight calls and phase semantics matter |
| Relation historical integrity/replay | ENFORCED | SQL guards, transactions, keys/FKs and behavior tests; no full-message guarantee |
| Message-stat date/count integrity | ENFORCED at current application write paths | 18 U13A tests + independent 26 invalid probes; complete period/counter validation is not complete identity/domain validation |
| Migration failure safety | ENFORCED | Backup/rollback/FK/future/idempotency tests and clean-room reproduction |
| Backup restore time/growth/capacity | PROPOSED-TBD | No measured restore workflow or retention capacity objective |
| Diagnostic age/contents | ENFORCED in bounded scope | Allowlisted counter JSON; 30-day eligible direct-file deletion on runtime triggers, not continuous/full erasure |
| Imports byte/ZIP entry budget | ENFORCED | 100 MiB upload/expanded budget, 1000 entries; not multipart spooling/CPU or all input-domain validation |
| Reproducible quality outcomes | ENFORCED locally | Missing/failing/skipped tests and missing fitness evidence fail; same CI command; only tested Windows versions claimed |
| Quality gate elapsed time | MEASURED | 14.309s canonical run; no SLA |
| Snapshot write sanity | MEASURED | Gate printed 0.0804s for two 1000-member snapshots + diff; no SLA |
| RAG retrieval metrics | MEASURED and acceptance ENFORCED | 18 cases; Recall@3/MRR/no-evidence=1.0; floors .90/.90/1.0; ranking-blind fixture warning |
| RAG performance sanity | MEASURED | 5000 short facts; build 52.283ms, median selective query 0.011ms; repeated query microbenchmark, not ingestion/inference latency |
| RAG factuality/prompt-injection immunity | UNSUPPORTED | FakeLLM proves structured mechanics only; residual model risk documented |

## New debt and architectural restraint

No demonstrated circular import, duplicate transport stack, new distributed service or breaker-sharing regression was found. The compatibility facade contains delegation, not duplicated LM transport. Shared breaker state is explicitly process/active-endpoint scoped; endpoint changes reset binding, model changes do not. RAG is a small separate use case over reusable provider contracts; direct SQLite corpus reading and explicit rebuild are justified at this scale. Exact SQLite DDL comparison is strict but intentional fail-closed schema governance, not a generalized migration framework.

Real residuals are the [eight registry findings](00_FINAL_CERTIFICATION_REPORT.md): monolithic collector, missing operational NFRs, SQL coupling, remaining demo/identity/atomicity controls (P2-05; concrete period/count defect resolved), stale docs, weak ranking discrimination, bounded privacy assurance and limited governance/platform evidence. Dependencies/import inventory show no K8s, Kafka, Redis, microservices, full CQRS bus, external vector DB, cloud embeddings, auth platform, multitenancy, MLflow, feature store, MAS or runtime MCP added for certification. Developer tooling is not application architecture.
