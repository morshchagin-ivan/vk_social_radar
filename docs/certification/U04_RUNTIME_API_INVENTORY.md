# U04 runtime API inventory

Captured BEFORE contract edits at U03 `1c619259691f5ddca232f1d67142bdf14c0be47b`. Static code and `app.openapi()` only; no server, lifespan, collector or DB opened.

All `/api` operations are PUBLIC (local callers); UI-used subset below. `/` is INTERNAL web-shell delivery. FastAPI framework `/openapi.json`, `/docs`, `/docs/oauth2-redirect`, `/redoc` and mounted `/static` are infrastructure, excluded from application operation counts. All application success statuses are 200. No application auth, security dependencies or custom exception handlers.

## Pre-build operations

| Method/path | Route name | Pre-U04 generated operationId → explicit U04 ID | Parameters/body | Success shape / implementation | Known errors | Class / UI |
|---|---|---|---|---|---|---|
| `GET /` | `index` | `index__get` → `index` | `none` | `FileResponse`, [main.py:34](../../app/main.py:34); see response audit below | none mapped | INTERNAL / shell |
| `GET /api/health` | `health` | `health_api_health_get` → `health` | `none` | `dict[str, str]`, [main.py:39](../../app/main.py:39); see response audit below | none mapped | PUBLIC / API-only |
| `GET /api/dashboard` | `get_dashboard` | `get_dashboard_api_dashboard_get` → `get_dashboard` | `none` | `dict[str, Any]`, [main.py:44](../../app/main.py:44); see response audit below | none mapped | PUBLIC / UI |
| `GET /api/people` | `get_people` | `get_people_api_people_get` → `get_people` | `none` | `list[dict[str, Any]]`, [main.py:49](../../app/main.py:49); see response audit below | none mapped | PUBLIC / UI |
| `GET /api/people/{person_id}` | `get_person` | `get_person_api_people__person_id__get` → `get_person` | `person_id: int` | `dict[str, Any]`, [main.py:54](../../app/main.py:54); see response audit below | 404, 422 | PUBLIC / UI |
| `GET /api/changes` | `get_changes` | `get_changes_api_changes_get` → `get_changes` | `limit: int=100` | `list[dict[str, Any]]`, [main.py:62](../../app/main.py:62); see response audit below | 422 | PUBLIC / UI |
| `GET /api/messages/leaderboard` | `get_message_leaderboard` | `get_message_leaderboard_api_messages_leaderboard_get` → `get_message_leaderboard` | `none` | `list[dict[str, Any]]`, [main.py:67](../../app/main.py:67); see response audit below | none mapped | PUBLIC / UI |
| `POST /api/import/snapshot` | `post_snapshot` | `post_snapshot_api_import_snapshot_post` → `post_snapshot` | `payload: dict[str, Any]` | `dict[str, Any]`, [main.py:72](../../app/main.py:72); see response audit below | 400, 422 | PUBLIC / UI |
| `POST /api/import/file` | `post_import_file` | `post_import_file_api_import_file_post` → `post_import_file` | `file: UploadFile=File(...), import_type: str=Form(...), relation_type: str &#124; None=Form(None), snapshot_date: str &#124; None=Form(None)` | `dict[str, Any]`, [main.py:80](../../app/main.py:80); see response audit below | 400, 422 | PUBLIC / UI |
| `GET /api/settings` | `settings_get` | `settings_get_api_settings_get` → `settings_get` | `none` | `dict[str, str]`, [main.py:102](../../app/main.py:102); see response audit below | none mapped | PUBLIC / UI |
| `PUT /api/settings` | `settings_put` | `settings_put_api_settings_put` → `settings_put` | `payload: dict[str, Any]` | `dict[str, str]`, [main.py:107](../../app/main.py:107); see response audit below | 422 | PUBLIC / UI |
| `GET /api/lmstudio/models` | `lm_models` | `lm_models_api_lmstudio_models_get` → `lm_models` | `none` | `list[dict[str, Any]]`, [main.py:112](../../app/main.py:112); see response audit below | 503 | PUBLIC / UI |
| `POST /api/lmstudio/test` | `lm_test` | `lm_test_api_lmstudio_test_post` → `lm_test` | `none` | `dict[str, Any]`, [main.py:122](../../app/main.py:122); see response audit below | 503 | PUBLIC / API-only |
| `POST /api/people/{person_id}/insight` | `create_insight` | `create_insight_api_people__person_id__insight_post` → `create_insight` | `person_id: int` | `dict[str, Any]`, [main.py:133](../../app/main.py:133); see response audit below | 404, 503, 422 | PUBLIC / UI |
| `POST /api/collector/start` | `collector_start` | `collector_start_api_collector_start_post` → `collector_start` | `none` | `dict[str, Any]`, [main.py:146](../../app/main.py:146); see response audit below | 500 | PUBLIC / UI |
| `POST /api/collector/close` | `collector_close` | `collector_close_api_collector_close_post` → `collector_close` | `none` | `dict[str, Any]`, [main.py:154](../../app/main.py:154); see response audit below | none mapped | PUBLIC / UI |
| `DELETE /api/collector/profile` | `collector_delete_profile` | `collector_delete_profile_api_collector_profile_delete` → `collector_delete_profile` | `none` | `dict[str, Any]`, [main.py:159](../../app/main.py:159); see response audit below | none mapped | PUBLIC / UI |
| `GET /api/collector/status` | `collector_status` | `collector_status_api_collector_status_get` → `collector_status` | `none` | `dict[str, Any]`, [main.py:164](../../app/main.py:164); see response audit below | none mapped | PUBLIC / UI |
| `POST /api/collector/check-auth` | `collector_check_auth` | `collector_check_auth_api_collector_check_auth_post` → `collector_check_auth` | `none` | `dict[str, Any]`, [main.py:169](../../app/main.py:169); see response audit below | 400 | PUBLIC / UI |
| `POST /api/collector/navigate/{target}` | `collector_navigate` | `collector_navigate_api_collector_navigate__target__post` → `collector_navigate` | `target: str` | `dict[str, Any]`, [main.py:177](../../app/main.py:177); see response audit below | 400, 422 | PUBLIC / API-only |
| `POST /api/collector/collect/{kind}` | `collector_collect` | `collector_collect_api_collector_collect__kind__post` → `collector_collect` | `kind: str` | `dict[str, Any]`, [main.py:185](../../app/main.py:185); see response audit below | 400, 422 | PUBLIC / UI |
| `GET /api/collector/source/classify` | `collector_source_classify` | `collector_source_classify_api_collector_source_classify_get` → `collector_source_classify` | `source_url: str` | `dict[str, Any]`, [main.py:193](../../app/main.py:193); see response audit below | 422 | PUBLIC / API-only |
| `POST /api/collector/organization-source` | `collector_organization_source` | `collector_organization_source_api_collector_organization_source_post` → `collector_organization_source` | `payload: dict[str, Any]` | `dict[str, Any]`, [main.py:198](../../app/main.py:198); see response audit below | 400, 422 | PUBLIC / API-only |
| `POST /api/collector/organization-source/jobs` | `collector_organization_source_job_create` | `collector_organization_source_job_create_api_collector_organization_source_jobs_post` → `collector_organization_source_job_create` | `payload: dict[str, Any]` | `dict[str, Any]`, [main.py:210](../../app/main.py:210); see response audit below | 400, 422 | PUBLIC / API-only |
| `GET /api/collector/organization-source/jobs/{operation_id}` | `collector_organization_source_job_status` | `collector_organization_source_job_status_api_collector_organization_source_jobs__operation_id__get` → `collector_organization_source_job_status` | `operation_id: str` | `dict[str, Any]`, [main.py:219](../../app/main.py:219); see response audit below | 404, 422 | PUBLIC / API-only |
| `GET /api/collector/organization-source/jobs/{operation_id}/result` | `collector_organization_source_job_result` | `collector_organization_source_job_result_api_collector_organization_source_jobs__operation_id__result_get` → `collector_organization_source_job_result` | `operation_id: str` | `dict[str, Any]`, [main.py:227](../../app/main.py:227); see response audit below | 404, 422 | PUBLIC / API-only |
| `POST /api/collector/organization-source/jobs/{operation_id}/cancel` | `collector_organization_source_job_cancel` | `collector_organization_source_job_cancel_api_collector_organization_source_jobs__operation_id__cancel_post` → `collector_organization_source_job_cancel` | `operation_id: str` | `dict[str, Any]`, [main.py:235](../../app/main.py:235); see response audit below | 404, 422 | PUBLIC / API-only |
| `GET /api/collector/preview` | `collector_preview` | `collector_preview_api_collector_preview_get` → `collector_preview` | `none` | `dict[str, Any]`, [main.py:243](../../app/main.py:243); see response audit below | 404 | PUBLIC / API-only |
| `POST /api/collector/save-preview` | `collector_save_preview` | `collector_save_preview_api_collector_save_preview_post` → `collector_save_preview` | `none` | `dict[str, Any]`, [main.py:250](../../app/main.py:250); see response audit below | 400, 404 | PUBLIC / UI |
| `GET /api/dialogs` | `get_collected_dialogs` | `get_collected_dialogs_api_dialogs_get` → `get_collected_dialogs` | `limit: int=500` | `list[dict[str, Any]]`, [main.py:259](../../app/main.py:259); see response audit below | 422 | PUBLIC / UI |

