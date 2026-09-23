# ADR-006 — Local RAG Architecture

**Status:** ACCEPTED / IMPLEMENTATION PLANNED. **Implementation:** PLANNED; runtime **NO_RAG**. **Date:** 2026-09-23.
**Decision owners:** владелец VK Social Radar и architecture maintainer (роли).
**Related backlog:** [U08 RAG; prerequisites U03/U05/U07; evolution U17](../certification/05_UPGRADE_BACKLOG.md).

## Context

[FR-8/FR-9](../../spec.md) описывают локальный AI Pipeline/Chat по сохранённой истории. Сейчас [generate_person_insight](../../app/lmstudio.py) передаёт fixed context последнего периода и до 10 событий. Нет indexing/query retrieval/chunks/citations; strings в evidence не являются проверяемыми source citations.

## Decision

Создать минимальный локальный retrieval pipeline для выбранного report/Q&A scenario: versioned source ingestion, stable chunk/source IDs, index, query-dependent retrieval с scope filtering, context budget, prompt + provider call, проверяемые citations и no-evidence response. Сначала synthetic labelled corpus и evaluation baseline.

Vector DB, dense embeddings, hybrid, RRF и reranker **не обещаются**. Выбор lexical/structured/dense подхода и storage делается по corpus/query evaluation в U08. Уровень RAG классифицируется по реализованному механизму, не по наличию prompt с данными.

## Current implementation status

PLANNED / NO_RAG. Concrete LM Studio call существует; AI Chat отсутствует; ai_insights не equivalent snapshot AIReport. [Pattern audit](../certification/02_PATTERN_INVENTORY.md) фиксирует отсутствие ingestion/index/retrieval/evaluation.

## Alternatives considered

Fixed SQL context (текущий MVP); отправка всей истории в prompt; local lexical/structured retrieval; dense/hybrid stack. Fixed context недостаточен для query relevance; whole-history prompt не даёт управляемого scope/budget. Более сложный retrieval выбирается только после measurable improvement.

## Consequences

- Positive: scoped source evidence, grounded ответы, проверяемая freshness/relevance.
- Negative: index lifecycle, source/citation integrity и evaluation assets нужно поддерживать.
- Risks: stale index, нерелевантный контекст, hallucinated citations, prompt injection через source text; retrieval не гарантирует factuality автоматически.

## Security/Privacy impact

Corpus и inference остаются локальными по ADR-001; user/VK text трактуется как данные, не инструкции. Context minimization, source scope/deletion propagation и safe logging обязательны в target. Не использовать реальные private messages в CI/eval.

## Validation/Evidence

AS-IS: [lmstudio.py](../../app/lmstudio.py), [db.py](../../app/db.py), [audit NO_RAG](../certification/02_PATTERN_INVENTORY.md). Target U08 evidence: labelled relevance queries, source citation validation, insufficient-evidence case, freshness/metadata filter tests, mocked provider. Численные quality targets — [NFR baseline](../certification/NFR_BASELINE.md), TBD during U11/eval design.

## Evolution path

U03 стабильный source → U05 provider → U07 test gate → U08 minimal evaluated retrieval. U17 advanced search/reranking возможен позднее при подтверждённой пользе. Baseline заканчивается документацией и не начинает эту реализацию.
