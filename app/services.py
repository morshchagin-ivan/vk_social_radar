from __future__ import annotations

from datetime import date
from typing import Any
from uuid import uuid4

from .db import get_connection
from .message_stats import normalize_message_stats
from . import snapshots


def dashboard() -> dict[str, Any]:
    with get_connection() as conn:
        current_friends, previous_friends = snapshots.current_sets(conn, "friend")
        current_followers, previous_followers = snapshots.current_sets(conn, "follower")

        message_total = conn.execute(
            "SELECT COALESCE(SUM(incoming_count + outgoing_count), 0) AS total FROM message_stats"
        ).fetchone()["total"]
        changes = snapshots.changes(conn, 10)
        top_people = conn.execute(
            """
            SELECT p.id, p.full_name, p.profile_url, ms.incoming_count, ms.outgoing_count,
                   ms.active_days, ms.median_reply_minutes,
                   (ms.incoming_count + ms.outgoing_count) AS total_messages
            FROM message_stats ms JOIN people p ON p.id=ms.person_id
            ORDER BY total_messages DESC LIMIT 5
            """
        ).fetchall()
        import_status = conn.execute(
            """
            SELECT id, filename, import_type, status, imported_rows, error_text, created_at
            FROM import_jobs ORDER BY id DESC LIMIT 5
            """
        ).fetchall()

    return {
        "friends": {"current": len(current_friends), "added": len(current_friends-previous_friends), "removed": len(previous_friends-current_friends)},
        "followers": {"current": len(current_followers), "added": len(current_followers-previous_followers), "removed": len(previous_followers-current_followers)},
        "message_total": message_total,
        "changes": [dict(row) for row in changes],
        "top_people": [dict(row) for row in top_people],
        "recent_imports": [dict(row) for row in import_status],
    }


def list_people() -> list[dict[str, Any]]:
    with get_connection() as conn:
        friend_ids, _ = snapshots.current_sets(conn, "friend")
        follower_ids, _ = snapshots.current_sets(conn, "follower")
        rows = conn.execute(
            """
            SELECT p.id, p.vk_id, p.full_name, p.profile_url, p.avatar_url, p.is_deactivated,
                   COALESCE(ms.incoming_count,0) incoming_count,
                   COALESCE(ms.outgoing_count,0) outgoing_count,
                   COALESCE(ms.active_days,0) active_days,
                   ms.median_reply_minutes
            FROM people p
            LEFT JOIN message_stats ms ON ms.person_id=p.id
            ORDER BY (COALESCE(ms.incoming_count,0)+COALESCE(ms.outgoing_count,0)) DESC, p.full_name
            """
        ).fetchall()
    result = []
    for row in rows:
        item = dict(row)
        item["is_friend"] = item["id"] in friend_ids
        item["is_follower"] = item["id"] in follower_ids
        item["total_messages"] = item["incoming_count"] + item["outgoing_count"]
        result.append(item)
    return result


def person_detail(person_id: int) -> dict[str, Any] | None:
    with get_connection() as conn:
        person = conn.execute("SELECT * FROM people WHERE id=?", (person_id,)).fetchone()
        if not person:
            return None
        stats = conn.execute(
            "SELECT * FROM message_stats WHERE person_id=? ORDER BY period_end DESC",
            (person_id,),
        ).fetchall()
        events = snapshots.changes(conn, -1, person_id)
        insights = conn.execute(
            """
            SELECT id,created_at,model,status,confidence,summary,evidence_json,cautions_json
            FROM ai_insights WHERE person_id=? ORDER BY id DESC LIMIT 10
            """,
            (person_id,),
        ).fetchall()
    return {
        "person": dict(person),
        "message_stats": [dict(row) for row in stats],
        "events": [dict(row) for row in events],
        "insights": [dict(row) for row in insights],
    }


def list_changes(limit: int = 100) -> list[dict[str, Any]]:
    with get_connection() as conn:
        return snapshots.changes(conn, limit)


