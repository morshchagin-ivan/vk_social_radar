# U06 threat model and pre-build control inventory

Captured at U04 `5223de98daee53f606623a16d867835599cbd9f5`, before controls were edited. Single-user local desktop: trusted OS account, loopback web UI, no application authentication, persistent authenticated Chromium profile, SQLite and local LLM. This is not zero-trust or multi-user isolation.

| Asset | Threat | Before U06 | Intended control | Residual risk | Backlog |
|---|---|---|---|---|---|
| Local API/SQLite | Remote access, DNS rebinding, cross-origin browser requests | launcher binds 127.0.0.1; no Host/Origin check | loopback launcher, strict local Host and same-origin checks, no permissive CORS | local OS processes remain trusted; alternate launch configuration is operator-controlled | U06 |
| AI context | Arbitrary configured endpoint, proxy/redirect exfiltration | local default but any URL accepted | offline URL policy at settings and provider; loopback only, no userinfo/query/fragment, no proxy environment or redirects | local inference server/OS compromise; no encryption at rest | U06 |
| Diagnostics | Raw HTML, screenshot, URL/title/report disclosure | `_save_diagnostics` captures all; no retention | counter-only diagnostic JSON; 30-day top-level recognized-file retention, no symlink traversal | historical raw files remain until runtime retention; local backups outside scope | U06/U11 |
| Browser profile | Session exposure, unsafe override/delete/serve | dedicated ignored directory; arbitrary environment override | fixed dedicated root, containment/reparse checks, no arbitrary file route | trusted local user can read session; OS permissions/encryption remain operator concern | U06 |
| Imports | Traversal, collisions, symlink escape, malformed/expanded ZIP | basename sanitization, overwrite; size checked after read | strict filename/containment, unique storage, bounded bytes and archive expansion, generic failure category | archive-wide atomicity and full erasure remain separate | U06/U13 |
| API/logs | Raw errors reveal SQL, paths, payloads or credential URLs | several str(exc) responses; validation echoes input; access logs include query | stable public errors, safe validation envelope, no default access log, sanitized collector error state | debugging/third-party logging and local-process access remain broader risks | U06/U11 |
| Repository | Runtime files/sidecars/secrets committed | ignored directories; sidecars/env incomplete | tracked-name disclosure guard and obvious-source-secret scan, strengthened ignores | no complete historical/semantic secret certification | U06/U07 |
| UI/model output | HTML injection or javascript links | text mostly escaped; href scheme unchecked | safe link scheme handling plus focused rendering checks; model output remains data | no rich HTML rendering; no model/tool execution introduced | U06 |

Final bounded controls passed the offline U06 gate; the pre-build inventory above remains historical. No user database, Chromium profile or existing diagnostics are modified during this build.


## Final control status

| Asset | Threat | Control | Residual risk | Status | Backlog |
|---|---|---|---|---|---|
| API | remote/default bind and hostile browser origin | fixed 127.0.0.1 launcher; local Host, same Origin and cross-site Fetch Metadata denial; no CORS wildcard | alternative launcher or malicious local process is outside trusted-OS model | IMPLEMENTED | U06 complete; broader operations U11 |
| AI context | remote/LAN/proxy/redirect transfer | offline parsed loopback-only policy at save/composition/adapter; localhost normalized, credentials/query denied; trust_env/follow_redirects false | local server/OS compromise; no remote opt-in | IMPLEMENTED | U06 complete |
| Diagnostic files | excess raw data and indefinite old captures | counter-only new JSON, 30-day direct-file cleanup; link/reparse refusal | legacy files wait for trigger; no background timer, no preview/import cleanup | IMPLEMENTED in stated scope | U11 broader budgets |
| Profile/session | serving/export/unsafe path | fixed ignored dedicated directory, safe-directory check before start/delete; static separation | local user can read session; no encryption | IMPLEMENTED boundary | U06 complete; full erasure U13 |
| Collector context | page-origin local/external requests and guard bypass | HTTP/WebSocket VK suffix policy, no localhost, service workers blocked, errors abort/close | not a browser-wide firewall; live compatibility untested | IMPLEMENTED request boundary | U11 broader operations |
| API/log errors | payload/credential/SQL/path leakage | stable mapped errors, safe 422, generic 500 middleware, origin-only status URL, path labels, no access log | third-party debug logging/operator reconfiguration not comprehensively controlled | PARTIAL overall logging; tested paths IMPLEMENTED | U11 |
| Imports | traversal, overwrite, expansion | strict filename, safe root, UUID exclusive creation, 100 MiB bytes/expanded ZIP and 1000 entries; parse without extraction | multipart spooling/CPU DoS and archive-wide atomicity remain | IMPLEMENTED bounded checks | U13/U11 |
| Git | accidental runtime or obvious secret commit | ignore sidecars/env, tracked guard including archive names and source signatures; file/category output | full history and arbitrary encoded/binary secrets not certified | IMPLEMENTED bounded guard | U07 CI integration |
| UI | XSS via names/insights/links | escaping retained/extended; href accepts HTTP(S) without userinfo; rel=noopener noreferrer | externally followed HTTP(S) links still require user judgment | IMPLEMENTED reviewed paths | U06 complete |

[Classification](DATA_CLASSIFICATION.md) · [U06 report](U06_PRIVACY_ACCESS_HARDENING_REPORT.md). Auth and encryption remain NOT IMPLEMENTED; no zero-trust claim.
