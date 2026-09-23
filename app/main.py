from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

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

app = FastAPI(title="VK Social Radar", version="0.4.2")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.on_event("startup")
def startup() -> None:
    init_db()
    seed_demo_data()


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": "0.4.2"}


@app.get("/api/dashboard")
def get_dashboard() -> dict[str, Any]:
    return dashboard()


@app.get("/api/people")
def get_people() -> list[dict[str, Any]]:
    return list_people()


@app.get("/api/people/{person_id}")
def get_person(person_id: int) -> dict[str, Any]:
    result = person_detail(person_id)
    if not result:
        raise HTTPException(status_code=404, detail="Person not found")
    return result


@app.get("/api/changes")
def get_changes(limit: int = 100) -> list[dict[str, Any]]:
    return list_changes(max(1, min(limit, 500)))


@app.get("/api/messages/leaderboard")
def get_message_leaderboard() -> list[dict[str, Any]]:
    return message_leaderboard()


@app.post("/api/import/snapshot")
def post_snapshot(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        return import_snapshot(payload)
    except (ValueError, KeyError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/import/file")
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


@app.get("/api/settings")
def settings_get() -> dict[str, str]:
    return get_settings()


@app.put("/api/settings")
def settings_put(payload: dict[str, Any]) -> dict[str, str]:
    return save_settings(payload)


@app.get("/api/lmstudio/models")
def lm_models() -> list[dict[str, Any]]:
    try:
        return [model.as_dict() for model in get_provider().list_models()]
    except ProviderError as exc:
        raise HTTPException(status_code=503, detail=f"LM Studio недоступна: {exc}") from exc
    except Exception:
        raise HTTPException(status_code=503, detail="LM Studio недоступна") from None


@app.post("/api/lmstudio/test")
def lm_test() -> dict[str, Any]:
    try:
        models = get_provider().list_models()
        return {"ok": True, "models_count": len(models), "models": [model.id for model in models]}
    except ProviderError as exc:
        raise HTTPException(status_code=503, detail=f"LM Studio недоступна: {exc}") from exc
    except Exception:
        raise HTTPException(status_code=503, detail="LM Studio недоступна") from None


@app.post("/api/people/{person_id}/insight")
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


@app.post("/api/collector/start")
async def collector_start() -> dict[str, Any]:
    try:
        return await collector.start()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Не удалось запустить Chromium: {exc}") from exc


@app.post("/api/collector/close")
async def collector_close() -> dict[str, Any]:
    return await collector.close()


@app.delete("/api/collector/profile")
async def collector_delete_profile() -> dict[str, Any]:
    return await collector.delete_profile()


@app.get("/api/collector/status")
async def collector_status() -> dict[str, Any]:
    return await collector.get_status()


@app.post("/api/collector/check-auth")
async def collector_check_auth() -> dict[str, Any]:
    try:
        return await collector.check_auth()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/collector/navigate/{target}")
async def collector_navigate(target: str) -> dict[str, Any]:
    try:
        return await collector.navigate(target)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/collector/collect/{kind}")
async def collector_collect(kind: str) -> dict[str, Any]:
    try:
        return await collector.collect(kind)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/collector/source/classify")
def collector_source_classify(source_url: str) -> dict[str, Any]:
    return classify_public_vk_source(source_url)


@app.post("/api/collector/organization-source")
async def collector_organization_source(payload: dict[str, Any]) -> dict[str, Any]:
    source_url = str(payload.get("source_url") or "").strip()
    if not source_url:
        raise HTTPException(status_code=400, detail="source_url is required")
    options = payload.get("options") if isinstance(payload.get("options"), dict) else {}
    try:
        return await collector.collect_public_organization_source(source_url, options)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/collector/organization-source/jobs")
async def collector_organization_source_job_create(payload: dict[str, Any]) -> dict[str, Any]:
    source_url = str(payload.get("source_url") or "").strip()
    if not source_url:
        raise HTTPException(status_code=400, detail="source_url is required")
    options = payload.get("options") if isinstance(payload.get("options"), dict) else {}
    return await collector.start_organization_source_job(source_url, options)


@app.get("/api/collector/organization-source/jobs/{operation_id}")
async def collector_organization_source_job_status(operation_id: str) -> dict[str, Any]:
    try:
        return await collector.get_organization_source_job(operation_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="operation not found") from exc


@app.get("/api/collector/organization-source/jobs/{operation_id}/result")
async def collector_organization_source_job_result(operation_id: str) -> dict[str, Any]:
    try:
        return await collector.get_organization_source_job_result(operation_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="operation not found") from exc


@app.post("/api/collector/organization-source/jobs/{operation_id}/cancel")
async def collector_organization_source_job_cancel(operation_id: str) -> dict[str, Any]:
    try:
        return await collector.cancel_organization_source_job(operation_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="operation not found") from exc


@app.get("/api/collector/preview")
async def collector_preview() -> dict[str, Any]:
    if not collector.state.preview:
        raise HTTPException(status_code=404, detail="Preview ещё не создан")
    return collector.state.preview


@app.post("/api/collector/save-preview")
async def collector_save_preview() -> dict[str, Any]:
    if not collector.state.preview:
        raise HTTPException(status_code=404, detail="Preview ещё не создан")
    try:
        return save_collector_preview(collector.state.preview)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.get("/api/dialogs")
def get_collected_dialogs(limit: int = 500) -> list[dict[str, Any]]:
    return list_collected_dialogs(max(1,min(limit,2000)))
