# Baseline → final findings matrix

Evidence scope: full certification audit at U08 (4ff2e09fe97e846d74c00977e3bb90a01ebfeb77), followed by focused post-U13A delta verification at 53a35014e75bedc4e69691d38f39c4752cd4bd68. Unchanged architecture findings and independent U08 probes are carried forward; the full canonical suite was rerun. This is not a full-from-zero re-audit.

Audited HEAD: `53a35014e75bedc4e69691d38f39c4752cd4bd68`. Original evidence: [00 repository](../00_REPOSITORY_AS_IS.md), [01 inventory](../01_ARCHITECTURE_INVENTORY.md), [02 patterns](../02_PATTERN_INVENTORY.md), [03 gaps](../03_SDD_CODE_GAP_ANALYSIS.md), [04 readiness](../04_CERTIFICATION_READINESS.md). The original 05 was also read with `git show e346244:docs/certification/05_UPGRADE_BACKLOG.md`; [current 05](../05_UPGRADE_BACKLOG.md) is an updated document and cannot substitute for the original backlog.

RESOLVED means the original defect is corrected in the stated runtime scope. PARTIALLY_RESOLVED preserves the remainder. SUPERSEDED means an earlier presentation/expectation has an explicit current replacement, not that target code was built. STILL_OPEN remains applicable debt. NOT_IN_SCOPE identifies a deferred target capability. Repeated baseline statements are normalized to G/U identifiers below; original reports are not rewritten.

## Every numbered baseline finding

