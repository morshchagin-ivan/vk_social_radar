# Defense evidence map

Evidence scope: full certification audit at U08 (4ff2e09fe97e846d74c00977e3bb90a01ebfeb77), followed by focused post-U13A delta verification at 53a35014e75bedc4e69691d38f39c4752cd4bd68. Unchanged architecture findings and independent U08 probes are carried forward; the full canonical suite was rerun. This is not a full-from-zero re-audit.

HEAD `53a35014e75bedc4e69691d38f39c4752cd4bd68`. Present concrete scope and limits alongside every claim. Strong claims below have code, wiring and freshly executed automated evidence. Existing Markdown scenarios and live-service behavior are not test results.

## Claim → code → test → decision → demonstration

| Strong claim | Exact code file / symbol | Exact executable test evidence | ADR / document | Offline demo |
|---|---|---|---|---|
| Supported legacy DB upgrades preserve rows and take backup before mutation | [migrations.py](../../../app/migrations.py): migrate, backup_database; [db.py](../../../app/db.py): init_db | [test_migrations.py](../../../tests/test_migrations.py): MigrationTests.test_mig_002_legacy_preservation_and_backup; test_mig_003_real_runtime_write_after_migration; test_mig_005_ddl_failure_rolls_back_and_surfaces; test_backup_failure_blocks_all_schema_mutation | [ADR-005](../../adr/ADR-005-sqlite-for-mvp.md), [data consistency](03_ARCHITECTURE_CONSISTENCY_FINAL.md) | Command A |
| v1→v2 retains prior guarantees, fresh/current/future behavior is safe | migrations.detect_schema/validate_schema; snapshot_schema.create_schema/validate_schema | [test_snapshots.py](../../../tests/test_snapshots.py): SnapshotMigrationTests.test_mig_snp_001_v1_v2_preserves_all_data_backup_and_fk; test_mig_snp_002_backup_refusal_and_ddl_rollback; test_mig_snp_005_fresh_v2_and_future_guard | ADR-005 / [U03 report](../U03_IMMUTABLE_SNAPSHOT_REPORT.md) | Command B; independent audit used protected U02 DDL |
| Relation history cannot be overwritten by mutable people | [snapshots.py](../../../app/snapshots.py): create_snapshot/read_snapshot/changes; [snapshot_schema.py](../../../app/snapshot_schema.py): finalized source guards | SnapshotTests.test_snp_002_projection_immutable_and_evt_003_historical_display; test_complete_source_sql_mutations_rejected | [ADR-003](../../adr/ADR-003-immutable-snapshot-source-of-truth.md) | Command B |
| Empty, same-day, replay and backdated histories are well-defined | snapshots.predecessor/_diff/_derive/create_snapshot | SnapshotTests.test_snp_001_same_day_distinct_and_snp_007_tie_order; test_snp_004_empty_complete_and_evt_005_replay; test_evt_004_backdated_rebuilds_only_affected_edges | ADR-003; [final baseline G02](01_BASELINE_TO_FINAL_MATRIX.md) | Command B |
| Incomplete collection cannot replace known COMPLETE truth | snapshots.latest/current_sets; services.save_collector_preview | SnapshotTests.test_snp_005_incomplete_failed_creating_do_not_replace_current; test_preview_friends_followers_unknown_replay_dialogs_unchanged | ADR-003 / [data status](../DATA_MODEL_STATUS.md) | Command B |
| API contract is the actual runtime surface | [main.py](../../../app/main.py), [api_models.py](../../../app/api_models.py), [export_openapi.py](../../../scripts/export_openapi.py): render | [test_api_contract.py](../../../tests/test_api_contract.py): ContractGateTests.test_yaml_subset_parse_export_and_local_refs; test_api_contract_001_routes_enumerated_without_io; test_api_contract_002_all_frontend_calls; test_drift_gate_rejects_route_request_response_security_and_id_mutations | [U04 report](../U04_API_CONTRACT_REPORT.md), [canonical OpenAPI](../../../11_OPENAPI.yaml) | Command C |
| Provider abstraction is a real substitution seam | [provider.py](../../../app/ai/provider.py): LLMProvider; [service.py](../../../app/ai/service.py): AIInsightService; [composition.py](../../../app/ai/composition.py): get_provider/get_insight_service | [test_ai_provider.py](../../../tests/test_ai_provider.py): InsightTests.test_llm_port_001_fake_substitution_and_context_scope; ArchitectureTests.test_llm_port_014_dependency_fitness | [ADR-004](../../adr/ADR-004-local-llm-provider-abstraction.md), with [stale prose correction](03_ARCHITECTURE_CONSISTENCY_FINAL.md) | Command D |
| Adapter has normalized transport contract, not Person logic | [providers/lmstudio.py](../../../app/ai/providers/lmstudio.py): LMStudioProvider._request/list_models/generate; contracts.py | AdapterTests.test_llm_port_002_request_mapping_and_timeout; test_llm_port_006_malformed_envelopes; QualityGateTests.test_adapter_remains_transport_only | ADR-004; U05 | Commands D/F |
| Bad Insight output is never persisted | AIInsightService.generate/create; validate_insight/store_insight | InsightTests.test_llm_port_008_invalid_json_not_persisted; test_llm_port_010_enums_ranges_types_and_extra_fields; test_no_models_or_provider_error_does_not_persist | [U05 report](../U05_LLM_PROVIDER_REPORT.md) | Command D |
| Retry/breaker are implemented stateful behavior | [resilience.py](../../../app/ai/resilience.py): ResilientLLMProvider._admit/_generate/_complete; ResiliencePolicy | [test_llm_resilience.py](../../../tests/test_llm_resilience.py): ResilienceTests.test_res_002_exhaustion_and_cb_009_counts_one; test_res_004_exact_capped_exponential_delays; test_cb_010_half_open_concurrent_single_probe; test_stale_closed_success_cannot_close_newly_open_circuit | [U09 report](../U09_LLM_RESILIENCE_REPORT.md), [NFR limits](03_ARCHITECTURE_CONSISTENCY_FINAL.md) | Command E |
| Breaker survives requests through production composition | composition._active_provider/get_provider | CompositionTests.test_shared_binding_endpoint_change_and_concurrent_creation; API recovery tests in test_llm_resilience.py | U09 | Command E |
| Local inference is enforced without DNS | [privacy.py](../../../app/privacy.py): local_llm_url; ai/settings.save_settings; adapter._request | [test_privacy.py](../../../tests/test_privacy.py): NetworkPrivacyTests.test_sec_llm_002_003_004_008_remote_and_lan_always_rejected; test_sec_llm_009_validation_without_dns_network; test_proxy_environment_and_redirects_disabled | [ADR-001](../../adr/ADR-001-local-first-architecture.md) | Command G |
| Browser/request/file controls have executable evidence | [access.py](../../../app/access.py): LocalAccessMiddleware; privacy.safe_directory/prune_diagnostics; collector._route_request/_save_diagnostics | StoragePrivacyTests.test_collector_request_guard_is_fail_closed; test_diagnostics_do_not_capture_page_or_sensitive_report; test_import_byte_archive_expansion_and_member_paths_bounded | [security audit](04_SECURITY_PRIVACY_FINAL.md) | Command G |
| CI/quality verdicts are dynamic and fail closed | [run_quality_gates.py](../../../scripts/run_quality_gates.py): discover_tests/summarize_tests/fitness_results/execute_gates; workflow | [test_quality_gates.py](../../../tests/test_quality_gates.py): QualityGateTests.test_ci_001_unified_discovery_includes_all_modules_and_eight_legacy_tests; test_ci_002_failure_exit_is_nonzero_and_stops_dependent_gates; test_ci_007_fitness_registry_requires_executed_successful_evidence; test_workflow_and_bat_invoke_same_runner_without_app_secrets | [quality reference](../QUALITY_GATE_REFERENCE.md), qualified remote evidence in final report | Command F / canonical |
| Domain integrity validation closes the reproduced period/counter defect | [message_stats.py](../../../app/message_stats.py): normalize_message_stats; [services.py](../../../app/services.py): import_message_stats; importers._dispatch/import_uploaded_file; seed.seed_demo_data | [test_message_stats_validation.py](../../../tests/test_message_stats_validation.py): MessageStatsValidationTests.test_val_001_malformed_periods_rejected_at_both_boundaries; test_val_003_negative_incoming_rejected; test_val_004_negative_outgoing_rejected; test_val_009_direct_service_batch_remains_atomic; test_val_010_invalid_upload_has_only_existing_failed_attempt_bookkeeping; test_val_012_api_preserves_safe_400_and_valid_success | U13A contract; [independent delta evidence](00_FINAL_CERTIFICATION_REPORT.md); [data-integrity audit](04_SECURITY_PRIVACY_FINAL.md) | Command I; canonical Domain validation (U13A) 18/18; independent 26 invalid/6 valid route cases |
| RAG sources/IDs/index are real and derived | [rag/corpus.py](../../../app/rag/corpus.py): build_corpus; [models.py](../../../app/rag/models.py): stable_id/Document; [retrieval.py](../../../app/rag/retrieval.py): LexicalIndex | [test_rag.py](../../../tests/test_rag.py): RAGTests.test_stable_ids_independent_of_input_order; test_idempotent_reingestion_without_duplicates; test_event_identity_survives_derived_row_id_recreation; test_rebuild_removes_obsolete_derived_edges | [ADR-006](../../adr/ADR-006-rag-architecture.md) | Command H |
| No evidence bypasses all model calls | [rag/service.py](../../../app/rag/service.py): RAGService.answer before list_models/generate | RAGTests.test_no_evidence_bypasses_all_llm_calls; test_context_budget_dedup_and_oversize_bypass | ADR-006 / [RAG audit](05_RAG_EVALUATION_AUDIT.md) | Command H |
| RAG citation IDs cannot refer outside supplied context | RAGService.answer schema and local subset/duplicate checks | RAGTests.test_citations_constrained_to_retrieved_context; test_structured_output_validation; test_fake_llm_receives_only_retrieved_context | ADR-006 | Command H; distinguish structure from entailment |
| RAG evaluation is deterministic/synthetic | [evaluation.py](../../../app/rag/evaluation.py): evaluate/enforce_thresholds; [JSONL](../../../tests/fixtures/rag_eval.jsonl) | RAGTests.test_eval_fixture_synthetic_only; test_evaluation_metrics_and_threshold_failures; test_evaluation_thresholds_and_baseline | [independent metrics/candidate-set audit](05_RAG_EVALUATION_AUDIT.md) | Command H; explicitly disclose ranking-blind candidate sets |

