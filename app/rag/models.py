from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Protocol


class RAGValidationError(ValueError):
    """Safe input/output validation category, without query or provider payloads."""


def stable_id(source_type: str, *identity: str) -> str:
    encoded = json.dumps([source_type, *identity], ensure_ascii=False, separators=(',', ':'))
    return f'rag:v1:{source_type}:' + hashlib.sha256(encoded.encode('utf-8')).hexdigest()


def validate_query(query: str, top_k: int) -> None:
    if not isinstance(query, str) or not query.strip() or len(query) > 1000:
        raise RAGValidationError('RAG query must contain 1 to 1000 characters')
    if type(top_k) is not int or not 1 <= top_k <= 10:
        raise RAGValidationError('RAG top_k must be between 1 and 10')


@dataclass(frozen=True)
class Document:
    document_id: str
    source_type: str
    source_id: str
    snapshot_id: str
    captured_at: str
    capture_precision: str
    relation_type: str
    person_key: str
    content: str
    provenance: tuple[tuple[str, str], ...]

    @property
    def chunk_id(self) -> str:
        # Short structured facts are atomic evidence, never arbitrary token slices.
        return self.document_id + ':chunk:0'

    def metadata(self) -> dict:
        return {key: getattr(self, key) for key in (
            'document_id', 'chunk_id', 'source_type', 'source_id', 'snapshot_id',
            'captured_at', 'capture_precision', 'relation_type', 'person_key',
        )} | {'provenance': dict(self.provenance)}


@dataclass(frozen=True)
class Filters:
    source_type: str | None = None
    snapshot_id: str | None = None
    person_key: str | None = None
    relation_type: str | None = None
    captured_date: str | None = None

    def __post_init__(self):
        from datetime import date
        if self.source_type not in (None, 'snapshot', 'membership', 'event'):
            raise RAGValidationError('Invalid RAG source filter')
        if self.relation_type not in (None, 'friend', 'follower'):
            raise RAGValidationError('Invalid RAG relation filter')
        for value in (self.snapshot_id, self.person_key):
            if value is not None and (not isinstance(value, str) or not value or len(value) > 200):
                raise RAGValidationError('Invalid RAG identity filter')
        if self.captured_date is not None:
            try:
                if date.fromisoformat(self.captured_date).isoformat() != self.captured_date:
                    raise ValueError
            except (TypeError, ValueError):
                raise RAGValidationError('Invalid RAG date filter') from None

    def matches(self, document: Document) -> bool:
        return all(value is None or getattr(document, key) == value for key, value in (
            ('source_type', self.source_type), ('snapshot_id', self.snapshot_id),
            ('person_key', self.person_key), ('relation_type', self.relation_type),
        )) and (self.captured_date is None or document.captured_at[:10] == self.captured_date)


@dataclass(frozen=True)
class Hit:
    document: Document
    score: float

    def as_dict(self) -> dict:
        return {**self.document.metadata(), 'score': self.score, 'evidence': self.document.content}


class Retriever(Protocol):
    def retrieve(self, query: str, *, top_k: int = 3, filters: Filters | None = None) -> tuple[Hit, ...]: ...


@dataclass(frozen=True)
class Answer:
    status: str
    answer: str
    evidence_ids: tuple[str, ...]
    evidence: tuple[Hit, ...]
    inferences: tuple[str, ...] = ()

    def as_dict(self) -> dict:
        return {'status': self.status, 'answer': self.answer,
                'evidence_ids': list(self.evidence_ids),
                'evidence': [hit.as_dict() for hit in self.evidence],
                'inferences': list(self.inferences)}
