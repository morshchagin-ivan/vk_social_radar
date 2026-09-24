"""Read persisted v2 COMPLETE sources; never mutate source or build from live profiles."""
from __future__ import annotations

import json
import sqlite3

from .models import Document, RAGValidationError, stable_id


def normalized(value: str) -> str:
    return ' '.join(value.split())


def build_corpus(conn: sqlite3.Connection) -> tuple[Document, ...]:
    """A read snapshot across all SELECTs; SAVEPOINT does not commit caller writes."""
    if conn.execute('PRAGMA user_version').fetchone()[0] != 2:
        raise RAGValidationError('RAG requires an initialized v2 database')
    documents = []
    conn.execute('SAVEPOINT rag_corpus_read')
    try:
        cursor = conn.execute("""SELECT id, relation_type, captured_at, capture_precision, item_count
                                 FROM snapshots WHERE status='COMPLETE' ORDER BY id""")
        headers = {row[0]: dict(zip([item[0] for item in cursor.description], row)) for row in cursor}
        for sid, header in headers.items():
            relation, at = header['relation_type'], header['captured_at']
            content = f"Snapshot снимок {relation}. Captured {at}. Member count {header['item_count']}."
            if header['item_count'] == 0:
                content += ' Empty пустой declared complete set; not a failed collection.'
            documents.append(Document(
                stable_id('snapshot', sid), 'snapshot', sid, sid, at,
                header['capture_precision'], relation, '', normalized(content),
                (('table', 'snapshots'), ('id', sid)),
            ))
        rows = conn.execute("""SELECT sp.snapshot_id, sp.external_key, sp.full_name
                               FROM snapshot_people sp JOIN snapshots s ON s.id=sp.snapshot_id
                               WHERE s.status='COMPLETE' ORDER BY sp.snapshot_id, sp.external_key""")
        for sid, key, name in rows:
            header = headers[sid]
            identity = json.dumps([sid, key], separators=(',', ':'))
            content = f"Membership observation: {name}. Relation {header['relation_type']}. Snapshot captured {header['captured_at']}."
            documents.append(Document(
                stable_id('membership', sid, key), 'membership', identity, sid, header['captured_at'],
                header['capture_precision'], header['relation_type'], key, normalized(content),
                (('table', 'snapshot_people'), ('snapshot_id', sid), ('external_key', key)),
            ))
        rows = conn.execute("""SELECT e.from_snapshot_id,e.to_snapshot_id,e.projection_snapshot_id,
                                      e.external_key,e.event_type,sp.full_name
                               FROM snapshot_events e
                               JOIN snapshots a ON a.id=e.from_snapshot_id
                               JOIN snapshots b ON b.id=e.to_snapshot_id
                               JOIN snapshot_people sp ON sp.snapshot_id=e.projection_snapshot_id AND sp.external_key=e.external_key
                               WHERE a.status='COMPLETE' AND b.status='COMPLETE'
                                 AND a.relation_type=b.relation_type
                               ORDER BY e.from_snapshot_id,e.to_snapshot_id,e.external_key,e.event_type""")
        for before, after, projection, key, event_type, name in rows:
            header = headers[after]
            identity = json.dumps([before, after, event_type, key], separators=(',', ':'))
            action = event_type.rsplit('_', 1)[-1]
            content = (f"Timeline change: {name} {header['relation_type']} {action}. "
                       f"Observed between {headers[before]['captured_at']} and {header['captured_at']}. "
                       'This is an observation interval, not the exact time or reason of a social action.')
            documents.append(Document(
                stable_id('event', before, after, event_type, key), 'event', identity, after,
                header['captured_at'], header['capture_precision'], header['relation_type'], key,
                normalized(content), (('table', 'snapshot_events'), ('from_snapshot_id', before),
                ('to_snapshot_id', after), ('event_type', event_type), ('external_key', key),
                ('projection_snapshot_id', projection)),
            ))
    finally:
        conn.execute('RELEASE rag_corpus_read')
    return tuple(sorted(documents, key=lambda document: document.document_id))
