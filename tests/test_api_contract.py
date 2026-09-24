"""U04 executable runtime/canonical/frontend gate, without lifespan or network."""
from __future__ import annotations

import copy
import io
import json
import re
import runpy
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from app import db, importers, main
from app.ai.contracts import ProviderUnavailableError
from app.ai.resilience import ResilientLLMProvider, ResiliencePolicy
from app.ai.service import AIInsightService
from scripts.export_openapi import render
from test_ai_provider import FakeProvider, NetworkBlockedTests

ROOT = Path(__file__).resolve().parents[1]
METHODS = {"get", "post", "put", "delete", "patch", "head", "options"}


def operations(schema):
    return {(method.upper(), path): op for path, item in schema["paths"].items()
            for method, op in item.items() if method in METHODS}


def frontend_calls(source):
    """Fail closed on new fetch wrappers/dynamic paths; support this small vanilla JS UI."""
    assert re.findall(r'\bfetch\(([^)]*)\)', source) == ['path,options'], 'New fetch call needs inventory'
    assert 'async function api(path,options={})' in source
    assert 'await api(path,{method:"POST"})' in source
    assert 'async function collectorAction(path, button, successText)' in source
    calls = []
    for match in re.finditer(r'\b(api|collectorAction)\(', source):
        if re.search(r'function\s+$', source[max(0, match.start()-20):match.start()]):
            continue
        tail = source[match.end():]
        if tail.startswith('path,{method:"POST"})') and match[1] == 'api':
            continue  # the single inventoried collectorAction forwarding call
        literal = re.match(r'(["`])(/api/.*?)\1\s*([,)])', tail)
        assert literal, 'Uninventoried dynamic API call: ' + tail[:60]
        method = 'POST' if match[1] == 'collectorAction' else 'GET'
        if literal[3] == ',' and match[1] == 'api':
            options = re.match(r'\s*\{\s*method:\s*"([A-Z]+)"', tail[literal.end():])
            assert options, 'Uninventoried API options'
            method = options[1]
        calls.append((method, re.sub(r'\$\{[^}]+\}', 'synthetic', literal[2])))
    return calls


def validate_value(value, schema, document):
    """Behavior-fixture check for the emitted schema subset, NOT a formal OpenAPI validator."""
    if '$ref' in schema:
        target = document
        for part in schema['$ref'].split('/')[1:]:
            target = target[part]
        return validate_value(value, target, document)
    if 'anyOf' in schema:
        for option in schema['anyOf']:
            try:
                validate_value(value, option, document)
                return
            except AssertionError:
                pass
        raise AssertionError('No anyOf option matches')
    types = schema.get('type')
    if types:
        types = types if isinstance(types, list) else [types]
        actual = ('null' if value is None else 'boolean' if isinstance(value, bool) else
                  'integer' if isinstance(value, int) else 'number' if isinstance(value, float) else
                  'string' if isinstance(value, str) else 'array' if isinstance(value, list) else
                  'object' if isinstance(value, dict) else 'unknown')
        assert actual in types or actual == 'integer' and 'number' in types, (actual, types)
    if 'enum' in schema:
        assert value in schema['enum']
    if 'const' in schema:
        assert value == schema['const']
    if isinstance(value, dict):
        assert set(schema.get('required', [])) <= value.keys(), schema.get('required')
        props = schema.get('properties', {})
        for key, item in value.items():
            if key in props:
                validate_value(item, props[key], document)
            elif isinstance(schema.get('additionalProperties'), dict):
                validate_value(item, schema['additionalProperties'], document)
            else:
                assert schema.get('additionalProperties', True) is not False
    if isinstance(value, list):
        for item in value:
            validate_value(item, schema.get('items', {}), document)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        assert value >= schema.get('minimum', value)
        assert value <= schema.get('maximum', value)


