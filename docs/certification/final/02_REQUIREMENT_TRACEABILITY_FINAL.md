# Final requirement traceability

Evidence scope: full certification audit at U08 (4ff2e09fe97e846d74c00977e3bb90a01ebfeb77), followed by focused post-U13A delta verification at 53a35014e75bedc4e69691d38f39c4752cd4bd68. Unchanged architecture findings and independent U08 probes are carried forward; the full canonical suite was rerun. This is not a full-from-zero re-audit.

HEAD `53a35014e75bedc4e69691d38f39c4752cd4bd68`. Requirements come from [spec.md](../../../spec.md), its existing scope headings and explicit Uxx build invariants. No invented FR numbers. AUTOMATED means executed in the fresh 240-test gate; MANUAL means an operational scenario exists but was not run; DOCUMENTED_ONLY means specification, not completion. Internal-only services need no HTTP endpoint.

The release candidate implements a bounded subset. It does **not** complete all FR-1…FR-11. Accepted decisions and implemented mechanisms are different from full product acceptance.

## Requirement → architecture → code → API → evidence

| Requirement / accepted scope | Architecture and code | API if applicable | Acceptance / evidence type | Final status |
|---|---|---|---|---|
| FR-1.1 authorized session detection | Playwright persistent profile; SafeVKCollector._detect_authenticated/get_status | /api/collector/start, /check-auth, /status | AUTOMATED mocked status/security/contracts; MANUAL live login not run | Code/wiring IMPLEMENTED; operational correctness partial |
| FR-1.2 stop/message on unauthenticated collection | SafeVKCollector.collect auth check/state | /api/collector/collect/{kind} | Existing path/source checks and mocked collector API; real auth/captcha MANUAL | PARTIAL evidence |
| FR-1.3 sequential collection of all supported entities | Concrete kind branches; organization source separate | /collect/{kind}, /organization-source, /jobs | DOCUMENTED_ONLY full orchestration; current individual flows tested narrowly | PARTIAL; no full sequential pipeline |
| FR-1.4 errors and FR-1.5 collector journal | Safe statuses/operation traces/counter diagnostics | Collector status and jobs/result | AUTOMATED U06 safe errors/retention; volatile job contract U04 | PARTIAL: no durable run journal/full observability |
| FR-2 immutable capture: friends/followers | snapshots.create_snapshot; snapshot_schema.STATEMENTS | POST /api/import/snapshot; collector save yields INCOMPLETE | AUTOMATED U03 + independent temp immutability/empty/same-day checks | IMPLEMENTED relation foundation |
| FR-2 full corpus: subscriptions/dialogs/communities/channels/profiles/run metadata | Eleven-table physical model; dialogs separate; frozen relation name/URLs only | No full snapshot resource | DOCUMENTED_ONLY full target; no Message/CollectorRun entity | PLANNED/PARTIAL, not accepted as complete |
| FR-2 lifecycle creation/storage/import | Services, imports and migrations with source/event transaction | /api/import/file, /import/snapshot, /collector/save-preview | AUTOMATED migration/import/snapshot/API fixtures | IMPLEMENTED bounded formats/relations |
| FR-2 lifecycle browsing/export/deletion | read_snapshot is internal; deletion triggers intentionally deny | No snapshot list/export/delete API | DOCUMENTED_ONLY UI/export/retention lifecycle | PLANNED; not disguised by preview JSON |
| FR-3 selected/latest compatible diff | _diff/diff_snapshots, predecessor, _derive | Internal pair API; import derives events; /api/changes reads them | AUTOMATED test_diff_001_002_003_004_005_membership_cases, stream/backdated tests | IMPLEMENTED membership subset; attributes/activity diff planned |
| FR-4 Relationship Score | Existing message initiation percentage and relation events only | /api/messages/leaderboard is not a score API | AUTOMATED existing aggregates; DOCUMENTED_ONLY score semantics | NOT IMPLEMENTED full FR |
| FR-5 timeline | snapshots.changes joins frozen projection; legacy union labelled unknown | /api/changes; /api/people/{person_id} | AUTOMATED frozen historical names/pair provenance/order/idempotency | PARTIAL: membership history, not activity peaks/profile evolution |
| FR-6 Social Graph | No graph builder or edge model | None | DOCUMENTED_ONLY | PLANNED / NOT_IN_SCOPE |
| FR-7 Dashboard local reads | services.dashboard uses current_sets and SQLite; no VK dependency | /api/dashboard | AUTOMATED U03 empty/latest and U04 shapes | IMPLEMENTED local relation reads; PARTIAL full FR |
| FR-7 exclusively latest snapshot | Relation counts use latest COMPLETE per stream; message_total spans mutable periods | Existing dashboard contract explicitly says so | AUTOMATED scope tests; code inspection | NOT MET for all dashboard data; limitation disclosed |
| FR-8 automatic Diff→index→RAG→AI→dashboard | Diff derives on relation import; get_rag_service and Person Insight are explicitly invoked separately | Insight endpoint only; no pipeline endpoint | AUTOMATED each bounded mechanism; full orchestration DOCUMENTED_ONLY | PARTIAL; no automatic AI pipeline |
| FR-8 retrieval foundation / U08 | Readonly corpus → stable facts → BM25 → context → RAGService → provider | Internal Python get_rag_service; no RAG route | AUTOMATED 31 RAG tests + independent metrics | IMPLEMENTED STRUCTURED_RAG—LEXICAL |
| FR-9 local grounded Q&A principle | RAGService retrieves local immutable relation evidence with citation validation | Internal only | AUTOMATED FakeLLM, no-evidence/citations; no live prose-quality test | IMPLEMENTED mechanics; PARTIAL FR-9 |
| FR-9 AI Chat product and full knowledge sources | No sessions/chat UI; excludes ai_insights/message history | None | DOCUMENTED_ONLY chat product | PLANNED, not satisfied by an internal class name |
| FR-10 Personal CRM/reminders/VIP | No CRM module or scheduler | None | DOCUMENTED_ONLY | NOT_IN_SCOPE |
| FR-11 OSINT | classify_public_vk_source, _normalize_public_org_profile, public organization collector | Organization preview/job routes | AUTOMATED four classifiers + source checks and mocked API; MANUAL live collection not run | PARTIAL public-source preview; no generic organization save |
| Scope: Person Insight | AIInsightService.generate/create → LLMProvider → resilience/LM adapter | POST /api/people/{person_id}/insight | AUTOMATED valid persistence, invalid output refusal, compatibility and error cases | IMPLEMENTED fixed-context insight; not RAG or reproducible snapshot report |
| AF-3 unavailable LM Studio | Normalized provider errors, bounded retries, circuit, generic 503 | Existing LM/insight routes | AUTOMATED U05/U09 failures/recovery/concurrency | IMPLEMENTED bounded fail behavior; no cache/cloud fallback |
| AF-4 no network for local reads | services reads persisted SQLite | Dashboard/people/changes/messages | AUTOMATED isolated services/API; code dependency inspection | IMPLEMENTED read independence, not universal availability |
| AF-5 SQLite failure/recovery | Version guards, backup before migration, rollback; generic runtime errors | Startup migration; normal local reads | AUTOMATED U02/U03 fault fixtures; independent v1 backup probe | PARTIAL: no full restore product/RTO |

