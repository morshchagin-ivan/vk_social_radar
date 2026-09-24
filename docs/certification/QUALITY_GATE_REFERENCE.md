# Quality Gate Reference

U07 + U08 · 2026-09-24 · Runner and fitness IMPLEMENTED. Prior U07 remote Actions success is owner-reported; this U08 revision is locally verified only and has not been pushed. Branch settings are unchanged.

## Canonical command and environment

From the repository, using the prepared Python environment:

```powershell
python -m pip install -r requirements-dev.txt
python scripts/run_quality_gates.py
```

Installation is setup, not a test gate. On Windows with the existing virtual environment:

```powershell
.\.venv\Scripts\python.exe scripts/run_quality_gates.py
```

`run_tests.bat` is a thin wrapper for that command; it returns the same exit code and does not start the app, install Chromium or contain alternate test logic. Do not run `start.bat` to prepare a quality-only session: that starts the user application.

Evidence environment: Windows, **Python 3.13.2**, **Node.js 22.14.0**. The workflow chooses **windows-2022**, matching Windows path/device-name/reparse semantics instead of asserting an untested platform matrix. It pins these Python/Node versions. Node is already needed by the U06 actual JavaScript helper test; no frontend npm stack is added. `requirements-dev.txt` includes unchanged runtime requirements and **PyYAML 6.0.3** solely for local OpenAPI/workflow YAML parsing. Transitive runtime packages remain governed by the existing requirements; this is not a complete dependency lock or byte-identical build guarantee. Other OS/Python versions are not certified by U07.

## Gates and failure semantics

| Order | Gate | Executable behavior |
|---|---|---|
| 1 | Sensitive artifacts | Git tracked paths only; rejects DB/profile/import/preview/log contents, sidecars, env and cookie/session artifacts; `.gitkeep` permitted |
| 2 | Secret/privacy guard | Reuses U06 tracked source signatures, archive entry inventory and filesystem-link checks; prints file/category, never secret values |
| 3 | Syntax/imports | `compileall` on app/scripts/tests/launcher with a temporary bytecode cache; critical imports with DB/network/server/browser-start guards; Node syntax check |
| 4 | OpenAPI | PyYAML and JSON parse, FastAPI structural model, exact canonical/runtime export comparison; U04 semantic tests also run below |
| 5 | Documentation | Relative file links/reference definitions, containment/existence, accidental developer absolute paths and fence/Mermaid structural sanity |
| 6 | Automated regression | One unittest discovery/execution; measured per-module categories; duplicate, empty, omitted module/plain-function and category drift detection |
| 7 | Architecture fitness | Eighteen mandatory invariants (including six U08 RAG checks) derived from successful test IDs recorded in this same run; no repeated test execution |

Exit **0** means every mandatory gate passed; any failure exits **1**, stopping dependent gates. Missing/skipped/expected-failing/unexpected-successful tests cannot satisfy the mandatory suite or a fitness invariant. Interruptions also terminate unsuccessfully. No `continue-on-error`, optional regression suite or historical hardcoded test total is used. Summary counts come from discovery, execution and result callbacks; durations use a monotonic performance clock.

The initial full local U07 run measured **191 tests PASS**, **7 gates PASS**, **12 fitness invariants PASS**, **8.565 seconds** overall (6.990 seconds for tests). This is an observation, not an SLA. Historical U06 had 171 discovered tests plus 8 separately called functions. U07 converts those eight to `OrganizationSourceTests` without dropping assertions and adds 12 governance tests: that U07 discovery included all 191; current U08 adds 31 RAG tests for 222. Future totals change automatically when tests change.

## Architecture fitness registration

Exact evidence test IDs live in the `FITNESS` registry in [runner](../../scripts/run_quality_gates.py). The following is a readable mapping; all rows are **AUTOMATED** via the same workflow command.

| Invariant | Evidence module(s) | Enforced property |
|---|---|---|
| FITNESS-DB-001 | [migrations](../../tests/test_migrations.py), [snapshots](../../tests/test_snapshots.py) | Current schema v2, future guard and repeated initialization idempotency |
| FITNESS-SNAPSHOT-001 | [snapshots](../../tests/test_snapshots.py) | Frozen historical person projection and SQL source mutation refusal |
| FITNESS-SNAPSHOT-002 | [snapshots](../../tests/test_snapshots.py) | INCOMPLETE/FAILED/CREATING cannot replace current COMPLETE source |
| FITNESS-AI-001 | [provider](../../tests/test_ai_provider.py) | Use case imports the port; structural fake substitutes without vendor HTTP |
| FITNESS-AI-002 | [governance](../../tests/test_quality_gates.py), [provider](../../tests/test_ai_provider.py) | Adapter transport mapping, import boundaries and no current person/business-field coupling |
| FITNESS-RES-001 | [resilience](../../tests/test_llm_resilience.py) | Composition retains resilience wrapper around concrete adapter; import boundaries remain intact |
| FITNESS-RES-002 | [resilience](../../tests/test_llm_resilience.py) | Injected fake time/sleep/random produce exact bounded retry delays; real sleep rejected |
| FITNESS-API-001 | [contract](../../tests/test_api_contract.py) | Generated contract, methods/paths/parameters/IDs/UI calls/security truth and mutation rejection |
| FITNESS-SEC-001 | [privacy](../../tests/test_privacy.py) | Fixed default loopback launcher |
| FITNESS-SEC-002 | [privacy](../../tests/test_privacy.py) | Remote/LAN/deceptive URLs rejected offline and at settings/provider boundaries |
| FITNESS-SEC-003 | [privacy](../../tests/test_privacy.py) | Sensitive runtime paths ignored and untracked |
| FITNESS-UI-001 | [privacy](../../tests/test_privacy.py) | Actual escaping/safeHref helper behavior plus reviewed rendering paths |