class ContractGateTests(NetworkBlockedTests):
    def setUp(self):
        super().setUp()
        self.canonical = json.loads((ROOT / '11_OPENAPI.yaml').read_text(encoding='utf-8'))
        # No stale cached schema may conceal route edits in this process.
        main.app.openapi_schema = None
        self.runtime = main.app.openapi()
        self.ops = operations(self.canonical)

    def test_api_contract_001_routes_enumerated_without_io(self):
        with patch.object(db, 'get_connection', side_effect=AssertionError('DB forbidden')), \
             patch.object(main, 'init_db', side_effect=AssertionError('Startup forbidden')), \
             patch.object(main, 'seed_demo_data', side_effect=AssertionError('Seed forbidden')):
            main.app.openapi_schema = None
            self.assertEqual(main.app.openapi(), self.canonical)
        routes = [r for r in main.app.routes if isinstance(r, APIRoute)]
        self.assertEqual(len(routes), 30)
        self.assertEqual(sum(r.path.startswith('/api/') for r in routes), 29)

    def test_api_contract_002_all_frontend_calls(self):
        calls = frontend_calls((ROOT / 'static/app.js').read_text(encoding='utf-8'))
        self.assertEqual(len(calls), 21)
        for method, path in calls:
            matches = [(m, p) for m, p in self.ops if m == method and
                       re.fullmatch(re.sub(r'\{[^}]+\}', '[^/]+', p), path)]
            self.assertEqual(len(matches), 1, (method, path))
            self.assertIn(matches[0], operations(self.runtime))

    def test_api_contract_003_no_phantom_paths_or_target_resources(self):
        self.assertLessEqual(self.ops.keys(), operations(self.runtime).keys())
        self.assertFalse(any('/api/v1' in path or path.startswith(('/api/snapshots', '/api/graph', '/api/export', '/api/ai/chat'))
                             for _, path in self.ops))
        archive = (ROOT / 'specs/001-vk-profile-analysis/11_OPENAPI.yaml').read_text(encoding='utf-8')
        self.assertTrue(archive.startswith('# ARCHIVED TARGET PROPOSAL — NON-CANONICAL'))

    def test_api_contract_004_no_undocumented_public_operations(self):
        public = {(m, r.path) for r in main.app.routes if isinstance(r, APIRoute)
                  for m in r.methods if r.path.startswith('/api/')}
        self.assertLessEqual(public, self.ops.keys())
        self.assertEqual({k for k,v in self.ops.items() if v['x-audience'] == 'public'}, public)

    def test_api_contract_005_methods_exact(self):
        self.assertEqual(self.ops.keys(), operations(self.runtime).keys())

    def test_api_contract_006_path_parameters_required(self):
        for (method, path), op in self.ops.items():
            expected = set(re.findall(r'\{([^}]+)\}', path))
            params = [p for p in op.get('parameters', []) if p['in'] == 'path']
            self.assertEqual({p['name'] for p in params}, expected)
            self.assertTrue(all(p['required'] for p in params))
            self.assertEqual(op.get('parameters'), operations(self.runtime)[(method, path)].get('parameters'))

    def test_api_contract_007_explicit_unique_operation_ids(self):
        routes = [r for r in main.app.routes if isinstance(r, APIRoute)]
        ids = [r.operation_id for r in routes]
        self.assertTrue(all(ids))
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(re.fullmatch('[a-z][a-z0-9_]*', x) for x in ids))
        self.assertEqual(set(ids), {op['operationId'] for op in self.ops.values()})

    def test_api_contract_008_request_schemas_match(self):
        for key, op in self.ops.items():
            self.assertEqual(op.get('requestBody'), operations(self.runtime)[key].get('requestBody'))
        snapshot = self.ops['POST', '/api/import/snapshot']['requestBody']
        body = snapshot['content']['application/json']['schema']
        self.assertTrue(snapshot['required'])
        self.assertEqual(set(body['required']), {'people', 'relation_type'})
        self.assertIn('completeness', body['properties'])
        self.assertIn('multipart/form-data', self.ops['POST', '/api/import/file']['requestBody']['content'])

    def test_api_contract_009_success_schemas_match_and_are_meaningful(self):
        for key, op in self.ops.items():
            self.assertEqual(op['responses'], operations(self.runtime)[key]['responses'])
        for path in ('/api/health','/api/dashboard','/api/people','/api/people/{person_id}',
                     '/api/import/snapshot','/api/import/file','/api/changes','/api/dialogs',
                     '/api/people/{person_id}/insight','/api/collector/preview'):
            method = 'POST' if path in ('/api/import/snapshot','/api/import/file','/api/people/{person_id}/insight') else 'GET'
            schema = self.ops[method, path]['responses']['200']['content']['application/json']['schema']
            self.assertTrue('$ref' in schema or 'anyOf' in schema or '$ref' in schema.get('items', {}))

    def test_api_contract_012_no_fake_auth(self):
        self.assertFalse(self.canonical.get('security'))
        self.assertFalse(self.canonical['components'].get('securitySchemes'))
        self.assertTrue(all(not op.get('security') for op in self.ops.values()))
        self.assertTrue(all(not r.dependant.security_requirements for r in main.app.routes if isinstance(r, APIRoute)))

    def test_yaml_subset_parse_export_and_local_refs(self):
        self.assertEqual(self.canonical['openapi'], '3.1.0')
        self.assertEqual(render(self.runtime), (ROOT / '11_OPENAPI.yaml').read_text(encoding='utf-8'))
        def visit(value):
            if isinstance(value, dict):
                if '$ref' in value:
                    self.assertTrue(value['$ref'].startswith('#/'))
                    target = self.canonical
                    for key in value['$ref'].split('/')[1:]:
                        target = target[key]
                for item in value.values(): visit(item)
            elif isinstance(value, list):
                for item in value: visit(item)
        visit(self.canonical)

    def test_drift_gate_rejects_route_request_response_security_and_id_mutations(self):
        mutations = [
            lambda d: d['paths'].pop('/api/health'),
            lambda d: d['paths'].update({'/api/phantom': copy.deepcopy(d['paths']['/api/health'])}),
            lambda d: d['paths']['/api/health'].update({'post': d['paths']['/api/health'].pop('get')}),
            lambda d: d['paths']['/api/health']['get'].update(operationId=''),
            lambda d: d['paths']['/api/people/{person_id}']['get']['parameters'][0].update(required=False),
            lambda d: d['paths']['/api/import/snapshot']['post']['requestBody'].update(required=False),
            lambda d: d['components']['schemas']['Health']['properties']['status'].update(type='integer'),
            lambda d: d.update(security=[{'BearerAuth': []}]),
        ]
        for mutate in mutations:
            changed = copy.deepcopy(self.canonical)
            mutate(changed)
            with self.assertRaises(AssertionError):
                self.assertEqual(render(changed), render(self.runtime))
        source = (ROOT / 'static/app.js').read_text(encoding='utf-8')
        with self.assertRaises(AssertionError):
            frontend_calls(source + '\nfetch("/api/new");')

    def test_export_check_does_not_start_application(self):
        with patch('sys.argv', ['export_openapi.py', '--check']), \
             patch.object(main, 'init_db', side_effect=AssertionError('Startup forbidden')), \
             patch.object(db, 'get_connection', side_effect=AssertionError('DB forbidden')):
            runpy.run_path(str(ROOT / 'scripts/export_openapi.py'), run_name='__main__')