def message_leaderboard() -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT p.id person_id,p.full_name,p.profile_url,ms.*,
                   (ms.incoming_count+ms.outgoing_count) total_messages
            FROM message_stats ms JOIN people p ON p.id=ms.person_id
            ORDER BY total_messages DESC
            """
        ).fetchall()
    result = []
    for row in rows:
        item = dict(row)
        starts = item["initiated_by_person"] + item["initiated_by_me"]
        item["person_initiative_pct"] = round(100*item["initiated_by_person"]/starts,1) if starts else 0
        result.append(item)
    return result


def import_snapshot(payload: dict[str, Any]) -> dict[str, Any]:
    return snapshots.create_snapshot(payload)


def import_message_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    # Validate before any person upsert; keep the existing whole-batch transaction.
    rows = [normalize_message_stats(raw) for raw in rows]
    imported = 0
    with get_connection() as conn:
        for raw in rows:
            vk_id = int(raw["vk_id"])
            conn.execute(
                """
                INSERT INTO people(vk_id,full_name,profile_url,avatar_url)
                VALUES (?,?,?,?)
                ON CONFLICT(vk_id) DO UPDATE SET
                    full_name=excluded.full_name,profile_url=excluded.profile_url,avatar_url=excluded.avatar_url
                """,
                (vk_id,raw["full_name"],raw.get("profile_url"),raw.get("avatar_url","")),
            )
            person_id = conn.execute("SELECT id FROM people WHERE vk_id=?", (vk_id,)).fetchone()["id"]
            conn.execute(
                """
                INSERT INTO message_stats(
                    person_id,period_start,period_end,incoming_count,outgoing_count,
                    active_days,initiated_by_person,initiated_by_me,median_reply_minutes
                ) VALUES (?,?,?,?,?,?,?,?,?)
                ON CONFLICT(person_id,period_start,period_end) DO UPDATE SET
                    incoming_count=excluded.incoming_count,
                    outgoing_count=excluded.outgoing_count,
                    active_days=excluded.active_days,
                    initiated_by_person=excluded.initiated_by_person,
                    initiated_by_me=excluded.initiated_by_me,
                    median_reply_minutes=excluded.median_reply_minutes
                """,
                (
                    person_id,raw["period_start"],raw["period_end"],raw["incoming_count"],
                    raw["outgoing_count"],raw["active_days"],raw["initiated_by_person"],
                    raw["initiated_by_me"],raw.get("median_reply_minutes"),
                ),
            )
            imported += 1
    return {"imported": imported}


def save_collector_preview(preview: dict[str, Any]) -> dict[str, Any]:
    kind = preview.get("kind")
    items = preview.get("items") or []
    collected_at = preview.get("collected_at") or date.today().isoformat()

    if kind in {"friends", "followers"}:
        relation_type = "friend" if kind == "friends" else "follower"
        # Current DOM collector cannot prove full-set completeness. Retain its
        # observation without replacing COMPLETE relation state or deriving removals.
        return import_snapshot({
            "relation_type": relation_type, "captured_at": collected_at,
            "snapshot_id": preview.setdefault("snapshot_id", str(uuid4())),
            "people": items, "source": "collector_preview",
            "source_reference": preview.get("source_url"),
            "completeness": "UNKNOWN", "status": "INCOMPLETE",
        })

    if kind == "dialogs":
        saved = 0
        with get_connection() as conn:
            for item in items:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO collector_dialogs(
                        dialog_key, peer_id, full_name, dialog_url, preview, date_label,
                        unread, unread_count, outgoing, avatar_url, verified, collected_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        item["dialog_key"],
                        item.get("peer_id"),
                        item["full_name"],
                        item.get("dialog_url"), item.get("preview"), item.get("date_label"),
                        1 if item.get("unread") else 0, item.get("unread_count"),
                        1 if item.get("outgoing") else 0, item.get("avatar_url"),
                        1 if item.get("verified") else 0, collected_at,
                    ),
                )
                saved += 1
        return {"kind": "dialogs", "saved": saved, "collected_at": collected_at}

    raise ValueError("Неизвестный тип preview")

def list_collected_dialogs(limit: int = 500) -> list[dict[str, Any]]:
    with get_connection() as conn:
        latest=conn.execute("SELECT MAX(collected_at) latest FROM collector_dialogs").fetchone()["latest"]
        if not latest:return []
        rows=conn.execute("""SELECT * FROM collector_dialogs WHERE collected_at=? ORDER BY id LIMIT ?""",(latest,limit)).fetchall()
    return [dict(r) for r in rows]
