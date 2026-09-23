"""SQLite schema v1: additive dialog metadata, with a pre-upgrade backup.

The caller owns the transaction (including default settings). Never use
executescript here: it can commit a pending transaction before executing DDL.
"""
from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

CURRENT_SCHEMA_VERSION = 1
EXPECTED_TABLES = frozenset({
    "people", "relation_snapshots", "relation_events", "message_stats",
    "app_settings", "ai_insights", "collector_dialogs", "import_jobs",
})
# type, NOT NULL, default, primary-key position (PRAGMA table_info format).
LEGACY_COLUMNS = {
    "id": ("INTEGER", 0, None, 1),
    "dialog_key": ("TEXT", 1, None, 0),
    "peer_id": ("INTEGER", 0, None, 0),
    "full_name": ("TEXT", 1, None, 0),
    "dialog_url": ("TEXT", 0, None, 0),
    "collected_at": ("TEXT", 1, None, 0),
}
ADDED_COLUMNS = {
    "preview": "TEXT",
    "date_label": "TEXT",
    "unread": "INTEGER NOT NULL DEFAULT 0",
    "unread_count": "INTEGER",
    "outgoing": "INTEGER NOT NULL DEFAULT 0",
    "avatar_url": "TEXT",
    "verified": "INTEGER NOT NULL DEFAULT 0",
}
CURRENT_COLUMNS = {
    **LEGACY_COLUMNS,
    **{name: ("INTEGER", 1, "0", 0) if "DEFAULT" in ddl
       else (ddl, 0, None, 0) for name, ddl in ADDED_COLUMNS.items()},
}


class SchemaMigrationError(RuntimeError):
    """Startup must stop; the database needs a supported schema or recovery."""


def _dialog_columns(conn: sqlite3.Connection) -> dict:
    # xinfo also detects unexpected generated/hidden columns. Column order is
    # intentionally irrelevant: ADD COLUMN appends after legacy collected_at.
    rows = conn.execute("PRAGMA table_xinfo(collector_dialogs)").fetchall()
    if any(row[6] for row in rows):
        raise SchemaMigrationError("Unsupported collector_dialogs hidden columns")
    return {row[1]: (row[2].upper(), row[3], row[4], row[5]) for row in rows}


def detect_schema(conn: sqlite3.Connection) -> str:
    version = conn.execute("PRAGMA user_version").fetchone()[0]
    if version > CURRENT_SCHEMA_VERSION:
        raise SchemaMigrationError(
            f"Database schema version {version} is newer than supported {CURRENT_SCHEMA_VERSION}"
        )
    if version < 0:
        raise SchemaMigrationError(f"Unsupported database schema version {version}")
    if version == CURRENT_SCHEMA_VERSION:
        return "current"
    objects = conn.execute(
        "SELECT name FROM sqlite_master WHERE name NOT GLOB 'sqlite_*'"
    ).fetchall()
    if not objects:
        return "fresh"
    columns = _dialog_columns(conn)
    if columns == LEGACY_COLUMNS:
        return "legacy_dialogs"
    if columns == CURRENT_COLUMNS:
        return "unversioned_current"
    raise SchemaMigrationError("Unsupported unversioned database schema; no migration applied")


def backup_database(db_path: Path, backup_dir: Path) -> Path:
    """Copy committed pre-migration state, including any committed WAL pages.

    The caller holds BEGIN IMMEDIATE but has not changed anything. A separate
    read connection avoids backing up from our own active write transaction
    (which can block), while the reservation prevents competing writers.
    """
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    backup_path = backup_dir / f"schema-v0-to-v1-{stamp}-{uuid4().hex}.db"
    try:
        backup_dir.mkdir(parents=True, exist_ok=True)
        with backup_path.open("xb"):
            pass  # Exclusive creation: never overwrite an existing backup.
        with closing(sqlite3.connect(db_path.resolve().as_uri() + "?mode=ro", uri=True)) as source:
            with closing(sqlite3.connect(backup_path)) as target:
                source.backup(target)
                if target.execute("PRAGMA quick_check").fetchone()[0] != "ok":
                    raise SchemaMigrationError("Migration backup integrity check failed")
    except (OSError, sqlite3.Error, SchemaMigrationError) as exc:
        # Keep even incomplete files for operator inspection; no retention or
        # automatic deletion policy in U02. Do not include private row values.
        raise SchemaMigrationError("Schema migration backup failed; database unchanged") from exc
    return backup_path


def validate_schema(conn: sqlite3.Connection) -> None:
    tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if not EXPECTED_TABLES <= tables:
        raise SchemaMigrationError("Database schema is missing required tables")
    if _dialog_columns(conn) != CURRENT_COLUMNS:
        raise SchemaMigrationError("Database collector_dialogs schema does not match version 1")
    # Preserve the runtime's INSERT OR IGNORE deduplication contract.
    unique_keys = []
    for index in conn.execute("PRAGMA index_list(collector_dialogs)"):
        if index[2] and not index[4]:
            fields = tuple(row[2] for row in conn.execute(
                "SELECT * FROM pragma_index_info(?)", (index[1],)
            ))
            unique_keys.append(fields)
    if ("dialog_key", "collected_at") not in unique_keys:
        raise SchemaMigrationError("Database collector_dialogs uniqueness constraint is missing")
    if conn.execute("PRAGMA foreign_key_check").fetchone() is not None:
        raise SchemaMigrationError("Database foreign key validation failed")


def migrate(conn: sqlite3.Connection, schema: str, db_path: Path, backup_dir: Path) -> None:
    if not conn.in_transaction:
        raise SchemaMigrationError("Schema migration requires an explicit transaction")
    state = detect_schema(conn)
    if state in {"legacy_dialogs", "unversioned_current"}:
        backup_database(db_path, backup_dir)
    if state == "legacy_dialogs":
        # Unknown metadata stays NULL. Zero flags are compatibility sentinels
        # required by the existing DDL, not observations about legacy dialogs.
        for name, definition in ADDED_COLUMNS.items():
            conn.execute(f"ALTER TABLE collector_dialogs ADD COLUMN {name} {definition}")
    if state != "current":
        # Static application DDL only; statements contain no embedded semicolons.
        for statement in schema.split(";"):
            if statement.strip():
                conn.execute(statement)
    validate_schema(conn)
    if state != "current":
        conn.execute(f"PRAGMA user_version = {CURRENT_SCHEMA_VERSION}")
    if conn.execute("PRAGMA user_version").fetchone()[0] != CURRENT_SCHEMA_VERSION:
        raise SchemaMigrationError("Database schema version validation failed")
