# Architecture Status

Baseline 1.0 · 2026-09-23. Статусы capability: **IMPLEMENTED** — код и wiring подтверждены (уровень тестирования указан отдельно); **PARTIAL** — существует ограниченное подмножество; **PLANNED** — нужный механизм пока отсутствует; **NOT_PLANNED** — не входит в текущую evolution scope. PLANNED не означает implementation in progress.

Источник: [audit inventory](01_ARCHITECTURE_INVENTORY.md), [pattern verdicts](02_PATTERN_INVENTORY.md), [U02 report](U02_SCHEMA_MIGRATION_REPORT.md), [U05 report](U05_LLM_PROVIDER_REPORT.md), [U09 report](U09_LLM_RESILIENCE_REPORT.md). Все Uxx ссылаются на [upgrade backlog](05_UPGRADE_BACKLOG.md), обновлённый для U02/U03/U04/U05/U09. U03 реализует immutable relation Snapshot foundation; исторический audit verdict относится к pre-U03 коду. Full message/dialog/source corpus остаётся target.

| Capability / Pattern | Status | AS-IS evidence | Target | Backlog |
|---|---|---|---|---|
| Local-first controls | IMPLEMENTED in U06 bounded scope | fixed loopback, Host/Origin, local-only LLM, minimized diagnostics, path/Git/UI guards; [evidence](U06_PRIVACY_ACCESS_HARDENING_REPORT.md) | broader privacy assurance remains PARTIAL; no auth/encryption | U06 completed |
| Playwright | IMPLEMENTED | [SafeVKCollector.start/collect](../../app/collector.py), API wired; live run не повторён | сохранить web session boundary | [U10](05_UPGRADE_BACKLOG.md) evolution |
| Separate Chromium profile | IMPLEMENTED | collector.start → launch_persistent_context/user_data_dir; path test v03 | сохранение изоляции, privacy hardening | [U06](05_UPGRADE_BACKLOG.md) evolution |
| Preview-before-save | IMPLEMENTED | [main.collector_save_preview](../../app/main.py), [services.save_collector_preview](../../app/services.py); friends/followers/dialogs | explicit validated snapshot commit | [U03](05_UPGRADE_BACKLOG.md) evolution |
| SQLite | IMPLEMENTED | [get_connection/init_db](../../app/db.py), temp DB tests | дальнейшие изменения source model | [U03](05_UPGRADE_BACKLOG.md) evolution |
| Versioned schema migration | IMPLEMENTED | [migrations](../../app/migrations.py): current v2, preserved U02 0→1 dialog upgrade + U03 1→2 additive source schema; backup/rollback/FK/future guard PASS | user DB not migrated during build | U02/U03 completed |
| Relation history | IMPLEMENTED for new COMPLETE friend/follower snapshots | immutable header/membership/person projection; legacy retained as unknown history | message/dialog history outside U03 | U03 completed |
| Diff | IMPLEMENTED for relation membership | immutable compatible pair, deterministic order, empty/same-day/backdated repair; tests PASS | attribute/activity diff remains target | U03 completed |
| Timeline | PARTIAL | new snapshot_events have pair/projection provenance and DB uniqueness; legacy events labelled unknown | broader activity timeline remains target | U03/U04 completed |
| Analytics | PARTIAL | dashboard/message_leaderboard SQL; tests | consistent period/snapshot scope | [U03/U16](05_UPGRADE_BACKLOG.md) |
| LM Studio adapter | IMPLEMENTED | [LMStudioProvider](../../app/ai/providers/lmstudio.py): HTTP mapping, 8/120s timeouts, normalized errors; mock contract tests PASS; no live inference proof | сохранить contract при evolution | [U05](05_UPGRADE_BACKLOG.md) completed |
| LLM Provider abstraction | IMPLEMENTED | [LLMProvider Protocol](../../app/ai/provider.py), typed contracts, [composition](../../app/ai/composition.py), fake substitution and local validation PASS | only LM Studio bound; Ollama NOT IMPLEMENTED | [U05](05_UPGRADE_BACKLOG.md) completed |
| Retry / Exponential Backoff / Jitter | IMPLEMENTED | [ResilientLLMProvider](../../app/ai/resilience.py): generation only, 3 attempts, capped exponential full jitter, max sleep 1.5s; RES-001…007 PASS | total deadline NOT enforced; measured NFR pending U11 | [U09](05_UPGRADE_BACKLOG.md) completed |
| Circuit Breaker | IMPLEMENTED | shared per-process generation gate: CLOSED/OPEN/HALF_OPEN, 3 logical failures, 30s recovery, one probe, Lock; CB-001…010 PASS | no distributed state; discovery independent | [U09](05_UPGRADE_BACKLOG.md) completed |
| Immutable Snapshot aggregate | IMPLEMENTED for friend/follower foundation | [snapshots](../../app/snapshots.py), [DDL/triggers](../../app/snapshot_schema.py): UUID, capture/precision, lifecycle/completeness, immutable projection, explicit empty; [U03 evidence](U03_IMMUTABLE_SNAPSHOT_REPORT.md) | full corpus/Run aggregate not implemented | U03 completed |
| Repository | PLANNED | direct SQL in services | узкие persistence contracts | [U12](05_UPGRADE_BACKLOG.md) |
| DIP | IMPLEMENTED at AI provider boundary only | [AIInsightService](../../app/ai/service.py) depends on LLMProvider; no httpx/concrete adapter imports; SQL remains direct | persistence DIP still PLANNED | [U05](05_UPGRADE_BACKLOG.md) completed / U12 planned |
| Collector Strategy | PLANNED | if/elif + methods, no substitution seam | parser contract and replaceable strategies | [U10](05_UPGRADE_BACKLOG.md) |
| ACL/normalization | PARTIAL | importers._normalize_person, DOM cleaners/org mapper | typed boundary/identity validation | [U10/U13](05_UPGRADE_BACKLOG.md) |
| RAG | PLANNED | runtime NO_RAG; fixed person context | evaluated local query retrieval | [U08](05_UPGRADE_BACKLOG.md) |
| AI Chat | PLANNED | no route/session/retriever | narrow local grounded Q&A | [U08/U04](05_UPGRADE_BACKLOG.md) |
| AI Report | PARTIAL | ai_insights per person, not snapshot reports | source-bound report with citations | [U03/U05/U08](05_UPGRADE_BACKLOG.md) |
| Social Graph | PLANNED | docs only | defined edge semantics and provenance | [U16](05_UPGRADE_BACKLOG.md), P2 |
| Search | PARTIAL | [app.js](../../static/app.js) people/dialog client filters | scoped local search; evaluate ranking | [U17](05_UPGRADE_BACKLOG.md), P2 |
| Export | PLANNED | no export route; preview JSON not export product | local versioned round-trip | [U15](05_UPGRADE_BACKLOG.md), P2 |
| Scheduler | PLANNED | volatile asyncio jobs not scheduler | only with unattended collection requirement | [U14](05_UPGRADE_BACKLOG.md), P2 |
| Observability | PARTIAL | diagnostics/status/traces; raw data risk | safe correlated events and metrics | [U06/U11](05_UPGRADE_BACKLOG.md) |
| CI/CD | PLANNED | local bat scripts only | minimal reproducible test/release gate | [U07](05_UPGRADE_BACKLOG.md) |
| Privacy hardening | IMPLEMENTED bounded U06 / PARTIAL overall assurance | 31 security tests, tracked guard; no real data touched | operator/debug/history/full-erasure limitations remain; auth/encryption absent | U06 complete; U07/U11/U13 separate |
| Distributed infrastructure / tenancy / federated training | NOT_PLANNED | no current requirement/load evidence | reconsider only on changed requirements | none; [rationale](ARCHITECTURAL_PATTERNS.md) |

