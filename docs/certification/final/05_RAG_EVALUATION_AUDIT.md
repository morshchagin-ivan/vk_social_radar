# Independent U08 RAG evaluation audit

Evidence scope: full certification audit at U08 (4ff2e09fe97e846d74c00977e3bb90a01ebfeb77), followed by focused post-U13A delta verification at 53a35014e75bedc4e69691d38f39c4752cd4bd68. Unchanged architecture findings and independent U08 probes are carried forward; the full canonical suite was rerun. This is not a full-from-zero re-audit.

HEAD `53a35014e75bedc4e69691d38f39c4752cd4bd68`. **Maturity: STRUCTURED_RAG—LEXICAL.** Evaluation mechanics: **PASS WITH WARNING**. No live VK/model/network, embeddings, vector service, hybrid fusion or reranker. The U08 full audit independently recomputed metrics and candidate sets. The U13A diff changes no RAG code/corpus/evaluator/fixture; the fresh delta gate reran all 31 RAG tests and the production evaluator. The candidate-set analysis below is carried-forward independent U08 evidence, not a newly repeated independent arithmetic audit.

## Pipeline verified from code and wiring

| Stage | Verified implementation | Executable evidence |
|---|---|---|
| Persisted sources | build_corpus SELECTs v2 COMPLETE headers, frozen snapshot_people and compatible persisted snapshot_events within a savepoint | Actual source service seeds temp DB; no mutable people join for names; source dump unchanged |
| Documents/chunks | Frozen Document, canonical SHA-256 source identities; one short fact/one stable chunk | Stable order/replay/provenance tests; pair identity survives event row-ID recreation |
| Index lifecycle | LexicalIndex.rebuild replaces RAM postings/frequencies/documents/fingerprint; conflicting duplicate IDs fail | Rebuild/idempotency/conflict and obsolete backdated edge removal tests |
| Retrieval | Unicode NFKC/casefold, explicit stopwords/aliases, all informative query tokens required; BM25 k1=1.2/b=.75 | Relevant top-k, historical/source/person/date filters, tie and bounds tests |
| Context | Ranked whole facts; source dedupe, finite positive scores, evidence count and JSON character budget | Fake request inspection/budget/oversize bypass tests |
| Service/provider | get_rag_service readonly composition → RAGService(Retriever, LLMProvider); shared local provider | Port AST/fake substitution and factory tests; no endpoint is implied |
| Grounded result | Strict fields/status/types/size; unique citation IDs restricted to supplied context | Known/nonretrieved/invented citations, malformed JSON and provider abstention tests |
| No evidence | INSUFFICIENT_EVIDENCE + empty answer/IDs/evidence before discovery/generation | Zero model-list and generation calls; all five unsupported evaluation cases also checked |
| Injection | Evidence/question as JSON untrusted data, system guidance, no code/link execution | Synthetic malicious name; FakeLLM mechanics only, no immunity guarantee |
| Compatibility | Separate Person Insight remains fixed-context | test_person_insight_regression + U05/U09 suite PASS |

Code: [corpus](../../../app/rag/corpus.py), [models](../../../app/rag/models.py), [retrieval](../../../app/rag/retrieval.py), [service](../../../app/rag/service.py), [composition](../../../app/ai/composition.py). Tests: [test_rag.py](../../../tests/test_rag.py).

The index is derived, local and nonpersistent. A service's corpus reflects its construction time; no automatic refresh or incremental synchronization is implemented. Context is bounded in characters, not model tokens. A skipped oversized fact can cause abstention. Event timestamps represent observed intervals, not exact social-action times or causes. No source deletion/retention lifecycle is invented.

## Dataset and label independence

[Fixture](../../../tests/fixtures/rag_eval.jsonl): **18 cases**, **13 answerable**, **5 unanswerable**. [Seeder](../../../tests/rag_support.py) uses real snapshot import persistence on temporary SQLite. Corpus: **19 documents = 5 headers + 8 memberships + 6 events**. One incomplete capture is excluded. Dates/UUIDs/person keys/names are synthetic; URLs use example.invalid in fixtures. No real message/account dump is used. JSONL is included in the tracked secret guard.

Each case has committed literal expected document IDs, query, filter, answerable flag and evidence snippets. Retrieval imports neither fixture nor relevance labels; rankers see only query/filter and the persisted corpus. Labels resolve to stable source identities and expected facts. Therefore no runtime ground-truth leakage into retrieval was found. Label authorship is not an independent held-out study: fixture and implementation were developed together, with query wording closely matching facts.

There are **zero duplicate query+filter cases**, but **one repeated positive relevance set**: the Gamma timeline addition and Russian alias variant target the same event. That is legitimate alias coverage, not a second independent relevance challenge. Claims of 18 independent natural-language problems would overstate the set.

## Independent metric recomputation

