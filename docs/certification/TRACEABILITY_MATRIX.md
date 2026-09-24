# Traceability Matrix

Baseline 1.0 · 2026-09-23. Requirement IDs взяты только из [spec.md](../../spec.md). Если отдельного FR нет, указан section/name или существующий code contract — новые FR IDs не придуманы. API в обычных rows — current `/api`; target endpoints явно помечены. IMPLEMENTED подтверждает узкую capability, а не выполнение всего связанного FR.

Исходное test evidence относится к [аудиту](00_REPOSITORY_AS_IS.md). [U03 запуск](U03_IMMUTABLE_SNAPSHOT_REPORT.md): 34 new snapshot + 25 U09 + 26 U05 + [14 U02 migration tests](U02_SCHEMA_MIGRATION_REPORT.md) + 18 existing unittest = 117 standard PASS; 8 additional functions отдельно PASS. [Status definitions](ARCHITECTURE_STATUS.md), [backlog](05_UPGRADE_BACKLOG.md).

| Capability | Requirement | Current component | API | ADR | Test evidence | Status | Backlog |
|---|---|---|---|---|---|---|---|
| Collection/auth | FR-1, FR-1.1/1.2/1.4/1.5 | [SafeVKCollector](../../app/collector.py), separate context/status | POST `/api/collector/start`, `/check-auth`, `/collect/{kind}` | [002](../adr/ADR-002-playwright-instead-of-vk-api.md) | v03 path/preview; markers не live parsing | PARTIAL full FR | U10/U13/U07 |
| Friends | Scope / Data Collection: друзья | collect(friends), _collect_profiles; save→services | POST `/api/collector/collect/friends`, `/api/collector/save-preview` | [002](../adr/ADR-002-playwright-instead-of-vk-api.md) | [test_v03](../../tests/test_v03.py) test_save_friend_preview; no live DOM | IMPLEMENTED narrow flow | U03/U10 |
| Followers | Scope / Data Collection: подписчики | collect(followers), relation import | POST `/api/collector/collect/followers`, save-preview | [002](../adr/ADR-002-playwright-instead-of-vk-api.md) | shared code, seeded services; no dedicated live assertion | IMPLEMENTED code/wiring | U03/U10 |
| Dialogs | Scope / Data Collection: диалоги | _collect_dialogs, collector_dialogs | POST `/api/collector/collect/dialogs`; GET `/api/dialogs` | [002](../adr/ADR-002-playwright-instead-of-vk-api.md), [005](../adr/ADR-005-sqlite-for-mvp.md) | [v03](../../tests/test_v03.py)/[v04](../../tests/test_v04.py) fresh save; [MIG-003](../../tests/test_migrations.py) real service metadata save after legacy upgrade | IMPLEMENTED persistence on supported migrated schema; no new live collection proof | U02 completed / U10 planned |
| Schema migration | Existing SQLite persistence compatibility / U02 contract | [db.init_db](../../app/db.py), [migrations](../../app/migrations.py) | startup only; no new API | [005](../adr/ADR-005-sqlite-for-mvp.md) | [MIG-001…007 + failure/WAL/schema tests](../../tests/test_migrations.py), MIG-008 regression: [report](U02_SCHEMA_MIGRATION_REPORT.md) | IMPLEMENTED; user DB not migrated in build | U02 completed |
| Imports | Scope / Snapshot Management: импорт; existing file-import contract | [importers](../../app/importers.py) + services | POST `/api/import/file`, `/api/import/snapshot` | [005](../adr/ADR-005-sqlite-for-mvp.md) | [v02](../../tests/test_v02.py) CSV import/stat upsert | IMPLEMENTED file/relations; not snapshot package | U03/U13/U15 |
| Relation changes | FR-3 Diff; FR-5 Timeline (membership subset) | [snapshots](../../app/snapshots.py), derived snapshot_events; services reads | GET `/api/changes`, `/api/people/{person_id}` | [003](../adr/ADR-003-immutable-snapshot-source-of-truth.md) | DIFF-001…009, EVT-001…005; same-day/backdated/empty/idempotency PASS | IMPLEMENTED membership; PARTIAL broader FR | U03/U04 completed |
| Analytics | FR-7 Dashboard; FR-4 Relationship Intelligence | current relation counts from COMPLETE snapshots; legacy fallback per stream; message periods unchanged | GET `/api/dashboard`, `/api/messages/leaderboard` | [003](../adr/ADR-003-immutable-snapshot-source-of-truth.md) | empty/current/legacy precedence/API tests PASS; message stats not snapshot-scoped | PARTIAL full analytics | U03 completed / U16 planned |
| AI insight | Scope / AI Analyst; FR-8 AI Pipeline (full pipeline planned) | [AIInsightService](../../app/ai/service.py) → LLMProvider; validate then persist | POST `/api/people/{person_id}/insight` | [004](../adr/ADR-004-local-llm-provider-abstraction.md) | LLM-PORT-001/007–010/012: fake substitution, local validation, persistence/API; no live inference | IMPLEMENTED person insight boundary; PARTIAL full AI Pipeline | U05/U07/U08 completed in report scope |
| Provider abstraction / LM adapter | Existing AI transport compatibility; ADR-004 / U05 contract | [port](../../app/ai/provider.py), [adapter](../../app/ai/providers/lmstudio.py), [composition](../../app/ai/composition.py) | GET `/api/lmstudio/models`, POST `/api/lmstudio/test`; same insight route | [004](../adr/ADR-004-local-llm-provider-abstraction.md) | [LLM-PORT-002–006/011/014 + reusable provider contracts](../../tests/test_ai_provider.py) PASS | IMPLEMENTED provider/adapter; DIP at AI boundary only | U05 completed |
| Retry / Exponential Backoff / Jitter | U09 build contract; bounded transient recovery, not a new FR | [ResilientLLMProvider](../../app/ai/resilience.py) around port; internal typed policy | existing person insight route, unchanged response schema | [004](../adr/ADR-004-local-llm-provider-abstraction.md) boundary | [RES-001…007](../../tests/test_llm_resilience.py): selective retry, exact max attempts, delays/jitter, timeout, no validation retry; RES-API-001 PASS | IMPLEMENTED; max 3 attempts / 1.5s sleep; no total deadline | U09 completed / U11 measurement planned |
| Circuit Breaker | U09 build contract; fail-fast and controlled recovery | locked per-process wrapper retained by composition | insight 503/detail; models/test remain independent | [004](../adr/ADR-004-local-llm-provider-abstraction.md) boundary | CB-001…010, RES-API-002…004, stale completion and shared binding tests PASS; [evidence](U09_LLM_RESILIENCE_REPORT.md) | IMPLEMENTED CLOSED/OPEN/HALF_OPEN, single probe; no fallback | U09 completed |
| Settings | [BP-01 setup](../../14_BUSINESS_PROCESSES.md); current three LM keys | [ai.settings](../../app/ai/settings.py) get_settings/save_settings | GET/PUT `/api/settings` | [001](../adr/ADR-001-local-first-architecture.md), [004](../adr/ADR-004-local-llm-provider-abstraction.md) | v02 default; LLM-PORT-013 API compatibility; composition mapping PASS | IMPLEMENTED current keys, no llm_provider selector | U05/U04 completed / U06 planned |
| Organization source | FR-11 OSINT is broader; current public organization API | collect_public_organization_source, RAM jobs | POST `/api/collector/organization-source`, `/jobs`; GET status/result | [002](../adr/ADR-002-playwright-instead-of-vk-api.md) | [v043](../../tests/test_v043_organization_source.py): 4 classifiers + 4 source checks | PARTIAL vs full OSINT/persistence | U10/U13 |
| Immutable relation Snapshot | FR-2 subset: friends/followers; full lifecycle/corpus target | snapshots/snapshot_people + SQL guards; [module](../../app/snapshots.py) | existing POST `/api/import/snapshot`, `/api/collector/save-preview`; no snapshot browser route | [003](../adr/ADR-003-immutable-snapshot-source-of-truth.md) | SNP-001…007, MIG-SNP-001…005, atomicity/SQL immutability tests; [U03 evidence](U03_IMMUTABLE_SNAPSHOT_REPORT.md) | IMPLEMENTED relation foundation; broader FR-2 PARTIAL | U03 completed |
| Local RAG | FR-8 retrieval subset; supporting FR-9 | [corpus/index/service](../../app/rag/service.py), composition → Retriever/LLMProvider | internal service only; no new route | [006](../adr/ADR-006-rag-architecture.md) | [31 tests + 18 synthetic labelled cases](U08_LOCAL_RAG_REPORT.md), six fitness checks | IMPLEMENTED — STRUCTURED_RAG—LEXICAL; broader FR remains partial | U08 complete / U17 planned |
| AI Chat target | FR-9 AI Chat | absent | target POST `/api/v1/ai/chat` | [006](../adr/ADR-006-rag-architecture.md), [004](../adr/ADR-004-local-llm-provider-abstraction.md) | none | PLANNED | U08/U04 |
| Graph target | FR-6 Social Graph | absent | target GET `/api/v1/graph` | [003](../adr/ADR-003-immutable-snapshot-source-of-truth.md) source decision only | none; Markdown scenarios not results | PLANNED | U16 |
| Export target | FR-2 Snapshot Lifecycle / экспорт | absent; local previews not export service | target GET `/api/v1/export/json`, `/csv`; feature contract differs | [003](../adr/ADR-003-immutable-snapshot-source-of-truth.md), [005](../adr/ADR-005-sqlite-for-mvp.md) | none | PLANNED | U15/U04 |

