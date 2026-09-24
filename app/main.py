from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any

from fastapi import Body, FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import api_models as api
from .api_contract import errors, SNAPSHOT_BODY, SETTINGS_BODY, ORGANIZATION_BODY
from .db import init_db
from .collector import classify_public_vk_source, collector
from .importers import import_uploaded_file
from .ai.composition import get_insight_service, get_provider
from .ai.contracts import ProviderError
from .ai.service import AIConfigurationError, InsightValidationError
from .ai.settings import get_settings, save_settings
from .seed import seed_demo_data
from .services import dashboard, import_snapshot, list_changes, list_people, message_leaderboard, person_detail, save_collector_preview, list_collected_dialogs

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(
    title="VK Social Radar runtime API", version="0.4.2",
    description="IMPLEMENTED local single-user API. No authentication is enforced. "
                "Loopback is the default deployment boundary, not an access-control guarantee. "
                "U06 privacy/access policy remains planned. Canonical 11_OPENAPI.yaml is generated "
                "from this app; /api is preserved. No /api/v1 aliases or target-only resources.",
    servers=[{"url": "http://127.0.0.1:8765", "description": "Default local loopback server"}],
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.on_event("startup")
def startup() -> None:
    init_db()
    seed_demo_data()


@app.get("/",
    operation_id="index",
    description='Internal HTML application shell. Static assets and framework docs are infrastructure, outside application operation inventory.',
    responses={**errors(), 200: {"description": "HTML application shell", "content": {"text/html": {"schema": {"type": "string"}}}}},
    openapi_extra={"x-implementation-status": "IMPLEMENTED", "x-audience": "internal"},
    response_class=FileResponse)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health",
    operation_id="health",
    description='Liveness only; does not check DB, VK authentication or LM Studio readiness. Version remains the existing app version.',
    responses=errors(),
    openapi_extra={"x-implementation-status": "IMPLEMENTED", "x-audience": "public"},
    response_model=api.Health,
    response_model_exclude_unset=True)
def health() -> dict[str, str]:
    return {"status": "ok", "version": "0.4.2"}


@app.get("/api/dashboard",
    operation_id="get_dashboard",
    description='Current COMPLETE relation counts (legacy fallback until first COMPLETE per stream); recent frozen events. Message aggregates are not snapshot-scoped.',
    responses=errors(),
    openapi_extra={"x-implementation-status": "IMPLEMENTED", "x-audience": "public"},
    response_model=api.Dashboard,
    response_model_exclude_unset=True)
def get_dashboard() -> dict[str, Any]:
    return dashboard()


@app.get("/api/people",
    operation_id="get_people",
    description='Current person convenience projection and COMPLETE relation flags. Message periods can yield multiple rows per person; no pagination.',
    responses=errors(),
    openapi_extra={"x-implementation-status": "IMPLEMENTED", "x-audience": "public"},
    response_model=list[api.PersonListItem],
    response_model_exclude_unset=True)
def get_people() -> list[dict[str, Any]]:
    return list_people()


@app.get("/api/people/{person_id}",
    operation_id="get_person",
    description='Current person, message periods, frozen relation events and persisted insight JSON strings. Legacy historical attributes cannot be reconstructed.',
    responses=errors(404),
    openapi_extra={"x-implementation-status": "IMPLEMENTED", "x-audience": "public"},
    response_model=api.PersonDetail,
    response_model_exclude_unset=True)
def get_person(person_id: int) -> dict[str, Any]:
    result = person_detail(person_id)
    if not result:
        raise HTTPException(status_code=404, detail="Person not found")
    return result


@app.get("/api/changes",
    operation_id="get_changes",
    description='Membership timeline only; new events include immutable snapshot pair provenance, legacy events labelled legacy_unknown. Limit clamps to 1..500; no rejected range.',
    responses=errors(),
    openapi_extra={"x-implementation-status": "IMPLEMENTED", "x-audience": "public"},
    response_model=list[api.Change],
    response_model_exclude_unset=True)
def get_changes(limit: Annotated[int, Query(description="Clamped to 1..500; out-of-range integers are accepted")] = 100) -> list[dict[str, Any]]:
    return list_changes(max(1, min(limit, 500)))


@app.get("/api/messages/leaderboard",
    operation_id="get_message_leaderboard",
    description='Message-period aggregates, not a snapshot-reproducible message corpus.',
    responses=errors(),
    openapi_extra={"x-implementation-status": "IMPLEMENTED", "x-audience": "public"},
    response_model=list[api.LeaderboardItem],
    response_model_exclude_unset=True)
def get_message_leaderboard() -> list[dict[str, Any]]:
    return message_leaderboard()