These reuse behavior/import tests instead of replacing them with marker-only assertions. The adapter business-field check and legacy collector source checks are focused static checks, not proofs of arbitrary future semantics.

## Coverage categories and isolation

| Category | Automation status | Scope |
|---|---|---|
| Unit/regression | AUTOMATED | 26 existing tests, including eight converted organization-source classifiers/source checks |
| Migration/data, snapshots | AUTOMATED | 14 + 34 tests on temporary SQLite/storage/backup roots |
| AI provider, resilience | AUTOMATED | 26 + 25 tests; structural fakes, MockTransport, fake clock/sleep/random, synchronized concurrency |
| API contract/integration/smoke | AUTOMATED | 23 tests including in-process health/shell/settings/API integration; no real HTTP server or lifespan |
| Security/privacy | AUTOMATED | 31 tests; synthetic secrets/data, temp retention/profile/import roots, mocked browser routes, actual Node helpers |
| Quality governance | AUTOMATED | 12 helper/fitness tests including CI-001–008; only tiny synthetic suites, never recursive full-suite execution |
| Live VK/login/Chromium/LM Studio and visual UI walkthrough | MANUAL, NOT RUN | Separate authorized environment/session required; excluded from the mandatory gate |
| Broader Chat/Graph/Export/Scheduler cases in Markdown 01–07 | DOCUMENTED_ONLY | Specifications are not executable tests or completed acceptance evidence |

All existing temp-DB and mocked-transport fixtures remain in place. HTTP/network guards in AI/API/privacy/snapshot fixtures remain active. Import smoke prohibits DB connect, DNS/connection, server run and Playwright start. The runner forbids actual `time.sleep` and positive `asyncio.sleep`; zero-delay async yields are allowed for AnyIO scheduling. Concurrency tests use event synchronization with safety timeouts, not artificial waits. No user DB, login session, browser executable or live inference is needed. Setup actions/pip require ordinary dependency download access; **the tests themselves use no external network**. No test data/artifact upload step exists.

## Documentation limits

[check_docs.py](../../scripts/check_docs.py) scans certification/ADR documents, root README/API guide and test Markdown specifications. Relative `file.py:line` evidence links resolve to the file; historic line-number meaning is not re-certified. Four exact historical audit locations may retain their recorded workstation path; the maintained certification README uses a portable repository name. External URLs and local heading anchors are not fetched/semantically validated. General Markdown rendering is outside this small checker.

**Mermaid formal validation: NOT AVAILABLE.** No existing Mermaid CLI/parser was available; no Node/browser stack was installed. Fences, supported diagram declarations and flowchart subgraph balance are checked. This is structural sanity, not formal parse/render certification.

## Workflow and branch protection

[quality-gates.yml](../../.github/workflows/quality-gates.yml) runs on `pull_request` and pushes to `main` or `certification/architecture-upgrade`. Steps: checkout → Python → Node → runtime/dev dependency install → canonical runner. The built-in checkout token has `contents: read` and persisted credentials disabled. No PAT/VK/LLM/cloud/browser secret is needed. A configured workflow is not evidence of a successful remote run: Prior U07 remote Actions success is owner-reported; this U08 revision is locally verified only and has not been pushed. Branch settings are unchanged.

Recommendation only: protect `main`, require pull requests and the **Quality Gates** job status after the first observed workflow run. **Branch protection is NOT CONFIGURED**; no GitHub API/settings calls were made.

## Maintenance

Add tests as `unittest.TestCase` methods in `tests/test_*.py`; register a new module in `CATEGORIES`. Put the invariant's exact test IDs in `FITNESS` when adding architecture evidence. Add gate actions to the canonical runner and helper failure-path tests; do not add separate BAT/workflow logic. Failures should give safe file/category context. Never add real runtime fixtures/secrets or turn off mandatory checks to obtain green status.

For a focused diagnostic run (not the complete quality gate):

```powershell
python -m unittest discover -s tests -p test_quality_gates.py -v
python -m unittest discover -s tests -p test_api_contract.py -v
```

Regenerate an intentionally changed contract with `python scripts/export_openapi.py`, review its diff, then run the canonical command. The gate never regenerates drift away automatically.

[U07 report](U07_QUALITY_GATES_CI_REPORT.md) · [Traceability](TRACEABILITY_MATRIX.md) · [Checklist](CERTIFICATION_CHECKLIST.md).

## U08 additions

Current run: **222 tests, seven gates, 18 fitness invariants PASS**. Local RAG category: 31 tests. Critical import smoke includes corpus/retrieval/service; tracked privacy scanning includes JSONL. [U08 report](U08_LOCAL_RAG_REPORT.md) and [evaluation](RAG_EVALUATION.md) contain measured results and limitations.

| Invariant | Automated evidence module | Property |
|---|---|---|
| FITNESS-RAG-001 | test_rag | ports, no concrete transport/retriever dependency |
| FITNESS-RAG-002 | test_rag | derived rebuild/removal |
| FITNESS-RAG-003 | test_rag | no-evidence bypass |
| FITNESS-RAG-004 | test_rag | context-only citations and output validation |
| FITNESS-RAG-005 | test_rag | Recall@3 ≥ 0.90, MRR ≥ 0.90, no-evidence = 1.0 |
| FITNESS-RAG-006 | test_rag | synthetic labelled fixture |

These verdicts reuse executed test outcomes and do not add to the test total. No workflow branch or alternate CI command was added.
