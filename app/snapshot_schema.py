"""Version 2 relation-source schema. Statements are kept whole (triggers contain ';')."""

STATEMENTS = [
    ("people_snapshot_key", "CREATE UNIQUE INDEX people_snapshot_key ON people(snapshot_key)"),
    ("snapshots", """CREATE TABLE snapshots (
        sequence INTEGER PRIMARY KEY AUTOINCREMENT,
        id TEXT NOT NULL UNIQUE,
        relation_type TEXT NOT NULL CHECK(relation_type IN ('friend','follower')),
        captured_at TEXT NOT NULL,
        capture_precision TEXT NOT NULL CHECK(capture_precision IN ('date','datetime')),
        source TEXT NOT NULL,
        source_reference TEXT,
        status TEXT NOT NULL CHECK(status IN ('CREATING','COMPLETE','INCOMPLETE','FAILED')),
        completeness TEXT NOT NULL CHECK(completeness IN ('DECLARED_COMPLETE','UNKNOWN','PARTIAL')),
        item_count INTEGER NOT NULL CHECK(item_count >= 0),
        domain_version INTEGER NOT NULL DEFAULT 1 CHECK(domain_version = 1),
        created_at TEXT NOT NULL,
        CHECK(status != 'COMPLETE' OR completeness = 'DECLARED_COMPLETE')
    )"""),
    ("snapshots_order", "CREATE INDEX snapshots_order ON snapshots(relation_type, status, captured_at, sequence)"),
    ("snapshot_people", """CREATE TABLE snapshot_people (
        snapshot_id TEXT NOT NULL REFERENCES snapshots(id),
        external_key TEXT NOT NULL,
        person_id INTEGER REFERENCES people(id),
        vk_id INTEGER,
        full_name TEXT NOT NULL,
        profile_url TEXT NOT NULL,
        avatar_url TEXT NOT NULL,
        PRIMARY KEY(snapshot_id, external_key)
    )"""),
    ("snapshot_people_identity", "CREATE INDEX snapshot_people_identity ON snapshot_people(external_key, snapshot_id)"),
    ("snapshot_events", """CREATE TABLE snapshot_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        from_snapshot_id TEXT NOT NULL REFERENCES snapshots(id),
        to_snapshot_id TEXT NOT NULL REFERENCES snapshots(id),
        projection_snapshot_id TEXT NOT NULL,
        external_key TEXT NOT NULL,
        event_type TEXT NOT NULL CHECK(event_type IN ('friend_added','friend_removed','follower_added','follower_removed')),
        FOREIGN KEY(projection_snapshot_id, external_key) REFERENCES snapshot_people(snapshot_id, external_key),
        UNIQUE(from_snapshot_id, to_snapshot_id, event_type, external_key)
    )"""),
    ("snapshot_events_target", "CREATE INDEX snapshot_events_target ON snapshot_events(to_snapshot_id)"),
    ("snapshots_insert_guard", """CREATE TRIGGER snapshots_insert_guard BEFORE INSERT ON snapshots
        WHEN NEW.status != 'CREATING' OR EXISTS(SELECT 1 FROM snapshots WHERE id=NEW.id OR sequence=NEW.sequence)
        BEGIN SELECT RAISE(ABORT, 'Snapshot must start CREATING with a new identity'); END"""),
    ("snapshots_update_guard", """CREATE TRIGGER snapshots_update_guard BEFORE UPDATE ON snapshots
        WHEN OLD.status != 'CREATING' OR NEW.id != OLD.id OR NEW.sequence != OLD.sequence
        BEGIN SELECT RAISE(ABORT, 'Final snapshot is immutable'); END"""),
    ("snapshots_delete_guard", """CREATE TRIGGER snapshots_delete_guard BEFORE DELETE ON snapshots
        BEGIN SELECT RAISE(ABORT, 'Snapshot deletion requires an explicit retention policy'); END"""),
    ("snapshots_complete_guard", """CREATE TRIGGER snapshots_complete_guard BEFORE UPDATE OF status ON snapshots
        WHEN NEW.status = 'COMPLETE' AND (
          NEW.item_count != (SELECT COUNT(*) FROM snapshot_people WHERE snapshot_id=NEW.id)
          OR EXISTS(SELECT 1 FROM snapshot_people WHERE snapshot_id=NEW.id AND person_id IS NULL))
        BEGIN SELECT RAISE(ABORT, 'Invalid complete snapshot membership'); END"""),
    ("snapshot_people_insert_guard", """CREATE TRIGGER snapshot_people_insert_guard BEFORE INSERT ON snapshot_people
        WHEN (SELECT status FROM snapshots WHERE id=NEW.snapshot_id) != 'CREATING'
        BEGIN SELECT RAISE(ABORT, 'Snapshot membership is immutable'); END"""),
    ("snapshot_people_update_guard", """CREATE TRIGGER snapshot_people_update_guard BEFORE UPDATE ON snapshot_people
        WHEN (SELECT status FROM snapshots WHERE id=OLD.snapshot_id) != 'CREATING'
          OR (SELECT status FROM snapshots WHERE id=NEW.snapshot_id) != 'CREATING'
        BEGIN SELECT RAISE(ABORT, 'Snapshot membership is immutable'); END"""),
    ("snapshot_people_delete_guard", """CREATE TRIGGER snapshot_people_delete_guard BEFORE DELETE ON snapshot_people
        WHEN (SELECT status FROM snapshots WHERE id=OLD.snapshot_id) != 'CREATING'
        BEGIN SELECT RAISE(ABORT, 'Snapshot membership is immutable'); END"""),
]


def create_schema(conn):
    conn.execute("ALTER TABLE people ADD COLUMN snapshot_key TEXT")
    for _, sql in STATEMENTS:
        conn.execute(sql)


def validate_schema(conn):
    # Fail closed if constraints/triggers/indexes were removed or changed.
    actual = dict(conn.execute("SELECT name, sql FROM sqlite_master WHERE sql IS NOT NULL"))
    # Preserve literal case: changing 'COMPLETE' to 'complete' changes semantics.
    normalize = lambda sql: " ".join(sql.split()).rstrip(";")
    for name, sql in STATEMENTS:
        if name not in actual or normalize(actual[name]) != normalize(sql):
            raise ValueError("Snapshot schema object missing or changed: " + name)
    key = [row for row in conn.execute("PRAGMA table_xinfo(people)") if row[1] == "snapshot_key"]
    if len(key) != 1 or tuple(key[0][2:]) != ("TEXT", 0, None, 0, 0):
        raise ValueError("Current person snapshot identity column is missing or changed")
