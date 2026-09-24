# Certification checklist

Updated 2026-09-24 after U08. Checked boxes describe verified scope only; historical [baseline report](BASELINE_UPGRADE_REPORT.md) is unchanged.

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
- [ ] Remote U08 GitHub Actions run — not performed; prior U07 success is owner-reported. No push in this build.
- [ ] Main branch protection — NOT CONFIGURED; recommendation documented.
- [ ] Full message snapshot reproducibility, Chat UI/API, semantic retrieval, Graph, Export, Scheduler — not implemented by U04.

[U04 report](U04_API_CONTRACT_REPORT.md) · [API status](API_STATUS.md) · [Inventory](U04_RUNTIME_API_INVENTORY.md). Mermaid review is syntax screening, not a renderer certification. NFR proposals remain proposals, not verified SLAs.

Historical U06 evidence: 171 unittest + 8 additional PASS, no network/user DB/profile changes; diagnostic deletion tests use temporary roots only. [Report](U06_PRIVACY_ACCESS_HARDENING_REPORT.md). Tracked runtime/obvious-secret guard passed; it is not an exhaustive historical/binary secret scan.

**U08 current evidence:** STRUCTURED_RAG—LEXICAL, internal service only; 31 RAG tests, 222 total tests, seven gates and 18 fitness invariants PASS. [Report](U08_LOCAL_RAG_REPORT.md) · [Evaluation](RAG_EVALUATION.md). Prior U07 remote Actions success is owner-reported; this U08 revision is locally verified only and has not been pushed. Branch settings are unchanged.

- [x] U08 corpus/IDs/provenance/derived index, metadata retrieval, citation validation and no-evidence bypass — 31 tests PASS.
- [x] Synthetic 18-case eval with enforced Recall@3/MRR/no-evidence floors; baseline comparison reported without improvement claim.
- [x] STRUCTURED_RAG—LEXICAL maturity, six FITNESS-RAG checks; internal service only, API/UI/schema unchanged.
- [x] Protected U07 ancestry and all three milestone tags retained; user DB SHA-256 unchanged.
