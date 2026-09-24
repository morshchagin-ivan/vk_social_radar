from __future__ import annotations

import csv
import io
import json
import re
import zipfile
from datetime import date
from pathlib import Path
from typing import Any
from uuid import uuid4

from .db import IMPORT_DIR, get_connection
from .services import import_message_stats, import_snapshot
from .privacy import MAX_IMPORT_BYTES, PrivacyPolicyError, archive_member_name, safe_directory, upload_name


def _normalize_person(raw: dict[str, Any]) -> dict[str, Any]:
    vk_id = raw.get("vk_id") or raw.get("id") or raw.get("user_id")
    if vk_id is None:
        raise ValueError("У записи отсутствует vk_id/id/user_id")

    full_name = (
        raw.get("full_name")
        or raw.get("name")
        or " ".join(
            part for part in [raw.get("first_name"), raw.get("last_name")] if part
        )
    ).strip()
    if not full_name:
        full_name = f"VK user {vk_id}"

    return {
        "vk_id": int(vk_id),
        "full_name": full_name,
        "profile_url": raw.get("profile_url") or raw.get("url") or f"https://vk.com/id{vk_id}",
        "avatar_url": raw.get("avatar_url") or raw.get("photo") or "",
    }


def _parse_json(content: bytes) -> Any:
    return json.loads(content.decode("utf-8-sig"))


def _parse_csv(content: bytes) -> list[dict[str, Any]]:
    text = content.decode("utf-8-sig")
    sample = text[:4096]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
    except csv.Error:
        dialect = csv.excel
    return list(csv.DictReader(io.StringIO(text), dialect=dialect))


def _extract_vk_users_from_html(content: bytes) -> list[dict[str, Any]]:
    text = content.decode("utf-8", errors="ignore")
    pattern = re.compile(
        r'href=["\']https?://(?:www\.)?vk\.com/(?:id(?P<id>\d+)|(?P<slug>[\w.]+))["\'][^>]*>(?P<name>[^<]+)</a>',
        re.IGNORECASE,
    )
    people = []
    seen = set()
    for match in pattern.finditer(text):
        numeric_id = match.group("id")
        if not numeric_id:
            continue
        vk_id = int(numeric_id)
        if vk_id in seen:
            continue
        seen.add(vk_id)
        people.append(
            {
                "vk_id": vk_id,
                "full_name": re.sub(r"\s+", " ", match.group("name")).strip(),
                "profile_url": f"https://vk.com/id{vk_id}",
            }
        )
    return people


def _rows_from_file(filename: str, content: bytes) -> Any:
    suffix = Path(filename).suffix.lower()
    if suffix == ".json":
        return _parse_json(content)
    if suffix in {".csv", ".tsv"}:
        return _parse_csv(content)
    if suffix in {".html", ".htm"}:
        # Anchor extraction is an observation, not evidence of a complete relation list.
        return {"people": _extract_vk_users_from_html(content), "completeness": "UNKNOWN"}
    raise ValueError(f"Неподдерживаемый формат: {suffix}")


def import_uploaded_file(
    filename: str,
    content: bytes,
    import_type: str,
    relation_type: str | None = None,
    snapshot_date: str | None = None,
) -> dict[str, Any]:
    safe_name = upload_name(filename)
    if len(content) > MAX_IMPORT_BYTES:
        raise PrivacyPolicyError("Import size limit exceeded")
    if import_type not in {"relations", "message_stats"}:
        raise PrivacyPolicyError("Unsupported import type")
    storage = safe_directory(IMPORT_DIR)
    storage.mkdir(parents=True, exist_ok=True)
    stored_path = storage / f"{uuid4().hex}_{safe_name}"
    if stored_path.resolve().parent != storage.resolve():
        raise PrivacyPolicyError("Unsafe import path")
    with stored_path.open('xb') as output:
        output.write(content)

    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO import_jobs(filename, import_type, status) VALUES (?, ?, 'running')",
            (safe_name, import_type),
        )
        job_id = cursor.lastrowid

    try:
        if safe_name.lower().endswith(".zip"):
            result = _import_zip(content, import_type, relation_type, snapshot_date, f"import_job:{job_id}:{safe_name}")
        else:
            rows = _rows_from_file(safe_name, content)
            result = _dispatch(rows, import_type, relation_type, snapshot_date, f"import_job:{job_id}:{safe_name}")

        imported_rows = int(result.get("count") or result.get("imported") or 0)
        with get_connection() as conn:
            conn.execute(
                "UPDATE import_jobs SET status='done', imported_rows=? WHERE id=?",
                (imported_rows, job_id),
            )
        result["job_id"] = job_id
        result["stored_as"] = stored_path.name
        return result
    except Exception as exc:
        with get_connection() as conn:
            conn.execute(
                "UPDATE import_jobs SET status='error', error_text=? WHERE id=?",
                ("Import failed", job_id),
            )
        raise


