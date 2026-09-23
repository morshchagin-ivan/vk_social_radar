# Security / Privacy Status

Baseline 1.0 · 2026-09-23. Overall **PARTIAL**. This page reports bounded code/audit evidence, not security certification or a claim that Git is free of personal data.

## Implemented / observed

| Property | Evidence | Scope |
|---|---|---|
| Loopback server default | [run_server.py](../../run_server.py), 127.0.0.1:8765 | normal launcher only |
| Local SQLite/files | [db.py](../../app/db.py), imports/previews/diagnostics paths | locality is not encryption or retention |
| Separate Chromium profile | [collector.start](../../app/collector.py) | profile contains session data; not safe for publishing |
| No hardcoded secrets found in reviewed app code | [audit security review](00_REPOSITORY_AS_IS.md) | bounded code review, not full history/secret scan |
| No mandatory cloud LLM discovered | [lmstudio.py](../../app/lmstudio.py), local default/optional insight | arbitrary configured endpoint remains possible |
| Public-source interpretation constraint | collector._normalize_public_org_profile | membership_is_employment_proof=False; not a global privacy proof |

## Partial / risk

- Arbitrary LLM endpoint may receive name/metrics/events; local-only inference is not enforced.
- `_save_diagnostics` stores raw HTML, screenshots and page URL; selective trace sanitization does not cover all outputs.
- Browser request whitelist has a fail-open exception branch calling continue_.
- API currently has no bearer authentication despite target YAML; local bind alone is not a complete request-access policy.
- Git tracked files/history remain **UNVERIFIABLE**: no Git metadata in provided copy. `.gitignore` cannot prove a file was never tracked. No claim is made that cookies/private data are absent from Git.
- Audit identified real runtime artifacts by counts, without displaying their contents. Tests/demos must use synthetic data; private messages/tokens/cookies must not be printed.

## Planned — U06

Enforce endpoint policy, minimize/redact diagnostics, choose retention under U11, fail closed in browser request guard, define local API access policy, cover sidecars/profile overrides in packaging rules, and inspect actual Git index/history/package. Privacy tests belong to U07 and provider configuration to U05. No guard/ignore/security implementation changed in this baseline.

Evidence: [ADR-001](../adr/ADR-001-local-first-architecture.md), [NFR baseline](NFR_BASELINE.md), [technical debt](TECHNICAL_DEBT_REGISTER.md), [backlog](05_UPGRADE_BACKLOG.md).