@app.post("/api/import/snapshot",
    operation_id="post_snapshot",
    description='Immutable relation capture; new UUID unless explicit replay. Complete empty sets replace current state. Backdated captures repair predecessor/successor events atomically. First complete capture is a baseline; no observed-change event.',
    responses=errors(400),
    openapi_extra={"x-implementation-status": "IMPLEMENTED", "x-audience": "public"},
    response_model=api.SnapshotResult,
    response_model_exclude_unset=True)
def post_snapshot(payload: dict[str, Any] = Body(..., json_schema_extra=SNAPSHOT_BODY)) -> dict[str, Any]:
    try:
        return import_snapshot(payload)
    except (ValueError, KeyError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/import/file",
    operation_id="post_import_file",
    description='JSON/CSV/TSV/HTML/HTM/ZIP import; import_type relations or message_stats (business-validated 400). Relations require friend/follower. Maximum 100 MiB checked after read. HTML remains UNKNOWN. Archive members commit independently. Returns real local stored_as path; privacy hardening is U06.',
    responses=errors(400),
    openapi_extra={"x-implementation-status": "IMPLEMENTED", "x-audience": "public"},
    response_model=api.SnapshotFileResult | api.CountFileResult,
    response_model_exclude_unset=True)
async def post_import_file(
    file: UploadFile = File(...),
    import_type: str = Form(...),
    relation_type: str | None = Form(None),
    snapshot_date: str | None = Form(None),
) -> dict[str, Any]:
    try:
        content = await file.read()
        if len(content) > 100 * 1024 * 1024:
            raise ValueError("Файл больше 100 МБ")
        return import_uploaded_file(
            filename=file.filename or "upload.bin",
            content=content,
            import_type=import_type,
            relation_type=relation_type,
            snapshot_date=snapshot_date,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/settings",
    operation_id="settings_get",
    description='String-valued settings mapping; current defaults are three lmstudio keys.',
    responses=errors(),
    openapi_extra={"x-implementation-status": "IMPLEMENTED", "x-audience": "public"})
def settings_get() -> dict[str, str]:
    return get_settings()


@app.put("/api/settings",
    operation_id="settings_put",
    description='Only three lmstudio keys stored, all values stringified and unknown keys ignored; response is the settings mapping.',
    responses=errors(),
    openapi_extra={"x-implementation-status": "IMPLEMENTED", "x-audience": "public"})
def settings_put(payload: dict[str, Any] = Body(..., json_schema_extra=SETTINGS_BODY)) -> dict[str, str]:
    return save_settings(payload)


@app.get("/api/lmstudio/models",
    operation_id="lm_models",
    description='One model discovery call via provider port; vendor metadata preserved. No inference readiness guarantee.',
    responses=errors(503),
    openapi_extra={"x-implementation-status": "IMPLEMENTED", "x-audience": "public"},
    response_model=list[api.ModelInfo],
    response_model_exclude_unset=True)
def lm_models() -> list[dict[str, Any]]:
    try:
        return [model.as_dict() for model in get_provider().list_models()]
    except ProviderError as exc:
        raise HTTPException(status_code=503, detail=f"LM Studio недоступна: {exc}") from exc
    except Exception:
        raise HTTPException(status_code=503, detail="LM Studio недоступна") from None


@app.post("/api/lmstudio/test",
    operation_id="lm_test",
    description='Discovery connectivity test, not generation. Returns 200 even if models_count is zero.',
    responses=errors(503),
    openapi_extra={"x-implementation-status": "IMPLEMENTED", "x-audience": "public"},
    response_model=api.ModelTest,
    response_model_exclude_unset=True)
def lm_test() -> dict[str, Any]:
    try:
        models = get_provider().list_models()
        return {"ok": True, "models_count": len(models), "models": [model.id for model in models]}
    except ProviderError as exc:
        raise HTTPException(status_code=503, detail=f"LM Studio недоступна: {exc}") from exc
    except Exception:
        raise HTTPException(status_code=503, detail="LM Studio недоступна") from None


@app.post("/api/people/{person_id}/insight",
    operation_id="create_insight",
    description='Explicit person analysis and persistence. U09 generation: max 3 attempts, max retry sleep 1.5s, breaker 3 failures/30s. Open circuit, provider errors, invalid output/configuration map 503. No total deadline, fallback or RAG; discovery may occur while generation is open.',
    responses=errors(404, 503),
    openapi_extra={"x-implementation-status": "IMPLEMENTED", "x-audience": "public"},
    response_model=api.Insight,
    response_model_exclude_unset=True)