| Original | Final classification | Before → after / exact evidence | Residual |
|---|---|---|---|
| G01 FAIL immutable source | PARTIALLY_RESOLVED | snapshots.create_snapshot/read_snapshot; snapshot_schema guards; SnapshotTests.test_snp_002_projection_immutable_and_evt_003_historical_display | Relations implemented; full message/dialog/run corpus absent |
| G02 FAIL same-day/repeat/empty | RESOLVED | UUID identity; explicit zero header; _derive pair uniqueness; test_snp_003_exact_membership_and_no_daily_union, test_snp_004_empty_complete_and_evt_005_replay | Legacy history not reconstructed; corrected semantics apply to v2 |
| G03 FAIL installed schema | RESOLVED | migrations.migrate/backup_database; MigrationTests.test_mig_002_legacy_preservation_and_backup and test_mig_003_real_runtime_write_after_migration; independent v1 probe | Real user DB not migrated during audit |
| G04 FAIL API | RESOLVED | main metadata/api_models/api_contract; root OpenAPI exact app.openapi equality; ContractGateTests | Current /api only, 29 public + shell, honest auth/errors |
| G05 FAIL provider/Ollama | PARTIALLY_RESOLVED | LLMProvider, AIInsightService, LMStudioProvider, composition; test_llm_port_001_fake_substitution_and_context_scope | Only LM adapter; Ollama explicitly deferred; no provider selector needed for one adapter |
| G06 WARNING resilience | PARTIALLY_RESOLVED | ResilientLLMProvider; 25 U09 tests including threshold/recovery/concurrency | Attempts/sleep bounded; original total deadline expectation not met |
| G07 FAIL RAG/chat | PARTIALLY_RESOLVED | app/rag pipeline, get_rag_service, 31 tests, independent metric recomputation | Internal lexical use case; Chat API/UI absent |
| G08 FAIL C4 target/current | SUPERSEDED | C4_CURRENT shows static UI/local modules; C4_TARGET and root 08/09 banners distinguish intended components | Some stale prose remains P2-01; no React/Graph/Scheduler claim |
| G09 FAIL Repository/DIP | PARTIALLY_RESOLVED | AI/RAG port dependency tests PASS; raw SQL still in services and AI persistence | GLOBAL_DIP_PARTIAL; Repository U12 open |
| G10 WARNING collector Strategy/ACL | STILL_OPEN | SafeVKCollector.collect uses concrete methods; importers normalization remains procedural | U10 substitution/DOM fixtures absent |
| G11 FAIL ER/schema/run | PARTIALLY_RESOLVED | DATA_MODEL_STATUS matches eleven temp DB tables; v2 snapshots/projections/events have keys/FKs | CollectorRun volatile; dialogs/messages/full target ER not implemented |
| G12 FAIL analytic time/source scope | PARTIALLY_RESOLVED | dashboard/current_sets use latest COMPLETE relation streams; AI fixed person/latest period documented | message_stats mutable/period-based; full FR-7/8 not satisfied |
| G13 WARNING remote inference | RESOLVED | privacy.local_llm_url at settings/composition/adapter; deny LAN/public/userinfo/deceptive names; no DNS/proxy/redirect | Trusted local provider/OS remains assumption |
| G14 FAIL raw diagnostics/logging | PARTIALLY_RESOLVED | _save_diagnostics writes counter-only JSON; safe public errors; U06 log/retention tests | Full third-party logging, legacy retention/full erasure remain partial |
| G15 WARNING Git/distribution evidence | PARTIALLY_RESOLVED | Real Git known; tracked guard PASS; only placeholders tracked; historical path inventory clean | Not exhaustive encoded/binary/history/package-content assurance |
| G16 WARNING fail-open browser guard | RESOLVED | _route_request aborts and _route_web_socket closes on guard error; service workers blocked; U06 fake route tests | Live browser-wide behavior not audited |
| G17 FAIL discovery/coverage | PARTIALLY_RESOLVED | All eight legacy functions converted; 240 unified tests/18 invariants; U04 in-process behavior | Marker tests/live DOM/UI coverage limitations remain |
| G18 WARNING NFR/gates | PARTIALLY_RESOLVED | Unified gates and snapshot/RAG sanity timings exist; retry/input bounds enforced | API/collector/growth/recovery/deadline targets remain TBD |
| G19 FAIL async/durable sequences | SUPERSEDED | Current docs state synchronous insight/threadpool and volatile organization jobs; root sequence document TARGET | No durable queue/worker/scheduler added |
| G20 FAIL global search/export | NOT_IN_SCOPE | Existing client filters unchanged; RAG internal retrieval is not global product search; API excludes export | U15/U17 planned, not completed acceptance |
| G21 WARNING org preview/save mismatch | RESOLVED for documented preview-only scope | main collector_organization_source description and save-preview 400 contract; U04 organization/preview tests | No organization persistence product; no claim it exists |
| G22 WARNING automatic demo | PARTIALLY_RESOLVED | seed_demo_data now respects existing empty/incomplete v2 history; test_seed_does_not_replace_valid_empty_user_history | Truly empty DB still seeds automatically; explicit demo mode absent |
| G23 WARNING identity/validation/ZIP | PARTIALLY_RESOLVED | New relation external_key is namespaced; no modulo hash in new snapshot writes; bounded ZIP/path handling | U13A central validator + 18 tests + 26 independent invalid probes close malformed dates/negative counts. Legacy aliases/account switching and archive-wide atomicity remain deferred (P2-05) |
| G24 PASS analytics independence | RESOLVED / retained | services reads SQLite; no collector/httpx dependency | Not general dependency availability proof |
| G25 PASS isolated profile | RESOLVED / strengthened | Fixed PROFILE_DIR, safe-directory/reparse guard, unserved path | Authenticated profile remains locally sensitive |
| G26 PASS local persistence | RESOLVED / retained | SQLite + default loopback + local inference policy | No at-rest encryption or multi-user isolation |

Code/test files: [snapshots](../../../app/snapshots.py), [schema](../../../app/snapshot_schema.py), [migrations](../../../app/migrations.py), [services](../../../app/services.py), [importers](../../../app/importers.py), [collector](../../../app/collector.py), [privacy tests](../../../tests/test_privacy.py), [snapshot tests](../../../tests/test_snapshots.py), [migration tests](../../../tests/test_migrations.py), [API tests](../../../tests/test_api_contract.py), [provider tests](../../../tests/test_ai_provider.py), [resilience tests](../../../tests/test_llm_resilience.py), [RAG tests](../../../tests/test_rag.py).

U13A delta evidence: [normalize_message_stats](../../../app/message_stats.py) is invoked before service person/stat writes and by the seed writer; [18 validation tests](../../../tests/test_message_stats_validation.py) and independent direct/upload probes passed. Old P1-04's concrete defect is RESOLVED; its remaining policy/identity scope is P2-05. Current totals are P0=0/P1=3/P2=5; baseline priorities/facts below remain historical.

