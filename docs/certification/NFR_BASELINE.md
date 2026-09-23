# NFR Baseline

Baseline 1.0 · 2026-09-23. [Spec Performance](../../spec.md) explicitly leaves quantitative requirements undefined. Legacy [test specifications](../../tests/03_API_TESTS.md) are intended checks, not measured results or an adopted runtime SLO. No load/latency benchmark was executed in this iteration.

## Already guaranteed — narrowly evidenced properties

These are code/configuration properties under the normal launcher, not unconditional operational SLAs:

- [run_server.py](../../run_server.py) binds 127.0.0.1:8765; alternate launch commands can change this.
- [db.py](../../app/db.py) uses local SQLite paths and enables FK on its connections. That does not guarantee immutable snapshots or migration compatibility.
- [lmstudio.py](../../app/lmstudio.py) configures httpx timeout 8.0 s for models and 120.0 s for completions. These are client timeout settings, **not a total use-case deadline or measured latency**.
- [collector.start](../../app/collector.py) uses a separate persistent profile and configures ordinary browser/navigation timeouts 12 000/45 000 ms. Some organization options override navigation timeout; no end-to-end collector deadline is guaranteed.
- Non-AI [services](../../app/services.py) read local SQLite without calling VK or LLM. This is dependency isolation, not proof of availability under every failure.

## Proposed certification NFR — target, not measured

| Category / Metric | Current evidence | Target | Measurement method | Backlog |
|---|---|---|---|---|
| Local privacy: unauthorized external inference transfers | local default, arbitrary endpoint currently accepted | zero disallowed inference requests under agreed local policy; policy tests not yet implemented | fake transport + nonlocal/redirect/address cases, safe packet-level demo later if needed | U06/U05 |
| API latency: p50/p95/p99 on selected reads | no benchmark | TBD — measure during U11; declare hardware, corpus size and concurrency | synthetic DB, fixed read requests, warm/cold separation; exclude collector/inference from short-request class | U11/U07 |
| Collector execution: duration/completeness/error budget | per-operation browser timeouts, scroll bounds; no total SLA | TBD — measure during U11; partial/failed run never presented as complete | offline DOM fixtures/fake clock first; separate authorized live synthetic scenario later | U10/U11/U03 |
| LLM timeout/deadline: total elapsed time/attempts | client settings 8/120 s; no retry/breaker | TBD — measure during U11 before U09; budget includes discovery/retries/backoff | mocked slow models/completions, timeout classes, deterministic clocks/jitter | U05/U09/U11 |
| DB growth: bytes per complete source state and retention | local DB; no growth benchmark | TBD — measure during U11; no invented capacity claim | synthetic N-person/N-run corpus, measure DB/index/backups separately | U03/U11 |
| Recovery: migration failure safety / restore time | no migration/restore mechanism; backups directory only | failed migration preserves pre-upgrade data; restore time TBD — U11 | synthetic old schema, injected failure, verified recovery/restore rehearsal | U02/U11/U15 |
| Data integrity: immutable reads / duplicate operations | known same-day/repeat/empty defects | zero changes to completed source content, idempotent replay, confirmed empty state retained | fixture invariants, repeated/backdated import, partial vs empty scan | U03/U07 |
| Diagnostic retention: sensitive fields / age / size | raw DOM/screenshots, no general retention | safe default payload; age/size TBD — measure during U11; no real private data in CI | sensitive synthetic sentinel fixtures, retention boundaries, artifact inventory | U06/U11 |
| Reproducibility: runner collection / known revision / deterministic fixtures | prior 18 + 8 separate passes; revision unknown; no CI | one documented isolated runner; exact revision/dependency set; deterministic core gate | fresh offline test environment, complete test collection, artifact/version checks | U01/U07 |

Numeric operational targets are deliberately TBD. The zero-error/source-integrity conditions above are **proposed acceptance invariants**, not measurements or claims already achieved. [Security](SECURITY_PRIVACY_STATUS.md), [evolution](ARCHITECTURE_EVOLUTION.md), [backlog](05_UPGRADE_BACKLOG.md).
