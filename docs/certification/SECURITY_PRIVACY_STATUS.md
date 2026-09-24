# Security / Privacy Status

**U06 IMPLEMENTED in bounded local single-user scope · 2026-09-24. Overall privacy assurance remains PARTIAL.** [Threat model](THREAT_MODEL.md), [classification](DATA_CLASSIFICATION.md), [evidence](U06_PRIVACY_ACCESS_HARDENING_REPORT.md).

| Property | Status | Actual control / limit |
|---|---|---|
| Loopback default | IMPLEMENTED | launcher fixed 127.0.0.1:8765, no environment bind override; alternate operator launch outside guarantee |
| Host/Origin boundary | IMPLEMENTED | localhost/127.0.0.1/::1 only; same scheme/host/effective port Origin; cross-site Fetch Metadata denied; no permissive CORS; TestClient uses loopback base URL |
| LLM endpoint policy | IMPLEMENTED | parsed loopback HTTP(S) only; no userinfo/query/fragment, public/LAN/ambiguous host rejected; no DNS in validation, localhost normalized; proxy environment/redirect disabled |
| Existing unsafe settings | IMPLEMENTED | public base URL redacted to empty, inference fails closed; stored legacy value unchanged until explicit safe update |
| Browser request guard | IMPLEMENTED | HTTP and WebSocket VK suffix/scheme checks, localhost excluded, service workers blocked; exceptions abort/close; no raw URL in errors; not an OS firewall |
| Profile isolation | IMPLEMENTED | fixed dedicated ignored location, link/reparse checks, no arbitrary read route/static exposure; session never touched during build |
| Diagnostic minimization/retention | IMPLEMENTED narrowly | new JSON counters only, no raw DOM/PNG/title/URL; known top-level timestamped files older than 30 days pruned on runtime trigger; .gitkeep/subdirs/links preserved |
| API error safety | IMPLEMENTED tested paths | safe 400/503/startup detail; no 422 input/ctx; unexpected 500 plain text without raw exception propagation; no absolute path in profile/import status |
| Sensitive logging | PARTIAL overall | no prompt/output logger; default access log off; representative HTTPX and API-error sentinel tests pass; arbitrary third-party/operator debug configuration not certified |
| Git disclosure guard | IMPLEMENTED bounded | `scripts/check_privacy.py` reads tracked paths, archive entry names and obvious source secrets; values never printed; no full history/binary secret certification |
| Import/path limits | IMPLEMENTED bounded | filename/containment checks; unique exclusive storage; 100 MiB uploaded/expanded ZIP data, 1000 archive entries; no extraction/execution |
| UI/model output | IMPLEMENTED reviewed paths | text escaping; safe HTTP(S) hrefs without credentials; model output remains validated data and SQL parameters |
| App authentication | NOT IMPLEMENTED | trusted local OS account; no enterprise/multi-user claim |
| Encryption at rest | NOT IMPLEMENTED | OS permissions/encryption/backups are operator responsibilities |
| Full erasure, broader retention, unified CI | PLANNED | U13/U11/U07; diagnostics cleanup is not full erasure |

Gate: 31 new U06 + 140 previous = **171 unittest PASS**, plus **8 additional existing functions PASS**. U04 generated OpenAPI remains synchronized with real 400/403 access checks and settings policy. No live VK/LM/Chromium/network or real database/profile modification. No real secret or tracked runtime artifact was found by the bounded guard. Historical audits remain historical.
