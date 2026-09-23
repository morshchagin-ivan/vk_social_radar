"""Immutable relation captures and rebuildable adjacent-pair events, not Event Sourcing."""
from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from .db import get_connection


def _capture_time(value):
    if value is None:
        return datetime.now(timezone.utc).isoformat(timespec="microseconds"), "datetime"
    if not isinstance(value, str):
        raise ValueError("captured_at must be an ISO date or timestamp")
    if len(value) <= 10:
        return date.fromisoformat(value).isoformat(), "date"
    instant = datetime.fromisoformat(value)
    # Existing preview timestamps omit an offset. Interpret these as application
    # local time for compatibility; all new collector timestamps carry an offset.
    return instant.astimezone(timezone.utc).isoformat(timespec="microseconds"), "datetime"


def _people(rows):
    if not isinstance(rows, list):
        raise ValueError("people must be a list")
    result = {}
    for raw in rows:
        if not isinstance(raw, dict):
            raise ValueError("person must be an object")
        vk_id = raw.get("vk_id")
        screen = str(raw.get("screen_name") or "").strip().casefold()
        if vk_id is not None:
            if isinstance(vk_id, bool) or str(vk_id).strip() != str(int(vk_id)) or not 0 < int(vk_id) <= 2**63 - 1:
                raise ValueError("vk_id must be a positive integer")
            vk_id = int(vk_id)
            key = f"vk:{vk_id}"
            profile = f"https://vk.com/id{vk_id}"
        elif screen and all(c.isascii() and (c.isalnum() or c in "._") for c in screen):
            key = f"screen:{screen}"
            profile = f"https://vk.com/{screen}"
        else:
            raise ValueError("A numeric vk_id or valid screen_name is required")
        name = raw.get("full_name")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("full_name must be a nonempty string")
        urls = [raw.get("profile_url") or profile, raw.get("avatar_url") or ""]
        if not all(isinstance(url, str) for url in urls):
            raise ValueError("Person URLs must be strings")
        row = dict(external_key=key, vk_id=vk_id, full_name=name.strip(),
                   profile_url=urls[0], avatar_url=urls[1])
        if key in result:
            raise ValueError("Duplicate person identity in snapshot")
        result[key] = row
    return [result[key] for key in sorted(result)]


def _header(conn, snapshot_id):
    row = conn.execute("SELECT * FROM snapshots WHERE id=?", (snapshot_id,)).fetchone()
    if row is None:
        raise ValueError("Snapshot not found")
    return dict(row)


def _members(conn, snapshot_id):
    return {row["external_key"]: dict(row) for row in conn.execute(
        "SELECT * FROM snapshot_people WHERE snapshot_id=? ORDER BY external_key", (snapshot_id,))}


def read_snapshot(snapshot_id: str) -> dict[str, Any]:
    with get_connection() as conn:
        result = _header(conn, snapshot_id)
        result["people"] = list(_members(conn, snapshot_id).values())
        return result


def latest(conn, relation_type, limit=1):
    return [dict(row) for row in conn.execute(
        """SELECT * FROM snapshots WHERE relation_type=? AND status='COMPLETE'
           ORDER BY captured_at DESC, sequence DESC LIMIT ?""", (relation_type, limit))]


def predecessor(conn, current):
    row = conn.execute(
        """SELECT * FROM snapshots WHERE relation_type=? AND status='COMPLETE'
           AND (captured_at, sequence) < (?, ?) ORDER BY captured_at DESC, sequence DESC LIMIT 1""",
        (current["relation_type"], current["captured_at"], current["sequence"])).fetchone()
    return dict(row) if row else None


def _diff(conn, from_id, to_id):
    current = _header(conn, to_id)
    previous = _header(conn, from_id) if from_id else None
    if current["status"] != "COMPLETE" or (previous and (
        previous["status"] != "COMPLETE" or previous["relation_type"] != current["relation_type"])):
        raise ValueError("Diff requires COMPLETE snapshots of the same relation stream")
    before = _members(conn, from_id) if from_id else {}
    after = _members(conn, to_id)
    return {"from_snapshot_id": from_id, "to_snapshot_id": to_id,
            "added": [after[key] for key in sorted(after.keys() - before.keys())],
            "removed": [before[key] for key in sorted(before.keys() - after.keys())]}


def diff_snapshots(from_id: str, to_id: str) -> dict[str, Any]:
    with get_connection() as conn:
        return _diff(conn, from_id, to_id)