## All original P0/P1 backlog entries, plus P2 disposition

| Original priority / task | Classification against original acceptance | Delivered evidence / remaining scope |
|---|---|---|
| P0 U01 scope/revision/ADR | PARTIALLY_RESOLVED | Known protected history, current/target split, six ADRs, traceability; maintained prose drift remains and formal course rubric is unverified |
| P0 U02 migration | RESOLVED | U02/U03 migration tests + independent historical-DDL v1→v2 backup/preservation probe |
| P0 U03 snapshot integrity | PARTIALLY_RESOLVED | Relation empty/same-day/replay/backdated/frozen projection guarantees implemented; no full source/run aggregate |
| P0 U04 runtime API | RESOLVED | Canonical exact exported 30-operation contract + semantic/UI/error tests |
| P0 U05 provider | RESOLVED in stated port/LM scope | Structural fake/adapter contract, normalized errors, local validation, real production composition; Ollama explicitly deferred |
| P0 U06 privacy/disclosure | PARTIALLY_RESOLVED | Required bounded runtime controls and tracked evidence delivered; broad forensic/privacy/retention assurance remains partial |
| P0 U07 unified quality/CI | RESOLVED locally; external execution evidence qualified | Dynamic discovery/fitness + workflow; owner reports U07/U08 green, independent remote verification not performed |
| P0 U08 minimal evaluated RAG | RESOLVED in bounded scope | Real persisted corpus/query retrieval/provenance/citations/no-evidence/eval; lexical-only; ranking-evaluation warning |
| P1 U09 resilience/deadline | PARTIALLY_RESOLVED | Retry/backoff/jitter/breaker implemented; total deadline/cached fallback not provided and not claimed |
| P1 U10 parsers | STILL_OPEN | Concrete collector + marker tests; no parser port/substitution/representative DOM suite |
| P1 U11 NFR/observability | PARTIALLY_RESOLVED | Diagnostic minimization, retry/input bounds, development/performance sanity; broader operational metrics/targets absent |
| P1 U12 persistence ports | STILL_OPEN | AI vendor DIP does not remove SQLite knowledge from high-level persistence |
| P1 U13 demo/identity/validation | PARTIALLY_RESOLVED | New relation identity, incomplete collector policy, upload limits and preview-only contract fixed; U13A closes the reproduced period/counter integrity defect; demo/identity/broader-domain/atomicity residuals remain (P2-05) |
| P2 U14 scheduler/durable jobs | NOT_IN_SCOPE | Volatile operation dictionary explicitly documented |
| P2 U15 export/restore product | NOT_IN_SCOPE | Migration backup exists; user export/restore product does not |
| P2 U16 graph/score | NOT_IN_SCOPE | No graph builder/score semantics or routes claimed |
| P2 U17 advanced/global search | PARTIALLY_RESOLVED | U08 lexical foundation exists; global UI and advanced retrieval remain deferred |

Original P0 priority described the accepted scope, not a mandate to implement all target features. Partial rows here do not relabel full requirements as satisfied. The release verdict applies to the bounded implementation and residuals are carried explicitly.

## Unnumbered original document/evidence warnings