class APIBehaviorTests(NetworkBlockedTests):
    def setUp(self):
        super().setUp()
        temp = self.enterContext(tempfile.TemporaryDirectory())
        self.root = Path(temp)
        self.enterContext(patch.multiple(db, DATA_DIR=self.root, DB_PATH=self.root / 'test.db',
                                        IMPORT_DIR=self.root / 'imports', BACKUP_DIR=self.root / 'backups'))
        self.enterContext(patch.object(importers, 'IMPORT_DIR', self.root / 'imports'))
        db.init_db()
        self.enterContext(patch.object(main, 'init_db', side_effect=AssertionError('Lifespan forbidden')))
        self.enterContext(patch.object(main, 'seed_demo_data', side_effect=AssertionError('Seed forbidden')))
        self.enterContext(patch.object(main.collector.state, 'preview', None))
        self.client = TestClient(main.app, raise_server_exceptions=False)  # deliberately no context manager/lifespan
        self.addCleanup(self.client.close)
        self.schema = json.loads((ROOT / '11_OPENAPI.yaml').read_text(encoding='utf-8'))

    def check(self, method, path, status=200, template=None, **kwargs):
        response = self.client.request(method, path, **kwargs)
        self.assertEqual(response.status_code, status, response.text)
        spec = self.schema['paths'][template or path][method.lower()]['responses'][str(status)]
        media = response.headers['content-type'].split(';')[0]
        self.assertIn(media, spec['content'])
        value = response.json() if media == 'application/json' else response.text
        validate_value(value, spec['content'][media]['schema'], self.schema)
        return value

    def capture(self, people, at='2099-01-01', **kw):
        return self.check('POST', '/api/import/snapshot', json={
            'relation_type':'friend', 'people':people, 'captured_at':at, **kw})

    def test_health_shell_and_settings_coercion(self):
        self.assertEqual(self.check('GET', '/api/health'), {'status':'ok','version':'0.4.2'})
        self.check('GET', '/')
        self.check('GET', '/api/settings')
        saved = self.check('PUT', '/api/settings', json={'lmstudio_temperature':0.4,'ignored':True})
        self.assertEqual(saved['lmstudio_temperature'], '0.4')
        self.assertNotIn('ignored', saved)

    def test_api_contract_010_framework_and_domain_validation(self):
        self.check('POST', '/api/import/snapshot', 422)
        self.check('POST', '/api/import/snapshot', 422, json=[])
        self.check('POST', '/api/import/snapshot', 400, json={'relation_type':'friend'})
        self.check('POST', '/api/import/snapshot', 400, json={'relation_type':'other','people':[]})
        self.check('PUT', '/api/settings', 422, json=[])
        self.check('GET', '/api/people/not-int', 422, template='/api/people/{person_id}')
        self.check('GET', '/api/changes?limit=bad', 422, template='/api/changes')
        self.check('POST', '/api/import/file', 422)
        self.check('GET', '/api/collector/source/classify', 422)
        self.check('POST', '/api/collector/organization-source', 400, json={})

    def test_api_contract_011_missing_and_provider_errors(self):
        self.check('GET', '/api/people/999', 404, template='/api/people/{person_id}')
        self.check('POST', '/api/people/999/insight', 404, template='/api/people/{person_id}/insight')
        self.check('GET', '/api/collector/preview', 404)
        self.check('POST', '/api/collector/save-preview', 404)
        fake = FakeProvider(error=ProviderUnavailableError('Synthetic unavailable'))
        with patch.object(main, 'get_provider', return_value=fake):
            self.check('GET', '/api/lmstudio/models', 503)
            self.check('POST', '/api/lmstudio/test', 503)

    def test_snapshot_dashboard_timeline_and_person_shapes(self):
        first = self.capture([{'vk_id':1,'full_name':'Synthetic One'}])
        person = self.check('GET', '/api/people')[0]
        second = self.capture([], '2099-01-02')
        dashboard = self.check('GET', '/api/dashboard')
        self.assertEqual(dashboard['friends']['current'], 0)
        events = self.check('GET', '/api/changes?limit=0', template='/api/changes')
        self.assertEqual(events[0]['from_snapshot_id'], first['snapshot_id'])
        self.assertEqual(events[0]['to_snapshot_id'], second['snapshot_id'])
        self.check('GET', f'/api/people/{person["id"]}', template='/api/people/{person_id}')
        self.check('GET', '/api/messages/leaderboard')
        self.check('GET', '/api/dialogs?limit=999999', template='/api/dialogs')

    def test_fake_insight_models_and_open_circuit(self):
        self.capture([{'vk_id':1,'full_name':'Synthetic One'}])
        person_id = self.check('GET', '/api/people')[0]['id']
        fake = FakeProvider()
        with patch.object(main, 'get_provider', return_value=fake):
            self.assertIn('custom', self.check('GET', '/api/lmstudio/models')[0])
            self.check('POST', '/api/lmstudio/test')
        with patch.object(main, 'get_insight_service', return_value=AIInsightService(fake, model='model-a')):
            self.check('POST', f'/api/people/{person_id}/insight', template='/api/people/{person_id}/insight')
        fake.error = ProviderUnavailableError('Synthetic failure')
        wrapper = ResilientLLMProvider(fake, ResiliencePolicy(failure_threshold=1),
                                      clock=lambda:0, sleep=lambda _:None, random_value=lambda:0)
        with patch.object(main, 'get_insight_service', return_value=AIInsightService(wrapper, model='model-a')), \
             patch.object(fake, 'generate', wraps=fake.generate) as generate:
            self.check('POST', f'/api/people/{person_id}/insight', 503, template='/api/people/{person_id}/insight')
            self.assertEqual(generate.call_count, 3)
            self.check('POST', f'/api/people/{person_id}/insight', 503, template='/api/people/{person_id}/insight')
            self.assertEqual(generate.call_count, 3)  # Open circuit bypasses the provider entirely.
        self.check('GET', f'/api/people/{person_id}', template='/api/people/{person_id}')

    def test_collector_mocked_routes_and_error_mapping(self):
        status = {name:'' for name in ('status','current_url','last_error','last_action','profile_dir','operation_id','operation_state','collection_surface')}
        status.update(authenticated=False, has_preview=False, blocked_hosts=[], members_discovered=0,
                      members_deduped=0, progress={}, result_available=False)
        for method, path, target in [('POST','start','start'),('POST','close','close'),('GET','status','get_status'),
                                     ('POST','check-auth','check_auth'),('POST','navigate/home','navigate')]:
            with patch.object(main.collector, target, new=AsyncMock(return_value=status)):
                self.check(method, '/api/collector/'+path,
                           template='/api/collector/navigate/{target}' if path.startswith('navigate/') else None)
        with patch.object(main.collector, 'delete_profile', new=AsyncMock(return_value={'ok':True,'deleted':'synthetic-profile'})):
            self.check('DELETE', '/api/collector/profile')
        for path, target, code in [('start','start',500),('check-auth','check_auth',400),
                                   ('navigate/bad','navigate',400),('collect/bad','collect',400)]:
            with patch.object(main.collector, target, new=AsyncMock(side_effect=RuntimeError('Synthetic failure'))):
                template = '/api/collector/navigate/{target}' if path.startswith('navigate/') else '/api/collector/collect/{kind}' if path.startswith('collect/') else None
                self.check('POST', '/api/collector/'+path, code, template=template)

    def test_previews_incomplete_and_dialog_persistence(self):
        for kind in ('friends','followers','dialogs'):
            item = {'vk_id':1,'full_name':'Synthetic One'} if kind != 'dialogs' else {'dialog_key':'synthetic-1','full_name':'Synthetic Dialog'}
            preview = {'kind':kind,'collected_at':'2099-01-01','count':1,'items':[item],'report':{}}
            with patch.object(main.collector, 'collect', new=AsyncMock(return_value=preview)):
                self.check('POST', '/api/collector/collect/'+kind, template='/api/collector/collect/{kind}')
            main.collector.state.preview = preview
            self.check('GET', '/api/collector/preview')
            saved = self.check('POST', '/api/collector/save-preview')
            if kind != 'dialogs':
                self.assertEqual(saved['status'], 'INCOMPLETE')
                self.assertEqual(saved['snapshot_id'], self.check('POST', '/api/collector/save-preview')['snapshot_id'])
        self.assertEqual(len(self.check('GET', '/api/dialogs')), 1)
        self.assertEqual(self.check('GET', '/api/dashboard')['friends']['current'], 0)

    def test_files_relations_message_stats_and_zip(self):
        def upload(name, data, kind='relations'):
            return self.check('POST','/api/import/file', data={'import_type':kind,'relation_type':'friend'},
                              files={'file':(name, data, 'application/octet-stream')})
        upload('empty.json', b'{"people": []}')
        upload('messages.json', json.dumps([{'vk_id':1,'full_name':'Synthetic One','period_start':'2099-01-01',
                                            'period_end':'2099-01-02','incoming_count':2}]).encode(), 'message_stats')
        self.check('GET','/api/messages/leaderboard')
        self.check('GET','/api/dashboard')
        archive = io.BytesIO()
        with zipfile.ZipFile(archive, 'w') as z:
            z.writestr('empty.json', '{"people": []}')
        result = upload('synthetic.zip', archive.getvalue())
        self.assertEqual(result['processed_files'], ['empty.json'])
        self.check('POST','/api/import/file',400, data={'import_type':'relations'}, files={'file':('bad.json',b'invalid')})

    def test_organization_previews_jobs_and_pending_busy_semantics(self):
        self.check('GET','/api/collector/source/classify?source_url=https://vk.com/club1',template='/api/collector/source/classify')
        result = {'source':'vk','source_url':'https://vk.com/club1','profiles':[],'diagnostics':{'status':'PARSER_DEGRADED'}}
        with patch.object(main.collector,'collect_public_organization_source',new=AsyncMock(return_value=result)):
            self.check('POST','/api/collector/organization-source',json={'source_url':'https://vk.com/club1','options':[]})
        main.collector.state.preview = result
        self.assertEqual(self.check('GET','/api/collector/preview'), result)
        self.check('POST','/api/collector/save-preview',400)
        for response in ({'operation_id':'synthetic','state':'QUEUED'},
                         {'status':'COLLECTOR_BUSY','state':'COLLECTOR_BUSY','operation_id':'',
                          'current_operation':{'operation_id':'synthetic','state':'RUNNING'}}):
            with patch.object(main.collector,'start_organization_source_job',new=AsyncMock(return_value=response)):
                self.check('POST','/api/collector/organization-source/jobs',json={'source_url':'https://vk.com/club1'})
        for method, suffix, target, result in [('GET','','get_organization_source_job',{'operation_id':'synthetic','state':'RUNNING'}),
                ('GET','/result','get_organization_source_job_result',{'operation':{'operation_id':'synthetic','state':'RUNNING'},'result_available':False}),
                ('POST','/cancel','cancel_organization_source_job',{'operation_id':'synthetic','state':'CANCELLED'})]:
            base='/api/collector/organization-source/jobs/'
            with patch.object(main.collector,target,new=AsyncMock(return_value=result)):
                self.check(method,base+'synthetic'+suffix,template=base+'{operation_id}'+suffix)
            with patch.object(main.collector,target,new=AsyncMock(side_effect=KeyError('missing'))):
                self.check(method,base+'missing'+suffix,404,template=base+'{operation_id}'+suffix)

    def test_unhandled_500_is_plain_text_not_fake_json_envelope(self):
        with patch.object(main,'dashboard',side_effect=RuntimeError('Synthetic failure')):
            self.assertEqual(self.check('GET','/api/dashboard',500), 'Internal Server Error')
