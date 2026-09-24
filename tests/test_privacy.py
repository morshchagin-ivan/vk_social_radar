"""U06 local boundary tests. Only synthetic data, temp files and mocked transports."""
from __future__ import annotations
import ast
import asyncio
import io
import json
import os
import runpy
import socket
import stat
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import httpx
from fastapi.testclient import TestClient

from app import collector as collector_module, db, importers, main, privacy
from app.ai import composition
from app.ai.contracts import GenerationRequest, Message, ProviderUnavailableError
from app.ai.providers.lmstudio import LMStudioProvider
from app.ai.settings import save_settings
from scripts.check_privacy import check, secret_categories, sensitive_name
from test_ai_provider import NetworkBlockedTests

ROOT = Path(__file__).resolve().parents[1]
SENTINEL = 'SYNTHETIC_PRIVATE_PERSON_PROMPT_TOKEN'


class PrivacyFixture(NetworkBlockedTests):
    def setUp(self):
        super().setUp()
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.enterContext(patch.multiple(db, DATA_DIR=self.root, DB_PATH=self.root/'test.db',
                         IMPORT_DIR=self.root/'imports', BACKUP_DIR=self.root/'backups'))
        self.enterContext(patch.object(importers,'IMPORT_DIR',self.root/'imports'))
        db.init_db()
        self.enterContext(patch.object(main,'init_db',side_effect=AssertionError('No lifespan')))
        self.client=TestClient(main.app,base_url='http://127.0.0.1',raise_server_exceptions=False)
        self.addCleanup(self.client.close)