FR-1.3 full sequential collection, FR-2 snapshot lifecycle, FR-8 automatic AI pipeline пока не выполнены целиком. Наличие части связанных flows не закрывает требование. Target API rows describe the archived non-canonical proposal; U04 canonical runtime excludes them. They are not a future contract guarantee.

U03 completeness is evidence-based: declared full-set imports may become COMPLETE; current collector and HTML extraction stay INCOMPLETE/UNKNOWN. No new event-sourcing, RAG or automatic AI pipeline claim. U05/U09/settings/dialog/file regressions PASS.

| Capability | Requirement | Current component | API | Decision | Test evidence | Status | Backlog |
|---|---|---|---|---|---|---|---|
| Runtime API contract governance | U04 build invariant; no new FR invented | [main/models](../../app/main.py), [export](../../scripts/export_openapi.py) | 29 public `/api` + HTML shell; [canonical](../../11_OPENAPI.yaml) | compatibility decision in [U04 report](U04_API_CONTRACT_REPORT.md) | API-CONTRACT-001…012 + mutation/export/behavior tests: 23 PASS; full 140 + 8 PASS | IMPLEMENTED, current API drift RESOLVED | U04 completed; U06/U07 separate |


| Capability | Requirement / decision | Current implementation | Evidence | Status / scope |
|---|---|---|---|---|
| Local privacy/access | Privacy/local single-user principles; ADR-001; U06 | local Host/Origin; loopback-only LLM; safe errors/diagnostics/imports/UI; tracked guard | [31 SEC tests](../../tests/test_privacy.py), [report](U06_PRIVACY_ACCESS_HARDENING_REPORT.md); U04 contract still PASS | IMPLEMENTED bounded controls; no auth/encryption/zero-trust claim |

