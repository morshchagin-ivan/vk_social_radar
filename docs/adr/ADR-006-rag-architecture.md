# ADR-006 — Local RAG Architecture

**Status:** ACCEPTED. **Implementation:** IMPLEMENTED — **STRUCTURED_RAG—LEXICAL**, internal service only. **Updated:** 2026-09-24 (U08).
**Decision owners:** VK Social Radar owner and architecture maintainer (roles).
**Related backlog:** [U08 completed; U17 retrieval evolution](../certification/05_UPGRADE_BACKLOG.md).

## Context

FR-8/FR-9 describe local AI over stored history. Before U08, Person Insight used fixed context and runtime was NO_RAG. U03 supplies immutable COMPLETE friend/follower snapshots, frozen person projections and derived pair events. Message aggregates are mutable and not snapshot-scoped; actual message text is unavailable. Current dependencies/repository assets contain no ready local embedding runtime/model suitable for offline CI.

## Decision

Implement a separate [RAGService](../../app/rag/service.py) over Retriever and LLMProvider ports, composed in [get_rag_service](../../app/ai/composition.py). Preserve Person Insight and existing API/UI. Service-only delivery avoids introducing chat sessions or an unevaluated product surface; no RAG endpoint is added.

[CorpusBuilder](../../app/rag/corpus.py) reads existing v2 COMPLETE headers, immutable memberships and compatible persisted timeline edges. Each short structured fact is one document/chunk. SHA-256 IDs derive from stable source keys, not position or mutable event row IDs. Provenance includes table and source identities; names remain untrusted evidence. No mutable profiles, legacy unknown events, messages, ai_insights, browser/session data or raw source references enter the corpus.

[LexicalIndex](../../app/rag/retrieval.py) is a rebuildable in-memory inverted index, versioned by a content/metadata fingerprint. Rebuild replaces all derived state, including obsolete edges after backdated insertion. No schema migration, persistent index or model download. Deterministic Unicode tokenization, small explicit English/Russian aliases and conjunctive eligibility precede BM25 ranking. Metadata filters apply before top-k; equal scores sort by document ID. This conservative baseline can miss paraphrases and multi-fact questions.

Context assembly deduplicates source identity and bounds whole serialized facts by count/characters. Empty acceptable context returns INSUFFICIENT_EVIDENCE before any model discovery/generation. Prompts delimit untrusted data, request evidence citations and separate inferences. Local structured validation rejects citations outside supplied context. The existing local-only provider and shared resilience binding remain authoritative.

## Alternatives considered

Fixed context lacks query retrieval. Whole-history prompting lacks a useful budget. Raw term-frequency ranking is an implemented comparison baseline. BM25 scores account for term rarity and document length, but the small synthetic evaluation shows **no improvement over term frequency**. Embeddings, vector storage, hybrid fusion and reranking remain unimplemented until available offline assets and measured benefit justify them. No Advanced RAG claim.

## Consequences and privacy

Stable citations and deterministic evaluation make the bounded source-to-answer mechanics testable. The index is local derived state and a service instance represents its construction-time corpus; callers create a new service after source changes. It is not automatically refreshed or a source of truth. No queries, evidence or answers are logged/persisted by the RAG modules. Safe provenance omits profile URLs and file references, but names and person keys remain personal data in real operation.

Prompt delimiters are guidance, not a security sandbox. Corpus text may influence generated prose. Citation membership validation proves source identity, not entailment, truth or causality; natural-language inline references are not independently verified. FakeLLM tests certify mechanics only. No code/link execution or remote fallback is introduced.

## Validation and evolution

[U08 report](../certification/U08_LOCAL_RAG_REPORT.md), [evaluation](../certification/RAG_EVALUATION.md), [31 tests](../../tests/test_rag.py), [18-case synthetic fixture](../../tests/fixtures/rag_eval.jsonl). Recall@3 and MRR each 1.0 on 13 answerable cases; no-evidence accuracy 1.0 on five unanswerable cases. Thresholds 0.90/0.90/1.0 are enforced by FITNESS-RAG-005. Six RAG fitness invariants join the existing U07 runner.

U17 may expand the held-out corpus/query workload and compare semantic/hybrid retrieval. AI Chat UI/API, durable reports, full message source reproduction and automatic AI pipelines remain planned; U08 does not complete all FR-8/FR-9.