Where a row abbreviates the method's class for space, the file and exact method name identify executable evidence unambiguously. All listed tests are in the 240-test run; supplemental audit probes are separate and uncounted.

## Safe demonstrations

Use the existing prepared environment (Python 3.13.2, Node 22.14.0). The canonical command is sufficient to demonstrate all mandatory evidence:

```powershell
.\.venv\Scripts\python.exe -B scripts/run_quality_gates.py
```

Focused diagnostic commands, all using temporary data and fake transports:

```powershell
# A — legacy schema migration
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p test_migrations.py -v
# B — relation source integrity and v1-to-v2 migration
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p test_snapshots.py -v
# C — runtime contract and frontend call coverage
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p test_api_contract.py -v
# D — provider, transport mapping and Insight validation
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p test_ai_provider.py -v
# E — retry and breaker with fake time
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p test_llm_resilience.py -v
# F — runner and CI governance
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p test_quality_gates.py -v
# G — local privacy, paths, diagnostics and UI helpers
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p test_privacy.py -v
# H — RAG corpus, grounding mechanics, metrics and sanity timing
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p test_rag.py -v
# I — domain date/count validation, direct service, imports and safe API errors
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p test_message_stats_validation.py -v
```

Do not use start.bat, production startup or a real get_rag_service call as an audit demonstration: startup migrates/seeds the user DB, and an evidence-backed real RAG answer calls the local model. The test demonstrations avoid those effects. No installation, Chromium download, user login or model service is part of the mandatory verification.