## U07 executable invariant → test → gate mapping

All rows below are **AUTOMATED** by the canonical runner, which is also the single command in the locally configured Actions workflow. Verdicts use successful test IDs from the same run; [reference](QUALITY_GATE_REFERENCE.md) and the [registry](../../scripts/run_quality_gates.py) contain exact method IDs. Prior U07 remote Actions success is owner-reported; this U08 revision is locally verified only and has not been pushed. Branch settings are unchanged.

| Invariant | Automated test module | Canonical/CI gate |
|---|---|---|
| FITNESS-DB-001 current version/idempotency | test_migrations.py; test_snapshots.py | Automated regression → architecture fitness |
| FITNESS-SNAPSHOT-001 immutable history | test_snapshots.py | Automated regression → architecture fitness |
| FITNESS-SNAPSHOT-002 incomplete/failed cannot become current | test_snapshots.py | Automated regression → architecture fitness |
| FITNESS-AI-001 use case depends on provider port | test_ai_provider.py | Automated regression → architecture fitness |
| FITNESS-AI-002 adapter transport-only | test_ai_provider.py; test_quality_gates.py | Automated regression → architecture fitness |
| FITNESS-RES-001 wrapper composition/imports | test_llm_resilience.py | Automated regression → architecture fitness |
| FITNESS-RES-002 deterministic fake delays | test_llm_resilience.py | Automated regression with sleep guard → architecture fitness |
| FITNESS-API-001 canonical/runtime/UI/security contract | test_api_contract.py | OpenAPI YAML/export + regression → architecture fitness |
| FITNESS-SEC-001 fixed loopback | test_privacy.py | Automated regression → architecture fitness |
| FITNESS-SEC-002 remote endpoint denial | test_privacy.py | Automated regression → architecture fitness |
| FITNESS-SEC-003 sensitive ignored/untracked paths | test_privacy.py | Sensitive artifacts/secret guard + regression → architecture fitness |
| FITNESS-UI-001 unsafe rendering protection | test_privacy.py | Node syntax + regression → architecture fitness |

Module links: [migration](../../tests/test_migrations.py), [snapshot](../../tests/test_snapshots.py), [AI](../../tests/test_ai_provider.py), [resilience](../../tests/test_llm_resilience.py), [API](../../tests/test_api_contract.py), [privacy](../../tests/test_privacy.py), [governance](../../tests/test_quality_gates.py). CI-001–008 and four additional governance checks are AUTOMATED. The eight [organization-source tests](../../tests/test_v043_organization_source.py) are now discoverable and retain their limited classifier/source-check scope.

**MANUAL / NOT RUN:** live VK/session/Chromium/LM Studio and visual browser walkthroughs. **DOCUMENTED_ONLY:** test Markdown 01–07 scenarios not mapped to executable methods, plus broader Chat/Graph/Export/Scheduler acceptance. Current authoritative total: **222**; Markdown checks and the 18 derived fitness verdicts are not added to that test count.

## U08 invariant → test → gate mapping

All six are AUTOMATED through the same canonical/CI runner and [test_rag.py](../../tests/test_rag.py). Exact method IDs are in the [U08 report](U08_LOCAL_RAG_REPORT.md) and registry.

| Invariant | Property | Gate |
|---|---|---|
| FITNESS-RAG-001 | Retriever/LLMProvider dependency ports | regression → fitness |
| FITNESS-RAG-002 | derived rebuildable index, obsolete edge removal | regression → fitness |
| FITNESS-RAG-003 | no-evidence bypasses discovery/generation | regression → fitness |
| FITNESS-RAG-004 | citations belong to supplied context; strict output | regression → fitness |
| FITNESS-RAG-005 | deterministic retrieval acceptance thresholds | regression → fitness |
| FITNESS-RAG-006 | synthetic committed evaluation fixture | tracked privacy + regression → fitness |
