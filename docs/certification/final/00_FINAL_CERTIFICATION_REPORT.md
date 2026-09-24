# VK Social Radar — Final certification verification

Evidence scope: full certification audit at U08 (4ff2e09fe97e846d74c00977e3bb90a01ebfeb77), followed by focused post-U13A delta verification at 53a35014e75bedc4e69691d38f39c4752cd4bd68. Unchanged architecture findings and independent U08 probes are carried forward; the full canonical suite was rerun. This is not a full-from-zero re-audit.

**VERDICT: CERTIFICATION READY WITH WARNINGS**

Audit date: 2026-09-24. Audited branch: `certification/architecture-upgrade`. Exact HEAD: `53a35014e75bedc4e69691d38f39c4752cd4bd68` (`fix(data): enforce message statistics invariants`). This is a release-candidate assessment of the bounded implemented architecture, not acceptance of the entire target SDD or a formal course certificate.

The post-U13A canonical gate was rerun before supplemental probes and evidence refresh: **exit 0; 240 discovered/executed/passed tests; 18/18 fitness invariants; 7/7 gates; 14.309 seconds overall**. Zero failed, errored, skipped or omitted tests were reported. Code and wiring inspection plus separate temporary-database probes support the core claims. No P0 blocker or newly reproduced functional regression was found. Eight grouped residual findings remain: **P0=0, P1=3, P2=5**. These are engineering priorities, not eight newly introduced defects.

## Executive matrix

| Area | Baseline | Final | Evidence | Residual |
|---|---|---|---|---|
| Schema Evolution | Installed dialogs 6 columns; no version/backup migration | Supported v0/v1→v2, pre-change SQLite backup, transactional rollback, validation | migrations.migrate; 14 U02 + U03 migration tests; independent historical-v1 DDL probe | Unknown shapes refused; no operational restore-time guarantee |
| Snapshot | Daily union, empty loss, duplicate events, mutable historical names | UUID COMPLETE relation sources, frozen projections, deterministic derived pair events | 34 U03 tests; independent empty/same-day/backdated/immutability probe | Messages/dialogs/full lifecycle and legacy reconstruction excluded |
| OpenAPI | Wrong prefix, paths, schemas and phantom Bearer auth | Canonical runtime 3.1.0; 30 app operations / 29 public; 21 UI call sites | app.openapi equality independently recomputed; 23 U04 tests | No formal external validator/client generation; no new target endpoints |
| Provider/DIP | Concrete mixed HTTP/business module | AI_BOUNDARY_IMPLEMENTED; RAG also depends on ports | AIInsightService/RAGService → LLMProvider; fake substitution; transport tests | GLOBAL_DIP_PARTIAL; direct persistence SQL; Ollama absent |
| Resilience | HTTP timeout only | Selective bounded retry, exponential backoff/full jitter, locked three-state breaker | 25 U09 tests, production shared binding | No total elapsed deadline, cache or fallback |
| Privacy | Arbitrary inference endpoint, raw diagnostics, fail-open routing | Loopback policy, Host/Origin guard, minimized diagnostics, safe paths/UI/errors | 31 U06 tests; tracked guard and independent ignore/path checks | Trusted OS model; logging/retention/full-history assurance partial |
| Quality Gates | 18 tests + 8 omitted plain functions; no unified governance | One runner, dynamic counts and recorded fitness outcomes | run_quality_gates.main; 12 governance tests | Focused marker tests remain; no percentage coverage claim |
| CI | No application workflow | Valid Windows workflow invokes the same runner | Local YAML/test inspection; user-observed U07 and U08 green runs | U13A remote run NOT YET RUN; U08 green is only user-observed; branch protection not verified |
| RAG | NO_RAG fixed context | STRUCTURED_RAG—LEXICAL, internal service only | Persisted corpus → BM25 → bounded context → provider → validated citation IDs | No semantic retrieval/chat API; ranking-blind small fixture; no entailment proof |
| Tests/Fitness | 18 discovered + 8 manual function calls; none registered | 240 automated tests / 18 registered invariants PASS | Fresh canonical execution, not copied historical totals | Live VK/LLM/Chromium excluded; fake mechanics only |
| SDD consistency | Target presented as current; duplicate contracts | Current/target split, canonical API, formal ADR register | C4, API, data and traceability review | Stale maintained ADR/security/evolution statements remain (P2-01) |

## Audit boundary and method

The U08 full audit read original audit documents 00–04 and both the original backlog at baseline Git revision and current 05. Reviewed migration/snapshot/API/provider/resilience/privacy/quality/RAG code, applicable tests, current/target diagrams, ADR-001…006, specification FRs, NFRs and workflow. Recomputed routes and RAG metrics independently of the production evaluator. Supplemental data was synthetic and confined to temporary directories; production startup, collector, inference and network were not invoked. The real DB was not opened; only its file hash was checked.

During this delta audit no production, test, ordinary documentation, dependency, workflow, Git config, branch, tag or DB edits occurred. No commit, push, fetch, merge, tag creation or fix. Only the eight existing Markdown artifacts in this directory were refreshed after verification and canonical PASS; none are staged or committed.