Evidence modules: [migrations](../../../tests/test_migrations.py), [snapshots](../../../tests/test_snapshots.py), [API](../../../tests/test_api_contract.py), [provider](../../../tests/test_ai_provider.py), [resilience](../../../tests/test_llm_resilience.py), [privacy](../../../tests/test_privacy.py), [RAG](../../../tests/test_rag.py), [organization](../../../tests/test_v043_organization_source.py). Exact claim/test/command pairs are in [defense evidence](07_DEFENSE_EVIDENCE_MAP.md).

## Cross-cutting certification contracts

| Existing principle/build contract | Architecture → implementation | Evidence / status |
|---|---|---|
| Privacy / ADR-001 local-first | LocalAccessMiddleware, local_llm_url, fixed launcher/profile, minimized diagnostics, safe imports/UI | AUTOMATED U06; bounded controls implemented, overall assurance PARTIAL |
| U02 safe schema evolution | db.init_db → detect_schema → locked migration/backup/validation | AUTOMATED 14 U02 + six U03 migration methods; clean-room PASS |
| U04 contract governance | main/api_models/api_contract → generated root OpenAPI | AUTOMATED export/semantic mutation/UI tests; exact comparison recomputed |
| U05 provider independence | Use cases depend on LLMProvider, composition binds transport | AUTOMATED structural fake/AST/adapter tests; AI_BOUNDARY_IMPLEMENTED, GLOBAL_DIP_PARTIAL |
| U07 reproducible quality | One runner, one test execution, dynamic categories/FITNESS outcomes | AUTOMATED 240 tests/18 invariants; no legacy separate-eight path |
| U13A period/counter integrity | message_stats.normalize_message_stats → services.import_message_stats before person/stat writes; importers._dispatch → service; seed writer also validates | AUTOMATED 18 U13A tests in canonical 240/240; independent 26 invalid/6 valid direct-upload probes PASS; safe API 400, no invalid domain rows. IMPLEMENTED; identity/demo/broader atomicity DEFERRED (P2-05) |
| U08 evidence mechanics | Stable IDs, source filters, context budget, citation subset/no-evidence | AUTOMATED with synthetic persisted facts and FakeLLM; not factuality certification |
| Maintainability/extensibility | Local modular monolith with selected AI/RAG ports | PARTIAL: collector remains concrete, persistence SQL remains coupled |
| Reliability: preserved history | Immutable finalized sources, backups, transactional writes | ENFORCED/AUTOMATED for relations; full message/run source history absent |

