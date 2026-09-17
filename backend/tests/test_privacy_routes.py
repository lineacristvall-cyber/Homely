"""Real loopback HTTP export tests with isolated temporary data and mocked auth."""
import http.client
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
from backend import server
from backend.cloud.supabase import CloudError
from backend.privacy import SCHEMA_VERSION

A, B = 'owner-a', 'owner-b'
SA, SB = 'A' * 43, 'B' * 43


def project(identifier, name):
    return {'id': identifier, 'name': name, 'createdAt': '2026-09-13T00:00:00Z',
            'brief': {'quantity': 6}, 'candidates': [], 'decisions': []}


class Session:
    def __init__(self, owner):
        self.owner = owner
        self.access_token = 'PRIVATE_JWT_' + owner

    def user(self):
        return {'id': self.owner}


class PrivacyRouteTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.base = Path(temp.name)
        for name in ('projects', 'assets', 'jobs', 'web'):
            (self.base / name).mkdir()
        (self.base / 'projects' / 'local.json').write_text(json.dumps(project('local-id', 'Local private project')))
        self.mode = True
        self.failure = None
        self.malformed = False
        self.calls = []
        self.contexts = []
        self.sessions = {SA: Session(A), SB: Session(B)}
        case = self

        class Auth:
            def resolve(self, sid):
                return case.sessions.get(sid)

        class Store:
            def __init__(self, session):
                self.owner = session.owner
                case.assertIs(server.CURRENT_CLOUD.get(), session)
                case.assertEqual(server.CURRENT_OWNER.get(), self.owner)

            def list_for_export(self):
                case.calls.append(self.owner)
                if case.failure:
                    raise case.failure
                if case.malformed:
                    return [{'id': self.owner, 'brief': {'quantity': float('nan')}}]
                value = project('project-' + self.owner, 'Private ' + self.owner)
                value['access_token'] = 'PRIVATE_JWT_' + self.owner
                value['storagePath'] = str(case.base / 'private-cloud-cache' / 'secret.png')
                value['sessions'] = {'cookie': SA}
                return [value]

        class Handler(server.Handler):
            def _dispatch(self, handler):
                try:
                    return super()._dispatch(handler)
                finally:
                    case.contexts.append((server.CURRENT_CLOUD.get(), server.CURRENT_OWNER.get()))

        replacements = {'ROOT': self.base, 'DATA': self.base, 'PROJECTS': self.base / 'projects',
                        'ASSETS': self.base / 'assets', 'JOBS': self.base / 'jobs', 'WEB': self.base / 'web'}
        for key, value in replacements.items():
            patcher = patch.object(server, key, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        for patcher in (patch.object(server, 'cloud_enabled', side_effect=lambda: self.mode),
                        patch.object(server, 'auth_manager', return_value=Auth()),
                        patch.object(server, 'CloudProjectStore', Store),
                        patch.object(server, 'api_key', return_value=None)):
            patcher.start()
            self.addCleanup(patcher.stop)
        self.http = server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.thread = threading.Thread(target=self.http.serve_forever, kwargs={'poll_interval': .01}, daemon=True)
        self.thread.start()
        self.addCleanup(self.stop)

    def stop(self):
        self.http.shutdown()
        self.http.server_close()
        self.thread.join(timeout=3)

    def request(self, session=None, path='/api/privacy/export', headers=None):
        values = dict(headers or {})
        if session:
            values['Cookie'] = 'homely_auth=' + session
        connection = http.client.HTTPConnection('127.0.0.1', self.http.server_port, timeout=3)
        try:
            connection.request('GET', path, headers=values)
            response = connection.getresponse()
            body = response.read()
            return response.status, json.loads(body), dict(response.getheaders())
        finally:
            connection.close()

    def _export_rows_through_real_store(self, count):
        from backend.cloud.supabase import CloudSession, CloudSettings
        from backend.cloud.project_store import CloudProjectStore
        owner = 'aaaaaaaa-1111-4111-8111-111111111111'
        session = CloudSession(CloudSettings(publishable_key='sb_publishable_fixture'), 'fixture-jwt')
        self.sessions[SA] = session
        rows = [{'id': '%08x-0000-4000-8000-000000000000' % n, 'owner_id': owner, 'name': 'Project ' + str(n),
                 'mode': 'designer', 'version': 4, 'created_at': '2026-09-13T00:00:00Z',
                 'updated_at': '2026-09-13T00:00:00Z', 'data': {'brief': {'quantity': 6},
                 'decisions': [{'id': 'decision-' + str(n), 'projectVersion': 3}]}} for n in range(1, count + 1)]
        pages = []

        def page(method, table, filters):
            self.assertEqual((method, table), ('GET', 'homely_projects'))
            self.assertEqual(filters['owner_id'], 'eq.' + owner)
            self.assertEqual(filters['order'], 'id.asc')
            pages.append(dict(filters))
            cursor = filters.get('id', 'gt.').removeprefix('gt.')
            return [row for row in rows if row['id'] > cursor][:int(filters['limit'])]

        with patch.object(server, 'CloudProjectStore', CloudProjectStore), patch.object(session, 'user', return_value={'id': owner}), patch.object(session, '_rows', side_effect=page):
            response = self.request(SA)
        return response, pages

    def test_export_101_projects_traverses_real_owner_pagination(self):
        (status, value, headers), pages = self._export_rows_through_real_store(101)
        self.assertEqual(status, 200)
        self.assertEqual(value['projectCount'], 101)
        self.assertEqual(len({row['id'] for row in value['projects']}), 101)
        self.assertEqual(value['projects'][-1]['name'], 'Project 101')
        self.assertEqual(value['projects'][-1]['decisions'][0]['projectVersion'], 3)
        self.assertEqual(len(pages), 3)  # 100, 1, explicit terminal empty page
        self.assertNotIn('owner_id', json.dumps(value))
        self.assertIn('attachment', headers['Content-Disposition'])

    def test_export_overflow_is_explicit_without_partial_attachment(self):
        (status, value, headers), pages = self._export_rows_through_real_store(1001)
        self.assertEqual(status, 413)
        self.assertEqual(set(value), {'error'})
        self.assertIn('no partial export', value['error'])
        self.assertNotIn('Content-Disposition', headers)
        self.assertEqual(headers['Cache-Control'], 'no-store')
        self.assertEqual(len(pages), 11)
        self.assertEqual(pages[-1]['limit'], '1')

    def test_anonymous_and_invalid_session_denied_before_store(self):
        for session in (None, 'invalid', 'C' * 43):
            status, value, headers = self.request(session)
            self.assertEqual(status, 401)
            self.assertNotIn('projects', value)
            self.assertEqual(headers['Cache-Control'], 'no-store')
            self.assertNotIn('Content-Disposition', headers)
        self.assertEqual(self.calls, [])

    def test_each_owner_exports_only_current_store_rows_even_with_foreign_selector(self):
        for session, owner, other in ((SA, A, B), (SB, B, A)):
            status, value, headers = self.request(session, '/api/privacy/export?ownerId=' + other)
            self.assertEqual(status, 200)
            self.assertEqual(value['schemaVersion'], SCHEMA_VERSION)
            self.assertEqual(value['projectCount'], 1)
            self.assertEqual([p['id'] for p in value['projects']], ['project-' + owner])
            text = json.dumps(value)
            for secret in ('Private ' + other, 'Local private project', 'PRIVATE_JWT_', SA, SB, str(self.base)):
                self.assertNotIn(secret, text)
            self.assertEqual(headers['Content-Disposition'], 'attachment; filename="homely-project-export.json"')
            self.assertEqual(headers['Cache-Control'], 'no-store')
            self.assertEqual(headers['X-Content-Type-Options'], 'nosniff')
            self.assertTrue(headers['Content-Type'].startswith('application/json'))
            self.assertNotIn('Set-Cookie', headers)
        self.assertEqual(self.calls, [A, B])

    def test_store_error_safe_and_no_cloud_to_local_fallback(self):
        for failure, expected in ((CloudError('PRIVATE_JWT_ /Users/private/secrets', 503), 503),
                                  (RuntimeError('PRIVATE_JWT_ /Users/private/secrets'), 500)):
            self.failure = failure
            status, value, headers = self.request(SA)
            self.assertEqual(status, expected)
            self.assertEqual(set(value), {'error'})
            self.assertNotIn('PRIVATE_JWT_', json.dumps(value))
            self.assertNotIn('/Users/', json.dumps(value))
            self.assertNotIn('Content-Disposition', headers)
        self.failure = None
        self.assertEqual(self.request(SB)[1]['projects'][0]['id'], 'project-' + B)
        self.assertTrue(all(pair == (None, None) for pair in self.contexts))

    def test_invalid_project_json_returns_safe_validation_error(self):
        self.malformed = True
        status, value, headers = self.request(SA)
        self.assertEqual(status, 422)
        self.assertEqual(value, {'error': 'Project data could not be exported safely.'})
        self.assertNotIn('Content-Disposition', headers)

    def test_explicit_local_mode_exports_only_local_workspace(self):
        self.mode = False
        status, value, headers = self.request()
        self.assertEqual(status, 200)
        self.assertEqual([p['id'] for p in value['projects']], ['local-id'])
        self.assertEqual(self.calls, [])
        self.assertIn('attachment', headers['Content-Disposition'])
        self.assertNotIn(str(self.base), json.dumps(value))

    def test_foreign_origin_and_host_rejected_before_export(self):
        for headers in ({'Origin': 'https://foreign.example'}, {'Host': 'foreign.example'}, {'Sec-Fetch-Site': 'cross-site'}):
            self.assertEqual(self.request(SA, headers=headers)[0], 403)
        self.assertEqual(self.calls, [])


if __name__ == '__main__':
    unittest.main()
