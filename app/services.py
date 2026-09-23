from __future__ import annotations

from datetime import date
from typing import Any

from .db import get_connection


def _latest_snapshot_dates(conn, relation_type: str) -> list[str]:
    rows = conn.execute(
        """
        SELECT DISTINCT snapshot_date FROM relation_snapshots
        WHERE relation_type = ?
        ORDER BY snapshot_date DESC LIMIT 2
        """,
        (relation_type,),
    ).fetchall()
    return [row["snapshot_date"] for row in rows]


def _snapshot_ids(conn, relation_type: str, snapshot_date: str | None) -> set[int]:
    if not snapshot_date:
        return set()
    rows = conn.execute(
        "SELECT person_id FROM relation_snapshots WHERE relation_type=? AND snapshot_date=?",
        (relation_type, snapshot_date),
    ).fetchall()
    return {row["person_id"] for row in rows}


def dashboard() -> dict[str, Any]:
    with get_connection() as conn:
        friend_dates = _latest_snapshot_dates(conn, "friend")
        follower_dates = _latest_snapshot_dates(conn, "follower")
        current_friends = _snapshot_ids(conn, "friend", friend_dates[0] if friend_dates else None)
        previous_friends = _snapshot_ids(conn, "friend", friend_dates[1] if len(friend_dates) > 1 else None)
        current_followers = _snapshot_ids(conn, "follower", follower_dates[0] if follower_dates else None)
        previous_followers = _snapshot_ids(conn, "follower", follower_dates[1] if len(follower_dates) > 1 else None)

        message_total = conn.execute(
            "SELECT COALESCE(SUM(incoming_count + outgoing_count), 0) AS total FROM message_stats"
        ).fetchone()["total"]
        changes = conn.execute(
            """
            SELECT re.id, re.event_type, re.event_date, re.details, p.full_name, p.profile_url
            FROM relation_events re JOIN people p ON p.id=re.person_id
            ORDER BY re.event_date DESC, re.id DESC LIMIT 10
            """
        ).fetchall()
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
        fd = _latest_snapshot_dates(conn, "friend")
        fld = _latest_snapshot_dates(conn, "follower")
        friend_ids = _snapshot_ids(conn, "friend", fd[0] if fd else None)
        follower_ids = _snapshot_ids(conn, "follower", fld[0] if fld else None)
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
        events = conn.execute(
            "SELECT event_type,event_date,details FROM relation_events WHERE person_id=? ORDER BY event_date DESC,id DESC",
            (person_id,),
        ).fetchall()
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
        rows = conn.execute(
            """
            SELECT re.id,re.event_type,re.event_date,re.details,
                   p.id person_id,p.full_name,p.profile_url
            FROM relation_events re JOIN people p ON p.id=re.person_id
            ORDER BY re.event_date DESC,re.id DESC LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


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
    snapshot_date = payload.get("snapshot_date") or date.today().isoformat()
    relation_type = payload.get("relation_type")
    people = payload.get("people", [])
    if relation_type not in {"friend","follower"}:
        raise ValueError("relation_type must be 'friend' or 'follower'")
    if not isinstance(people,list):
        raise ValueError("people must be a list")

    with get_connection() as conn:
        dates = _latest_snapshot_dates(conn, relation_type)
        previous_date = dates[0] if dates and dates[0] != snapshot_date else (dates[1] if len(dates)>1 else None)
        previous_ids = _snapshot_ids(conn, relation_type, previous_date)
        current_ids = set()

        for raw in people:
            vk_id_raw = raw.get("vk_id")
            screen_name = str(raw.get("screen_name") or "").strip()
            if vk_id_raw is None:
                if not screen_name:
                    raise ValueError("У профиля нет vk_id или screen_name")
                vk_id = -int.from_bytes(screen_name.encode("utf-8"), "little", signed=False) % 2_000_000_000 - 1
            else:
                vk_id = int(vk_id_raw)
            full_name = str(raw["full_name"]).strip()
            profile_url = raw.get("profile_url") or (f"https://vk.com/{screen_name}" if screen_name else f"https://vk.com/id{vk_id}")
            avatar_url = raw.get("avatar_url") or ""
            conn.execute(
                """
                INSERT INTO people(vk_id,full_name,profile_url,avatar_url)
                VALUES (?,?,?,?)
                ON CONFLICT(vk_id) DO UPDATE SET
                    full_name=excluded.full_name,profile_url=excluded.profile_url,avatar_url=excluded.avatar_url
                """,
                (vk_id,full_name,profile_url,avatar_url),
            )
            person_id = conn.execute("SELECT id FROM people WHERE vk_id=?", (vk_id,)).fetchone()["id"]
            current_ids.add(person_id)
            conn.execute(
                "INSERT OR IGNORE INTO relation_snapshots(person_id,relation_type,snapshot_date) VALUES (?,?,?)",
                (person_id,relation_type,snapshot_date),
            )

        added = current_ids-previous_ids
        removed = previous_ids-current_ids

        if previous_date:
            added_event = "friend_added" if relation_type=="friend" else "follower_added"
            removed_event = "friend_removed" if relation_type=="friend" else "follower_removed"
            for person_id in added:
                conn.execute(
                    "INSERT INTO relation_events(person_id,event_type,event_date,details) VALUES (?,?,?,?)",
                    (person_id,added_event,snapshot_date,f"Новая связь: {relation_type}"),
                )
            for person_id in removed:
                conn.execute(
                    "INSERT INTO relation_events(person_id,event_type,event_date,details) VALUES (?,?,?,?)",
                    (person_id,removed_event,snapshot_date,f"Связь исчезла: {relation_type}"),
                )

            # Upgrade same-day friend removal + follower presence to transition.
            if relation_type == "follower":
                for person_id in added:
                    friend_removed = conn.execute(
                        """
                        SELECT id FROM relation_events
                        WHERE person_id=? AND event_type='friend_removed' AND event_date=?
                        ORDER BY id DESC LIMIT 1
                        """,
                        (person_id,snapshot_date),
                    ).fetchone()
                    if friend_removed:
                        conn.execute("DELETE FROM relation_events WHERE id=?", (friend_removed["id"],))
                        conn.execute(
                            """
                            UPDATE relation_events SET event_type='friend_to_follower',
                                details='Удалился из друзей, остался подписчиком'
                            WHERE person_id=? AND event_type='follower_added' AND event_date=?
                            """,
                            (person_id,snapshot_date),
                        )

    return {"snapshot_date":snapshot_date,"relation_type":relation_type,"count":len(current_ids),"added":len(added),"removed":len(removed)}


def import_message_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
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
        snapshot_date = collected_at[:10]
        return import_snapshot(
            {
                "relation_type": relation_type,
                "snapshot_date": snapshot_date,
                "people": items,
            }
        )

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
