# Release-candidate readiness checklist

Evidence scope: full certification audit at U08 (4ff2e09fe97e846d74c00977e3bb90a01ebfeb77), followed by focused post-U13A delta verification at 53a35014e75bedc4e69691d38f39c4752cd4bd68. Unchanged architecture findings and independent U08 probes are carried forward; the full canonical suite was rerun. This is not a full-from-zero re-audit.

**VERDICT: CERTIFICATION READY WITH WARNINGS**

Branch `certification/architecture-upgrade`; audited HEAD `53a35014e75bedc4e69691d38f39c4752cd4bd68`. The checked scope is the implemented local prototype plus bounded U02/U03/U04/U05/U06/U07/U08/U09/U13A increments. Full target SDD completion is not certified.

## Release evidence

| Check | Result | Evidence / qualification |
|---|---|---|
| Delta canonical gate rerun before refresh | PASS, exit 0 | python scripts/run_quality_gates.py via prepared .venv and -B |
| Authoritative automated count | 240 discovered / 240 executed / 240 passed | Zero failures/errors/skips/omitted tests |
| Architecture fitness count | 18/18 PASS | Same-run successful IDs, not separately counted tests |
| Mandatory gates | 7/7 PASS | Sensitive artifacts, secret guard, syntax/imports, OpenAPI, docs, regression, fitness |
| Elapsed time | 14.309 seconds | Tests 12.544 seconds; no SLA |
| Expected state before delta audit | PASS | Exactly eight allowed untracked final artifacts; none staged; no other change |
| Correct branch and U13A HEAD | PASS | Exact SHA above; unchanged by audit |
| Protected ancestry | PASS | U08 direct parent/merge-base; prior milestone ancestry carried forward |
| Protected tags | PASS | v0.4.2 baseline, v0.5 U09, v0.6 U07 match expected commits |
| User DB untouched | PASS | Hash unchanged; no DB connection/migration against real data |
| Network/live VK/LLM/Chromium | NOT USED | Mandatory and supplemental evidence isolated/fake/temp |
| Fresh/v1→current clean room | PASS (U08 probes + rerun regression) | Eleven tables, v2, seven guards, FK clean; old row/pre-change backup preserved |
| Empty/same-day/backdated/frozen history | PASS | Canonical behavior tests rerun; independent U08 probe carried forward |
| Runtime API/OpenAPI | PASS | 30 app / 29 public operations; root exact runtime 3.1.0; no fake auth/RAG route |
| Provider/resilience | PASS bounded scope | Ports/fakes, normalized errors, local validation, shared retry/breaker |
| Local privacy | PASS bounded scope / PARTIAL assurance | No auth/encryption/full logging/erasure claim |
| RAG pipeline | PASS | Real persisted source chain, stable IDs, derived RAM index, citation checks/no-evidence bypass |
| RAG evaluation | PASS WITH WARNING | 18 cases, 13/5 split, scores 1.0; candidate sets contain no irrelevant distractors |
| CI configuration | PASS locally | Same runner, Windows/Python/Node pins, triggers/failure policy, no app secrets |
| U08 remote CI | USER-OBSERVED EXTERNAL EVIDENCE | U07 green; U08 Quality Gates #2 at 4ff2e09, ~2m7s; no independent verification |
| U13A remote CI | NOT YET RUN | Prior U08 green is not evidence for this HEAD |
| Branch protection | NOT INDEPENDENTLY VERIFIED | Existing recommendation is not proof of configured settings |
| Documentation | PARTIAL consistency | Current core diagrams/contract coherent; ADR-002/004 and other stale prose listed in P2-01 |
| Formal Mermaid rendering | NOT AVAILABLE | Structural checks only |
| Live E2E / full target acceptance | NOT RUN / NOT COMPLETE | Not silently promoted by unit tests or Markdown |
| New functional regressions | NONE REPRODUCED | Scope-limited evidence, not exhaustive absence proof |
| Outstanding grouped findings | P0=0, P1=3, P2=5 | Registry below; roadmap exclusions not counted again |
| U13A concrete integrity defect | RESOLVED | 18/18 tests; independent 26 invalid rejections and 6 valid cases + CSV; no invalid-record domain side effect |
| U13A commit hygiene | PASS | Six intended files; no final artifact/schema/dependency/API/RAG change |
| Recommend v1.0.0-certification-rc | YES, bounded scope with warnings | Recommendation only; tag was not created |

## Required carried warnings

- **P1-01:** concrete collector/extraction and incomplete DOM test coverage; U10.
- **P1-02:** unmeasured operational NFRs/full deadline/restore/growth/observability; U11 and deferred U09 deadline.
- **P1-03:** raw SQL persistence and GLOBAL_DIP_PARTIAL; U12.
- **Old P1-04 concrete defect: RESOLVED.** Invalid dates and negative counts rejected through direct service and upload; no invalid domain rows or associated person changes.
- **P2-05:** remaining U13 identity/account/alias checks, demo policy and broader domain/archive atomicity. Severity reassessment and rationale in the final registry.
- **P2-01:** stale maintained ADR/current prose; historical reports themselves are allowed to stay historical.
- **P2-02:** small RAG fixture cannot discriminate ranking quality; no BM25 improvement claim.
- **P2-03:** overall privacy/logging/retention/history assurance remains partial.
- **P2-04:** Windows-only evidence, nonlocked transitives, no formal renderer/live E2E and qualified remote/governance evidence.

See [finding registry](00_FINAL_CERTIFICATION_REPORT.md), [baseline dispositions](01_BASELINE_TO_FINAL_MATRIX.md), [NFR classification](03_ARCHITECTURE_CONSISTENCY_FINAL.md). No P0 correctness/data-loss/security blocker was found. Missing full-target features are excluded from the candidate's claims; if those features become mandatory certification scope, this verdict must be reconsidered.

## Read-only audit compliance

- [x] No source, test, ordinary documentation, workflow or dependency modification during delta audit.
- [x] No Git commit/push/fetch/merge/amend/rebase/tag/config/branch change.
- [x] No user DB/profile/previews/imports/log cleanup or content access.
- [x] Only synthetic temporary databases and mocked/blocked network transports used.
- [x] Only the eight existing audit Markdown files refreshed under docs/certification/final/ after canonical PASS.
- [x] Audit files left uncommitted; final worktree dirtiness is intentional and limited to those untracked paths.
- [x] Audit artifact links/fences checked; production gate result remains the pre-refresh canonical measurement.

The eight files are 00_FINAL_CERTIFICATION_REPORT.md, 01_BASELINE_TO_FINAL_MATRIX.md, 02_REQUIREMENT_TRACEABILITY_FINAL.md, 03_ARCHITECTURE_CONSISTENCY_FINAL.md, 04_SECURITY_PRIVACY_FINAL.md, 05_RAG_EVALUATION_AUDIT.md, 06_RELEASE_READINESS_CHECKLIST.md and 07_DEFENSE_EVIDENCE_MAP.md.

A tag of the existing HEAD would not contain these uncommitted artifacts. Their preservation/publication and any future warning remediation require a separate user action; this audit performs none of them. RC recommendation is not a claim that branch protection, live operation or the full course rubric has been verified.

Next actions, not performed by this audit: commit the refreshed final package; push certification/architecture-upgrade; wait for green GitHub Actions on the new release commit; fast-forward main if eligible; create the RC tag. Recheck the exact release SHA/gate/CI evidence before those release actions.
