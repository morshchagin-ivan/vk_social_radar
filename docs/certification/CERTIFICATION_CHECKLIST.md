# Certification checklist

Updated 2026-09-24 after U07. Checked boxes describe verified scope only; historical [baseline report](BASELINE_UPGRADE_REPORT.md) is unchanged.

- [x] Git branch/revisions and protected tags verified; U03 ancestor retained.
- [x] Current/target distinction preserved in README, architecture status, C4 and ADRs.
- [x] U02/U03 migration and immutable relation evidence retained on temporary databases.
- [x] One canonical runtime OpenAPI 3.1 artifact at root; old feature proposal clearly archived/non-canonical.
- [x] 30 application operations (29 public + shell), explicit unique operationIds and 21 frontend calls covered.
- [x] Request/response/error and security semantics aligned; `/api` compatibility preserved, no fake Bearer auth.
- [x] Contract governance IMPLEMENTED: standard-discoverable runtime/export/semantic/UI drift tests and mutation rejection.
- [x] 23 U04 tests + existing regressions: 140 unittest PASS; 8 additional functions separately PASS.
- [x] YAML/JSON parsing, component reference checks, FastAPI structural model and generated comparison PASS.
- [x] No real DB writes, network, live browser/provider calls or new dependencies.
- [ ] Formal OpenAPI spec validator/client generation — unavailable/not run, not claimed.
- [ ] Live VK/LM Studio/Chromium E2E — not run.
- [x] U06 bounded privacy/access hardening — 31 tests PASS; authentication/encryption remain explicitly absent.
- [x] U07 unified runner and architecture fitness — 191 discoverable tests, 7 gates and 12 invariant verdicts PASS; eight plain functions converted.
- [x] GitHub Actions workflow CONFIGURED LOCALLY with the same canonical runner.
- [ ] Remote GitHub Actions execution — NOT YET VERIFIED; no push performed.
- [ ] Main branch protection — NOT CONFIGURED; recommendation documented.
- [ ] Full message snapshot reproducibility, RAG, Graph, Export, Scheduler — not implemented by U04.

[U04 report](U04_API_CONTRACT_REPORT.md) · [API status](API_STATUS.md) · [Inventory](U04_RUNTIME_API_INVENTORY.md). Mermaid review is syntax screening, not a renderer certification. NFR proposals remain proposals, not verified SLAs.

Historical U06 evidence: 171 unittest + 8 additional PASS, no network/user DB/profile changes; diagnostic deletion tests use temporary roots only. [Report](U06_PRIVACY_ACCESS_HARDENING_REPORT.md). Tracked runtime/obvious-secret guard passed; it is not an exhaustive historical/binary secret scan.

U07 current local evidence: **191 automated tests PASS**, zero omitted legacy functions. Syntax/imports, tracked privacy/secrets, OpenAPI, documentation and architecture gates PASS. [Report](U07_QUALITY_GATES_CI_REPORT.md), [reference](QUALITY_GATE_REFERENCE.md). Previous build counts above are historical; MANUAL and DOCUMENTED_ONLY scenarios are not counted as tests.
