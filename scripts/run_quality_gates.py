"""Canonical offline quality command: python scripts/run_quality_gates.py.

Tests run once. Fitness verdicts refer to their measured outcomes, never rerun them.
"""
from __future__ import annotations

import ast
import asyncio
import compileall
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass
import importlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import check_docs, check_privacy

# IDs name existing executable evidence. Missing, skipped or failing evidence fails fitness.
FITNESS = {
    'FITNESS-DB-001': (
        'test_migrations.MigrationTests.test_mig_004_three_initializations_are_idempotent',
        'test_snapshots.SnapshotMigrationTests.test_mig_snp_005_fresh_v2_and_future_guard',
        'test_snapshots.SnapshotMigrationTests.test_mig_snp_003_three_initializations_unchanged',
    ),
    'FITNESS-SNAPSHOT-001': (
        'test_snapshots.SnapshotTests.test_snp_002_projection_immutable_and_evt_003_historical_display',
        'test_snapshots.SnapshotTests.test_complete_source_sql_mutations_rejected',
    ),
    'FITNESS-SNAPSHOT-002': (
        'test_snapshots.SnapshotTests.test_snp_005_incomplete_failed_creating_do_not_replace_current',
    ),
    'FITNESS-AI-001': (
        'test_ai_provider.ArchitectureTests.test_llm_port_014_dependency_fitness',
        'test_ai_provider.InsightTests.test_llm_port_001_fake_substitution_and_context_scope',
    ),
    'FITNESS-AI-002': (
        'test_quality_gates.QualityGateTests.test_adapter_remains_transport_only',
        'test_ai_provider.AdapterTests.test_llm_port_002_request_mapping_and_timeout',
    ),
    'FITNESS-RES-001': (
        'test_llm_resilience.ResilienceTests.test_architecture_import_fitness',
        'test_llm_resilience.CompositionTests.test_shared_binding_endpoint_change_and_concurrent_creation',
    ),
    'FITNESS-RES-002': (
        'test_llm_resilience.ResilienceTests.test_res_001_transient_then_success_and_cb_008_no_failure',
        'test_llm_resilience.ResilienceTests.test_res_004_exact_capped_exponential_delays',
        'test_llm_resilience.ResilienceTests.test_res_005_full_jitter_bounds',
    ),
    'FITNESS-API-001': (
        'test_api_contract.ContractGateTests.test_yaml_subset_parse_export_and_local_refs',
        'test_api_contract.ContractGateTests.test_api_contract_001_routes_enumerated_without_io',
        'test_api_contract.ContractGateTests.test_api_contract_002_all_frontend_calls',
        'test_api_contract.ContractGateTests.test_api_contract_005_methods_exact',
        'test_api_contract.ContractGateTests.test_api_contract_006_path_parameters_required',
        'test_api_contract.ContractGateTests.test_api_contract_007_explicit_unique_operation_ids',
        'test_api_contract.ContractGateTests.test_api_contract_012_no_fake_auth',
        'test_api_contract.ContractGateTests.test_drift_gate_rejects_route_request_response_security_and_id_mutations',
    ),
    'FITNESS-SEC-001': (
        'test_privacy.NetworkPrivacyTests.test_sec_001_002_launcher_is_fixed_loopback_and_access_logs_off',
    ),
    'FITNESS-SEC-002': (
        'test_privacy.NetworkPrivacyTests.test_sec_llm_002_003_004_008_remote_and_lan_always_rejected',
        'test_privacy.NetworkPrivacyTests.test_sec_llm_009_validation_without_dns_network',
        'test_privacy.NetworkPrivacyTests.test_settings_policy_is_atomic_and_provider_rechecks_existing_db',
    ),
    'FITNESS-SEC-003': (
        'test_privacy.StoragePrivacyTests.test_sec_data_001_ignored_sensitive_paths',
        'test_privacy.StoragePrivacyTests.test_sec_data_002_tracked_privacy_guard',
    ),
    'FITNESS-UI-001': (
        'test_privacy.StoragePrivacyTests.test_sec_xss_001_actual_helpers_and_rendering_boundaries',
    ),
    'FITNESS-RAG-001': ('test_rag.RAGTests.test_rag_service_depends_on_ports',),
    'FITNESS-RAG-002': (
        'test_rag.RAGTests.test_index_is_derived_rebuildable_and_conflicts_fail',
        'test_rag.RAGTests.test_rebuild_removes_obsolete_derived_edges',
    ),
    'FITNESS-RAG-003': ('test_rag.RAGTests.test_no_evidence_bypasses_all_llm_calls',),
    'FITNESS-RAG-004': (
        'test_rag.RAGTests.test_citations_constrained_to_retrieved_context',
        'test_rag.RAGTests.test_structured_output_validation',
    ),
    'FITNESS-RAG-005': ('test_rag.RAGTests.test_evaluation_thresholds_and_baseline',),
    'FITNESS-RAG-006': ('test_rag.RAGTests.test_eval_fixture_synthetic_only',),
}