NFR-specific MEASURED / ENFORCED / PROPOSED-TBD / UNSUPPORTED classifications: [architecture/NFR audit](03_ARCHITECTURE_CONSISTENCY_FINAL.md).

## Orphan requirements and implementation

Requirements without corresponding completed runtime acceptance: full sequential collection, full-corpus snapshot lifecycle, attribute/activity diff, Relationship Score, Social Graph, wholly snapshot-scoped dashboard, automatic AI pipeline, AI Chat UI/session/report corpus, CRM, scheduler, export/restore and generalized search. They are visible roadmap items, not silent passes. The separate test-management feature's TestDefinition/TestRun and /api/tests are also not implemented and not the developer quality runner.

Exact U13A trace: calendar-valid YYYY-MM-DD/start <= end → normalize_message_stats → MessageStatsValidationTests.test_val_001_malformed_periods_rejected_at_both_boundaries, test_val_002_real_calendar_validation, test_missing_dates_and_reversed_range_rejected; non-negative incoming/outgoing → test_val_003_negative_incoming_rejected/test_val_004_negative_outgoing_rejected; direct/import atomic rejection → test_val_009_direct_service_batch_remains_atomic/test_val_010_invalid_upload_has_only_existing_failed_attempt_bookkeeping; HTTP compatibility → test_val_012_api_preserves_safe_400_and_valid_success. [Test file](../../../tests/test_message_stats_validation.py) is registered in the runner's Domain validation (U13A) category; no extra fitness count was invented. Total is a derived read expression, not an independent input invariant.

Implemented details without a dedicated FR number: migration/version guards, canonical OpenAPI governance, provider/resilience mechanics, Host/Origin and local endpoint policy, quality/fitness registry, organization job lifecycle, and internal RAG composition. Each has a Uxx contract, ADR/principle or documented runtime contract; no invented requirement ID is needed. Temporary synthetic evaluation/performance tools are development evidence, not product endpoints.

No unexplained new product subsystem was found. The legacy app/lmstudio.py facade is compatibility code; production API imports app.ai composition directly, and test_v02 still exercises its settings import. It is not a second transport implementation.
