"""Offline retrieval metrics, not an LLM/prose evaluator."""
from __future__ import annotations

from .models import Filters, RAGValidationError

THRESHOLDS = {'recall_at_k': 0.90, 'mrr': 0.90, 'no_evidence_accuracy': 1.0}


def evaluate(retrieve, cases: list[dict], *, k: int = 3) -> dict:
    recalls, ranks, abstentions = [], [], []
    for case in cases:
        expected = set(case['relevant_document_ids'])
        if bool(expected) != case['answerable']:
            raise RAGValidationError('Invalid evaluation relevance labels')
        hits = retrieve(case['query'], top_k=k, filters=Filters(**case.get('filters', {})))
        found = [hit.document.document_id for hit in hits]
        if expected:
            recalls.append(len(expected.intersection(found)) / len(expected))
            ranks.append(next((1 / rank for rank, key in enumerate(found, 1) if key in expected), 0.0))
        else:
            abstentions.append(float(not found))
    if not recalls or not abstentions:
        raise RAGValidationError('Evaluation requires answerable and unanswerable cases')
    return {'cases': len(cases), 'k': k, 'answerable': len(recalls), 'unanswerable': len(abstentions),
            'recall_at_k': sum(recalls) / len(recalls), 'mrr': sum(ranks) / len(ranks),
            'no_evidence_accuracy': sum(abstentions) / len(abstentions)}


def enforce_thresholds(metrics: dict) -> None:
    if any(not metrics.get(key, -1) >= threshold for key, threshold in THRESHOLDS.items()):
        raise RAGValidationError('RAG retrieval evaluation below certification thresholds')