def create_insight(person_id: int) -> dict[str, Any]:
    data = person_detail(person_id)
    if not data:
        raise HTTPException(status_code=404, detail="Person not found")
    try:
        return get_insight_service().create(person_id, data)
    except (ProviderError, InsightValidationError, AIConfigurationError) as exc:
        raise HTTPException(status_code=503, detail=f"Не удалось получить анализ: {exc}") from exc
    except Exception:
        raise HTTPException(status_code=503, detail="Не удалось получить анализ") from None


@app.post("/api/collector/start",
    operation_id="collector_start",
    description='Starts separate persistent Chromium and returns status. Explicit startup failures use JSON 500.',
    responses=errors(500),
    openapi_extra={"x-implementation-status": "IMPLEMENTED", "x-audience": "public"},
    response_model=api.CollectorStatus,
    response_model_exclude_unset=True)
async def collector_start() -> dict[str, Any]:
    try:
        return await collector.start()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Не удалось запустить Chromium: {exc}") from exc


@app.post("/api/collector/close",
    operation_id="collector_close",
    description='Closes the collector browser and returns status.',
    responses=errors(),
    openapi_extra={"x-implementation-status": "IMPLEMENTED", "x-audience": "public"},
    response_model=api.CollectorStatus,
    response_model_exclude_unset=True)
async def collector_close() -> dict[str, Any]:
    return await collector.close()


@app.delete("/api/collector/profile",
    operation_id="collector_delete_profile",
    description='Closes browser and deletes its separate local profile. Returns deleted path. No API authentication is implemented.',
    responses=errors(),
    openapi_extra={"x-implementation-status": "IMPLEMENTED", "x-audience": "public"},
    response_model=api.ProfileDeleted,
    response_model_exclude_unset=True)
async def collector_delete_profile() -> dict[str, Any]:
    return await collector.delete_profile()


@app.get("/api/collector/status",
    operation_id="collector_status",
    description='Collector state with extensible diagnostic/progress fields; does not authenticate the HTTP caller.',
    responses=errors(),
    openapi_extra={"x-implementation-status": "IMPLEMENTED", "x-audience": "public"},
    response_model=api.CollectorStatus,
    response_model_exclude_unset=True)
async def collector_status() -> dict[str, Any]:
    return await collector.get_status()


@app.post("/api/collector/check-auth",
    operation_id="collector_check_auth",
    description='Checks VK login inside the separate browser; this is not API authentication.',
    responses=errors(400),
    openapi_extra={"x-implementation-status": "IMPLEMENTED", "x-audience": "public"},
    response_model=api.CollectorStatus,
    response_model_exclude_unset=True)
async def collector_check_auth() -> dict[str, Any]:
    try:
        return await collector.check_auth()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/collector/navigate/{target}",
    operation_id="collector_navigate",
    description='Supported target values home/friends/followers/dialogs; invalid target or collector failure is 400, not framework enum validation.',
    responses=errors(400),
    openapi_extra={"x-implementation-status": "IMPLEMENTED", "x-audience": "public"},
    response_model=api.CollectorStatus,
    response_model_exclude_unset=True)
async def collector_navigate(target: str) -> dict[str, Any]:
    try:
        return await collector.navigate(target)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/collector/collect/{kind}",
    operation_id="collector_collect",
    description='Supported kind friends/followers/dialogs; invalid kind, busy, stopped, unauthenticated or zero valid items maps 400. Nonempty observation is a preview, not a complete snapshot. No automatic save.',
    responses=errors(400),
    openapi_extra={"x-implementation-status": "IMPLEMENTED", "x-audience": "public"},
    response_model=api.Preview,
    response_model_exclude_unset=True)
async def collector_collect(kind: str) -> dict[str, Any]:
    try:
        return await collector.collect(kind)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/collector/source/classify",
    operation_id="collector_source_classify",
    description='Pure source URL classification; unsupported/blank URL returns an UNKNOWN classification, not 400.',
    responses=errors(),
    openapi_extra={"x-implementation-status": "IMPLEMENTED", "x-audience": "public"},
    response_model=api.SourceClassification,
    response_model_exclude_unset=True)
def collector_source_classify(source_url: str) -> dict[str, Any]:
    return classify_public_vk_source(source_url)


@app.post("/api/collector/organization-source",
    operation_id="collector_organization_source",
    description='Synchronous public organization preview with extensible report/diagnostics; result may describe partial/failure in a 200 body. Generic save-preview does not support organization previews.',
    responses=errors(400),
    openapi_extra={"x-implementation-status": "IMPLEMENTED", "x-audience": "public"},
    response_model=api.OrganizationResult,
    response_model_exclude_unset=True)
