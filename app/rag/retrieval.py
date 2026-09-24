"""Deterministic BM25 with conservative conjunctive evidence eligibility. No embeddings."""
from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json
import math
import re
import unicodedata

from .models import Document, Filters, Hit, RAGValidationError, validate_query

STOP = frozenset('a an the what who when which is was were are did does do at in on of to for about show tell me and or и кто что когда в на о об у был была были для покажи'.split())
ALIASES = {word: canonical for canonical, words in {
    'friend': 'friend friends друг друзья друзей',
    'follower': 'follower followers подписчик подписчики подписчиков',
    'added': 'added addition добавлен добавился добавилась',
    'removed': 'removed removal удален удалился удалилась',
    'snapshot': 'snapshot snapshots снимок снимки снимка',
    'empty': 'empty пустой пустые',
    'change': 'change changes изменение изменения',
}.items() for word in words.split()}


def tokens(text: str) -> tuple[str, ...]:
    words = re.findall(r'[^\W_]+', unicodedata.normalize('NFKC', text).casefold(), re.UNICODE)
    return tuple(ALIASES.get(word, word) for word in words if word not in STOP)


class LexicalIndex:
    """Replace/rebuild derived state atomically; sorted IDs settle score ties."""
    def __init__(self, documents=()):
        self.rebuild(documents)

    def rebuild(self, documents) -> None:
        unique = {}
        for document in documents:
            if document.document_id in unique and unique[document.document_id] != document:
                raise RAGValidationError('Conflicting RAG source identity')
            unique[document.document_id] = document
        ordered = tuple(unique[key] for key in sorted(unique))
        frequencies = {doc.document_id: Counter(tokens(doc.content)) for doc in ordered}
        postings = defaultdict(set)
        for key, words in frequencies.items():
            for word in words:
                postings[word].add(key)
        self.documents = ordered
        self._by_id = unique
        self._frequencies = frequencies
        self._postings = dict(postings)
        self._lengths = {key: sum(words.values()) for key, words in frequencies.items()}
        self._average = sum(self._lengths.values()) / len(ordered) if ordered else 1
        version = [(doc.document_id, doc.content, doc.metadata()) for doc in ordered]
        self.version = hashlib.sha256(json.dumps(version, ensure_ascii=False, sort_keys=True).encode('utf-8')).hexdigest()

    def retrieve(self, query: str, *, top_k: int = 3, filters: Filters | None = None) -> tuple[Hit, ...]:
        return self._search(query, top_k, filters, baseline=False)

    def baseline(self, query: str, *, top_k: int = 3, filters: Filters | None = None) -> tuple[Hit, ...]:
        """Comparison: same tokenizer/eligibility/filters, raw term-frequency ranking."""
        return self._search(query, top_k, filters, baseline=True)

    def _search(self, query, top_k, filters, baseline):
        validate_query(query, top_k)
        if filters is not None and not isinstance(filters, Filters):
            raise RAGValidationError('RAG filters must be typed metadata filters')
        terms = set(tokens(query))
        if not terms:
            return ()
        # Every informative query token must appear in a fact. This deliberately
        # abstains on unsupported questions rather than matching a common name alone.
        candidates = set.intersection(*(set(self._postings.get(term, ())) for term in sorted(terms)))
        hits = []
        for key in sorted(candidates):
            document = self._by_id[key]
            if filters and not filters.matches(document):
                continue
            score = 0.0
            for term in sorted(terms):
                frequency = self._frequencies[key][term]
                if baseline:
                    score += frequency
                else:
                    df, n = len(self._postings[term]), len(self.documents)
                    idf = math.log(1 + (n - df + 0.5) / (df + 0.5))
                    denominator = frequency + 1.2 * (1 - 0.75 + 0.75 * self._lengths[key] / self._average)
                    score += idf * frequency * 2.2 / denominator
            hits.append(Hit(document, score))
        return tuple(sorted(hits, key=lambda hit: (-hit.score, hit.document.document_id))[:top_k])
