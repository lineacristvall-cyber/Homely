import json
import io
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch, MagicMock
from urllib.error import HTTPError, URLError
from backend.cloud.supabase import CloudSettings, CloudSession
from backend.cloud import session_auth as auth

A = 'aaaaaaaa-1111-4111-8111-111111111111'
B = 'bbbbbbbb-2222-4222-8222-222222222222'


def user(user_id=A):
    return {'id': user_id, 'email': 'person@example.invalid', 'user_metadata': {'secret': 'not-public'}}


def tokens(access='access-A', refresh='refresh-A', expires=60):
    return {'access_token': access, 'refresh_token': refresh, 'expires_in': expires, 'user': {'id': B}}


class SessionTests(unittest.TestCase):
    def setUp(self):
        self.now = [100.0]
        self.settings = CloudSettings(publishable_key='sb_publishable_fixture')
        self.manager = auth.AuthManager(self.settings, clock=lambda: self.now[0], refresh_leeway=10)

    def login(self, identity=A, access='access-A', refresh='refresh-A', expires=60):
        with patch.object(auth, '_auth_request', side_effect=[tokens(access, refresh, expires), user(identity)]):
            return self.manager.sign_in('person@example.invalid', 'fixture-password')

    def test_recovery_and_resend_are_explicit_generic_requests(self):
        with patch.object(auth, '_auth_request', return_value={}) as request:
            self.assertIn('If', self.manager.recover('person@example.invalid')['message'])
            self.assertIn('If', self.manager.resend('person@example.invalid')['message'])
        self.assertEqual([c.args[2] for c in request.call_args_list], ['/auth/v1/recover', '/auth/v1/resend'])
        self.assertEqual(request.call_args_list[1].args[3]['type'], 'signup')

    def test_recovery_verifies_token_before_update_and_invalidates_only_owner(self):
        own = self.login()['session_id']
        other = self.login(B)['session_id']
        with patch.object(auth, '_auth_request', side_effect=[tokens(), user(), user(), {}]) as request:
            result = self.manager.reset_password('r' * 40, 'new-fixture-password')
        self.assertEqual(request.call_args_list[0].args[3], {'token_hash': 'r' * 40, 'type': 'recovery'})
        self.assertEqual([c.args[1] for c in request.call_args_list], ['POST', 'GET', 'PUT', 'POST'])
        self.assertNotIn(self.manager._session_key(own), self.manager._sessions)
        self.assertIn(self.manager._session_key(other), self.manager._sessions)
        for secret in ('access-A', 'refresh-A', 'new-fixture-password', 'r' * 40):
            self.assertNotIn(secret, json.dumps(result))

    def test_invalid_recovery_never_updates_password(self):
        with patch.object(auth, '_auth_request', side_effect=auth.AuthError('Expired', 401)) as request:
            with self.assertRaises(auth.AuthError):
                self.manager.reset_password('r' * 40, 'new-fixture-password')
        self.assertEqual(request.call_count, 1)
        with patch.object(auth, '_auth_request') as request:
            for token, password in [('', 'long-password'), ('r' * 40, 'short'), ('r' * 40, 'x' * 1025)]:
                with self.assertRaises(auth.AuthError):
                    self.manager.reset_password(token, password)
            request.assert_not_called()

    def test_failed_recovery_update_discards_temporary_session(self):
        with patch.object(auth, '_auth_request', side_effect=[tokens(), user(), auth.AuthError('Rejected', 401), {}]) as request:
            with self.assertRaises(auth.AuthError):
                self.manager.reset_password('r' * 40, 'new-fixture-password')
        self.assertEqual(request.call_args_list[-1].args[2], '/auth/v1/logout?scope=local')
        self.assertEqual(self.manager._sessions, {})

    def test_signin_validates_remote_user_and_redacts_tokens(self):
        with patch.object(auth, '_auth_request', side_effect=[tokens(), user()]) as request:
            result = self.manager.sign_in(' person@example.invalid ', 'fixture-password')
        self.assertEqual(request.call_args_list[0].args[2], '/auth/v1/token?grant_type=password')
        self.assertEqual(request.call_args_list[1].args[2], '/auth/v1/user')
        self.assertEqual(result['user'], {'id': A, 'email': 'person@example.invalid'})
        self.assertEqual(len(result['session_id']), 43)
        self.assertNotIn(result['session_id'], self.manager._sessions)
        for value in ('access-A', 'refresh-A', 'fixture-password', 'not-public'):
            self.assertNotIn(value, json.dumps(result))
            self.assertNotIn(value, repr(self.manager))
            self.assertNotIn(value, repr(self.manager._sessions))

    def test_resolve_returns_account_specific_scope(self):
        first = self.login()
        second = self.login(B, 'access-B', 'refresh-B')
        def answer(settings, method, path, payload=None, access_token=None):
            return user(A if access_token == 'access-A' else B)
        with patch.object(auth, '_auth_request', side_effect=answer):
            first_scope = self.manager.resolve(first['session_id'])
            second_scope = self.manager.resolve(second['session_id'])
        self.assertIsInstance(first_scope, CloudSession)
        self.assertEqual(first_scope._token, 'access-A')
        self.assertEqual(second_scope._token, 'access-B')
        self.assertIsNot(first_scope, second_scope)
        self.assertIsNone(self.manager.resolve(None))
        self.assertIsNone(self.manager.resolve('unknown'))

    def test_refresh_rotates_tokens_and_checks_identity(self):
        sid = self.login()['session_id']
        self.now[0] = 151
        with patch.object(auth, '_auth_request', side_effect=[tokens('new-access', 'new-refresh'), user()]) as request:
            scope = self.manager.resolve(sid)
        self.assertEqual(scope._token, 'new-access')
        self.assertEqual(request.call_args_list[0].args[2], '/auth/v1/token?grant_type=refresh_token')
        self.assertEqual(request.call_args_list[0].args[3], {'refresh_token': 'refresh-A'})
        entry = self.manager._sessions[self.manager._session_key(sid)]
        self.assertEqual(entry.refresh_token, 'new-refresh')

    def test_refresh_concurrent_calls_do_not_reuse_rotating_token(self):
        sid = self.login()['session_id']
        self.now[0] = 151
        started, release = threading.Event(), threading.Event()
        calls = []
        def answer(settings, method, path, payload=None, access_token=None):
            calls.append(path)
            if 'grant_type=refresh_token' in path:
                started.set()
                self.assertTrue(release.wait(2))
                return tokens('new-access', 'new-refresh')
            return user()
        with patch.object(auth, '_auth_request', side_effect=answer), ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(self.manager.resolve, sid)
            self.assertTrue(started.wait(2))
            second = pool.submit(self.manager.resolve, sid)
            release.set()
            self.assertEqual(first.result(timeout=3)._token, 'new-access')
            self.assertEqual(second.result(timeout=3)._token, 'new-access')
        self.assertEqual(sum('grant_type=refresh_token' in path for path in calls), 1)

    def test_idle_and_absolute_expiry_stop_before_network(self):
        self.manager = auth.AuthManager(self.settings, idle_ttl=10, absolute_ttl=25, clock=lambda: self.now[0], refresh_leeway=0)
        sid = self.login(expires=3600)['session_id']
        self.now[0] += 11
        with patch.object(auth, '_auth_request') as request:
            self.assertIsNone(self.manager.resolve(sid))
            request.assert_not_called()
        sid = self.login(expires=3600)['session_id']
        with patch.object(auth, '_auth_request', return_value=user()):
            for _ in range(3):
                self.now[0] += 8
                self.assertIsNotNone(self.manager.resolve(sid))
            self.now[0] += 2
            self.assertIsNone(self.manager.resolve(sid))

    def test_revoked_or_wrong_user_invalidates_locally(self):
        for response in (auth.AuthError('revoked', 401), user(B)):
            sid = self.login()['session_id']
            with patch.object(auth, '_auth_request', side_effect=response if isinstance(response, Exception) else None, return_value=response):
                self.assertIsNone(self.manager.resolve(sid))
            self.assertIsNone(self.manager.resolve(sid))

    def test_uncertain_refresh_fails_closed_without_retry(self):
        sid = self.login()['session_id']
        self.now[0] = 151
        with patch.object(auth, '_auth_request', side_effect=auth.AuthError('provider unavailable', 503)) as request:
            with self.assertRaises(auth.AuthError):
                self.manager.resolve(sid)
            self.assertEqual(request.call_count, 1)
        self.assertIsNone(self.manager.resolve(sid))

    def test_refresh_cannot_change_account(self):
        sid = self.login()['session_id']
        self.now[0] = 151
        with patch.object(auth, '_auth_request', side_effect=[tokens('access-B', 'refresh-B'), user(B)]):
            self.assertIsNone(self.manager.resolve(sid))
        self.assertIsNone(self.manager.resolve(sid))

    def test_provider_outage_does_not_resolve_or_destroy_unexpired_session(self):
        sid = self.login()['session_id']
        with patch.object(auth, '_auth_request', side_effect=auth.AuthError('unavailable', 503)):
            with self.assertRaises(auth.AuthError):
                self.manager.resolve(sid)
        with patch.object(auth, '_auth_request', return_value=user()):
            self.assertIsNotNone(self.manager.resolve(sid))

    def test_signout_is_local_scope_and_always_forgets(self):
        first = self.login()['session_id']
        second = self.login(B, 'access-B', 'refresh-B')['session_id']
        with patch.object(auth, '_auth_request', side_effect=auth.AuthError('unavailable', 503)) as request:
            result = self.manager.sign_out(first)
        self.assertEqual(result, {'signed_out': True, 'provider_revoked': False})
        self.assertEqual(request.call_args.args[2], '/auth/v1/logout?scope=local')
        self.assertIsNone(self.manager.resolve(first))
        with patch.object(auth, '_auth_request', return_value=user(B)):
            self.assertIsNotNone(self.manager.resolve(second))

    def test_signout_during_refresh_prevents_scope_return(self):
        sid = self.login()['session_id']
        self.now[0] = 151
        started, release = threading.Event(), threading.Event()
        def answer(settings, method, path, payload=None, access_token=None):
            if 'grant_type=refresh_token' in path:
                started.set()
                release.wait(2)
                return tokens('new-access', 'new-refresh')
            return user() if path.endswith('/user') else {}
        with patch.object(auth, '_auth_request', side_effect=answer), ThreadPoolExecutor(max_workers=2) as pool:
            resolving = pool.submit(self.manager.resolve, sid)
            self.assertTrue(started.wait(2))
            removed = threading.Event()
            class ObservedSessions(dict):
                def pop(self, key, default=None):
                    result = super().pop(key, default)
                    removed.set()
                    return result
            with self.manager._lock:
                self.manager._sessions = ObservedSessions(self.manager._sessions)
            signing_out = pool.submit(self.manager.sign_out, sid)
            self.assertTrue(removed.wait(2))
            release.set()
            self.assertIsNone(resolving.result(timeout=3))
            self.assertEqual(signing_out.result(timeout=3), {'signed_out': True, 'provider_revoked': True})
        self.assertIsNone(self.manager.resolve(sid))

    def test_signup_never_returns_or_retains_tokens(self):
        with patch.object(auth, '_auth_request', return_value={'user': user()}):
            result = self.manager.sign_up('person@example.invalid', 'fixture-password')
        self.assertTrue(result['email_confirmation_required'])
        self.assertEqual(len(self.manager._sessions), 0)
        with patch.object(auth, '_auth_request', side_effect=[tokens(), {}]):
            result = self.manager.sign_up('person@example.invalid', 'fixture-password')
        self.assertTrue(result['sign_in_required'])
        self.assertNotIn('access_token', result)
        self.assertEqual(len(self.manager._sessions), 0)

    def test_invalid_inputs_configuration_and_token_response(self):
        with patch.object(auth, '_auth_request') as request:
            for email, password in [('invalid', 'password'), ('a@b.test', ''), ('a@b.test', 'x' * 1025)]:
                with self.assertRaises(auth.AuthError):
                    self.manager.sign_in(email, password)
            request.assert_not_called()
        with self.assertRaises(auth.AuthError):
            auth.AuthManager(self.settings, absolute_ttl=999999)
        with patch.object(auth, '_auth_request', return_value=tokens(expires=float('nan'))):
            with self.assertRaises(auth.AuthError):
                self.manager.sign_in('a@b.test', 'password')