def _import_zip(
    content: bytes,
    import_type: str,
    relation_type: str | None,
    snapshot_date: str | None,
    source_reference: str | None = None,
) -> dict[str, Any]:
    imported = 0
    processed = []
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        entries = archive.infolist()
        if len(entries) > 1000 or sum(item.file_size for item in entries) > MAX_IMPORT_BYTES:
            raise PrivacyPolicyError("Archive size limit exceeded")
        remaining = MAX_IMPORT_BYTES
        for info in entries:
            if info.is_dir():
                continue
            suffix = Path(info.filename).suffix.lower()
            if suffix not in {".json", ".csv", ".tsv", ".html", ".htm"}:
                continue
            # Members are parsed in memory, never extracted; safe relative folders remain supported.
            archive_member_name(info.filename)
            with archive.open(info) as member:
                content = member.read(remaining + 1)
            if len(content) > remaining:
                raise PrivacyPolicyError("Archive size limit exceeded")
            remaining -= len(content)
            rows = _rows_from_file(info.filename, content)
            result = _dispatch(rows, import_type, relation_type, snapshot_date, f"{source_reference}!{info.filename}")
            imported += int(result.get("count") or result.get("imported") or 0)
            processed.append(info.filename)
    if not processed:
        raise ValueError("В ZIP не найдено поддерживаемых JSON/CSV/HTML файлов")
    return {"imported": imported, "processed_files": processed}


def _dispatch(
    payload: Any,
    import_type: str,
    relation_type: str | None,
    snapshot_date: str | None,
    source_reference: str | None = None,
) -> dict[str, Any]:
    metadata = payload if isinstance(payload, dict) else {}
    if isinstance(payload, dict):
        payload = next((payload[key] for key in ("people", "items", "messages") if key in payload), [payload])

    if not isinstance(payload, list):
        raise ValueError("Ожидался массив записей")

    if import_type == "relations":
        if relation_type not in {"friend", "follower"}:
            raise ValueError("Для relations требуется friend или follower")
        people = [_normalize_person(item) for item in payload]
        return import_snapshot(
            {
                "relation_type": relation_type,
                "snapshot_date": snapshot_date or metadata.get("snapshot_date") or date.today().isoformat(),
                "people": people,
                "captured_at": metadata.get("captured_at"),
                "completeness": metadata.get("completeness", "DECLARED_COMPLETE"),
                "status": metadata.get("status"),
                "source": "file_import", "source_reference": source_reference,
            }
        )

    if import_type == "message_stats":
        rows = []
        for item in payload:
            person = _normalize_person(item)
            rows.append(
                {
                    **person,
                    "period_start": item.get("period_start"),
                    "period_end": item.get("period_end"),
                    # Preserve types until the shared domain validator; int() here
                    # would silently turn fractional JSON values/bools into counts.
                    "incoming_count": item.get("incoming_count", 0),
                    "outgoing_count": item.get("outgoing_count", 0),
                    "active_days": item.get("active_days", 0),
                    "initiated_by_person": item.get("initiated_by_person", 0),
                    "initiated_by_me": item.get("initiated_by_me", 0),
                    "median_reply_minutes": (
                        float(item["median_reply_minutes"])
                        if item.get("median_reply_minutes") not in (None, "")
                        else None
                    ),
                }
            )
        return import_message_stats(rows)

    raise ValueError("Неизвестный import_type")