def _derive(conn, current):
    previous = predecessor(conn, current)
    from_id = previous["id"] if previous else None
    result = _diff(conn, from_id, current["id"])
    # Replace only obsolete edges; replay retains event IDs and UNIQUE dedups.
    conn.execute("DELETE FROM snapshot_events WHERE to_snapshot_id=? AND from_snapshot_id IS NOT ?",
                 (current["id"], from_id))
    if previous:  # First observation establishes a baseline, not an observed addition event.
        rows = []
        for action in ("added", "removed"):
            projection = current["id"] if action == "added" else from_id
            rows.extend((from_id, current["id"], projection, member["external_key"],
                         f'{current["relation_type"]}_{action}') for member in result[action])
        conn.executemany("""INSERT OR IGNORE INTO snapshot_events
            (from_snapshot_id,to_snapshot_id,projection_snapshot_id,external_key,event_type)
            VALUES (?,?,?,?,?)""", rows)
    return result


def derive_events(to_id: str) -> dict[str, Any]:
    with get_connection() as conn:
        conn.execute("BEGIN IMMEDIATE")
        current = _header(conn, to_id)
        if current["status"] != "COMPLETE":
            raise ValueError("Only COMPLETE snapshots have derived events")
        return _derive(conn, current)


def _bind_people(conn, members):
    # Adopt existing numeric identities without rewriting historical legacy rows.
    numeric = [row for row in members if row["vk_id"] is not None]
    conn.executemany("UPDATE people SET snapshot_key=? WHERE vk_id=? AND snapshot_key IS NULL",
                     [(r["external_key"], r["vk_id"]) for r in numeric])
    conn.executemany("""INSERT INTO people(snapshot_key,vk_id,full_name,profile_url,avatar_url)
        VALUES (:external_key,:vk_id,:full_name,:profile_url,:avatar_url)
        ON CONFLICT(snapshot_key) DO NOTHING""", members)
    mapping = {}
    for start in range(0, len(members), 400):
        keys = [r["external_key"] for r in members[start:start+400]]
        slots = ",".join("?" for _ in keys)
        mapping.update((r["snapshot_key"], r["id"]) for r in conn.execute(
            f"SELECT snapshot_key,id FROM people WHERE snapshot_key IN ({slots})", keys))
    return mapping


def _refresh_projection(conn, members):
    # One set query per batch, with latest historical projection per identity.
    for start in range(0, len(members), 400):
        keys = [r["external_key"] for r in members[start:start+400]]
        slots = ",".join("?" for _ in keys)
        rows = conn.execute(f"""SELECT * FROM (
            SELECT sp.*, ROW_NUMBER() OVER (PARTITION BY external_key
                ORDER BY s.captured_at DESC,s.sequence DESC) AS rank
            FROM snapshot_people sp JOIN snapshots s ON s.id=sp.snapshot_id
            WHERE s.status='COMPLETE' AND sp.external_key IN ({slots})) WHERE rank=1""", keys)
        conn.executemany("UPDATE people SET full_name=?,profile_url=?,avatar_url=? WHERE id=?",
                         [(r["full_name"], r["profile_url"], r["avatar_url"], r["person_id"]) for r in rows])