The U08 full audit directly called index.retrieve/index.baseline with K=3, then computed intersections and reciprocal ranks in a separate loop without calling app.rag.evaluation.evaluate or enforce_thresholds. It also independently scanned tokenized documents and filters to enumerate eligible candidates.

For answerable query q, Recall@3 = relevant hits in top three divided by all labelled relevant IDs; MRR is mean 1/rank of the first relevant hit, or zero. Both means exclude unanswerable queries. No-evidence accuracy is empty-retrieval fraction over the five unanswerable cases. Production evaluator formulas match these definitions; metric and below-threshold unit tests also pass.

| Ranker | Recall@3 | MRR | No-evidence accuracy | Gate floor / verdict |
|---|---|---|---|---|
| BM25 | 1.000 | 1.000 | 1.000 | ≥.90 / ≥.90 / 1.00 — PASS |
| Raw term-frequency baseline | 1.000 | 1.000 | 1.000 | Comparison; ties BM25 |

The code stores thresholds explicitly as .90/.90/1.0 and fails below them. With 13 positives, one wholly missed positive can pass the aggregate .90 floor; two cannot. All five unsupported cases must return zero hits. These are regression criteria, not production SLOs or confidence estimates.

## Candidate-set audit: the material warning

| Fixture case suffix | Answerable | Eligible candidates | Relevant IDs | Retrieved at K=3 |
|---|---|---|---|---|
| exact-alpha | YES | 1 | 1 | 1 |
| historical-beta | YES | 1 | 1 | 1 |
| same-day-gamma | YES | 1 | 1 | 1 |
| historical-removal | YES | 1 | 1 | 1 |
| empty-state-change | YES | 1 | 1 | 1 |
| explicit-empty | YES | 1 | 1 | 1 |
| follower | YES | 1 | 1 | 1 |
| ambiguous-history | YES | 3 | 3 | 3 |
| person-filter | YES | 2 | 2 | 2 |
| timeline-added | YES | 1 | 1 | 1 |
| untrusted-name | YES | 1 | 1 | 1 |
| russian-alias | YES | 1 | 1 | 1 |
| no-message-history | NO | 0 | 0 | 0 |
| unsupported-attribute | NO | 0 | 0 | 0 |
| incomplete-excluded | NO | 0 | 0 | 0 |
| source-isolation | NO | 0 | 0 | 0 |
| relation-isolation | NO | 0 | 0 | 0 |
| snapshot-count | YES | 1 | 1 | 1 |

**Every eligible candidate set equals the labelled relevant set.** Eleven positives have one candidate; the other two have at most K, all relevant. No case contains an eligible irrelevant distractor. Any ordering of these candidates yields the reported perfect Recall@3/MRR. Consequently the fixture demonstrates token eligibility, filters, source isolation and abstention mechanics; it cannot detect poor BM25 ordering or prove BM25 improves over a simpler ranker. This is **P2-02**, not evidence that metrics were arithmetically fabricated. The implementation/report honestly claims a baseline tie and small-set limitations, so bounded U08 acceptance passes with warning.

Conjunctive matching can abstain on unsupported words, paraphrases or questions requiring evidence across records, and lexical overlap can still admit irrelevant meaning. No broad Russian-language, semantic or conversational quality claim is justified. Future U17 evaluation should add eligible distractors, more than K relevant candidates, held-out paraphrases, multi-fact questions and independently curated judgements before comparing ranking changes. No dataset was modified here.

## Grounding, security and prose limits

FakeLLM checks exactly which evidence reaches the provider, accepts valid IDs, rejects invented or real-but-nonretrieved IDs, verifies structured output and bypasses provider calls for unsupported cases. Inferences are separately labelled but not semantically verified. A returned allowed ID may still accompany an incorrect assertion; natural-language inline references are not independently validated. GROUNDED is a structural status, not a truth/causality guarantee.

The malicious synthetic source contains instructions, a delimiter and an invalid link. Test evidence establishes placement in data, unchanged system instructions and no execution. It cannot establish that a live model ignores it. No RAG content logging, browser/session corpus, cloud embeddings, persisted index or new network path was found. Existing U06 provider locality and U09 shared resilience are reused.

## Performance and reproduction

Fresh canonical run: **5000 synthetic short facts; index build 52.283 ms; median retrieval 0.011 ms** over 25 repetitions of one selective query. This times in-memory index build and selective lookup, not DB ingestion, broad queries, model latency or end-to-end throughput. No timing assertion/SLA/hardware-generalization claim. Full gate took 14.309 seconds.

```powershell
python scripts/run_quality_gates.py
python -B -m unittest discover -s tests -p test_rag.py -v
```

The second command is focused diagnostics and includes the production evaluator, FakeLLM tests and performance output. The carried-forward U08 independent audit arithmetic reproduced 1.0/1.0/1.0 outside that evaluator and enumerated candidate sets as above. Supplemental probes do not increase the authoritative 240-test count. No live model or user DB is required.
