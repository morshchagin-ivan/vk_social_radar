# VK Social Radar runtime API guide

**IMPLEMENTED U04 — 2026-09-24.** Canonical contract: [11_OPENAPI.yaml](11_OPENAPI.yaml). Source of truth for authoring: FastAPI route metadata in [main.py](app/main.py), [response models](app/api_models.py) and [request/error metadata](app/api_contract.py). The root file is the generated published artifact, not a second hand-maintained definition. [Inventory](docs/certification/U04_RUNTIME_API_INVENTORY.md) · [Evidence](docs/certification/U04_API_CONTRACT_REPORT.md).

## Base URL and trust boundary

Default server: `http://127.0.0.1:8765`. Public API prefix: `/api`. JSON is used except multipart file upload, HTML `/`, and unhandled plain-text errors. Health reports the existing application version `0.4.2`; the contract format is OpenAPI `3.1.0`, independent of SQLite schema version 2.

No Bearer token, API authentication or multi-user authorization is implemented. The default loopback bind expresses local single-user deployment, not an enforced access-control or privacy guarantee. Collector `check-auth` checks VK browser login, not the HTTP caller. U06 remains the access/privacy hardening work. Never infer readiness from health or full inference availability from model discovery.

Preserve `/api` for existing clients. No `/api/v1` aliases were added. A future incompatible change needs a reviewed version/compatibility policy and explicit client migration; changing a historical target file is not a versioning requirement. Stable snake_case operationIds are explicit metadata; Python handlers remain named as before.

## Implemented endpoint groups

All application successes below are **200**, including job start, pending and busy results. No 201/202/204/409 semantics are implied.

| Group | Operations | Success and input semantics |
|---|---|---|
| Health | GET `/api/health` | `{status: "ok", version: "0.4.2"}`; liveness only |
| Dashboard | GET `/api/dashboard` | friends/followers counts, message_total, changes, top_people, recent_imports |
| People | GET `/api/people`; GET `/api/people/{person_id}` | list with current flags/message counts; detail with person/message_stats/events/insights; integer internal DB ID, absent person 404 |
| Timeline | GET `/api/changes?limit=100` | frozen new relation events and labelled legacy events; limit clamps to 1..500, it is not a validation bound |
| Message aggregates | GET `/api/messages/leaderboard` | message-period rows with total_messages/person_initiative_pct; not snapshot-scoped |
| Relation import | POST `/api/import/snapshot` | object with relation_type + people; immutable capture result |
| File import | POST `/api/import/file` | multipart file + import_type required; relation_type/snapshot_date optional at framework boundary; business requirements below |
| Settings | GET and PUT `/api/settings` | string-valued mapping; PUT accepts object, stores only three lmstudio keys, stringifies values and ignores other keys |
| Local models | GET `/api/lmstudio/models`; POST `/api/lmstudio/test` | id plus vendor metadata; test returns ok/models_count/models; discovery only |
| Insight | POST `/api/people/{person_id}/insight` | persisted id/model/status/confidence/summary/evidence/cautions; missing person 404; provider/config/output/circuit errors 503 |
| Browser control | POST `/api/collector/start`, `/close`, `/check-auth`; DELETE `/api/collector/profile`; GET `/api/collector/status` | status or ok/deleted; profile deletion is the existing explicit action; runtime diagnostic path fields remain |
| Browser navigation | POST `/api/collector/navigate/{target}` | target home/friends/followers/dialogs; service error 400, no framework enum restriction |
| Collection | POST `/api/collector/collect/{kind}` | kind friends/followers/dialogs; preview only; busy, stopped, invalid kind or no valid items 400 |
| Preview/save | GET `/api/collector/preview`; POST `/api/collector/save-preview` | missing preview 404; relation/dialog and organization result variants; organization save remains unsupported 400 |
| Dialogs | GET `/api/dialogs?limit=500` | latest collected_at batch; clamps limit to 1..2000 |
| Source classification | GET `/api/collector/source/classify?source_url=...` | source_type/source_url/normalized_url/eligible_for_collection; missing query 422, unsupported source classified in 200 |
| Organization preview | POST `/api/collector/organization-source` | object source_url/options; variable diagnostics/profiles; no automatic persistence |
| Organization jobs | POST `/api/collector/organization-source/jobs`; GET `/api/collector/organization-source/jobs/{operation_id}`; GET same path + `/result`; POST same path + `/cancel` | in-memory job state; unknown ID 404; pending result_available=false is 200; busy is COLLECTOR_BUSY in 200 |

There are 29 public operations plus one internal HTML shell (`GET /`) in the 30-operation canonical artifact. Framework docs/OpenAPI delivery and `/static` are infrastructure, not additional business operations. See the inventory for each handler, parameter, response reference and frontend call site.

## Snapshot-v2 example and semantics

Synthetic request: `POST /api/import/snapshot`, `Content-Type: application/json`:

```json
{"relation_type":"friend","captured_at":"2099-01-01","people":[{"vk_id":101,"full_name":"Synthetic Person"}]}
```

Illustrative response (identity generated; no real data):

```json
{"snapshot_id":"00000000-0000-4000-8000-000000000001","snapshot_date":"2099-01-01","captured_at":"2099-01-01","relation_type":"friend","status":"COMPLETE","completeness":"DECLARED_COMPLETE","count":1,"added":1,"removed":0}
```

relation_type is friend/follower; people is a required array, including explicit `[]`. Members need nonblank full_name and positive numeric vk_id (integer or canonical numeric string up to signed 64-bit maximum), or valid screen_name when numeric ID is absent/null. Duplicate identities are rejected. Optional source/source_reference, snapshot_id, captured_at/snapshot_date, completeness and status are documented in the contract. Extra input fields are ignored.