Unhandled exceptions remain default 500 text/plain `Internal Server Error`; there is no uniform JSON catch-all. Mapped HTTPException responses use `{detail: string}`; framework validation uses 422 `{detail: [{loc,msg,type,...}]}`. Collector job busy/result-pending states are 200 payloads, not 409/202.

## Frontend call sites

| Method | Literal/template |
|---|---|
| GET | `/api/dashboard` |
| GET | `/api/people` |
| GET | `/api/people/${id}` |
| GET | `/api/messages/leaderboard` |
| GET | `/api/changes` |
| POST | `/api/people/${id}/insight` |
| GET | `/api/settings` |
| GET | `/api/lmstudio/models` |
| POST | `/api/import/snapshot` |
| POST | `/api/import/file` |
| PUT | `/api/settings` |
| GET | `/api/collector/status` |
| POST | `/api/collector/start` |
| POST | `/api/collector/check-auth` |
| POST | `/api/collector/collect/friends` |
| POST | `/api/collector/collect/followers` |
| POST | `/api/collector/collect/dialogs` |
| POST | `/api/collector/close` |
| DELETE | `/api/collector/profile` |
| POST | `/api/collector/save-preview` |
| GET | `/api/dialogs` |

`api(path)` uses GET unless options specify method; `collectorAction(path, ...)` always forwards POST. These are the only dynamic wrappers. Person `${id}` maps to `{person_id}`; literal collect friends/followers/dialogs maps to `{kind}`. External VK profile/avatar links are not application API calls.

