from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
IMPORT_DIR = DATA_DIR / "imports"
BACKUP_DIR = DATA_DIR / "backups"
DB_PATH = DATA_DIR / "social_radar.db"


def init_storage() -> None:
    for directory in (DATA_DIR, IMPORT_DIR, BACKUP_DIR):
        directory.mkdir(parents=True, exist_ok=True)


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    init_storage()
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def init_db() -> None:
    schema = """
    CREATE TABLE IF NOT EXISTS people (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vk_id INTEGER UNIQUE,
        full_name TEXT NOT NULL,
        profile_url TEXT,
        avatar_url TEXT,
        is_deactivated INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS relation_snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        person_id INTEGER NOT NULL,
        relation_type TEXT NOT NULL CHECK(relation_type IN ('friend', 'follower')),
        snapshot_date TEXT NOT NULL,
        FOREIGN KEY(person_id) REFERENCES people(id) ON DELETE CASCADE,
        UNIQUE(person_id, relation_type, snapshot_date)
    );

    CREATE TABLE IF NOT EXISTS relation_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        person_id INTEGER NOT NULL,
        event_type TEXT NOT NULL,
        event_date TEXT NOT NULL,
        details TEXT,
        FOREIGN KEY(person_id) REFERENCES people(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS message_stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        person_id INTEGER NOT NULL,
        period_start TEXT NOT NULL,
        period_end TEXT NOT NULL,
        incoming_count INTEGER NOT NULL DEFAULT 0,
        outgoing_count INTEGER NOT NULL DEFAULT 0,
        active_days INTEGER NOT NULL DEFAULT 0,
        initiated_by_person INTEGER NOT NULL DEFAULT 0,
        initiated_by_me INTEGER NOT NULL DEFAULT 0,
        median_reply_minutes REAL,
        FOREIGN KEY(person_id) REFERENCES people(id) ON DELETE CASCADE,
        UNIQUE(person_id, period_start, period_end)
    );

    CREATE TABLE IF NOT EXISTS app_settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS ai_insights (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        person_id INTEGER NOT NULL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        model TEXT NOT NULL,
        status TEXT NOT NULL,
        confidence REAL NOT NULL,
        summary TEXT NOT NULL,
        evidence_json TEXT NOT NULL,
        cautions_json TEXT NOT NULL,
        FOREIGN KEY(person_id) REFERENCES people(id) ON DELETE CASCADE
    );


    CREATE TABLE IF NOT EXISTS collector_dialogs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dialog_key TEXT NOT NULL,
        peer_id INTEGER,
        full_name TEXT NOT NULL,
        dialog_url TEXT,
        preview TEXT,
        date_label TEXT,
        unread INTEGER NOT NULL DEFAULT 0,
        unread_count INTEGER,
        outgoing INTEGER NOT NULL DEFAULT 0,
        avatar_url TEXT,
        verified INTEGER NOT NULL DEFAULT 0,
        collected_at TEXT NOT NULL,
        UNIQUE(dialog_key, collected_at)
    );

    CREATE TABLE IF NOT EXISTS import_jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT NOT NULL,
        import_type TEXT NOT NULL,
        status TEXT NOT NULL,
        imported_rows INTEGER NOT NULL DEFAULT 0,
        error_text TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """
    with get_connection() as conn:
        conn.executescript(schema)
        defaults = {
            "lmstudio_base_url": "http://127.0.0.1:1234/v1",
            "lmstudio_model": "",
            "lmstudio_temperature": "0.2",
        }
        for key, value in defaults.items():
            conn.execute(
                "INSERT OR IGNORE INTO app_settings(key, value) VALUES (?, ?)",
                (key, value),
            )
