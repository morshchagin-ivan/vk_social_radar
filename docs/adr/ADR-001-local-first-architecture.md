# ADR-001 — Local-first Architecture

**Status:** ACCEPTED. **Implementation:** IMPLEMENTED for U06 bounded local controls; broader privacy assurance remains PARTIAL. **Updated:** 2026-09-24.
**Decision owners:** project owner and architecture maintainer.
**Related backlog:** [U06 complete, U07 integration, U11 measurement](../certification/05_UPGRADE_BACKLOG.md).

## Context

The local single-user application holds relations, dialogs, message aggregates and an authenticated Chromium session. Loopback defaults alone did not constrain arbitrary LLM URLs, hostile browser requests, raw diagnostics or exception leakage. The OS account is trusted; multi-user/zero-trust IAM is outside scope.

## Decision

Keep the fixed loopback launcher and local storage. Enforce local Host/same-origin browser checks without inventing API authentication. Require parsed HTTP(S) loopback LLM URLs at settings and outbound adapter boundaries; no remote/LAN opt-in or fallback. Disable environment proxies and redirects. VK web collection remains an explicit external activity under its fail-closed host policy.

New diagnostics contain only allowlisted counters; direct recognized diagnostic files older than 30 days expire on collector start/diagnostic write. Protect dedicated storage paths against links/reparse points, bound imports, keep profile outside static, escape UI text and reject executable href schemes. Use safe error categories and a tracked disclosure guard.

## Current implementation / evidence

[privacy.py](../../app/privacy.py), [access.py](../../app/access.py), [collector](../../app/collector.py), [provider](../../app/ai/providers/lmstudio.py), [tracked guard](../../scripts/check_privacy.py). [31 U06 tests](../../tests/test_privacy.py), 171 unittest + 8 additional PASS; no real DB/profile/network used. [Report](../certification/U06_PRIVACY_ACCESS_HARDENING_REPORT.md), [threat model](../certification/THREAT_MODEL.md), [classification](../certification/DATA_CLASSIFICATION.md).

## Alternatives considered

Remote inference opt-in, broad private-LAN allowlisting, bearer token/login infrastructure and unrestricted diagnostics. They add exposure/complexity without a current single-user requirement. A future remote inference feature requires a separate explicit decision and data-transfer disclosure.

## Consequences and security impact

Positive: testable deny-by-default outbound inference, same-origin browser boundary, reduced diagnostic/error disclosure, bounded storage operations. Negative: previously remote or credentialed LLM settings must be explicitly replaced with safe local settings; former external Chromium profile override is ignored. No user data or profile migration is performed by the build.

Residual: local OS/server compromise, unencrypted files, user-managed backups, third-party debug configuration, multipart spooling/CPU limits, broader retention and full erasure. Host/Origin checks do not authenticate a local process. Retention is trigger-based, not continuous or a secure-wipe guarantee. Source guards do not certify every historical/binary secret.

## Evolution

U07 integrates the existing gates into unified runner/CI. U11 measures resource/logging/retention budgets; U13 addresses full lifecycle/import atomicity. Auth or remote inference is a new scope decision, not an implied completion of U06.