CATEGORIES = {
    'Migration/data (U02)': {'test_migrations'},
    'Snapshot (U03)': {'test_snapshots'},
    'AI provider (U05)': {'test_ai_provider'},
    'Resilience (U09)': {'test_llm_resilience'},
    'API contract/in-process integration (U04)': {'test_api_contract'},
    'Security/privacy (U06)': {'test_privacy'},
    'Quality governance (U07)': {'test_quality_gates'},
    'Local RAG (U08)': {'test_rag'},
    'Unit/regression': {'test_services', 'test_v02', 'test_v03', 'test_v031',
                        'test_v04', 'test_v041', 'test_v042', 'test_v043_organization_source'},
}


class GateFailure(Exception):
    """A safe message produced by a repository gate, never external payload text."""


@dataclass
class GateResult:
    name: str
    passed: bool
    seconds: float
    detail: str


def execute_gates(gates, emit=print):
    """Fail fast on mandatory failures; used by the CLI and synthetic helper tests."""
    results = []
    for name, action in gates:
        started = time.perf_counter()
        try:
            detail = action() or ''
            passed = True
        except Exception as exc:
            detail = str(exc) if isinstance(exc, GateFailure) else type(exc).__name__
            passed = False
        row = GateResult(name, passed, time.perf_counter() - started, detail)
        results.append(row)
        emit(f'{name}: {"PASS" if passed else "FAIL"} ({row.seconds:.3f}s) {detail}')
        if not passed:
            break
    return results, 0 if results and all(row.passed for row in results) else 1


