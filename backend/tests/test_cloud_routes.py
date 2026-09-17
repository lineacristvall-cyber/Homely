"""Local HTTP integration checks. No real credentials, cloud calls or app data."""
import copy
import http.client
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
from backend import server
from backend.cloud.supabase import CloudError

A = 'aaaaaaaa-1111-4111-8111-111111111111'
B = 'bbbbbbbb-2222-4222-8222-222222222222'
PA = 'cccccccc-3333-4333-8333-333333333333'
PB = 'dddddddd-4444-4444-8444-444444444444'
LOCAL = 'eeeeeeee-5555-4555-8555-555555555555'
JA = 'aaaaaaaa-6666-4666-8666-666666666666'
JB = 'bbbbbbbb-7777-4777-8777-777777777777'
JL = 'cccccccc-8888-4888-8888-888888888888'
SA, SB = 'A' * 43, 'B' * 43


def project(project_id, name):
    return {'id': project_id, 'name': name, 'mode': 'pro', 'version': 1,
            'createdAt': '2026-09-13T00:00:00Z', 'updatedAt': '2026-09-13T00:00:00Z',
            'brief': {'quantity': 6, 'itemType': 'chairs'}, 'room': None, 'candidates': [], 'decisions': []}


class FakeSession:
    def __init__(self, owner):
        self.owner = owner

    def user(self):
        return {'id': self.owner}


class FakeAuthManager:
    def __init__(self):
        self.sessions = {SA: FakeSession(A), SB: FakeSession(B)}
        self.calls = []

    def resolve(self, sid):
        self.calls.append(('resolve', sid))
        return self.sessions.get(sid)

    def sign_in(self, email, password):
        self.calls.append(('sign_in', email))
        if email != 'a@example.invalid' or password != 'fixture-password':
            raise CloudError('Unable to authenticate.', 401)
        return {'session_id': SA, 'user': {'id': A, 'email': email},
                'access_token': 'fixture-auth-jwt-never-public', 'refresh_token': 'fixture-refresh-never-public'}

    def public_user(self, sid):
        session = self.sessions.get(sid)
        return {'id': session.owner} if session else None

    def sign_out(self, sid):
        self.sessions.pop(sid, None)
        return {'signed_out': True, 'provider_revoked': True}


class CloudRouteTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        for name in ('projects', 'assets', 'jobs', 'web', 'private-cloud-jobs', 'private-cloud-cache'):
            (self.base / name).mkdir()
        (self.base / 'web' / 'index.html').write_text('fixture-static')
        (self.base / 'projects' / (LOCAL + '.json')).write_text(json.dumps(project(LOCAL, 'LOCAL PRIVATE PROJECT')))
        (self.base / 'assets' / (LOCAL + '.png')).write_bytes(b'LOCAL PRIVATE IMAGE')
        for job_id, owner in ((JA, A), (JB, B), (JL, None)):
            (self.base / 'private-cloud-jobs' / (job_id + '.json')).write_text(json.dumps({'id': job_id, 'ownerId': owner, 'status': 'completed', 'projectId': PA if owner == A else PB}))
        (self.base / 'jobs' / (JL + '.json')).write_text(json.dumps({'id': JL, 'ownerId': None, 'status': 'completed', 'projectId': LOCAL}))
        self.cloud_mode = True
        self.auth = FakeAuthManager()
        self.context_records = []
        self.store_calls = []
        self.cloud_failure = None
        test = self

        class Store:
            def __init__(self, session):
                self.owner = session.owner
                if server.CURRENT_CLOUD.get() is not session or server.CURRENT_OWNER.get() != self.owner:
                    raise AssertionError('Request cloud context was not account-specific')
                test.store_calls.append(('scope', self.owner))

            def list(self):
                test.store_calls.append(('list', self.owner))
                if test.cloud_failure:
                    raise test.cloud_failure
                return [project(PA, 'Cloud A')] if self.owner == A else [project(PB, 'Cloud B')]

            def get(self, project_id):
                test.store_calls.append(('get', self.owner, project_id))
                if test.cloud_failure:
                    raise test.cloud_failure
                expected = PA if self.owner == A else PB
                return project(expected, 'Cloud ' + ('A' if self.owner == A else 'B')) if expected == project_id else None

            def create(self, value):
                test.store_calls.append(('create', self.owner))
                if test.cloud_failure:
                    raise test.cloud_failure
                result = copy.deepcopy(value)
                result['id'] = PA if self.owner == A else PB
                return result

            def read(self, asset_id):
                test.store_calls.append(('read', self.owner, asset_id))
                if asset_id != (PA if self.owner == A else PB):
                    raise CloudError('Asset not found.', 404)
                return b'private-image-' + self.owner.encode(), 'image/png'

        class RecordingHandler(server.Handler):
            def _dispatch(self, handler):
                try:
                    return super()._dispatch(handler)
                finally:
                    test.context_records.append((server.CURRENT_CLOUD.get(), server.CURRENT_OWNER.get()))

        self.patchers = [patch.object(server, 'ROOT', self.base), patch.object(server, 'DATA', self.base),
                         patch.object(server, 'PROJECTS', self.base / 'projects'), patch.object(server, 'ASSETS', self.base / 'assets'),
                         patch.object(server, 'JOBS', self.base / 'jobs'), patch.object(server, 'WEB', self.base / 'web'),
                         patch.object(server, 'cloud_enabled', side_effect=lambda: self.cloud_mode), patch.object(server, 'auth_manager', return_value=self.auth),
                         patch.object(server, 'CloudProjectStore', Store), patch.object(server, 'api_key', return_value=None)]
        for patcher in self.patchers:
            patcher.start()
            self.addCleanup(patcher.stop)
        self.http = server.ThreadingHTTPServer(('127.0.0.1', 0), RecordingHandler)
        self.port = self.http.server_address[1]
        self.thread = threading.Thread(target=self.http.serve_forever, kwargs={'poll_interval': .01}, daemon=True)
        self.thread.start()
        self.addCleanup(self.stop_http)

    def stop_http(self):
        self.http.shutdown()
        self.http.server_close()
        self.thread.join(timeout=3)

    def request(self, method, path, body=None, session=None, headers=None):
        values = {'Content-Type': 'application/json'}
        if session is not None:
            values['Cookie'] = 'homely_auth=' + session
        values.update(headers or {})
        payload = json.dumps(body).encode() if body is not None else None
        connection = http.client.HTTPConnection('127.0.0.1', self.port, timeout=5)
        try:
            connection.request(method, path, body=payload, headers=values)
            response = connection.getresponse()
            raw = response.read()
            result = json.loads(raw) if response.getheader('Content-Type', '').startswith('application/json') else raw
            return response.status, result, dict(response.getheaders())
        finally:
            connection.close()

    def test_watch_routes_require_session_and_isolate_authenticated_owners(self):
        from backend.price_watch import PriceWatchStore
        from backend.tests.test_price_watch import product
        from datetime import datetime, timezone
        clock = lambda: datetime(2026, 9, 17, 10, tzinfo=timezone.utc).timestamp()
        store = PriceWatchStore(self.base / 'private-watches.json', checker=lambda url, brief: product(), clock=clock)
        watch = store.subscribe(A, product(), consent=True)
        with patch.object(server, 'price_watch_store', return_value=store):
            self.assertEqual(self.request('GET', '/api/watches')[0], 401)
            self.assertEqual(self.request('GET', '/api/watches', session=SA)[1]['watches'][0]['id'], watch['id'])
            self.assertEqual(self.request('GET', '/api/watches', session=SB)[1]['watches'], [])
            self.assertEqual(self.request('POST', '/api/watches/' + watch['id'] + '/cancel', {}, session=SB)[0], 400)
            self.assertEqual(store.list(A)[0]['status'], 'paused')

    def test_recovery_routes_are_explicit_origin_protected_and_clear_cookie(self):
        from unittest.mock import MagicMock
        self.auth.recover = MagicMock(return_value={'message': 'If eligible, check email.'})
        self.auth.resend = MagicMock(return_value={'message': 'If eligible, check email.'})
        self.auth.reset_password = MagicMock(return_value={'message': 'Updated. Sign in.'})
        for path in ('recover', 'resend', 'reset'):
            self.assertEqual(self.request('POST', '/api/auth/' + path, {}, headers={'Origin':'https://evil.invalid'})[0], 403)
        self.auth.reset_password.assert_not_called()
        self.assertEqual(self.request('POST', '/api/auth/recover', {'email':'a@example.invalid'})[0], 200)
        self.assertEqual(self.request('POST', '/api/auth/resend', {'email':'a@example.invalid'})[0], 200)
        status, result, headers = self.request('POST', '/api/auth/reset', {'tokenHash':'r'*40, 'newPassword':'fixture-password'})
        self.assertEqual(status, 200)
        self.assertIn('Max-Age=0', headers['Set-Cookie'])
        self.assertIn('no-store', headers['Cache-Control'])
        self.auth.reset_password.assert_called_once_with('r'*40, 'fixture-password')
        self.assertNotIn('fixture-password', json.dumps(result))

    def test_anonymous_cloud_project_job_asset_and_mutation_requests_denied(self):
        for method, path, body in (('GET', '/api/projects', None), ('GET', '/api/projects/' + PA, None),
                                   ('GET', '/api/jobs/' + JA, None), ('GET', '/api/cloud-assets/' + PA, None),
                                   ('POST', '/api/projects', {'name': 'No auth'}),
                                   ('PATCH', '/api/projects/' + PA + '/brief', {'expectedVersion': 1, 'brief': {}})):
            with self.subTest(path=path):
                self.assertEqual(self.request(method, path, body)[0], 401)
        self.assertEqual(self.store_calls, [])

    def test_user_project_context_isolation_and_no_default_account(self):
        self.assertEqual(self.request('GET', '/api/projects', session=SA)[1]['projects'][0]['id'], PA)
        self.assertEqual(self.request('GET', '/api/projects', session=SB)[1]['projects'][0]['id'], PB)
        self.assertEqual(self.request('GET', '/api/projects/' + PA, session=SB)[0], 404)
        self.assertEqual(self.request('GET', '/api/projects/' + PB, session=SA)[0], 404)
        self.assertEqual(self.request('GET', '/api/projects', session='invalid-cookie')[0], 401)
        self.assertIn(('scope', A), self.store_calls)
        self.assertIn(('scope', B), self.store_calls)

    def test_job_files_are_filtered_by_authenticated_owner(self):
        self.assertEqual(self.request('GET', '/api/jobs/' + JA, session=SA)[0], 200)
        self.assertEqual(self.request('GET', '/api/jobs/' + JA, session=SB)[0], 404)
        self.assertEqual(self.request('GET', '/api/jobs/' + JB, session=SA)[0], 404)
        self.assertEqual(self.request('GET', '/api/jobs/' + JL, session=SA)[0], 404)

    def test_local_assets_and_projects_never_leak_in_cloud_mode(self):
        status, body, _ = self.request('GET', '/api/assets/' + LOCAL + '.png', session=SA)
        self.assertEqual(status, 404)
        self.assertNotIn('LOCAL PRIVATE IMAGE', str(body))
        status, body, _ = self.request('GET', '/api/projects/' + LOCAL, session=SA)
        self.assertEqual(status, 404)
        self.assertNotIn('LOCAL PRIVATE PROJECT', str(body))

    def test_cloud_failure_does_not_fall_back_to_local_list_or_create(self):
        self.cloud_failure = CloudError('Cloud unavailable.', 503)
        before = {path.name: path.read_bytes() for path in (self.base / 'projects').iterdir()}
        status, body, _ = self.request('GET', '/api/projects', session=SA)
        self.assertEqual(status, 503)
        self.assertNotIn('LOCAL PRIVATE', str(body))
        status, _, _ = self.request('POST', '/api/projects', {'name': 'New cloud project', 'mode': 'pro'}, session=SA)
        self.assertEqual(status, 503)
        after = {path.name: path.read_bytes() for path in (self.base / 'projects').iterdir()}
        self.assertEqual(before, after)

    def test_switching_same_data_to_local_cannot_expose_cloud_jobs_or_cached_images(self):
        cloud_image = server.asset_directory() / (PA + '.png')
        cloud_image.write_bytes(b'CLOUD PRIVATE ORIGINAL')
        server.save_job({'id': JA, 'ownerId': A, 'status': 'completed', 'projectId': PA})
        self.assertEqual(cloud_image.parent, self.base / 'private-cloud-cache')
        self.assertTrue((self.base / 'private-cloud-jobs' / (JA + '.json')).is_file())
        self.assertFalse((self.base / 'jobs' / (JA + '.json')).exists())
        self.assertEqual(self.request('GET', '/api/jobs/' + JA, session=SA)[0], 200)
        self.assertEqual(self.request('GET', '/api/jobs/' + JA, session=SB)[0], 404)

        # Simulate restarting in local mode against the exact same data root.
        self.cloud_mode = False
        for job_id in (JA, JB):
            with self.subTest(job_id=job_id):
                self.assertEqual(self.request('GET', '/api/jobs/' + job_id)[0], 404)
        for path in ('/api/assets/' + PA + '.png', '/api/cloud-assets/' + PA,
                     '/private-cloud-cache/' + PA + '.png', '/api/assets/../private-cloud-cache/' + PA + '.png'):
            with self.subTest(path=path):
                status, body, _ = self.request('GET', path)
                self.assertEqual(status, 404)
                self.assertNotIn('CLOUD PRIVATE ORIGINAL', str(body))
        # Genuine local records/assets remain usable, proving this is isolation,
        # not a blanket denial of every asset and job endpoint.
        self.assertEqual(self.request('GET', '/api/jobs/' + JL)[0], 200)
        self.assertEqual(self.request('GET', '/api/assets/' + LOCAL + '.png')[1], b'LOCAL PRIVATE IMAGE')
        self.assertEqual(cloud_image.read_bytes(), b'CLOUD PRIVATE ORIGINAL')
        self.cloud_mode = True
        self.assertEqual(self.request('GET', '/api/jobs/' + JA, session=SA)[0], 200)
        self.assertEqual(self.request('GET', '/api/jobs/' + JA, session=SB)[0], 404)

    def test_signin_sets_opaque_httponly_cookie_but_no_tokens_in_json(self):
        status, body, headers = self.request('POST', '/api/auth/sign-in', {'email': 'a@example.invalid', 'password': 'fixture-password'})
        self.assertEqual(status, 200)
        self.assertEqual(body['user']['id'], A)
        cookie = headers['Set-Cookie']
        self.assertIn('homely_auth=' + SA, cookie)
        self.assertIn('HttpOnly', cookie)
        self.assertIn('SameSite=Strict', cookie)
        self.assertEqual(headers['Cache-Control'], 'no-store')
        serialized = json.dumps(body)
        for secret in (SA, 'fixture-auth-jwt-never-public', 'fixture-refresh-never-public', 'fixture-password'):
            self.assertNotIn(secret, serialized)
        session_body = self.request('GET', '/api/auth/session', session=SA)[1]
        self.assertEqual(session_body, {'mode': 'cloud', 'authenticated': True, 'user': {'id': A}})
        self.assertNotIn(SA, json.dumps(session_body))

    def test_signout_clears_cookie_and_future_access_without_other_account_loss(self):
        status, body, headers = self.request('POST', '/api/auth/sign-out', {}, session=SA)
        self.assertEqual(status, 200)
        self.assertTrue(body['signed_out'])
        self.assertIn('Max-Age=0', headers['Set-Cookie'])
        self.assertEqual(self.request('GET', '/api/projects', session=SA)[0], 401)
        self.assertEqual(self.request('GET', '/api/projects', session=SB)[0], 200)

    def test_foreign_origin_host_and_cross_site_block_before_auth(self):
        for headers in ({'Origin': 'https://evil.invalid'}, {'Host': 'evil.invalid'}, {'Sec-Fetch-Site': 'cross-site'}):
            with self.subTest(headers=headers):
                self.assertEqual(self.request('POST', '/api/auth/sign-in', {'email': 'a@example.invalid', 'password': 'fixture-password'}, headers=headers)[0], 403)
        self.assertEqual(self.auth.calls, [])
        self.assertEqual(self.request('GET', '/api/projects', session=SA, headers={'Origin': 'http://127.0.0.1:' + str(self.port)})[0], 200)

    def test_exception_resets_context_before_next_request(self):
        self.cloud_failure = CloudError('Injected fixture failure.', 503)
        self.assertEqual(self.request('GET', '/api/projects', session=SA)[0], 503)
        self.cloud_failure = None
        self.assertEqual(self.request('GET', '/api/projects', session=SB)[1]['projects'][0]['id'], PB)
        self.assertEqual(self.request('GET', '/api/projects')[0], 401)
        self.http.shutdown()
        self.thread.join(timeout=3)
        self.assertGreaterEqual(len(self.context_records), 3)
        self.assertTrue(all(context == (None, None) for context in self.context_records))

    def test_cloud_asset_read_is_private_and_account_scoped(self):
        status, body, headers = self.request('GET', '/api/cloud-assets/' + PA, session=SA)
        self.assertEqual(status, 200)
        self.assertEqual(body, b'private-image-' + A.encode())
        self.assertEqual(headers['Cache-Control'], 'private, no-store')
        self.assertEqual(self.request('GET', '/api/cloud-assets/' + PA, session=SB)[0], 404)

if __name__ == '__main__':
    unittest.main()
