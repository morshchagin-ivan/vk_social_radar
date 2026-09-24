"""U07 helper/fitness tests; never launch the full quality runner recursively."""
from __future__ import annotations

import ast
import asyncio
import io
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

import yaml

from scripts import check_docs, run_quality_gates as quality

ROOT = Path(__file__).resolve().parents[1]


class QualityGateTests(unittest.TestCase):
    def test_ci_001_unified_discovery_includes_all_modules_and_eight_legacy_tests(self):
        suite, ids = quality.discover_tests()
        self.assertEqual(suite.countTestCases(), len(ids))
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual({identifier.split('.')[0] for identifier in ids},
                         {path.stem for path in (ROOT/'tests').glob('test_*.py')})
        legacy = [identifier for identifier in ids if identifier.startswith('test_v043_organization_source.')]
        self.assertEqual(len(legacy), 8)
        self.assertTrue(all('.OrganizationSourceTests.test_' in identifier for identifier in legacy))
        self.assertEqual(set().union(*quality.CATEGORIES.values()), {identifier.split('.')[0] for identifier in ids})

    def test_ci_002_failure_exit_is_nonzero_and_stops_dependent_gates(self):
        calls = []
        def fail():
            calls.append('fail')
            raise quality.GateFailure('Synthetic failure')
        rows, code = quality.execute_gates([('first', lambda: 'ok'), ('second', fail),
                                            ('never', lambda: calls.append('never'))], emit=lambda _: None)
        self.assertNotEqual(code, 0)
        self.assertEqual([row.passed for row in rows], [True, False])
        self.assertEqual(calls, ['fail'])
        self.assertEqual(quality.execute_gates([('ok', lambda: 'ok')], emit=lambda _: None)[1], 0)
        self.assertNotEqual(quality.execute_gates([], emit=lambda _: None)[1], 0)

    def test_ci_003_synthetic_tracked_runtime_artifacts_rejected(self):
        names = ['data/social_radar.db', 'data/vk_browser_profile/Cookies', 'data/imports/input.json',
                 'data/collector_previews/private.json', 'logs/collector/raw.html',
                 'social_radar.db-wal', 'social_radar.db-shm', '.env', 'session.json']
        self.assertEqual({item[0] for item in quality.artifact_findings(names)}, set(names))

    def test_ci_004_tracked_gitkeep_and_sources_allowed(self):
        self.assertEqual(quality.artifact_findings(['data/imports/.gitkeep',
                         'data/vk_browser_profile/.gitkeep', 'logs/collector/.gitkeep',
                         'app/db.py', 'tests/test_privacy.py', '.env.example']), [])

    def test_ci_005_broken_relative_link_detected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            page = root/'README.md'
            page.write_text('[Missing](missing.md)\n[Outside](../outside.md)', encoding='utf-8')
            self.assertEqual(len(check_docs.check_document(page, root)), 2)

    def test_ci_006_known_valid_certification_link_passes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root/'docs').mkdir()
            (root/'docs/STATUS.md').write_text('Evidence', encoding='utf-8')
            page = root/'README.md'
            page.write_text('[Status](docs/STATUS.md:1)\n[ref]: docs/STATUS.md\n[External](https://example.invalid)', encoding='utf-8')
            self.assertEqual(check_docs.check_document(page, root), [])
        self.assertEqual(check_docs.check_document(ROOT/'docs/certification/THREAT_MODEL.md'), [])

    def test_ci_007_fitness_registry_requires_executed_successful_evidence(self):
        self.assertEqual(set(quality.FITNESS), {
            'FITNESS-DB-001', 'FITNESS-SNAPSHOT-001', 'FITNESS-SNAPSHOT-002',
            'FITNESS-AI-001', 'FITNESS-AI-002', 'FITNESS-RES-001', 'FITNESS-RES-002',
            'FITNESS-API-001', 'FITNESS-SEC-001', 'FITNESS-SEC-002', 'FITNESS-SEC-003', 'FITNESS-UI-001',
            'FITNESS-RAG-001', 'FITNESS-RAG-002', 'FITNESS-RAG-003',
            'FITNESS-RAG-004', 'FITNESS-RAG-005', 'FITNESS-RAG-006',
        })
        outcomes = {identifier: 'PASS' for evidence in quality.FITNESS.values() for identifier in evidence}
        self.assertTrue(all(quality.fitness_results(outcomes).values()))
        self.assertFalse(any(quality.fitness_results({}).values()))
        for invariant, evidence in quality.FITNESS.items():
            for status in ('FAIL', 'ERROR', 'SKIP'):
                changed = {**outcomes, evidence[0]: status}
                self.assertFalse(quality.fitness_results(changed)[invariant])

    def test_ci_008_summary_measures_success_failure_skip_and_subtest(self):
        # Small synthetic suites exercise result bookkeeping, not repository recursion.
        class Probe(unittest.TestCase):
            def success(self): pass
            def failure(self): self.fail('Synthetic failure')
            def skipped(self): self.skipTest('Synthetic skip')
            def subtest(self):
                with self.subTest(case='synthetic'): self.fail('Synthetic failure')
        for names, successes in [(('success',), 1), (('success', 'failure', 'skipped', 'subtest'), 1)]:
            cases = [Probe(name) for name in names]
            ids = [case.id() for case in cases]
            result = unittest.TextTestRunner(stream=io.StringIO(), resultclass=quality.MeasuredResult).run(unittest.TestSuite(cases))
            summary = quality.summarize_tests(ids, result)
            self.assertEqual(summary['discovered'], len(names))
            self.assertEqual(summary['executed'], len(names))
            self.assertEqual(summary['passed'], successes)
            self.assertEqual(summary['not_passed'], len(names) - successes)
            self.assertEqual(summary['ok'], len(names) == successes)
        with quality.no_real_delays():
            with self.assertRaises(AssertionError):
                time.sleep(0.01)
            with self.assertRaises(AssertionError):
                asyncio.run(asyncio.sleep(0.01))
            self.assertEqual(asyncio.run(asyncio.sleep(0, 'yielded')), 'yielded')

    def test_adapter_remains_transport_only(self):
        source = (ROOT/'app/ai/providers/lmstudio.py').read_text(encoding='utf-8')
        tree = ast.parse(source)
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                imported.update((node.module or '').split('.'))
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.Import):
                imported.update(part for alias in node.names for part in alias.name.split('.'))
        self.assertFalse(imported & {'db', 'services', 'service', 'settings', 'Person', 'AIInsightService'})
        literals = {node.value for node in ast.walk(tree) if isinstance(node, ast.Constant) and isinstance(node.value, str)}
        self.assertFalse(literals & {'person', 'full_name', 'message_stats', 'relationship_events', 'person_id', 'ai_insights'})

    def test_document_portability_and_mermaid_structure_failures(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            page = root/'README.md'
            page.write_text('Developer path: C:/work/repo\n```mermaid\nflowchart LR\nsubgraph A\n```', encoding='utf-8')
            issues = check_docs.check_document(page, root)
            self.assertTrue(any('absolute developer path' in issue for issue in issues))
            self.assertTrue(any('unbalanced Mermaid' in issue for issue in issues))
            page.write_text('```mermaid\nflowchart LR\nA --> B', encoding='utf-8')
            self.assertTrue(any('unclosed fence' in issue for issue in check_docs.check_document(page, root)))

    def test_workflow_and_bat_invoke_same_runner_without_app_secrets(self):
        text = (ROOT/'.github/workflows/quality-gates.yml').read_text(encoding='utf-8')
        workflow = yaml.load(text, Loader=yaml.BaseLoader)
        self.assertEqual(workflow['name'], 'Quality Gates')
        self.assertIn('pull_request', workflow['on'])
        self.assertEqual(set(workflow['on']['push']['branches']), {'main', 'certification/architecture-upgrade'})
        job = workflow['jobs']['quality-gates']
        self.assertEqual(job['runs-on'], 'windows-2022')
        versions = {step['uses'].split('@')[0]: step.get('with', {}) for step in job['steps'] if 'uses' in step}
        self.assertEqual(versions['actions/setup-python']['python-version'], '3.13.2')
        self.assertEqual(versions['actions/setup-node']['node-version'], '22.14.0')
        commands = [step['run'] for step in job['steps'] if 'run' in step]
        self.assertEqual(commands, ['python -m pip install -r requirements-dev.txt', 'python scripts/run_quality_gates.py'])
        self.assertNotIn('secrets.', text)
        self.assertNotIn('continue-on-error', text)
        self.assertEqual(workflow['permissions'], {'contents': 'read'})
        wrapper = (ROOT/'run_tests.bat').read_text(encoding='utf-8')
        self.assertIn('scripts\\run_quality_gates.py', wrapper)
        self.assertIn('exit /b %errorlevel%', wrapper)
        self.assertNotIn('unittest', wrapper)

    def test_openapi_gate_rejects_synthetic_drift(self):
        document = json.loads((ROOT/'11_OPENAPI.yaml').read_text(encoding='utf-8'))
        document['paths'].pop('/api/health')
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root/'11_OPENAPI.yaml').write_text(json.dumps(document), encoding='utf-8')
            with patch.object(quality, 'ROOT', root), self.assertRaises(quality.GateFailure):
                quality.openapi_gate()