## Old target contract operations (non-canonical proposal)

| Method | Old path (old server prefix `/api/v1`) | Classification |
|---|---|---|
| GET | `/health` | TARGET-only old URL; never exposed under `/api/v1` |
| GET | `/settings` | TARGET-only old URL; never exposed under `/api/v1` |
| PUT | `/settings` | TARGET-only old URL; never exposed under `/api/v1` |
| POST | `/collector/run` | TARGET-only old URL; never exposed under `/api/v1` |
| GET | `/collector/status` | TARGET-only old URL; never exposed under `/api/v1` |
| GET | `/snapshots` | TARGET-only old URL; never exposed under `/api/v1` |
| GET | `/snapshots/{snapshotId}` | TARGET-only old URL; never exposed under `/api/v1` |
| DELETE | `/snapshots/{snapshotId}` | TARGET-only old URL; never exposed under `/api/v1` |
| GET | `/persons` | TARGET-only old URL; never exposed under `/api/v1` |
| GET | `/persons/{personId}` | TARGET-only old URL; never exposed under `/api/v1` |
| GET | `/timeline` | TARGET-only old URL; never exposed under `/api/v1` |
| GET | `/relationships` | TARGET-only old URL; never exposed under `/api/v1` |
| GET | `/graph` | TARGET-only old URL; never exposed under `/api/v1` |
| POST | `/ai/report/{snapshotId}` | TARGET-only old URL; never exposed under `/api/v1` |
| POST | `/ai/chat` | TARGET-only old URL; never exposed under `/api/v1` |
| GET | `/search` | TARGET-only old URL; never exposed under `/api/v1` |
| GET | `/export/json` | TARGET-only old URL; never exposed under `/api/v1` |
| GET | `/export/csv` | TARGET-only old URL; never exposed under `/api/v1` |

## Response and business-validation audit

- Health: status/version, liveness only. Dashboard: friend/follower current/added/removed, message_total, frozen changes, top_people, recent_imports. People: current display, message counts and relation flags. Detail: person, message_stats, events and stored insights; absent ID 404. Changes use snapshot:/legacy: IDs, nullable pair IDs and snapshot/legacy_unknown provenance. Limit clamps 1..500; dialogs clamp 1..2000 (not request bounds).
- Snapshot import: arbitrary JSON object at framework boundary; relation_type and people validated in service, invalid domain input mapped 400. UUID/date/status/completeness/source metadata and explicit empty supported. Return snapshot_id/date/captured_at/relation_type/status/completeness/count/added/removed; no snapshot read/list route. Structured imports declare complete sets; collector saves remain incomplete.
- File import: required multipart file/import_type, optional relation_type/snapshot_date; content above 100 MiB rejected 400 after reading. Returns job_id/stored_as plus snapshot result, imported count, or archive files/imported. Formats JSON/CSV/TSV/HTML/HTM/ZIP. Business errors 400. Paths in returned stored_as are existing runtime behavior, never copied as real examples.
- Settings: string-valued mapping; PUT accepts arbitrary object, stringifies three lmstudio keys and ignores unknown keys. Models: id plus vendor metadata. Test: ok/models_count/models (discovery only). Insight: id/model/status/confidence/summary/evidence/cautions; provider, invalid output, configuration and open circuit map 503. No retry settings API.
- Collector status/start/close/auth/navigate: status/authenticated/current_url plus running state and diagnostic extensions. Delete returns ok/deleted. Collect/preview: kind/collected_at/count/items/report with relation/dialog-specific fields. Preview missing 404; save returns snapshot result or dialogs saved/collected_at. Organization previews cannot use generic save.
- Public organization classification: source_type/source_url/normalized_url/eligible_for_collection. Organization collect returns variable result/report diagnostic object. Jobs return operation metadata or busy payload; status/cancel return safe operation projection; result wraps operation/result_available and optional result. Options is arbitrary dictionary, non-dictionary coerced to empty; missing/blank source_url 400. No job persistence/restart guarantees.