## Suggested defense narrative

1. Show the exact SHA/tag ancestry and the fresh 240/18 canonical summary. Separate locally verified evidence from the user's observed U08 remote green run; U13A remote CI is NOT YET RUN.
2. Show the original G02/G03 failures, then migration backup/rollback and explicit empty/same-day/backdated test evidence. Explain relation-only immutability and mutable message periods.
3. Show root OpenAPI generated from the existing /api surface. No fake auth, phantom target routes or silent product expansion.
4. Trace AIInsightService → port → composition → resilience → LM adapter. Explain the shared breaker and why timeout settings do not imply a total deadline.
5. Trace actual persisted RAG facts through ID/index/filter/context/citation validation. Demonstrate unknown citation rejection and zero provider calls on no evidence.
6. Show perfect synthetic metrics together with the independent warning: every eligible candidate is labelled relevant, so the set cannot prove ranking superiority or live answer quality.
7. Explain that the U08 audit reproduced invalid period/negative count persistence; U13A centralized validation before writes. Show direct service/upload rejection, valid inputs, unchanged person rows and the full 240-test gate. Keep identity/demo/broader atomicity deferred as P2-05.
8. Close with explicit residuals and planned scope: U10–U13, no Chat UI/Graph/CRM/Export/Scheduler, no global DIP, no auth/encryption guarantee. Use this final map rather than the baseline-era DEFENSE_GUIDE answers.

The defensible claim is a controlled local architecture evolution with executable invariants, not that all target diagrams are implemented or that additional infrastructure would improve certification.
