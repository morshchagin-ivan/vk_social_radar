# U08 — Local RAG evaluation

2026-09-24 · **STRUCTURED_RAG—LEXICAL** · deterministic offline retrieval and FakeLLM mechanics. No live model judge, model download or network.

## Reproduction

Canonical acceptance: `python scripts/run_quality_gates.py`. Focused diagnostic run: `python -B -m unittest discover -s tests -p test_rag.py -v`. Both use the existing prepared environment. [Evaluation code](../../app/rag/evaluation.py), [tests](../../tests/test_rag.py), [fixture](../../tests/fixtures/rag_eval.jsonl), [source seeder](../../tests/rag_support.py).

The seeder writes synthetic records through the real snapshot import service into a temporary v2 SQLite database. Five COMPLETE captures (A–E), plus one excluded incomplete capture (F), produce **19 documents: 5 snapshot headers, 8 memberships and 6 timeline events**. Dates are in 2099, names have the Synthetic prefix, IDs are fixed synthetic UUIDs/namespaced keys, links use example.invalid. No real accounts, messages or user database are used. A/B are same-day friend captures; C is explicitly empty; D is an independent follower capture; E includes an injection-like synthetic name.

## Labels and coverage

Every JSONL record declares case_id, synthetic flag, query, literal relevant_document_ids, filters, answerable and expected_evidence_facts. Labels are committed independently of retrieval results; tests resolve IDs against persisted sources and check expected fact snippets. The malicious string deliberately contains an instruction, delimiter and invalid link, with no real credential. Fixture checks and the tracked privacy scanner include JSONL.

| Case | Query purpose | Expected source / scope |
|---|---|---|
| 01 | Exact Alpha lookup | membership in A |
| 02 | Historical Beta lookup | frozen membership in A |
| 03 | Same-day Gamma lookup | membership in B only |
| 04 | Beta removal | A→B event |
| 05 | Alpha removal into empty state | B→C event |
| 06 | Explicit empty capture | C header, count zero |
| 07 | Follower lookup | Delta in D |
| 08 | Ambiguous Alpha | all three matching memberships, K=3 |
| 09 | Person/relation filter | Alpha friend memberships A/B |
| 10 | Timeline addition | Gamma A→B event |
| 11 | Injection-like evidence | synthetic Inject membership |
| 12 | Russian alias lookup | Gamma addition event |
| 13 | Private message history | unanswerable; messages not stored in corpus |
| 14 | Unsupported phone attribute | unanswerable despite known name |
| 15 | Incomplete capture | unanswerable; unpublished source excluded |
| 16 | Wrong historical snapshot | unanswerable within requested A scope |
| 17 | Wrong relation | unanswerable within friend scope |
| 18 | Snapshot count/date | A header with declared count two |

This is a deliberately small certification regression set, not a held-out natural-language benchmark. Query wording aligns with structured facts; one bilingual alias example is not broad Russian-language coverage. Both rankers require every informative query token in one fact; unknown terms can cause false abstention, while lexical overlap alone can still retrieve semantically irrelevant facts. No general conversational answerability claim follows from these cases.

## Metrics, thresholds and measured result

Recall@K is macro-average `|relevant ∩ retrieved[:K]| / |relevant|` across answerable cases. MRR is the mean reciprocal rank of the first relevant hit (zero when absent) on the same cases. No-evidence accuracy is the fraction of unanswerable queries returning zero hits. It is not answer factuality or precision. K=3 is fixed for certification; score ties use stable ID.

| Retriever | Cases / answerable / unanswerable | Recall@3 | MRR | No-evidence accuracy |
|---|---|---|---|---|
| Raw term-frequency baseline | 18 / 13 / 5 | 1.000 | 1.000 | 1.000 |
| BM25, k1=1.2, b=0.75 | 18 / 13 / 5 | 1.000 | 1.000 | 1.000 |
| Mandatory minimum | same fixture | 0.900 | 0.900 | 1.000 |

Threshold rationale: lookup/history regression should retain high relevance while allowing a small aggregate ranking margin; the five explicit unsupported cases must all abstain to protect no-evidence behavior. On this set one wholly missed positive can pass the 0.90 macro floor, two cannot. Thresholds are certification criteria for this fixture, not production SLOs. `enforce_thresholds` fails below the floors; hand-computed reciprocal-rank and negative threshold tests guard the evaluator. No statistical significance or BM25 quality improvement is claimed: both rankers score equally on all reported metrics. Comparison shares tokenization, eligibility and filters, isolating ranking alone.

## Grounding mechanics

FakeLLM records the exact provider request and returns controlled structured JSON. Tests verify only selected evidence is supplied; correct IDs are accepted; invented or real-but-nonretrieved IDs fail; empty evidence makes zero discovery/generation calls; count/character budgets and source dedupe hold; malformed fields/status/citations fail; model abstention stays empty. Injection-like text stays in the user evidence data, never in the system instructions, and no subprocess/link execution occurs. This does **not** measure live model obedience, prose quality, entailment or hallucination rate. Provider-normalized failures propagate without RAG payload logging.

## Performance sanity

Observed in the first complete U08 canonical run on local Windows, Python 3.13.2 / Node 22.14.0: **5,000 synthetic short fact documents; index build 47.408 ms; median retrieval 0.011 ms over 25 repetitions of one selective query**. Corpus construction for this microbenchmark occurs before timing; measurements cover LexicalIndex construction and selective term retrieval, not DB ingestion, inference or end-to-end latency. Documents share a template with distinct synthetic item tokens; broad/common-token workloads and large user corpora are not benchmarked. No timing assertion or SLA. Later runs print their own timings; this single-machine sample is not a hardware-normalized comparison.

## Limits and next evidence

Embeddings/vector index/hybrid/RRF/reranker: **NO**. No raw message corpus, mutable profile enrichment or ai_insights recursion. No API/UI chat, persistent answer store, automatic index refresh or semantic citation verification. Before U17 ranking changes, expand independent labelled queries with paraphrases, harder distractors, cross-fact questions and broad retrieval workloads. Keep current fixture as regression evidence and compare new methods against this baseline. [Architecture and privacy decisions](U08_LOCAL_RAG_REPORT.md).