Counts: 30 application operations; 29 PUBLIC; 1 INTERNAL shell; 21 frontend call sites; 18 old target operations reclassified. All final IDs use explicit stable snake_case route names; Python function names need not change.

## Final contract shape index

Post-alignment generated evidence supplements the pre-edit inventory. All success codes remain 200. Component definitions are in canonical OpenAPI; ordinary dict request bodies retain service-level 400 semantics. Parameters below are framework-enforced.

| Operation | Parameters | Request | 200 media / schema | Documented errors |
|---|---|---|---|---|
| `GET /` | none | none | text/html: string | 500 |
| `GET /api/health` | none | none | application/json: Health | 500 |
| `GET /api/dashboard` | none | none | application/json: Dashboard | 500 |
| `GET /api/people` | none | none | application/json: array of PersonListItem | 500 |
| `GET /api/people/{person_id}` | path person_id: integer; required=True; default=none | none | application/json: PersonDetail | 404, 422, 500 |
| `GET /api/changes` | query limit: integer; required=False; default=100 | none | application/json: array of Change | 422, 500 |
| `GET /api/messages/leaderboard` | none | none | application/json: array of LeaderboardItem | 500 |
| `POST /api/import/snapshot` | none | application/json: object (required: relation_type, people) | application/json: SnapshotResult | 400, 422, 500 |
| `POST /api/import/file` | none | multipart/form-data: Body_post_import_file | application/json: SnapshotFileResult or CountFileResult | 400, 422, 500 |
| `GET /api/settings` | none | none | application/json: object | 500 |
| `PUT /api/settings` | none | application/json: object | application/json: object | 422, 500 |
| `GET /api/lmstudio/models` | none | none | application/json: array of ModelInfo | 500, 503 |
| `POST /api/lmstudio/test` | none | none | application/json: ModelTest | 500, 503 |
| `POST /api/people/{person_id}/insight` | path person_id: integer; required=True; default=none | none | application/json: Insight | 404, 422, 500, 503 |
| `POST /api/collector/start` | none | none | application/json: CollectorStatus | 500 |
| `POST /api/collector/close` | none | none | application/json: CollectorStatus | 500 |
| `DELETE /api/collector/profile` | none | none | application/json: ProfileDeleted | 500 |
| `GET /api/collector/status` | none | none | application/json: CollectorStatus | 500 |
| `POST /api/collector/check-auth` | none | none | application/json: CollectorStatus | 400, 500 |
| `POST /api/collector/navigate/{target}` | path target: string; required=True; default=none | none | application/json: CollectorStatus | 400, 422, 500 |
| `POST /api/collector/collect/{kind}` | path kind: string; required=True; default=none | none | application/json: Preview | 400, 422, 500 |
| `GET /api/collector/source/classify` | query source_url: string; required=True; default=none | none | application/json: SourceClassification | 422, 500 |
| `POST /api/collector/organization-source` | none | application/json: object (required: source_url) | application/json: OrganizationResult | 400, 422, 500 |
| `POST /api/collector/organization-source/jobs` | none | application/json: object (required: source_url) | application/json: CollectorOperation or CollectorBusy | 400, 422, 500 |
| `GET /api/collector/organization-source/jobs/{operation_id}` | path operation_id: string; required=True; default=none | none | application/json: CollectorOperation | 404, 422, 500 |
| `GET /api/collector/organization-source/jobs/{operation_id}/result` | path operation_id: string; required=True; default=none | none | application/json: CollectorJobResult | 404, 422, 500 |
| `POST /api/collector/organization-source/jobs/{operation_id}/cancel` | path operation_id: string; required=True; default=none | none | application/json: CollectorOperation | 404, 422, 500 |
| `GET /api/collector/preview` | none | none | application/json: Preview or OrganizationResult | 404, 500 |
| `POST /api/collector/save-preview` | none | none | application/json: SnapshotResult or DialogSave | 400, 404, 500 |
| `GET /api/dialogs` | query limit: integer; required=False; default=500 | none | application/json: array of Dialog | 422, 500 |