class NetworkPrivacyTests(PrivacyFixture):
    def test_sec_001_002_launcher_is_fixed_loopback_and_access_logs_off(self):
        with patch('uvicorn.run') as run:
            self.enterContext(patch.dict(os.environ,{'HOST':'0.0.0.0','PORT':'1'}))
            runpy.run_path(str(ROOT/'run_server.py'),run_name='__main__')
            run.assert_called_once_with('app.main:app',host='127.0.0.1',port=8765,reload=False,access_log=False)

    def test_sec_003_unexpected_host_rejected_before_handler(self):
        with patch.object(main,'dashboard',side_effect=AssertionError('Must not run')):
            for host in ['evil.example','127.0.0.1.evil.com','localhost.evil.com','user@localhost','127.0.0.1:','[::1']:
                self.assertEqual(self.client.get('/api/dashboard',headers={'Host':host}).status_code,400)
            self.assertEqual(self.client.get('/api/dashboard',headers=[('Host','localhost'),('Host','evil.example')]).status_code,400)

    def test_sec_004_local_hosts_and_same_origin_allowed(self):
        for host in ['127.0.0.1','localhost','[::1]','127.0.0.1:8765']:
            response=self.client.get('/api/health',headers={'Host':host,'Origin':'http://'+host})
            self.assertEqual(response.status_code,200)
            self.assertEqual(response.headers['x-content-type-options'],'nosniff')

    def test_sec_005_cors_and_cross_origin_rejected(self):
        for origin in ['https://evil.example','null','http://localhost','http://127.0.0.1:9999','http://127.0.0.1?']:
            response=self.client.put('/api/settings',headers={'Origin':origin},json={})
            self.assertEqual(response.status_code,403)
            self.assertNotIn('access-control-allow-origin',response.headers)
        self.assertEqual(self.client.get('/api/health',headers={'Sec-Fetch-Site':'cross-site'}).status_code,403)
        response=self.client.options('/api/settings',headers={'Origin':'https://evil.example','Access-Control-Request-Method':'PUT'})
        self.assertEqual(response.status_code,403)
        self.assertNotIn('access-control-allow-origin',response.headers)

    def test_sec_llm_001_007_loopback_forms(self):
        for value,expected in [('http://127.0.0.1:1234/v1/','http://127.0.0.1:1234/v1'),
                               ('http://LOCALHOST:1234/v1','http://127.0.0.1:1234/v1'),
                               ('http://[::1]:1234/v1','http://[::1]:1234/v1')]:
            self.assertEqual(privacy.local_llm_url(value),expected)

    def test_sec_llm_002_003_004_008_remote_and_lan_always_rejected(self):
        for value in ['http://127.0.0.1.evil.com/v1','https://example.com/v1','https://8.8.8.8/v1',
                      'http://192.168.1.2/v1','http://10.0.0.1/v1','http://localhost.evil.com/v1',
                      'http://[::ffff:127.0.0.1]/v1','http://127.1/v1','http://localhost./v1']:
            with self.assertRaises(privacy.PrivacyPolicyError): privacy.local_llm_url(value)

    def test_sec_llm_005_006_schemes_credentials_and_ambiguous_urls(self):
        for value in ['file:///secret','ftp://localhost/v1','http://user:pass@localhost/v1',
                      'http://localhost/v1?token='+SENTINEL,'http://localhost/v1#'+SENTINEL,
                      'http://localhost\\@evil.example','http://local%68ost/v1','http://localhost:0/v1',
                      'http://localhost:99999/v1','http://localhost:/v1','http://localhost/\nsecret','',None]:
            with self.assertRaises(privacy.PrivacyPolicyError) as error: privacy.local_llm_url(value)
            self.assertNotIn(SENTINEL,str(error.exception))

    def test_sec_llm_009_validation_without_dns_network(self):
        with patch.object(socket,'getaddrinfo',side_effect=AssertionError('No DNS')), \
             patch.object(socket.socket,'connect',side_effect=AssertionError('No sockets')):
            self.assertEqual(privacy.local_llm_url('http://localhost:1234/v1'),'http://127.0.0.1:1234/v1')
            with self.assertRaises(privacy.PrivacyPolicyError): privacy.local_llm_url('http://remote.example/v1')

    def test_settings_policy_is_atomic_and_provider_rechecks_existing_db(self):
        response=self.client.put('/api/settings',json={'lmstudio_model':'changed','lmstudio_base_url':'https://example.com/v1'})
        self.assertEqual(response.status_code,400)
        self.assertEqual(self.client.get('/api/settings').json()['lmstudio_model'],'')
        with db.get_connection() as conn:
            conn.execute("UPDATE app_settings SET value=? WHERE key='lmstudio_base_url'",('http://example.com/v1',))
        with patch.object(composition,'LMStudioProvider',side_effect=AssertionError('Must not construct')):
            with self.assertRaises(privacy.PrivacyPolicyError): composition.get_provider()
        self.assertEqual(self.client.get('/api/lmstudio/models').status_code,503)

    def test_legacy_credentialed_endpoint_is_redacted_without_rewriting_storage(self):
        unsafe='http://user:'+SENTINEL+'@example.com/v1'
        with db.get_connection() as conn:
            conn.execute("UPDATE app_settings SET value=? WHERE key='lmstudio_base_url'",(unsafe,))
        response=self.client.get('/api/settings')
        self.assertEqual(response.json()['lmstudio_base_url'],'')
        self.assertNotIn(SENTINEL,response.text)
        with db.get_connection() as conn:
            self.assertEqual(conn.execute("SELECT value FROM app_settings WHERE key='lmstudio_base_url'").fetchone()[0],unsafe)

    def test_provider_denies_remote_even_with_mock_transport(self):
        with self.assertRaises(privacy.PrivacyPolicyError):
            LMStudioProvider('https://remote.example/v1',transport=httpx.MockTransport(lambda _:None))
        transport=Mock()
        provider=LMStudioProvider('http://127.0.0.1:1234/v1',transport=transport)
        provider.base_url='https://remote.example/v1'
        with self.assertRaises(privacy.PrivacyPolicyError): provider.list_models()
        transport.handle_request.assert_not_called()

    def test_proxy_environment_and_redirects_disabled(self):
        requests=[]
        def handler(request):
            requests.append(request)
            return httpx.Response(302,headers={'Location':'https://evil.example/'+SENTINEL})
        original=httpx.Client
        with patch.object(httpx,'Client',wraps=original) as client:
            provider=LMStudioProvider('http://localhost:1234/v1',transport=httpx.MockTransport(handler))
            with self.assertRaises(Exception): provider.list_models()
            self.assertIs(client.call_args.kwargs['trust_env'],False)
            self.assertIs(client.call_args.kwargs['follow_redirects'],False)
        self.assertEqual(len(requests),1)
        self.assertEqual(requests[0].url.host,'127.0.0.1')

    def test_sec_log_001_provider_error_logs_no_payload(self):
        provider=LMStudioProvider('http://127.0.0.1:1234/v1',transport=httpx.MockTransport(
            lambda _:httpx.Response(500,text=SENTINEL)))
        with self.assertLogs('httpx',level='INFO') as logs:
            with self.assertRaises(ProviderUnavailableError) as error:
                provider.generate(GenerationRequest('synthetic',(Message('user',SENTINEL),),0.2))
        self.assertNotIn(SENTINEL,' '.join(logs.output)+str(error.exception))

    def test_sec_log_002_credential_and_query_urls_never_logged(self):
        for url in ['http://user:'+SENTINEL+'@localhost/v1','http://localhost/v1?token='+SENTINEL]:
            with self.assertNoLogs('httpx',level='DEBUG'):
                with self.assertRaises(privacy.PrivacyPolicyError): LMStudioProvider(url)

    def test_sec_err_001_public_exceptions_and_validation_hide_sensitive_data(self):
        raw=f'SQL password={SENTINEL} C:\\private\\session.db'
        with patch.object(main,'import_snapshot',side_effect=ValueError(raw)):
            response=self.client.post('/api/import/snapshot',json={})
            self.assertEqual(response.status_code,400)
            self.assertNotIn(SENTINEL,response.text)
            self.assertNotIn('session.db',response.text)
        response=self.client.post('/api/import/snapshot',content='{"secret":"'+SENTINEL,headers={'Content-Type':'application/json'})
        self.assertEqual(response.status_code,422)
        self.assertNotIn(SENTINEL,response.text)
        self.assertNotIn('input',response.json()['detail'][0])
        with patch.object(main,'dashboard',side_effect=RuntimeError(raw)), self.assertNoLogs('uvicorn.error',level='DEBUG'):
            response=self.client.get('/api/dashboard')
            self.assertEqual(response.status_code,500)
            self.assertEqual(response.text,'Internal Server Error')


