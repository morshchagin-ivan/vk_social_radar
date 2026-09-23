# NFR Baseline

Baseline 1.0 + U02/U05/U09 · 2026-09-23. [Spec Performance](../../spec.md) explicitly leaves quantitative requirements undefined. Legacy [test specifications](../../tests/03_API_TESTS.md) are intended checks, not measured results or an adopted runtime SLO. No load/latency benchmark was executed in this iteration. U09 internal policy values are tested bounds, not measured operational targets.

## Already guaranteed — narrowly evidenced properties

These are code/configuration properties under the normal launcher, not unconditional operational SLAs:

- [run_server.py](../../run_server.py) binds 127.0.0.1:8765; alternate launch commands can change this.
- [db.py](../../app/db.py) uses local SQLite paths and enables FK on its connections. [U02](U02_SCHEMA_MIGRATION_REPORT.md) proves supported schema migration/backup/rollback on synthetic databases, not immutable snapshots or arbitrary schema compatibility.
- [LMStudioProvider](../../app/ai/providers/lmstudio.py) configures httpx timeout 8.0 s for models and 120.0 s for completions. These are client timeout settings, **not a total use-case deadline or measured latency**.
- [U09 wrapper](../../app/ai/resilience.py) permits at most 3 generation attempts per CLOSED logical call. Full-jitter sleep ceilings are 0.5 + 1.0 = **1.5 s**; general bound is sum(min(max_delay, base_delay × 2^k)), k=0…N−2. HALF_OPEN permits one attempt and zero retry sleep; OPEN rejects generation without underlying calls.
- Three exhausted transient logical operations open the circuit; recovery eligibility starts after 30 s on a monotonic clock. Lock protects state and single probe admission; this is a per-process gate, not a distributed guarantee. Models/health are single-call and do not affect generation state.
- [collector.start](../../app/collector.py) uses a separate persistent profile and configures ordinary browser/navigation timeouts 12 000/45 000 ms. Some organization options override navigation timeout; no end-to-end collector deadline is guaranteed.
- Non-AI [services](../../app/services.py) read local SQLite without calling VK or LLM. This is dependency isolation, not proof of availability under every failure.

## Proposed certification NFR — target, not measured

| Category / Metric | Current evidence | Target | Measurement method | Backlog |
|---|---|---|---|---|
| Local privacy: unauthorized external inference transfers | local default, arbitrary endpoint currently accepted | zero disallowed inference requests under agreed local policy; policy tests not yet implemented | fake transport + nonlocal/redirect/address cases, safe packet-level demo later if needed | U06/U05 |
| API latency: p50/p95/p99 on selected reads | no benchmark | TBD — measure during U11; declare hardware, corpus size and concurrency | synthetic DB, fixed read requests, warm/cold separation; exclude collector/inference from short-request class | U11/U07 |
| Collector execution: duration/completeness/error budget | per-operation browser timeouts, scroll bounds; no total SLA | TBD — measure during U11; partial/failed run never presented as complete | offline DOM fixtures/fake clock first; separate authorized live synthetic scenario later | U10/U11/U03 |
| LLM timeout/deadline: total elapsed time/attempts | U09: max 3 attempts, 1.5s retry sleep; 8/120s HTTP timeouts; no enforced total deadline | U11 measure/tune and decide real total deadline; include discovery and in-flight work | [25 deterministic behavior/API tests](../../tests/test_llm_resilience.py); future synthetic workload benchmark | U09 IMPLEMENTED / U11 planned |
| DB growth: bytes per complete source state and retention | local DB; no growth benchmark | TBD — measure during U11; no invented capacity claim | synthetic N-person/N-run corpus, measure DB/index/backups separately | U03/U11 |
| Recovery: migration failure safety / restore time | U02 backup/transaction rollback and failure tests PASS; no measured restore time | restore time TBD — U11; restore workflow remains separate | synthetic old schema and injected failures already tested; future restore rehearsal | U02 IMPLEMENTED / U11/U15 planned |
| Data integrity: immutable reads / duplicate operations | known same-day/repeat/empty defects | zero changes to completed source content, idempotent replay, confirmed empty state retained | fixture invariants, repeated/backdated import, partial vs empty scan | U03/U07 |
| Diagnostic retention: sensitive fields / age / size | raw DOM/screenshots, no general retention | safe default payload; age/size TBD — measure during U11; no real private data in CI | sensitive synthetic sentinel fixtures, retention boundaries, artifact inventory | U06/U11 |
| Reproducibility: runner collection / known revision / deterministic fixtures | U09: 83 unittest + 8 separate functions PASS; known U05 start SHA; no CI | one documented isolated runner; exact revision/dependency set; deterministic core gate | temp DB/fake transport/clock/sleeper/random; [commands and provenance](U09_LLM_RESILIENCE_REPORT.md) | U07 planned |

Timeout implications: the scalar calculation 3 × 120 + 1.5 = **361.5 s** assumes every attempt lasts at most 120 s, which httpx's per-phase/inactivity timeouts do NOT guarantee. Automatic model discovery adds one 8 s timeout setting (scalar illustration 369.5 s). Neither value is a hard elapsed-time upper bound. Calls already admitted before another call opens the circuit may finish their bounded retry loops. Retries can repeat server inference after a client timeout; no exactly-once inference claim is made.

Numeric operational targets remain TBD. The source-integrity conditions above are **proposed acceptance invariants**, not claims already achieved. Tested U02/U09 properties are identified separately. [Security](SECURITY_PRIVACY_STATUS.md), [evolution](ARCHITECTURE_EVOLUTION.md), [backlog](05_UPGRADE_BACKLOG.md).
