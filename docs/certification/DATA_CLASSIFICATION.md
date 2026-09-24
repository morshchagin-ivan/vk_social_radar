# U06 data classification

2026-09-24. Classification determines handling, not encryption. The trusted local OS account can access these files. No real content or examples are included here.

| Asset/location | Class | Handling/control | Retention/deletion |
|---|---|---|---|
| `data/social_radar.db` and SQLite sidecars | SENSITIVE | local relation/person/dialog/message/AI/settings data; ignored and tracked-artifact guard | no automatic DB deletion or migration in U06 |
| `data/backups/**` | SENSITIVE | SQLite recovery copies; ignored/guarded | operator-managed; no automatic cleanup |
| `data/vk_browser_profile/**` | SECRET/SENSITIVE | authenticated browser session; fixed dedicated location, reparse checks, outside static, ignored/guarded | existing explicit profile-delete UI only; no full-data erasure |
| `data/collector_previews/**` | SENSITIVE | person/profile observations and reports; safe local root, unique files, ignored/guarded | no automatic preview cleanup; explicit broader retention remains U11/U13 |
| `data/imports/**` | SENSITIVE | uploaded source bytes, unique stored basenames; containment and size/type checks; ignored/guarded | no automatic import cleanup |
| `logs/collector/*.html/json/png` | SENSITIVE, including legacy raw captures | new diagnostic writes contain only allowlisted integer counters and kind; no DOM, screenshot, page title or URL | recognized direct timestamped files older than 30 days pruned on collector start or diagnostic write; links/subdirs/.gitkeep excluded |
| AI context/output and browser memory | SENSITIVE | loopback-only inference, no proxy/redirect; structured output treated as data; text escaped | RAM/process lifetime; persisted insights follow DB policy |
| Multipart temporary spool | SENSITIVE/transient | framework-owned temporary upload storage; content read bounded before import; no execution | framework request cleanup; transport/spool resource limits are not a complete DoS guarantee |
| Ordinary application/server logs | NON-SENSITIVE by policy | fixed public error categories, stripped validation input, no default access log or uncaught handler traceback propagation | no new file logger/retention framework |
| Source/docs/tests | PUBLIC only when synthetic | tracked runtime/obvious-secret guard; examples use synthetic IDs/values | Git review; no automatic history rewrite |

No encryption at rest, application authentication, secret vault, multi-user isolation or guaranteed full erasure is implemented. OS ACLs/full-disk encryption/backups remain operator responsibilities. The guard checks tracked working files and archive entry names; it is not proof that all historical commits or binary/archive contents are secret-free. Former external profile override is ignored; no profile migration occurs automatically.