| Baseline source finding | Classification | Final disposition |
|---|---|---|
| 00/01/04 Git revision unavailable; tracked cookies/dumps unverifiable | RESOLVED for current checkout; PARTIALLY_RESOLVED overall disclosure | Known graph/tags, no tracked sensitive paths; no exhaustive historic secret assurance |
| 00 unsafe default test file writes | RESOLVED | Temporary DB/storage/import path fixtures and guarded imports; canonical suite does not require user data |
| 00 incomplete sidecar/env/profile ignores | RESOLVED | .gitignore + U06 checks + eight independent ignore probes |
| 00 API auth absent/arbitrary profile override | SUPERSEDED / RESOLVED | Honest trusted-OS no-auth contract; fixed profile root replaces override |
| 00/04 no CI, runtime not pinned for CI | RESOLVED for configured pipeline | Windows 2022, Python 3.13.2, Node 22.14.0; same runner; no app secrets |
| 03 PROJECT_PASSPORT missing | NOT_IN_SCOPE | No separate passport invented; scope/identity live in README/certification docs |
| 03 spec, 08 architecture, 09 C4 duplicated/misleading | SUPERSEDED with residual | Target banners + current C4/status; copies/archive retained as historical target; P2-01 prose drift |
| 03 10 DATA_MODEL physical/target conflict | SUPERSEDED | DATA_MODEL_STATUS gives physical v2; root/feature ER remain target |
| 03 11 OpenAPI / 12 guide conflict | RESOLVED | Root runtime canonical; feature YAML explicitly archived/non-canonical; archive not a client contract |
| 03 14 BP / 15 sequence / 16 class pretend runtime | SUPERSEDED | Target banners; current flows mapped separately in final architecture report; no async/Repository inflation |
| 03 17 plan / 18 backlog / unchecked feature tasks | SUPERSEDED | Plans stay plans; U01–U17 reports record actual increments; unchecked work not treated as done |
| 03 test plan/API/integration/smoke/cases/checklist overclaim | PARTIALLY_RESOLVED | Current automated banners and maintained Python suite; broad Markdown scenarios remain DOCUMENTED_ONLY |
| 03 test data large/history/graph datasets absent | PARTIALLY_RESOLVED | Synthetic migration/snapshot/RAG fixtures + performance sanity; broad graph/live datasets absent |
| 03 missing standalone roadmap | SUPERSEDED | ARCHITECTURE_EVOLUTION and U01–U17 backlog provide roadmap without duplicate file |
| 03 no formal ADRs / confusing inline AD numbering | RESOLVED structurally; PARTIALLY_RESOLVED consistency | Six formal ADRs/register exist; stale ADR-002/004 current assertions remain |
| 03 old FILE_MANIFEST/README omitted org flow | PARTIALLY_RESOLVED | Current README/API inventory describe organization preview/jobs; manifest is historical, not Git evidence |
| 03 unresolved root-target references to passport/DB/AI/RAG docs | STILL_OPEN in historical target bodies | Those references are not implemented evidence; canonical runtime evidence uses existing files; docs gate does not certify every target link |
| 03 separate test-management feature lacks runtime | NOT_IN_SCOPE | TestDefinition/TestRun and /api/tests remain planned; unrelated to unified developer quality gate |
| 03 coverage/lint absent; marker assertions | STILL_OPEN as coverage limitation | No percent coverage/lint/live E2E claim; behavior checks materially expanded |

## Original pattern and readiness summaries

| Original pattern | Final classification / bounded state |
|---|---|
| Immutable Snapshot | PARTIALLY_RESOLVED: implemented relation aggregate, broader source model deferred |
| Repository | STILL_OPEN: no repository contract |
| DIP | PARTIALLY_RESOLVED: AI and RAG ports implemented, global persistence partial |
| Adapter | PARTIALLY_RESOLVED: tested LM adapter; browser/import boundaries remain concrete |
| Collector Strategy | STILL_OPEN |
| Pipeline | PARTIALLY_RESOLVED: atomic source/events and callable retrieval chain; no automatic full AI workflow |
| ACL | PARTIALLY_RESOLVED: namespaced relation keys and security validation; broad typed domain import remains open |
| RAG | RESOLVED for U08: STRUCTURED_RAG—LEXICAL, not full chat |
| Retry | RESOLVED bounded generation scope |
| Circuit Breaker | RESOLVED in-process shared generation scope |

Original 04 readiness areas 1–16 map respectively to: U01/P2-01; G08; G19/P2-01; G04; G01/G03/G11/G12; G09/G10; G07/U08; G05/U06; U05; G13–G16; G17/U07; ADR registry/P2-01; G14/G18; U07/P2-04; G18/P1-02; all fresh canonical/supplemental evidence. The historical 0 READY / 12 PARTIAL / 4 MISSING tally is not silently replaced with a fabricated full-SDD score.

Current prioritized residual counts and release interpretation: [final report](00_FINAL_CERTIFICATION_REPORT.md). Detailed evidence commands: [defense map](07_DEFENSE_EVIDENCE_MAP.md).