## Repository identity and protected history

The original U08 audit began clean. The delta audit began with **exactly eight expected untracked final Markdown files**, no staged or other changes. Remote configuration: origin points to `https://github.com/morshchagin-ivan/vk_social_radar.git`. The local remote-tracking reference already points at U08; no remote query was made. This does not prove CI execution.

| Milestone | Verified commit | Ancestor of HEAD |
|---|---|---|
| Baseline | e34624462fa8ef3cdf56e29ce64cab24aac61411 | YES |
| U02 | 894e86b4d34268cc609db870d7e7ed099a4be395 | YES |
| U05 | 2bf48476b396542fde83b3a8c87f27d4cbf2b335 | YES |
| U09 / v0.5 | 32a3d8f286cac2acbb27069a19e65055dacc1d74 | YES |
| U03 | 1c619259691f5ddca232f1d67142bdf14c0be47b | YES |
| U04 | 5223de98daee53f606623a16d867835599cbd9f5 | YES |
| U06 | a6a65c8b2ea0bd7c39fcfb2beff716ae58b71e9a | YES |
| U07 | 550bf894559744446e87ca52830843eb12157285 | YES |
| U08 / prior full audit | 4ff2e09fe97e846d74c00977e3bb90a01ebfeb77 | YES |
| U13A / HEAD | 53a35014e75bedc4e69691d38f39c4752cd4bd68 | YES |

The graph remains linear. The U08 audit checked all nine earlier ancestors; the delta verified that HEAD has U08 as its direct parent and that `git merge-base 4ff2e09 HEAD` is exactly U08. Tags resolve exactly: `v0.4.2-certification-baseline` → baseline; `v0.5.0-architecture-upgrade` → U09; `v0.6.0-certification-ready` → U07. No tag movement occurred.

User DB SHA-256 before/after audit checks: `0c20c00abed8fae1d154db1c0f04a45ba2512dfdd6f6c3d5e440422e5d459652`. Unchanged hash supports the no-write claim; it is not a schema or data-content audit of that DB.

## Measured canonical execution

Command: `.venv\Scripts\python.exe -B scripts/run_quality_gates.py`, the existing environment form of `python scripts/run_quality_gates.py`. Windows; Python 3.13.2; Node 22.14.0.

| Gate | Verdict | Seconds | Detail |
|---|---|---|---|
| Sensitive artifacts | PASS | 0.055 | Tracked paths only |
| Secret guard | PASS | 0.181 | Source signatures/archive names; no exhaustive secret assurance |
| Syntax/imports | PASS | 0.916 | Temporary compile cache, guarded imports, Node syntax |
| OpenAPI drift/YAML | PASS | 0.140 | Parse/structure/exact export |
| Documentation | PASS | 0.381 | 58 pre-refresh Markdown files; structural Mermaid only |
| Automated regression | PASS | 12.637 | Tests themselves 12.544 s; 240/240 |
| Architecture fitness | PASS | 0.000 rounded | 18 registered verdicts derived from successful test IDs |
| Total elapsed | PASS | 14.309 | Includes runner overhead |

Measured categories: U02 14, U03 34, U04 23, U05 26, U06 31, U07 12, U08 31, U09 25, U13A 18, other regression 26 = 240. Fitness and 18 RAG query cases are not extra tests. No test warnings appeared; the runner explicitly reports formal Mermaid validation unavailable.

Carried-forward U08 supplemental probes are separate from that count. Fresh DB: v2, eleven application tables, seven source guards, zero FK violations. Historical U02 DDL built an independent temporary v1 database; v1→v2 preserved a sentinel row and an exact pre-change backup, then repeated initialization was unchanged. Synthetic relation/RAG rebuild checks passed. One supplemental shell harness initially failed on newline-delimited Git path parsing; direct Git and corrected NUL-delimited checks passed. Windows denied sandbox Python startup for inline probes; authorized retries succeeded. Neither issue was a product or canonical-gate failure.

## Focused U13A verification

Reviewed every changed line in six committed files: app/message_stats.py, app/services.py, app/importers.py, app/seed.py, tests/test_message_stats_validation.py and scripts/run_quality_gates.py. Delta is 271 insertions/14 deletions. No final artifact, schema, dependency, public API, security policy, RAG source or evaluation fixture was committed in U13A.

The shared normalize_message_stats function accepts calendar-valid, exact YYYY-MM-DD endpoints with start <= end; period whitespace is rejected. Incoming/outgoing and three auxiliary counts are non-negative integers, including normalized CSV integer strings; bool/fractional counts are rejected. Zero, equal dates, leap day and a 10^12 count passed. Total remains derived. services.import_message_stats validates all rows before opening its write transaction/person upserts; importer preserves count types until this boundary. The seed writer calls the same validator inside its rollback-protected transaction. No new architectural layer or SQLite CHECK/migration was needed; arbitrary owner-issued SQL is outside this application-service guarantee, and old invalid stored data is not repaired.