Structured import is a whole-set declaration by default. UNKNOWN/PARTIAL observations remain INCOMPLETE by default. Only DECLARED_COMPLETE can be COMPLETE. A caller may retain FAILED or CREATING evidence, which never becomes current. First complete capture establishes a baseline without an observed-change event; `added` still reports its set size. Same-day captures have distinct identities; explicit UUID replay must match metadata/content. Date-only precision is retained; precise times normalize UTC, naive times use application-local timezone. A backdated capture atomically repairs its edge and its successor's edge.

An explicit complete empty set replaces current membership. Collector friends/followers saves always remain UNKNOWN/INCOMPLETE and do not replace current truth. Historical event fields come from frozen projections; legacy events remain legacy_unknown. Current person fields and message_stats remain mutable convenience/period data. There is **no snapshot read/list endpoint**, full immutable message corpus, or snapshot-reproducible AI promise.

The existing dict-based request boundary is retained. Service validation maps most domain failures to 400; framework malformed/missing/type-level input maps 422. Some malformed non-string UUID inputs can reach an uncaught 500; U04 documents this boundary rather than silently redefining all coercions.

## File import, settings and organization options

Multipart fields: file and import_type required; import_type accepts `relations` or `message_stats` in business validation. Relations additionally require relation_type friend/follower. snapshot_date may be omitted. JSON/CSV/TSV/HTML/HTM/ZIP are supported; supplied bytes above 100 MiB fail after reading. No ZIP expanded-size guard or archive-wide transaction is claimed. HTML extraction is UNKNOWN. Result is snapshot fields, imported count, or imported + processed_files, with job_id and stored_as. Real local paths are part of existing runtime responses, but not examples here.

Synthetic settings update: `PUT /api/settings` with `{"lmstudio_model":"synthetic-model","lmstudio_temperature":0.2}` stores string values. The three accepted keys are lmstudio_base_url, lmstudio_model, lmstudio_temperature. No retry knobs/provider selector, endpoint policy or temperature bounds are enforced at this API boundary. Settings unknown keys are ignored.

Organization source_url is string-coerced and stripped, absent/falsy/blank is 400. Non-object options become `{}`. Collection int-coerces/clamps max_member_index (or max_profiles) default 7000 to 1..20000; max_pages (or max_scrolls) default 800 to 1..2000; max_candidate_profile_enrichment default 30 to 0..200; max_ambiguous_profile_enrichment default 10 to 0..100; timeout_ms default 30000 to 5000..60000. Falsy values select defaults. Invalid conversions fail synchronously or become job failures. These are collector rules, not request-schema min/max validations. Diagnostic contents are intentionally extensible.

## Error contract and LLM resilience

| Status | Actual body | Scope |
|---|---|---|
| 400 | `{"detail":"..."}` | domain import/collector failures, missing source URL, unsupported save |
| 404 | `{"detail":"..."}` | missing person, preview or organization job |
| 422 | `{"detail":[{"loc":["path","person_id"],"msg":"...","type":"..."}]}` | FastAPI request validation; entries may also include input/ctx |
| 500 | plain text `Internal Server Error` | unhandled exception; no uniform JSON envelope |
| 500 | `{"detail":"..."}` | explicitly caught Chromium startup error |
| 503 | `{"detail":"..."}` | models/test provider failure; insight provider, invalid output/configuration or open generation circuit |

Only applicable mapped statuses are listed per operation. Generic unhandled 500 is documented everywhere. There is no invented bearer 401/403 policy or conflict 409 mapping. Frontend continues to read JSON detail when present and otherwise falls back to HTTP status text.

U09 generation retains max 3 attempts, capped retry sleep 1.5s, breaker threshold 3 logical failures and recovery 30s. These are internal defaults, not an HTTP latency guarantee. Discovery is not retried by that wrapper and may happen even when generation is open. No total deadline, fallback, RAG or extra AI routes were added.

## Contract governance and validation

Strategy **A**: deterministic FastAPI export. JSON-form YAML 1.2 permits strict stdlib JSON parsing without a new runtime or test dependency. Existing local PyYAML also parses it. Do not hand-edit the artifact:

```powershell
.\.venv\Scripts\python.exe -B scripts/export_openapi.py
.\.venv\Scripts\python.exe -B scripts/export_openapi.py --check
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p test_api_contract.py -v
```

Export imports the app and calls openapi only, without lifespan, DB, collector execution or provider calls. Standard discovery includes the gate. Exact generated-artifact comparison detects added/removed routes, methods, operationIds, params, bodies, responses, security and component drift. Semantic tests check API/UI coverage and required path params; mutation tests prove deliberate drift fails. Synthetic TestClient fixtures validate success/error bodies with temp storage, fake providers and mocked collector. Tests do not start Uvicorn.

PyYAML parse, local reference resolution, FastAPI OpenAPI structural model and runtime comparison passed. A formal OpenAPI spec validator is not installed; no formal spec-validation, Swagger client generation, full JSON Schema conformance, or live E2E claim is made. The small fixture validator covers the emitted subset only. U07 unified runner/CI remains separate.

## Planned, non-canonical design

The old [feature YAML](specs/001-vk-profile-analysis/11_OPENAPI.yaml) is an archived TARGET proposal and must not be used for runtime clients. It has 18 old `/api/v1` operations; 14 have no normalized runtime method/path equivalent, while health, settings GET/PUT and collector status correspond to existing capabilities at different URLs. Future snapshots resource, RAG/chat/reports, graph, export, scheduler, auth and multi-user capabilities remain planned; no canonical implemented operation advertises them.