[Current C4](C4_CURRENT.md) и [Target C4](C4_TARGET.md) намеренно различаются. Ни один PLANNED row не повышается до IMPLEMENTED только из-за появления ADR.

U09 evidence: 25 new + 26 U05 + 14 U02 + 18 existing = 83 unittest PASS; 8 additional functions PASS. No network/real sleep/user DB writes. Provider и AI-boundary DIP остаются IMPLEMENTED; global DIP PARTIAL, Ollama/fallback NO, RAG NO_RAG/PLANNED.

U03: 34 new tests; 117 standard unittest + 8 additional functions PASS. CREATING/FAILED/INCOMPLETE cannot become current. Collector previews and HTML extraction remain UNKNOWN/INCOMPLETE; explicit relation imports declare complete sets. Message_stats and AI are not snapshot-reproducible; RAG NO_RAG. [U03 evidence](U03_IMMUTABLE_SNAPSHOT_REPORT.md).

U04: **Contract Governance IMPLEMENTED; current API drift RESOLVED**. [Canonical runtime OpenAPI](../../11_OPENAPI.yaml), [inventory](U04_RUNTIME_API_INVENTORY.md) and [report](U04_API_CONTRACT_REPORT.md): 29 public + 1 shell, 21 frontend calls, 23 new tests; 140 unittest + 8 additional PASS. Auth/RAG/Graph/Export remain unimplemented; full CI is U07.

U06 adds explicit local privacy/access controls, not application login or encrypted storage. Latest gate: **171 unittest + 8 additional PASS**. [Threat model](THREAT_MODEL.md), [classification](DATA_CLASSIFICATION.md), [report](U06_PRIVACY_ACCESS_HARDENING_REPORT.md).