Independent inline probes used temporary SQLite, blocked DNS/HTTP transports, real production functions and no test helper/validator mock: 13 invalid cases through direct service plus the actual uploaded-JSON path (**26 rejected**) and three valid cases through each (**6 accepted**). Cases covered malformed/empty/wrong-type/whitespace dates, months 00/13, non-leap date, reversed range, negative incoming/outgoing, fractional and boolean counts. A valid preceding batch row and attempted existing-person rename also remained unpersisted. Thirteen failed uploads retained only existing generic error-job/file bookkeeping. The committed valid CSV fixture imported two rows; FK clean, schema v2 unchanged. No invalid-record domain side effect occurred. The 18 U13A tests independently cover API safe 400, seed writer and existing archive member commits and passed in the 240-test gate.

The recorded gate is one complete retained execution (exit 0, 14.309s); an initial invocation's combined tool output was truncated, so the gate was repeated to retain a complete result. Counts are never added across executions. Only the eight final artifacts were refreshed after PASS.

## Residual findings registry

| ID / priority | Evidence-based finding | Consequence / next acceptance | Origin |
|---|---|---|---|
| P1-01 | Collector remains a 2,691-line class with concrete branches and marker-heavy extraction tests | U10 DOM fixtures/parser substitution; no completeness/live-compatibility claim meanwhile | Existing G10/U10 |
| P1-02 | Operational API/collector/deadline/growth/restore NFRs and full structured observability remain unmeasured | U11 workload/hardware budgets; retries bound attempts/sleep, not elapsed time | Existing G18/U11; deferred part of original U09 |
| P1-03 | Persistence remains direct SQL in services, settings and AI persistence | U12 selected ports if needed; do not claim global DIP/Repository | Existing G09/U12 |
| P2-01 | Maintained ADR-002/004 and some status/debt/evolution prose lag current code | Reconcile current assertions separately; retain historical reports as historical | Documentation drift found in audit |
| P2-02 | All 18 RAG cases have eligible candidate sets exactly equal to relevance labels | Mechanics PASS; no ranking-discrimination evidence. Add distractors/held-out queries before claiming relevance improvement | U08 evaluation limitation, independently quantified |
| P2-03 | Privacy assurance is bounded: trigger-only retention, third-party debug settings, unencrypted backups/profile and incomplete forensic history audit | Keep logging/privacy PARTIAL; broader retention/operational assurance outside this gate | Existing documented U06 residual |
| P2-04 | Reproducibility/governance evidence is Windows-only, transitive dependencies not locked, formal diagrams/live E2E unavailable, remote/branch settings not independently checked | Preserve explicit limits; remote green is user-observed, not auditor-certified | Existing assurance limitations |
| P2-05 | Remaining U13: identity/account/alias validation, automatic demo policy, broader domain validation and archive-wide atomicity | Explicit demo mode/identity rules and batch policy remain deferred; failed-import records/files and prior successful ZIP members are intentionally retained | Residual portion of old P1-04; concrete date/count defect closed by U13A |

These three P1 and five P2 records are deduplicated audit-wide counts. **Old P1-04 concrete period/counter defect: RESOLVED.** Remaining U13 is retained as P2-05: validation now blocks the reproduced corruption; demo seeding is limited to a truly empty store and ZIP partial commits are existing explicit semantics. No separate high-impact integrity failure was established in this delta, so these bounded policy/identity gaps are medium-priority warnings, not proof of complete U13 acceptance. Reassess severity before account switching, unattended import or broader deployment. Security/data-integrity residuals are P2-03/P2-05; no P0 security finding. Planned Graph/CRM/Export/Scheduler/semantic retrieval are scope exclusions, not separately counted defects. No new functional regression was reproduced. No unjustified distributed/vector/auth infrastructure was found.

## CI and release recommendation

**USER-OBSERVED EXTERNAL EVIDENCE:** owner reports green U07 and green U08 `Quality Gates #2` at `4ff2e09`, about 2m7s. Locally verified workflow configuration and canonical behavior support reproducibility; they do not independently verify that remote run. **U13A remote CI: NOT YET RUN.** U08 green is not evidence for U13A. Branch protection is not proven configured, and no settings were changed.

**Recommend `v1.0.0-certification-rc`: YES**, for this exact HEAD and the bounded scope described here, carrying these warnings. Do not present it as full SDD completion, live VK/LLM certification, semantic RAG or a privacy/security guarantee. No tag was created. These uncommitted audit artifacts would not be included in a tag of the current HEAD.

Evidence detail: [baseline matrix](01_BASELINE_TO_FINAL_MATRIX.md), [requirements](02_REQUIREMENT_TRACEABILITY_FINAL.md), [architecture/ADR/NFR](03_ARCHITECTURE_CONSISTENCY_FINAL.md), [security](04_SECURITY_PRIVACY_FINAL.md), [RAG](05_RAG_EVALUATION_AUDIT.md), [release checklist](06_RELEASE_READINESS_CHECKLIST.md), [defense map](07_DEFENSE_EVIDENCE_MAP.md).