class GatewayTests(unittest.TestCase):
    def test_preauth_has_apikey_but_no_bearer_and_errors_are_generic(self):
        opener = MagicMock()
        opener.open.side_effect = HTTPError('https://example.invalid', 400, 'sensitive-body', {}, None)
        settings = CloudSettings(publishable_key='sb_publishable_fixture')
        with patch.object(auth, 'build_opener', return_value=opener):
            with self.assertRaises(auth.AuthError) as caught:
                auth._auth_request(settings, 'POST', '/auth/v1/token?grant_type=password', {'email': 'a@b.test', 'password': 'fixture-password'})
        request = opener.open.call_args.args[0]
        self.assertIsNone(request.get_header('Authorization'))
        self.assertEqual(request.get_header('Apikey'), 'sb_publishable_fixture')
        self.assertNotIn('sensitive', str(caught.exception))
        self.assertEqual(opener.open.call_count, 1)
        self.assertEqual(opener.open.call_args.kwargs['timeout'], 12)

    def test_allowlisted_provider_errors_never_expose_payload(self):
        cases = [('email_not_confirmed', 400, 'email_not_confirmed', 401),
                 ('invalid_credentials', 400, 'invalid_credentials', 401),
                 ('user_not_found', 400, 'invalid_credentials', 401),
                 ('over_request_rate_limit', 429, 'rate_limited', 429),
                 ('unexpected_failure', 500, 'provider_configuration', 503),
                 ('unrecognized_private_code', 403, 'invalid_credentials', 401)]
        for code, status, expected, outward_status in cases:
            with self.subTest(code=code):
                opener = MagicMock()
                payload = json.dumps({'code': code, 'message': 'PRIVATE PASSWORD TOKEN EMAIL'}).encode()
                opener.open.side_effect = HTTPError('https://example.invalid', status, 'private', {}, io.BytesIO(payload))
                with patch.object(auth, 'build_opener', return_value=opener):
                    with self.assertRaises(auth.AuthError) as caught:
                        auth._auth_request(self.settings if hasattr(self, 'settings') else CloudSettings(publishable_key='sb_publishable_fixture'), 'POST', '/auth/v1/token?grant_type=password', {})
                self.assertEqual(caught.exception.code, expected)
                self.assertEqual(caught.exception.status, outward_status)
                self.assertNotIn('PRIVATE', str(caught.exception))

    def test_unsupported_endpoint_never_sends_credentials(self):
        with patch.object(auth, 'build_opener') as opener:
            with self.assertRaises(auth.AuthError):
                auth._auth_request(CloudSettings(publishable_key='sb_publishable_fixture'), 'GET', 'https://attacker.invalid')
            opener.assert_not_called()

if __name__ == '__main__':
    unittest.main()