def create_snapshot(payload: dict[str, Any], *, conn=None) -> dict[str, Any]:
    if conn is None:
        with get_connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            return create_snapshot(payload, conn=connection)
    if not conn.in_transaction:
        raise RuntimeError("Snapshot creation requires an explicit transaction")
    relation = payload.get("relation_type")
    if relation not in {"friend", "follower"}:
        raise ValueError("relation_type must be 'friend' or 'follower'")
    members = _people(payload.get("people"))  # Missing capture is not an explicit empty set.
    snapshot_id = str(UUID(payload["snapshot_id"])) if payload.get("snapshot_id") else str(uuid4())
    existing = conn.execute("SELECT * FROM snapshots WHERE id=?", (snapshot_id,)).fetchone()
    capture_input = payload.get("captured_at") or payload.get("snapshot_date")
    if capture_input is None and existing:
        capture_input = existing["captured_at"]
    captured_at, precision = _capture_time(capture_input)
    completeness = payload.get("completeness", "DECLARED_COMPLETE")
    if completeness not in {"DECLARED_COMPLETE", "UNKNOWN", "PARTIAL"}:
        raise ValueError("Unsupported completeness")
    status = payload.get("status") or ("COMPLETE" if completeness == "DECLARED_COMPLETE" else "INCOMPLETE")
    if status not in {"COMPLETE", "INCOMPLETE", "FAILED", "CREATING"}:
        raise ValueError("Unsupported snapshot status")
    if status == "COMPLETE" and completeness != "DECLARED_COMPLETE":
        raise ValueError("COMPLETE requires an explicit full-set declaration")
    source = payload.get("source", "manual_import")
    reference = payload.get("source_reference")
    if not isinstance(source, str) or not source.strip() or (reference is not None and not isinstance(reference, str)):
        raise ValueError("Invalid snapshot source/reference")
    metadata = dict(id=snapshot_id, relation_type=relation, captured_at=captured_at,
                    capture_precision=precision, source=source, source_reference=reference,
                    status=status, completeness=completeness, item_count=len(members))
    if existing:
        old_members = [{key: row[key] for key in members[0]} for row in _members(conn, snapshot_id).values()] if members else []
        if any(existing[key] != value for key, value in metadata.items()) or old_members != members:
            raise ValueError("Snapshot ID replay must have identical metadata and content")
        current = dict(existing)
    else:
        conn.execute("""INSERT INTO snapshots
            (id,relation_type,captured_at,capture_precision,source,source_reference,status,completeness,item_count,created_at)
            VALUES (:id,:relation_type,:captured_at,:capture_precision,:source,:source_reference,'CREATING',:completeness,:item_count,:created_at)""",
            {**metadata, "created_at": datetime.now(timezone.utc).isoformat(timespec="microseconds")})
        mapping = _bind_people(conn, members) if status == "COMPLETE" else {}
        conn.executemany("""INSERT INTO snapshot_people
            (snapshot_id,external_key,person_id,vk_id,full_name,profile_url,avatar_url)
            VALUES (:snapshot_id,:external_key,:person_id,:vk_id,:full_name,:profile_url,:avatar_url)""",
            [{**r, "snapshot_id": snapshot_id, "person_id": mapping.get(r["external_key"])} for r in members])
        conn.execute("UPDATE snapshots SET status=? WHERE id=?", (status, snapshot_id))
        current = _header(conn, snapshot_id)
    delta = {"added": [], "removed": []}
    if status == "COMPLETE":
        delta = _derive(conn, current)
        successor = conn.execute("""SELECT * FROM snapshots WHERE relation_type=? AND status='COMPLETE'
            AND (captured_at,sequence) > (?,?) ORDER BY captured_at,sequence LIMIT 1""",
            (relation, captured_at, current["sequence"])).fetchone()
        if successor:
            _derive(conn, dict(successor))
        _refresh_projection(conn, members)
    return {"snapshot_id": snapshot_id, "snapshot_date": captured_at[:10], "captured_at": captured_at,
            "relation_type": relation, "status": status, "completeness": completeness,
            "count": len(members), "added": len(delta["added"]), "removed": len(delta["removed"])}


def current_sets(conn, relation):
    rows = latest(conn, relation, 2)
    if rows:
        current = {r["person_id"] for r in _members(conn, rows[0]["id"]).values()}
        previous = {r["person_id"] for r in _members(conn, rows[1]["id"]).values()} if len(rows) > 1 else set()
        return current, previous
    # Explicit compatibility: legacy membership only until first COMPLETE v2 in this stream.
    dates = [r[0] for r in conn.execute("""SELECT DISTINCT snapshot_date FROM relation_snapshots
        WHERE relation_type=? ORDER BY snapshot_date DESC LIMIT 2""", (relation,))]
    sets = [{r[0] for r in conn.execute("SELECT person_id FROM relation_snapshots WHERE relation_type=? AND snapshot_date=?",
                                      (relation, day))} for day in dates]
    return tuple((sets + [set(), set()])[:2])


def changes(conn, limit=100, person_id=None):
    # Legacy events are kept and labelled. New events render only immutable projections.
    return [dict(row) for row in conn.execute("""
        SELECT * FROM (
          SELECT 'snapshot:' || e.id AS id, sp.person_id, e.event_type,
            s.captured_at AS event_date, 'Изменение связи: ' || s.relation_type AS details,
            sp.full_name,sp.profile_url,e.from_snapshot_id,e.to_snapshot_id,
            'snapshot' AS provenance
          FROM snapshot_events e JOIN snapshots s ON s.id=e.to_snapshot_id
          JOIN snapshot_people sp ON sp.snapshot_id=e.projection_snapshot_id AND sp.external_key=e.external_key
          UNION ALL
          SELECT 'legacy:' || e.id,p.id,e.event_type,e.event_date,e.details,p.full_name,p.profile_url,
            NULL,NULL,'legacy_unknown' FROM relation_events e JOIN people p ON p.id=e.person_id
        ) WHERE (? IS NULL OR person_id=?) ORDER BY event_date DESC,id DESC LIMIT ?
        """, (person_id, person_id, limit))]
