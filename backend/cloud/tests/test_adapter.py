import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit
from backend.cloud.supabase import CloudError, CloudSession, CloudSettings, PROJECT_URL

A = 'aaaaaaaa-1111-4111-8111-111111111111'
B = 'bbbbbbbb-2222-4222-8222-222222222222'
P = 'cccccccc-3333-4333-8333-333333333333'

class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.settings = CloudSettings(publishable_key='sb_publishable_fixture')
        self.session = CloudSession(self.settings, 'fixture-user-token')

    def test_export_pagination_terminal_probe_and_owner_scope(self):
        ids = ['%08x-0000-4000-8000-000000000000' % n for n in range(1, 1001)]
        rows = [{'id': identifier, 'owner_id': A} for identifier in ids]
        with patch.object(self.session, 'user', return_value={'id': A}), patch.object(self.session, '_rows', side_effect=[rows[n:n + 100] for n in range(0, 1000, 100)] + [[]]) as request:
            self.assertEqual(self.session.list_projects_for_export(), rows)
        self.assertEqual(request.call_count, 11)
        for index, call in enumerate(request.call_args_list):
            query = call.args[2]
            self.assertEqual(query['owner_id'], 'eq.' + A)
            self.assertEqual(query['order'], 'id.asc')
            if index:
                self.assertEqual(query['id'], 'gt.' + ids[index * 100 - 1])
        self.assertEqual(request.call_args.args[2]['limit'], '1')

    def test_export_does_not_treat_short_page_as_complete(self):
        first = {'id': '00000001-0000-4000-8000-000000000000', 'owner_id': A}
        second = {'id': '00000002-0000-4000-8000-000000000000', 'owner_id': A}
        with patch.object(self.session, 'user', return_value={'id': A}), patch.object(self.session, '_rows', side_effect=[[first], [second], []]) as request:
            self.assertEqual(self.session.list_projects_for_export(), [first, second])
        self.assertEqual(request.call_count, 3)

    def test_export_rejects_wrong_owner_repeated_cursor_and_page_failure(self):
        first = {'id': P, 'owner_id': A}
        for pages in ([[{'id': P, 'owner_id': B}]], [[first], [first]], [[first], CloudError('Fixture outage', 503)]):
            with self.subTest(pages=len(pages)), patch.object(self.session, 'user', return_value={'id': A}), patch.object(self.session, '_rows', side_effect=pages), self.assertRaises(CloudError):
                self.session.list_projects_for_export()

    def test_export_limits_fail_closed_and_leave_ui_list_unchanged(self):
        for invalid in (True, 0, 1001, '1000'):
            with self.subTest(invalid=invalid), self.assertRaises(CloudError):
                self.session.list_projects_for_export(invalid)
        rows = [{'id': '%08x-0000-4000-8000-000000000000' % n, 'owner_id': A} for n in range(1, 12)]
        with patch.object(self.session, 'user', return_value={'id': A}), patch.object(self.session, '_rows', side_effect=[[row] for row in rows]), self.assertRaises(CloudError) as caught:
            self.session.list_projects_for_export()
        self.assertEqual(caught.exception.status, 413)
        with patch.object(self.session, 'user', return_value={'id': A}), patch.object(self.session, '_rows', return_value=[]) as request:
            self.session.list_projects()
        self.assertEqual(request.call_args.args[2]['limit'], '100')
        self.assertEqual(request.call_args.args[2]['order'], 'updated_at.desc')

    def test_credentials_redacted_and_service_keys_rejected(self):
        self.assertNotIn('sb_publishable_fixture', repr(self.settings))
        self.assertNotIn('fixture-user-token', repr(self.session))
        for key in ('sb_secret_fixture', 'eyJfixture', ''):
            with self.assertRaises(CloudError):
                CloudSettings(publishable_key=key)

    def test_unapproved_project_rejected(self):
        with self.assertRaises(CloudError):
            CloudSettings(url='https://attacker.example', publishable_key='sb_publishable_fixture')

    def test_owner_comes_from_auth_not_caller_or_jwt_decode(self):
        with patch('backend.cloud.supabase._request', side_effect=[{'id': A}, [{'id': P}]]) as request:
            self.session.create_project('Room')
        self.assertEqual(request.call_args_list[0].args[3], '/auth/v1/user')
        self.assertEqual(request.call_args_list[1].args[4]['owner_id'], A)

    def test_list_scopes_each_user(self):
        for owner in (A, B):
            with patch('backend.cloud.supabase._request', side_effect=[{'id': owner}, []]) as request:
                self.assertEqual(self.session.list_projects(), [])
            query = parse_qs(urlsplit(request.call_args.args[3]).query)
            self.assertEqual(query['owner_id'], ['eq.' + owner])

    def test_cross_account_project_returns_not_found(self):
        with patch('backend.cloud.supabase._request', side_effect=[{'id': B}, []]):
            with self.assertRaises(CloudError) as caught:
                self.session.get_project(P)
        self.assertEqual(caught.exception.status, 404)

    def test_update_has_atomic_owner_and_version_predicate(self):
        with patch('backend.cloud.supabase._request', side_effect=[{'id': A}, []]) as request:
            with self.assertRaises(CloudError) as caught:
                self.session.update_project(P, 3, data={'brief': {}})
        self.assertEqual(caught.exception.status, 409)
        query = parse_qs(urlsplit(request.call_args.args[3]).query)
        self.assertEqual(query['version'], ['eq.3'])
        self.assertEqual(query['owner_id'], ['eq.' + A])
        self.assertNotIn('version', request.call_args.args[4])

    def test_invalid_auth_stops_before_data_request(self):
        with patch('backend.cloud.supabase._request', return_value={}) as request:
            with self.assertRaises(CloudError):
                self.session.list_projects()
        self.assertEqual(request.call_count, 1)

    def test_anonymous_account_cannot_persist(self):
        with patch('backend.cloud.supabase._request', return_value={'id': A, 'is_anonymous': True}):
            with self.assertRaises(CloudError):
                self.session.list_projects()

    def test_upload_consent_and_mime_guard(self):
        project = {'id': P, 'owner_id': A}
        with patch.object(self.session, 'get_project', return_value=project), patch('backend.cloud.supabase._request') as request:
            for content, mime, consent in [(b'wrong', 'image/png', {'upload': True}), (b'\x89PNG\r\n\x1a\nfixture', 'image/png', {})]:
                with self.assertRaises(CloudError):
                    self.session.upload_asset(P, 'room_original', content, mime, consent)
            self.assertEqual(request.call_count, 0)

    def test_upload_uses_owner_project_path_without_overwrite(self):
        with patch.object(self.session, 'get_project', return_value={'id': P, 'owner_id': A}), patch('backend.cloud.supabase._request', return_value=[]) as request:
            asset = self.session.upload_asset(P, 'room_original', b'\x89PNG\r\n\x1a\nfixture', 'image/png', {'upload': True})
        self.assertTrue(asset['object_path'].startswith(A + '/' + P + '/'))
        self.assertEqual(request.call_args.args[5]['x-upsert'], 'false')
        self.assertIn('/rest/v1/homely_assets', request.call_args_list[0].args[3])

    def test_private_link_checks_owner_and_short_ttl(self):
        with patch('backend.cloud.supabase._request', side_effect=[{'id': A}, [{'object_path': B + '/' + P + '/file'}]]):
            with self.assertRaises(CloudError):
                self.session.signed_asset_url(P)
        with patch('backend.cloud.supabase._request', return_value={'id': A}):
            with self.assertRaises(CloudError):
                self.session.signed_asset_url(P, 3600)

if __name__ == '__main__':
    unittest.main()