def flatten(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from flatten(item)
        else:
            yield item


def discover_tests(root=ROOT):
    loader = unittest.TestLoader()
    suite = loader.discover(str(root/'tests'), pattern='test_*.py')
    if loader.errors:
        raise GateFailure('Test import/discovery failed; check module syntax and dependencies')
    cases = list(flatten(suite))
    ids = [case.id() for case in cases]
    if not ids or len(ids) != len(set(ids)):
        raise GateFailure('Empty or duplicate test discovery')
    # No silent recurrence of the historical plain-function discovery gap.
    for source in (root/'tests').glob('test_*.py'):
        tree = ast.parse(source.read_text(encoding='utf-8-sig'))
        if any(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith('test_') for node in tree.body):
            raise GateFailure(f'{source.name}: non-discoverable module-level test function')
        if not any(identifier.startswith(source.stem + '.') for identifier in ids):
            raise GateFailure(f'{source.name}: no discovered tests')
    return suite, ids


class MeasuredResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.outcomes = {}

    def addSuccess(self, test):
        super().addSuccess(test)
        self.outcomes[test.id()] = 'PASS'

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.outcomes[test.id()] = 'FAIL'

    def addError(self, test, err):
        super().addError(test, err)
        self.outcomes[test.id()] = 'ERROR'

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.outcomes[test.id()] = 'SKIP'

    def addExpectedFailure(self, test, err):
        super().addExpectedFailure(test, err)
        self.outcomes[test.id()] = 'EXPECTED_FAILURE'

    def addUnexpectedSuccess(self, test):
        super().addUnexpectedSuccess(test)
        self.outcomes[test.id()] = 'UNEXPECTED_SUCCESS'

    def addSubTest(self, test, subtest, err):
        super().addSubTest(test, subtest, err)
        if err is not None:
            self.outcomes[test.id()] = 'FAIL'


def summarize_tests(ids, result):
    passed = sum(result.outcomes.get(identifier) == 'PASS' for identifier in ids)
    return {'discovered': len(ids), 'executed': result.testsRun, 'passed': passed,
            'not_passed': len(ids) - passed,
            'ok': result.wasSuccessful() and result.testsRun == len(ids) and passed == len(ids)}


def fitness_results(outcomes):
    return {key: all(outcomes.get(identifier) == 'PASS' for identifier in evidence)
            for key, evidence in FITNESS.items()}


def artifact_findings(tracked):
    return [(name, 'sensitive-runtime-artifact') for name in tracked if check_privacy.sensitive_name(name)]


@contextmanager
def no_real_delays():
    original_async_sleep = asyncio.sleep

    async def scheduler_yield_only(delay, result=None):
        if delay != 0:
            raise AssertionError('Real async delay forbidden')
        return await original_async_sleep(0, result)  # AnyIO's cooperative checkpoint.

    with patch('time.sleep', side_effect=AssertionError('Real sleep forbidden')), \
         patch('asyncio.sleep', side_effect=scheduler_yield_only):
        yield


def sensitive_gate():
    tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode('utf-8').split('\0')
    findings = artifact_findings(filter(None, tracked))
    for name, category in findings:
        print(f'{name}: {category}')
    if findings:
        raise GateFailure('Tracked runtime artifacts found')
    return 'tracked paths only; local untracked data is not scanned'


def secret_gate():
    findings = check_privacy.check(ROOT)
    for name, category in findings:
        print(f'{name}: {category}')
    if findings:
        raise GateFailure('Privacy/secret guard findings require review; values suppressed')
    return 'U06 tracked source/archive-name guard; no full-history claim'


def syntax_import_gate():
    if sys.flags.optimize:
        raise GateFailure('Optimized Python would disable assertions; rerun without -O')
    with tempfile.TemporaryDirectory() as cache:
        with patch.object(sys, 'pycache_prefix', cache):
            targets = [ROOT/'app', ROOT/'scripts', ROOT/'tests', ROOT/'run_server.py']
            for target in targets:
                ok = (compileall.compile_dir(target, quiet=2, force=True) if target.is_dir()
                      else compileall.compile_file(target, quiet=2, force=True))
                if not ok:
                    raise GateFailure('Python compilation failed')
    # Import smoke only: never invoke lifespan, migrations, collector start or server.
    with ExitStack() as guards:
        for target in ('sqlite3.connect', 'socket.create_connection', 'socket.getaddrinfo',
                       'uvicorn.run', 'playwright.async_api._context_manager.PlaywrightContextManager.start'):
            guards.enter_context(patch(target, side_effect=AssertionError('Import side effect forbidden')))
        for module in ('app.main', 'app.collector', 'app.importers', 'app.snapshots',
                       'app.ai.composition', 'app.ai.service', 'app.ai.resilience',
                       'app.rag.corpus', 'app.rag.retrieval', 'app.rag.service'):
            importlib.import_module(module)
    if shutil.which('node') is None:
        raise GateFailure('Node.js is required for the existing U06 UI helper checks')
    subprocess.run(['node', '--check', str(ROOT/'static/app.js')], check=True, cwd=ROOT)
    return 'Python compileall/critical imports and Node syntax; no lifespan'


def openapi_gate():
    import json
    import yaml
    from fastapi.openapi.models import OpenAPI
    from app.main import app
    from scripts.export_openapi import render
    source = (ROOT/'11_OPENAPI.yaml').read_text(encoding='utf-8')
    canonical = yaml.safe_load(source)
    app.openapi_schema = None
    runtime = app.openapi()
    if canonical != json.loads(source) or source != render(runtime):
        raise GateFailure('OpenAPI drift: regenerate and review 11_OPENAPI.yaml')
    OpenAPI.model_validate(canonical)
    return 'YAML/JSON/FastAPI structure and exact export; semantic U04 tests follow'


def documentation_gate():
    issues = check_docs.check(ROOT)
    for issue in issues:
        print(issue)
    if issues:
        raise GateFailure('Documentation links/path/fence checks failed')
    return f'{len(check_docs.documents(ROOT))} Markdown files; Mermaid formal validation NOT AVAILABLE'


def main():
    os.chdir(ROOT)
    sys.dont_write_bytecode = True
    started = time.perf_counter()
    print('VK SOCIAL RADAR - UNIFIED QUALITY GATES', flush=True)
    measured = {}

    def automated_tests():
        suite, ids = discover_tests()
        registered = set().union(*CATEGORIES.values())
        modules = {identifier.split('.')[0] for identifier in ids}
        if modules != registered:
            raise GateFailure('Test category registration drift: ' + ', '.join(sorted(modules ^ registered)))
        missing = {item for items in FITNESS.values() for item in items} - set(ids)
        if missing:
            raise GateFailure('Missing fitness evidence: ' + ', '.join(sorted(missing)))
        # Existing fixtures isolate data/transports. This also rejects any real sleep
        # in legacy/new tests; retry tests explicitly inject fake time/sleep/random.
        with no_real_delays():
            result = unittest.TextTestRunner(stream=sys.stdout, verbosity=1, resultclass=MeasuredResult).run(suite)
        measured.update(outcomes=result.outcomes)
        summary = summarize_tests(ids, result)
        print('Automated tests: ' + ', '.join(f'{key}={value}' for key, value in summary.items()))
        for category, module_names in CATEGORIES.items():
            subset = [identifier for identifier in ids if identifier.split('.')[0] in module_names]
            count = sum(result.outcomes.get(identifier) == 'PASS' for identifier in subset)
            print(f'  {category}: {count}/{len(subset)} PASS')
        if not summary['ok']:
            raise GateFailure('Mandatory automated tests failed/missing/skipped')
        return f"{summary['passed']} measured tests PASS; no separate plain functions"

    def architecture_fitness():
        verdicts = fitness_results(measured.get('outcomes', {}))
        for key, passed in verdicts.items():
            print(f'  {key}: {"PASS" if passed else "FAIL"}')
        if not all(verdicts.values()):
            raise GateFailure('Architecture fitness evidence failed/missing')
        return f'{len(verdicts)} invariants checked against tests executed in this run'

    gates = [
        ('Sensitive artifacts', sensitive_gate), ('Secret guard', secret_gate),
        ('Syntax/imports', syntax_import_gate), ('OpenAPI drift/YAML', openapi_gate),
        ('Documentation', documentation_gate), ('Automated regression', automated_tests),
        ('Architecture fitness', architecture_fitness),
    ]
    rows, code = execute_gates(gates)
    print(f'Gates executed: {len(rows)}/{len(gates)}; passed: {sum(row.passed for row in rows)}')
    print(f'Local duration: {time.perf_counter() - started:.3f}s')
    print('RESULT: ' + ('PASS' if code == 0 else 'FAIL'))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
