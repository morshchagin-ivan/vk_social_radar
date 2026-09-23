# Technical Debt Register

Baseline 1.0 · 2026-09-23. **Defect/debt** = нарушенное текущее свойство/несовместимость; **roadmap gap** = запланированная отсутствующая функция, не runtime defect. Номер Dxx — идентификатор записи этого реестра, не новый requirement. Все resolution — будущая работа из [Uxx backlog](05_UPGRADE_BACKLOG.md).

| Debt ID | Area | Description | Risk | Evidence | Resolution | Backlog | Priority |
|---|---|---|---|---|---|---|---|
| D01 | DB migration, defect | installed dialogs 6 columns vs DDL 13 | metadata INSERT incompatible | [audit schema](01_ARCHITECTURE_INVENTORY.md), [db.init_db](../../app/db.py) | versioned old→new migration, preservation/rollback tests | U02 | P0 |
| D02 | Snapshot semantics, defect | same-day stale members; duplicate events; empty state lost | false analytics/history | [audit probes](03_SDD_CODE_GAP_ANALYSIS.md), [import_snapshot](../../app/services.py) | aggregate/invariants and regression tests | U03 | P0 |
| D03 | API documentation debt | YAML target ≠ runtime prefix/routes/security/schemas | consumers cannot rely on contract | [API_STATUS](API_STATUS.md) | reconcile typed contract/error/auth, compatibility gate | U04 | P0 |
| D04 | Provider roadmap gap | concrete LM HTTP exists, abstraction absent | vendor/test coupling; false architectural claim if unlabelled | [LLM verdict](02_PATTERN_INVENTORY.md) | port + adapter + selection + output validation | U05 | P0 for accepted target |
| D05 | RAG roadmap gap | no index/query retrieval/citations | planned Q&A unavailable | [ADR-006](../adr/ADR-006-rag-architecture.md) | minimal evaluated local retrieval | U08 | P0 for accepted target |
| D06 | Privacy diagnostics debt | raw DOM/PNG/URL, incomplete sanitization | personal/session-bearing data in artifacts | [collector._save_diagnostics](../../app/collector.py) | minimize/redact/retain safely; synthetic log tests | U06/U11 | P0 |
| D07 | Git evidence gap | no Git metadata | tracked/history/package safety unknown | [audit 00](00_REPOSITORY_AS_IS.md); baseline git probes | inspect actual checkout/index/history without printing secrets | U01/U06 | P0 |
| D08 | Runner/coverage debt | bat collects 18 unittest, omits 8 plain functions | misleading green gate | [run_tests.bat](../../run_tests.bat), [v043](../../tests/test_v043_organization_source.py) | unified collection and isolated filesystem, behavioral tests | U07 | P0 |
| D09 | NFR evidence gap | no adopted measured quantitative baseline | no bounded performance/recovery claim | [spec Performance](../../spec.md), [NFR](NFR_BASELINE.md) | define workload/hardware/targets and measure | U11 | P1 |
| D10 | Collector coupling debt | large class owns browser/state/parsing/policies | DOM change impact; no replaceable strategy | [collector.collect](../../app/collector.py) | narrow parser interface/fixtures; no framework rewrite | U10 | P1 |
| D11 | SQL coupling debt | services/client/importers directly execute SQL | business logic knows physical schema | [services](../../app/services.py), [lmstudio](../../app/lmstudio.py) | selected persistence ports/SQLite adapter contracts | U12 | P1 |
| D12 | Demo isolation debt | startup seeds empty people table | demo vs user provenance confusion | [main.startup](../../app/main.py), [seed](../../app/seed.py) | explicit demo mode, tests | U13 | P1 |
| D13 | Identity/validation debt | modulo screen_name surrogate; loose dict/ZIP validation | collision, malformed records/resource consumption | [services.import_snapshot](../../app/services.py), [importers](../../app/importers.py) | namespace identity, typed validation, expanded ZIP budget | U13 | P1 |
| D14 | Local policy debt | arbitrary LLM URL; whitelist exception fail-open | privacy invariant unenforced | [lmstudio._base_url](../../app/lmstudio.py), [collector._route_request](../../app/collector.py) | endpoint policy/fail-closed negative tests | U06 | P0 |
| D15 | LLM resilience gap | timeouts only, no retry/breaker | repeated long failures | [pattern audit](02_PATTERN_INVENTORY.md) | bounded deadline/retry and breaker subject to accepted NFR | U09/U11 | P1 |
| D16 | Organization save contract debt | org preview differs from generic save schema | save-preview rejects this kind | [save_collector_preview](../../app/services.py), organization result | declare preview-only or separate validated persistence | U13 | P1 |
| D17 | Graph/Export/Scheduler roadmap | no respective runtime service | future scope unavailable, not a defect in limited MVP | [status](ARCHITECTURE_STATUS.md) | only scoped increments, no implied completion | U14/U15/U16 | P2 |

Banner/ADR/status pages close the misleading-presentation part of documentation debt, **not** D01–D17 implementation/evidence gaps. U01 documentary work is complete within this iteration; revision proof still open. Old audit remains unchanged.
