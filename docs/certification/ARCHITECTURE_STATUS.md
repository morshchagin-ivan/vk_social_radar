# Architecture Status

Baseline 1.0 · 2026-09-23. Статусы capability: **IMPLEMENTED** — код и wiring подтверждены (уровень тестирования указан отдельно); **PARTIAL** — существует ограниченное подмножество; **PLANNED** — нужный механизм пока отсутствует; **NOT_PLANNED** — не входит в текущую evolution scope. PLANNED не означает implementation in progress.

Источник: [audit inventory](01_ARCHITECTURE_INVENTORY.md), [pattern verdicts](02_PATTERN_INVENTORY.md). Все Uxx ссылаются на неизменённый [upgrade backlog](05_UPGRADE_BACKLOG.md). Immutable Snapshot отмечен PLANNED как aggregate; audit PARTIAL относится только к существующей истории membership, а immutability audit verdict — CONTRADICTED_BY_CODE.

| Capability / Pattern | Status | AS-IS evidence | Target | Backlog |
|---|---|---|---|---|
| Local-first | PARTIAL | [db](../../app/db.py) local files; [server](../../run_server.py) loopback; endpoint unrestricted | enforced local processing policy | [U06](05_UPGRADE_BACKLOG.md) |
| Playwright | IMPLEMENTED | [SafeVKCollector.start/collect](../../app/collector.py), API wired; live run не повторён | сохранить web session boundary | [U10](05_UPGRADE_BACKLOG.md) evolution |
| Separate Chromium profile | IMPLEMENTED | collector.start → launch_persistent_context/user_data_dir; path test v03 | сохранение изоляции, privacy hardening | [U06](05_UPGRADE_BACKLOG.md) evolution |
| Preview-before-save | IMPLEMENTED | [main.collector_save_preview](../../app/main.py), [services.save_collector_preview](../../app/services.py); friends/followers/dialogs | explicit validated snapshot commit | [U03](05_UPGRADE_BACKLOG.md) evolution |
| SQLite | IMPLEMENTED | [get_connection/init_db](../../app/db.py), temp DB tests | migration discipline | [U02](05_UPGRADE_BACKLOG.md) evolution |
| Relation history | PARTIAL | relation_snapshots/date, mutable people | versioned immutable source | [U03](05_UPGRADE_BACKLOG.md) |
| Diff | PARTIAL | services.import_snapshot set differences; removed assertion | two complete comparable snapshots | [U03](05_UPGRADE_BACKLOG.md) |
| Timeline | PARTIAL | relation_events/list_changes/person_detail | provenance and stable chronology | [U03/U04](05_UPGRADE_BACKLOG.md) |
| Analytics | PARTIAL | dashboard/message_leaderboard SQL; tests | consistent period/snapshot scope | [U03/U16](05_UPGRADE_BACKLOG.md) |
| LM Studio integration | IMPLEMENTED | [generate_person_insight](../../app/lmstudio.py), main/create_insight, UI; no live inference proof | сохранить concrete adapter, добавить contract tests | [U05/U07](05_UPGRADE_BACKLOG.md) evolution |
| LLM Provider abstraction | PLANNED | direct LM module imports; no port/selection | provider port + LM adapter | [U05](05_UPGRADE_BACKLOG.md) |
| Retry/backoff/jitter | PLANNED | только HTTP timeout, retry отсутствует | bounded policy, accepted NFR | [U09/U11](05_UPGRADE_BACKLOG.md) |
| Circuit Breaker | PLANNED | только try/except → 503 | stateful gate subject to NFR | [U09/U11](05_UPGRADE_BACKLOG.md) |
| Immutable Snapshot aggregate | PLANNED | relation rows не immutable aggregate; audit defects | header/items/completeness/run/version | [U03](05_UPGRADE_BACKLOG.md) |
| Repository | PLANNED | direct SQL in services | узкие persistence contracts | [U12](05_UPGRADE_BACKLOG.md) |
| DIP | PLANNED | concrete db/client imports | application ports at IO seams | [U05/U12](05_UPGRADE_BACKLOG.md) |
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
| Privacy hardening | PARTIAL | local defaults, whitelist/sanitizer; fail-open/raw DOM gaps | enforced policy and Git/package evidence | [U06](05_UPGRADE_BACKLOG.md) |
| Distributed infrastructure / tenancy / federated training | NOT_PLANNED | no current requirement/load evidence | reconsider only on changed requirements | none; [rationale](ARCHITECTURAL_PATTERNS.md) |

[Current C4](C4_CURRENT.md) и [Target C4](C4_TARGET.md) намеренно различаются. Ни один PLANNED row не повышается до IMPLEMENTED только из-за появления ADR.