async def collector_organization_source(payload: dict[str, Any] = Body(..., json_schema_extra=ORGANIZATION_BODY)) -> dict[str, Any]:
    source_url = str(payload.get("source_url") or "").strip()
    if not source_url:
        raise HTTPException(status_code=400, detail="source_url is required")
    options = payload.get("options") if isinstance(payload.get("options"), dict) else {}
    try:
        return await collector.collect_public_organization_source(source_url, options)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/collector/organization-source/jobs",
    operation_id="collector_organization_source_job_create",
    description='Starts an in-memory job. Both queued and COLLECTOR_BUSY return 200; no 202/409. Jobs are not durable.',
    responses=errors(400),
    openapi_extra={"x-implementation-status": "IMPLEMENTED", "x-audience": "public"},
    response_model=api.CollectorOperation | api.CollectorBusy,
    response_model_exclude_unset=True)
async def collector_organization_source_job_create(payload: dict[str, Any] = Body(..., json_schema_extra=ORGANIZATION_BODY)) -> dict[str, Any]:
    source_url = str(payload.get("source_url") or "").strip()
    if not source_url:
        raise HTTPException(status_code=400, detail="source_url is required")
    options = payload.get("options") if isinstance(payload.get("options"), dict) else {}
    return await collector.start_organization_source_job(source_url, options)


@app.get("/api/collector/organization-source/jobs/{operation_id}",
    operation_id="collector_organization_source_job_status",
    description='In-memory operation projection; unknown ID 404.',
    responses=errors(404),
    openapi_extra={"x-implementation-status": "IMPLEMENTED", "x-audience": "public"},
    response_model=api.CollectorOperation,
    response_model_exclude_unset=True)
async def collector_organization_source_job_status(operation_id: str) -> dict[str, Any]:
    try:
        return await collector.get_organization_source_job(operation_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="operation not found") from exc


@app.get("/api/collector/organization-source/jobs/{operation_id}/result",
    operation_id="collector_organization_source_job_result",
    description='Returns operation/result_available and optional result. Pending remains 200; unknown ID 404.',
    responses=errors(404),
    openapi_extra={"x-implementation-status": "IMPLEMENTED", "x-audience": "public"},
    response_model=api.CollectorJobResult,
    response_model_exclude_unset=True)
async def collector_organization_source_job_result(operation_id: str) -> dict[str, Any]:
    try:
        return await collector.get_organization_source_job_result(operation_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="operation not found") from exc


@app.post("/api/collector/organization-source/jobs/{operation_id}/cancel",
    operation_id="collector_organization_source_job_cancel",
    description='Requests cancellation and returns operation projection; unknown ID 404.',
    responses=errors(404),
    openapi_extra={"x-implementation-status": "IMPLEMENTED", "x-audience": "public"},
    response_model=api.CollectorOperation,
    response_model_exclude_unset=True)
async def collector_organization_source_job_cancel(operation_id: str) -> dict[str, Any]:
    try:
        return await collector.cancel_organization_source_job(operation_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="operation not found") from exc


@app.get("/api/collector/preview",
    operation_id="collector_preview",
    description='Last in-memory relation/dialog/organization preview; missing preview 404. Items/report retain collector-specific diagnostic fields.',
    responses=errors(404),
    openapi_extra={"x-implementation-status": "IMPLEMENTED", "x-audience": "public"},
    response_model=api.Preview | api.OrganizationResult,
    response_model_exclude_unset=True)
async def collector_preview() -> dict[str, Any]:
    if not collector.state.preview:
        raise HTTPException(status_code=404, detail="Preview ещё не создан")
    return collector.state.preview


@app.post("/api/collector/save-preview",
    operation_id="collector_save_preview",
    description='Explicit save: friends/followers are UNKNOWN/INCOMPLETE with no current replacement; dialogs return saved count. Same preview identity is replayed. Missing preview 404, unsupported organization preview or save failure 400.',
    responses=errors(400, 404),
    openapi_extra={"x-implementation-status": "IMPLEMENTED", "x-audience": "public"},
    response_model=api.SnapshotResult | api.DialogSave,
    response_model_exclude_unset=True)
async def collector_save_preview() -> dict[str, Any]:
    if not collector.state.preview:
        raise HTTPException(status_code=404, detail="Preview ещё не создан")
    try:
        return save_collector_preview(collector.state.preview)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.get("/api/dialogs",
    operation_id="get_collected_dialogs",
    description='Latest collected_at dialog batch; limit clamps to 1..2000. No snapshot-scoped message corpus.',
    responses=errors(),
    openapi_extra={"x-implementation-status": "IMPLEMENTED", "x-audience": "public"},
    response_model=list[api.Dialog],
    response_model_exclude_unset=True)
def get_collected_dialogs(limit: Annotated[int, Query(description="Clamped to 1..2000; out-of-range integers are accepted")] = 500) -> list[dict[str, Any]]:
    return list_collected_dialogs(max(1,min(limit,2000)))
