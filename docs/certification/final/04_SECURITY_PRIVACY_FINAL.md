# Final security, privacy and CI audit

Evidence scope: full certification audit at U08 (4ff2e09fe97e846d74c00977e3bb90a01ebfeb77), followed by focused post-U13A delta verification at 53a35014e75bedc4e69691d38f39c4752cd4bd68. Unchanged architecture findings and independent U08 probes are carried forward; the full canonical suite was rerun. This is not a full-from-zero re-audit.

HEAD `53a35014e75bedc4e69691d38f39c4752cd4bd68`. **No P0 security blocker found in the audited scope.** Local-first controls are implemented for a trusted single-user OS account. Overall logging/privacy assurance remains **PARTIAL**. This is not a penetration test, full forensic secret audit, zero-trust certification or endorsement of exposing the server beyond loopback.

Audit-wide finding counts are P0=0/P1=3/P2=5; [registry](00_FINAL_CERTIFICATION_REPORT.md). Security/data-integrity-relevant residuals are **P2-05** (remaining demo/identity/atomicity policy) and **P2-03** (bounded privacy assurance); old P1-04's concrete period/count defect is RESOLVED. They are existing limitations, not newly reproduced exfiltration or data-loss regressions.

## Controls traced to implementation and automated evidence

| Boundary | Current control | Evidence / result | Limit |
|---|---|---|---|
| Listener | run_server.py fixes 127.0.0.1:8765, reload/access log off | NetworkPrivacyTests.test_sec_001_002_launcher_is_fixed_loopback_and_access_logs_off PASS | Operator can invoke another launcher; no network perimeter service |
| Host/Origin/CORS | LocalAccessMiddleware rejects invalid/duplicate/nonlocal hosts, foreign origins and cross-site Fetch Metadata; no permissive CORS | test_sec_003_unexpected_host_rejected_before_handler, test_sec_004_local_hosts_and_same_origin_allowed, test_sec_005_cors_and_cross_origin_rejected PASS | No application authentication; local processes are trusted |
| Inference URL | local_llm_url parses scheme/authority/IP, rejects public/LAN/deceptive hostnames, credentials, query, fragment, ambiguous escapes; localhost maps to numeric loopback | U06 sec_llm_001…009 cases; settings atomicity and provider recheck PASS | Only local LM configured; no remote opt-in |
| DNS/proxy/redirect | URL validation uses ipaddress, not DNS; adapter trust_env=False/follow_redirects=False | test_sec_llm_009_validation_without_dns_network; test_proxy_environment_and_redirects_disabled PASS | Local inference server/OS could itself be compromised |
| Browser request policy | HTTP/WebSocket suffix policy; exceptions abort/close; service workers blocked | test_collector_request_guard_is_fail_closed, test_collector_guard_allowed_hosts_and_safe_error_status PASS | Not a complete browser-wide firewall or live site compatibility proof |
| Profile/session | Fixed dedicated root, no environment override, safe_directory reparse checks; outside static | test_sec_browser_001_002_profile_not_served_or_overridden and temp-root deletion checks PASS | Unencrypted authenticated profile remains sensitive; no real profile inspected/deleted |
| Diagnostics | _save_diagnostics writes only allowlisted counters; no page content/screenshot/title/URL | test_diagnostics_do_not_capture_page_or_sensitive_report PASS | Preview payloads are separate personal-data storage |
| Retention | Eligible direct diagnostic files >30 days removed at collector start/write; links/subdirectories excluded | sec_data_003…005 and reparse/unlink tests PASS | Not continuous cleanup, full erasure or preview/import/backup retention; old files await trigger |
| Upload path | Strict filename/device/path rejection, safe root, UUID exclusive create, basename response | sec_path_001 and unique/contained import tests PASS | Trusted OS can change filesystem; not a hostile-local-user sandbox |
| Input resource budget | Read MAX_IMPORT_BYTES+1, 100 MiB expanded ZIP, 1000 entries, no extraction | test_import_byte_archive_expansion_and_member_paths_bounded; test_upload_read_is_bounded PASS | Multipart spooling/CPU/deep JSON and archive-wide atomicity not fully bounded |
| UI/XSS | Escaped text, safeHref scheme/userinfo handling, noopener/noreferrer | Node-based test_sec_xss_001_actual_helpers_and_rendering_boundaries PASS | No full browser UI proof; external HTTP links can still be explicitly followed |
| Exceptions/access logs | Generic public errors, input-redacted 422, generic 500 middleware; disabled default access log | sec_err_001 and provider/log tests PASS | Third-party debugging/operator configuration not comprehensively controlled |
| Message-stat input | normalize_message_stats before service person/stat writes; same validator in seed | 18 U13A tests and independent direct/upload probes PASS; controlled field/category error, public API retains generic 400 | No retroactive row repair, DB-owner SQL constraint, full identity validation or archive-wide rollback |
| LLM output | Insight/RAG validate local structure before persistence/return | U05 invalid JSON/fields tests; U08 citation/structured cases PASS | Structural validity is not semantic truth |
| No hidden cloud path | Existing provider port binds local LM adapter; RAG imports no external embedding/vector SDK | Requirements, AST import roots, composition and source inspection | Does not certify behavior of the separately installed local model server |

Source: [privacy](../../../app/privacy.py), [access](../../../app/access.py), [collector](../../../app/collector.py), [adapter](../../../app/ai/providers/lmstudio.py), [importers](../../../app/importers.py), [main](../../../app/main.py), [UI](../../../static/app.js), [tests](../../../tests/test_privacy.py). All 31 U06 tests ran in the canonical suite.

## Repository disclosure audit