class StoragePrivacyTests(PrivacyFixture):
    def test_sec_data_001_ignored_sensitive_paths(self):
        paths=['data/social_radar.db','data/social_radar.db-wal','data/social_radar.db-shm',
               'data/vk_browser_profile/Default/Cookies','data/collector_previews/private.json',
               'data/imports/private.csv','logs/collector/raw.html','.env','.env.local','cookies.txt']
        result=subprocess.run(['git','check-ignore','-z','--stdin'],input=('\0'.join(paths)+'\0').encode(),cwd=ROOT,capture_output=True)
        self.assertEqual(set(result.stdout.decode().strip('\0').split('\0')),set(paths))

    def test_sec_data_002_tracked_privacy_guard(self):
        self.assertEqual(check(ROOT),[])
        self.assertTrue(sensitive_name('data/private.db-wal'))
        self.assertTrue(sensitive_name('nested/.env'))
        self.assertFalse(sensitive_name('data/imports/.gitkeep'))

    def test_obvious_secret_guard_reports_only_categories(self):
        key='-----BEGIN '+'PRIVATE KEY-----'
        self.assertEqual(secret_categories(key),{'private-key'})
        self.assertEqual(secret_categories('api_key = "'+'sk-'+'a'*40+'"'),{'token-literal','credential-literal'})
        self.assertFalse(secret_categories('password = "synthetic-placeholder"'))

    def test_sec_data_003_004_005_retention_bounded_and_keeps_structure(self):
        diagnostics=self.root/'logs'/'collector'
        diagnostics.mkdir(parents=True)
        outside=self.root/'imports'; outside.mkdir(exist_ok=True)
        sibling=outside/'friends_20000101_000000.json'; sibling.write_text(SENTINEL)
        old=diagnostics/'friends_20000101_000000.json'; old.write_text('synthetic')
        raw=diagnostics/'dialogs_20000101_000000.html'; raw.write_text('synthetic')
        current=diagnostics/'friends_20990101_000000.json'; current.write_text('synthetic')
        keep=diagnostics/'.gitkeep'; keep.touch()
        other=diagnostics/'notes.txt'; other.write_text('synthetic')
        nested=diagnostics/'nested'; nested.mkdir()
        (nested/'dialogs_20000101_000000.png').write_bytes(b'synthetic')
        for p in [old,raw,sibling,keep,other]: os.utime(p,(1,1))
        self.assertEqual(privacy.prune_diagnostics(diagnostics),2)
        self.assertEqual(sibling.read_text(),SENTINEL)
        for p in [current,keep,other,nested/'dialogs_20000101_000000.png']: self.assertTrue(p.exists())
        self.assertEqual(privacy.prune_diagnostics(self.root/'missing'),0)

    def test_retention_refuses_reparse_ancestor_and_tolerates_unlink_failure(self):
        diagnostics=self.root/'collector'; diagnostics.mkdir()
        item=diagnostics/'dialogs_20000101_000000.json'; item.write_text(SENTINEL); os.utime(item,(1,1))
        original=Path.lstat
        def reparse(path,*args,**kwargs):
            if path==diagnostics:
                return SimpleNamespace(st_mode=stat.S_IFDIR,st_file_attributes=stat.FILE_ATTRIBUTE_REPARSE_POINT)
            return original(path,*args,**kwargs)
        with patch.object(Path,'lstat',reparse): self.assertEqual(privacy.prune_diagnostics(diagnostics),0)
        with patch.object(Path,'unlink',side_effect=PermissionError): self.assertEqual(privacy.prune_diagnostics(diagnostics),0)
        self.assertEqual(item.read_text(),SENTINEL)

    def test_diagnostics_do_not_capture_page_or_sensitive_report(self):
        instance=collector_module.SafeVKCollector()
        instance.page=Mock()
        diagnostics=self.root/'collector'
        with patch.object(collector_module,'DIAGNOSTICS_DIR',diagnostics):
            name=asyncio.run(instance._save_diagnostics('../../escape',{'html':SENTINEL,'url':SENTINEL,'profiles_found':3,'title':SENTINEL}))
        payload=(diagnostics/name).read_text()
        self.assertNotIn(SENTINEL,payload)
        self.assertEqual(json.loads(payload),{'kind':'collector','counts':{'profiles_found':3}})
        instance.page.content.assert_not_called()
        instance.page.screenshot.assert_not_called()
        self.assertEqual(len(list(diagnostics.iterdir())),1)

    def test_sec_browser_001_002_profile_not_served_or_overridden(self):
        self.assertFalse(collector_module.PROFILE_DIR.is_relative_to(main.STATIC_DIR))
        self.assertNotIn('VK_COLLECTOR_PROFILE_DIR',(ROOT/'app/collector.py').read_text(encoding='utf-8'))
        routes=[r.path for r in main.app.routes if hasattr(r,'path')]
        self.assertNotIn('/data/{path:path}',routes)
        self.assertEqual(self.client.get('/data/vk_browser_profile/synthetic').status_code,404)
        function=next(n for n in ast.parse((ROOT/'app/main.py').read_text(encoding='utf-8')).body if isinstance(n,ast.FunctionDef) and n.name=='index')
        self.assertIn("FileResponse(STATIC_DIR / 'index.html')",ast.unparse(function))

    def test_profile_delete_stays_in_explicit_temp_root_and_rejects_unsafe_storage(self):
        profile=self.root/'profile'
        profile.mkdir()
        self.assertTrue(profile.resolve().is_relative_to(self.root.resolve()))
        (profile/'synthetic-session').write_text(SENTINEL)
        outside=self.root/'outside'; outside.write_text(SENTINEL)
        instance=collector_module.SafeVKCollector()
        with patch.object(collector_module,'PROFILE_DIR',profile):
            result=asyncio.run(instance.delete_profile())
            self.assertEqual(result,{'ok':True,'deleted':'dedicated-local-profile'})
            with patch.object(collector_module,'safe_directory',side_effect=privacy.PrivacyPolicyError('unsafe')), \
                 patch.object(collector_module.shutil,'rmtree') as remove:
                with self.assertRaises(privacy.PrivacyPolicyError): asyncio.run(instance.delete_profile())
                remove.assert_not_called()
        self.assertFalse(profile.exists())
        self.assertEqual(outside.read_text(),SENTINEL)

    def test_sec_path_001_upload_traversal_absolute_and_windows_paths(self):
        for name in ['../escape.json','..\\escape.json','C:\\escape.json','/escape.json','\\\\server\\share.json','stream:secret.json','CON.json']:
            with self.assertRaises(privacy.PrivacyPolicyError): importers.import_uploaded_file(name,b'[]','relations','friend')
        self.assertEqual(list((self.root/'imports').iterdir()),[])

    def test_imports_unique_contained_and_no_absolute_path_in_response(self):
        a=importers.import_uploaded_file('synthetic.json',b'[]','relations','friend')
        b=importers.import_uploaded_file('synthetic.json',b'[]','relations','friend')
        self.assertNotEqual(a['stored_as'],b['stored_as'])
        self.assertEqual(Path(a['stored_as']).name,a['stored_as'])
        self.assertTrue((self.root/'imports'/a['stored_as']).exists())

    def test_sec_import_001_malformed_payload_safely_reported_and_stored(self):
        response=self.client.post('/api/import/file',data={'import_type':'relations','relation_type':'friend'},
                                  files={'file':('synthetic.json',SENTINEL.encode())})
        self.assertEqual(response.status_code,400)
        self.assertNotIn(SENTINEL,response.text)
        with db.get_connection() as conn:
            self.assertEqual(conn.execute('SELECT error_text FROM import_jobs').fetchone()[0],'Import failed')

    def test_import_byte_archive_expansion_and_member_paths_bounded(self):
        with patch.object(importers,'MAX_IMPORT_BYTES',8):
            with self.assertRaises(privacy.PrivacyPolicyError): importers.import_uploaded_file('synthetic.json',b'x'*9,'relations','friend')
        for member,content in [('../escape.json','[]'),('big.json','x'*100)]:
            archive=io.BytesIO()
            with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z: z.writestr(member,content)
            with patch.object(importers,'MAX_IMPORT_BYTES',50):
                with self.assertRaises(privacy.PrivacyPolicyError): importers._import_zip(archive.getvalue(),'relations','friend',None)
        self.assertFalse((self.root/'escape.json').exists())
        archive=io.BytesIO()
        with zipfile.ZipFile(archive,'w') as z: z.writestr('nested/empty.json','[]')
        result=importers._import_zip(archive.getvalue(),'relations','friend',None)
        self.assertEqual(result['processed_files'],['nested/empty.json'])
        self.assertFalse((self.root/'nested').exists())

    def test_upload_read_is_bounded(self):
        file=SimpleNamespace(filename='synthetic.json',read=AsyncMock(return_value=b'x'*9))
        with patch.object(main,'MAX_IMPORT_BYTES',8):
            with self.assertRaises(Exception): asyncio.run(main.post_import_file(file,'relations','friend',None))
        file.read.assert_awaited_once_with(9)

    def test_collector_request_guard_is_fail_closed(self):
        instance=collector_module.SafeVKCollector()
        for url in ['http://127.0.0.1:8765','http://localhost','https://evil.example/'+SENTINEL,'file:///secret','https://vk.com.evil.example','https://user:secret@vk.com']:
            route=SimpleNamespace(continue_=AsyncMock(),abort=AsyncMock())
            asyncio.run(instance._route_request(route,SimpleNamespace(url=url)))
            route.continue_.assert_not_awaited(); route.abort.assert_awaited_once()
        route=SimpleNamespace(continue_=AsyncMock(side_effect=RuntimeError(SENTINEL)),abort=AsyncMock())
        asyncio.run(instance._route_request(route,SimpleNamespace(url='https://vk.com')))
        route.continue_.assert_awaited_once(); route.abort.assert_awaited_once()
        self.assertNotIn(SENTINEL,str(instance.state))
        for url in ['ws://localhost','wss://evil.example','wss://user:secret@vk.com']:
            route=SimpleNamespace(url=url,connect_to_server=Mock(),close=AsyncMock())
            asyncio.run(instance._route_web_socket(route))
            route.connect_to_server.assert_not_called(); route.close.assert_awaited_once()
        route=SimpleNamespace(url='wss://vk.com',connect_to_server=Mock(side_effect=RuntimeError(SENTINEL)),close=AsyncMock())
        asyncio.run(instance._route_web_socket(route))
        route.connect_to_server.assert_called_once(); route.close.assert_awaited_once()
        self.assertNotIn(SENTINEL,str(instance.state))

    def test_collector_guard_allowed_hosts_and_safe_error_status(self):
        instance=collector_module.SafeVKCollector()
        instance.state.last_error=None
        status=asyncio.run(instance.get_status())
        with patch.object(main.collector,'get_status',new=AsyncMock(return_value=status)):
            response=self.client.get('/api/collector/status')
            self.assertEqual(response.status_code,200)
            self.assertIsNone(response.json()['last_error'])
        for url in ['https://vk.com','https://cdn.vkuserphoto.ru','data:text/plain,synthetic','about:blank']:
            route=SimpleNamespace(continue_=AsyncMock(),abort=AsyncMock())
            asyncio.run(instance._route_request(route,SimpleNamespace(url=url)))
            route.continue_.assert_awaited_once(); route.abort.assert_not_awaited()
        instance._set_error(SENTINEL)
        status=asyncio.run(instance.get_status())
        self.assertNotIn(SENTINEL,json.dumps(status))
        self.assertEqual(status['profile_dir'],'dedicated-local-profile')
        self.assertEqual(privacy.safe_url_display('https://user:password@vk.com/id1?token='+SENTINEL),'https://vk.com')
        route=SimpleNamespace(url='wss://push.vk.com',connect_to_server=Mock(),close=AsyncMock())
        asyncio.run(instance._route_web_socket(route))
        route.connect_to_server.assert_called_once(); route.close.assert_not_awaited()
        source=(ROOT/'app/collector.py').read_text(encoding='utf-8')
        self.assertIn('service_workers="block"',source)
        self.assertIn('await self.context.route_web_socket("**/*", self._route_web_socket)',source)

    def test_sec_xss_001_actual_helpers_and_rendering_boundaries(self):
        source=(ROOT/'static/app.js').read_text(encoding='utf-8')
        helpers=source[source.index('function esc('):source.index('async function api(')]
        script=helpers+'''
const assert=require('node:assert/strict');
for(const v of ['javascript:alert(1)','data:text/html,<script>x</script>','file:///secret','https://user:pass@vk.com']) assert.equal(safeHref(v),'#');
assert.ok(safeHref('https://vk.com/id1').startsWith('https://vk.com/'));
assert.equal(esc('<img src=x onerror="alert(1)">'), '&lt;img src=x onerror=&quot;alert(1)&quot;&gt;');
'''
        result=subprocess.run(['node','-e',script],text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(source.count('href="${safeHref('),3)
        self.assertNotIn('href="${esc(',source)
        for escaped in ['esc(x.summary)','esc(e)','esc(x.cautions.join','esc(i.full_name)','esc(d.preview','esc(i.details']:
            self.assertIn(escaped,source)
        self.assertNotIn('eval(',source)
        self.assertNotIn('new Function',source)