Read-only `git ls-files` inspection found only these tracked runtime-root placeholders: data/.gitkeep; data/backups/.gitkeep; data/collector_previews/.gitkeep; data/imports/.gitkeep; data/vk_browser_profile/.gitkeep; logs/.gitkeep; logs/collector/.gitkeep. No tracked DB, profile content, previews, imports, logs or .env was found.

The canonical source/secret guard and an independent invocation of check_privacy.check both returned zero findings. It includes .jsonl and archive entry names, rejects filesystem links and prints filename/category only. Independent ignore probes covered DB, WAL, SHM, .env, profile cookies, preview, import and diagnostic paths: **8/8 ignored**. Historical path-name inventory across available local refs found no sensitive-named paths; this was **path inventory only**, not a full history/content scan. No private runtime contents were read or printed.

Limitations: heuristic secret patterns are not comprehensive; encoded/binary values and arbitrary ZIP contents are not exhaustively scanned. A .gitignore file alone is not evidence of safe history, which is why tracked/path checks were repeated. Existing ignored runtime assets may still be present locally; the audit neither enumerated profile contents nor cleaned them. A future release package must exclude local ignored data and respect the archive's documented historical scope.

The delta canonical documentation checker passed 58 pre-refresh files. Four exact original-audit environment lines are deliberate historical absolute-path exceptions; they are not current usable links. The maintained canonical pages checked contain no unintended developer-path findings. Broader target SDD/archived documents are not all validated by that checker; they remain target context, not runtime authority. New final artifacts use portable repository-relative links and are checked separately.

## P1-04 concrete integrity defect: RESOLVED by U13A

Historical U08 audit: a temporary import accepted malformed period strings and negative incoming count. That observation remains the reason for U13A, not current behavior. At 53a35014e75bedc4e69691d38f39c4752cd4bd68, central normalization enforces exact calendar dates/order and non-negative integer counts before person/stat mutation. The importer no longer truncates fractional JSON values or coerces bools to counts. Total is derived, not an independently stored field.

Independent delta probes rejected 13 invalid cases through each of the direct service and real uploaded-JSON paths (26 total), preserving an existing person/stat row and rejecting a preceding valid row in the same batch. Six valid route/case probes and the two-row CSV fixture passed. All 18 U13A tests passed, including the existing safe API 400, seed validation and archive semantics. Service errors identify only field/category; public errors remain generic. Failed upload files and 13 generic error jobs are existing attempt bookkeeping, not invalid domain records. No real DB was opened.

Remaining U13 is **P2-05**, not erased: identity/account/alias validation, explicit demo mode, broader input/domain validation and archive-wide atomicity. Demo seeding still runs on a truly empty store; a valid earlier ZIP member still commits before a later invalid member fails. These are disclosed bounded policies with no new high-impact failure established by this delta; severity should be reassessed before broader use. No authentication, logging, retention or privacy assurance was upgraded by this fix. Application-level validation does not constrain arbitrary owner SQL or repair legacy invalid rows.

## RAG privacy/injection boundary

Corpus excludes browser/session files, diagnostics, raw source_reference/profile/avatar URLs, message_stats, collector_dialogs and ai_insights. COMPLETE headers/frozen memberships/compatible persisted events are the only sources. Names and person keys are still personal data; safe provenance is not anonymization. Index lives in process memory and is not persisted, so no generated-index ignore entry is needed.

No RAG query/evidence/answer logging, persistence, subprocess execution or URL fetching was found. Question/evidence are JSON data with explicit delimiters, a system instruction and restricted structured citation IDs. FakeLLM malicious-evidence tests prove data placement and no execution; they cannot prove a live model ignores injected instructions. Citation membership does not validate entailment or natural-language inline references. Existing documentation correctly admits residual prompt-injection and model-output risks.

## CI configuration and external evidence

Inspected [.github/workflows/quality-gates.yml](../../../.github/workflows/quality-gates.yml): valid YAML structure, pull_request plus push on main and certification/architecture-upgrade; windows-2022; Python 3.13.2; Node 22.14.0; 15-minute job timeout; setup via requirements-dev.txt then exactly `python scripts/run_quality_gates.py`. Permissions are contents:read; checkout persist-credentials is false. No application secrets, real data fixture, artifact upload, browser install, live LLM, continue-on-error or ignored mandatory failure branch is present. Framework checkout credentials are platform-provided, not an app secret in source.

Counts come from unittest discovery/results, not hardcoded success totals. Missing/duplicate/omitted module tests, skipped/failed evidence and category/fitness drift fail. The helper tests include deliberate failing/skipped tiny synthetic suites to verify failure semantics; these are not skipped mandatory repository tests. run_tests.bat delegates and returns the runner exit code. Mandatory tests need no network; CI dependency setup itself normally downloads packages.

**USER-OBSERVED EXTERNAL EVIDENCE:** user reports green U07 and green U08 `Quality Gates #2`, commit `4ff2e09`, about 2m7s. No independent remote API/log verification was attempted because the audit prohibits network. **U13A remote CI: NOT YET RUN.** U08 green cannot establish U13A success. Local origin tracking at U08 does not establish CI status. Branch protection is not independently proven; current documentation recommends it, and no settings were changed. Actions use version tags and transitive dependencies are not fully locked; this supports P2-04 reproducibility limits, not a detected supply-chain incident.

## Safety outcome

No real DB connection/migration, browser/session access, live inference, network, commit/push/tag or cleanup. User DB hash remained `0c20c00abed8fae1d154db1c0f04a45ba2512dfdd6f6c3d5e440422e5d459652`. Auth/encryption/zero-trust are not claimed. Overall verdict and prioritized limits: [final report](00_FINAL_CERTIFICATION_REPORT.md).
