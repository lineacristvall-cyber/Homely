"""Server-only Supabase Auth and bounded in-memory opaque sessions.

No tokens are returned in public user data. Integrator must put session_id only in
an HttpOnly, SameSite cookie (Secure on HTTPS), apply CSRF/origin checks to mutations,
set Cache-Control: no-store, and never serialize a CloudSession. Restart signs all
local sessions out. This is single-process state, not a distributed session store.
"""
from __future__ import annotations
from dataclasses import dataclass, field
import hashlib
import json
import math
import re
import secrets
import threading
import time
import uuid
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener, HTTPRedirectHandler
from .supabase import CloudSettings, CloudSession, CloudError


class AuthError(CloudError):
    def __init__(self, message, status=401, code='authentication_failed'):
        super().__init__(message, status)
        self.code = code


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, newurl):
        return None


def _auth_request(settings, method, path, payload=None, access_token=None):
    allowed = {('POST', '/auth/v1/token?grant_type=password'), ('POST', '/auth/v1/token?grant_type=refresh_token'),
               ('GET', '/auth/v1/user'), ('POST', '/auth/v1/logout?scope=local'), ('POST', '/auth/v1/signup'), ('POST', '/auth/v1/recover'),
               ('POST', '/auth/v1/resend'), ('POST', '/auth/v1/verify'), ('PUT', '/auth/v1/user')}
    if (method, path) not in allowed:
        raise AuthError('Unsupported authentication operation.', 400, 'invalid_operation')
    headers = {'apikey': settings.publishable_key, 'Content-Type': 'application/json', 'Accept': 'application/json'}
    if access_token is not None:
        headers['Authorization'] = 'Bearer ' + access_token
    data = json.dumps(payload, allow_nan=False).encode() if payload is not None else None
    request = Request(settings.url.rstrip('/') + path, data=data, headers=headers, method=method)
    try:
        with build_opener(_NoRedirect()).open(request, timeout=12) as response:
            body = response.read(100001)
        if len(body) > 100000:
            raise AuthError('Authentication response exceeded its limit.', 502, 'provider_response')
        result = json.loads(body) if body else {}
        if not isinstance(result, dict):
            raise ValueError()
        return result
    except HTTPError as exc:
        # Read only a bounded machine code; never log or return provider payloads.
        # Unknown accounts and wrong passwords deliberately share one response.
        provider_code = None
        try:
            error_body = exc.read(4097)
            if len(error_body) <= 4096:
                parsed = json.loads(error_body)
                if isinstance(parsed, dict):
                    provider_code = parsed.get('error_code') or parsed.get('code')
        except (OSError, ValueError, TypeError, AttributeError):
            pass
        if provider_code == 'email_not_confirmed' and path == '/auth/v1/token?grant_type=password':
            raise AuthError('Confirm your email using the Homely confirmation email, then sign in again.', 401, 'email_not_confirmed') from None
        if provider_code in ('over_request_rate_limit', 'over_email_send_rate_limit'):
            raise AuthError('Authentication is rate limited. Please try again later.', 429, 'rate_limited') from None
        if provider_code in ('bad_jwt', 'unexpected_failure'):
            raise AuthError('Authentication service configuration needs attention. Please contact the workspace owner.', 503, 'provider_configuration') from None
        if exc.code in (400, 401, 403, 422):
            raise AuthError('The email and password combination was not accepted. Check both fields and try again. If needed, request password recovery; no reset has been sent.', 401, 'invalid_credentials') from None
        if exc.code == 429:
            raise AuthError('Authentication is rate limited. Please try again later.', 429, 'rate_limited') from None
        raise AuthError('Authentication service is unavailable. Please try again later.', 502, 'provider_error') from None
    except (URLError, OSError):
        raise AuthError('Authentication service could not be reached. Please try again later.', 503, 'provider_unavailable') from None
    except (ValueError, TypeError):
        raise AuthError('Authentication service returned an invalid response.', 502, 'provider_response') from None


def _credentials(email, password):
    if not isinstance(email, str) or not 3 <= len(email.strip()) <= 254 or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email.strip()):
        raise AuthError('Enter a valid email address.', 400, 'invalid_input')
    if not isinstance(password, str) or not 1 <= len(password) <= 1024 or '\x00' in password:
        raise AuthError('Enter a password between 1 and 1,024 characters.', 400, 'invalid_input')
    return email.strip(), password


def _token(value):
    return isinstance(value, str) and 1 <= len(value) <= 16000 and not any(c.isspace() for c in value)


def _public_user(value):
    if not isinstance(value, dict) or value.get('is_anonymous') is True:
        raise AuthError('A permanent authenticated account is required.', 401)
    try:
        user_id = str(uuid.UUID(value.get('id', '')))
    except (ValueError, TypeError, AttributeError):
        raise AuthError('The authentication service did not verify a user.', 401) from None
    email = value.get('email')
    return {'id': user_id, 'email': email if isinstance(email, str) and len(email) <= 254 else None}


@dataclass(repr=False)
class _Session:
    user: dict
    access_token: str
    refresh_token: str
    access_expires: float
    absolute_expires: float
    idle_expires: float
    lock: object = field(default_factory=threading.Lock)


class AuthManager:
    """Single-process session gateway; methods never select a default account.

    resolve validates /auth/v1/user each time and serializes rotating refreshes.
    Unknown/expired/revoked sessions return None. Provider outages raise AuthError;
    an uncertain refresh invalidates locally because retry could reuse an already
    rotated token. Remote revocation may remain undetectable until token expiry,
    depending on Supabase access-token behavior; local sign_out is immediate.
    """
    def __init__(self, settings: CloudSettings, *, idle_ttl=1800, absolute_ttl=28800,
                 refresh_leeway=30, max_sessions=1000, clock=time.monotonic):
        if not isinstance(settings, CloudSettings):
            raise AuthError('Valid cloud settings are required.', 503, 'not_configured')
        for value, low, high in ((idle_ttl, 1, 3600), (absolute_ttl, 1, 86400),
                                 (refresh_leeway, 0, 120), (max_sessions, 1, 10000)):
            if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
                raise AuthError('Invalid server session lifetime or capacity.', 500, 'session_configuration')
        self.settings = settings
        self._idle_ttl = min(idle_ttl, absolute_ttl)
        self._absolute_ttl = absolute_ttl
        self._leeway = refresh_leeway
        self._max_sessions = max_sessions
        self._clock = clock
        self._sessions = {}
        self._lock = threading.Lock()

    def __repr__(self):
        return 'AuthManager(credentials=<redacted>, sessions=<private>)'

    @staticmethod
    def _session_key(session_id):
        if not isinstance(session_id, str) or not re.fullmatch(r'[A-Za-z0-9_-]{43}', session_id):
            return None
        return hashlib.sha256(session_id.encode()).hexdigest()

    def _verified_tokens(self, result):
        if not isinstance(result, dict) or not _token(result.get('access_token')) or not _token(result.get('refresh_token')):
            raise AuthError('The authentication service did not return a usable session.', 502, 'provider_response')
        lifetime = result.get('expires_in')
        try:
            valid = isinstance(lifetime, (int, float)) and not isinstance(lifetime, bool) and math.isfinite(lifetime) and lifetime > 0
        except OverflowError:
            valid = False
        if not valid:
            raise AuthError('The authentication service returned an invalid session expiry.', 502, 'provider_response')
        user = _public_user(_auth_request(self.settings, 'GET', '/auth/v1/user', access_token=result['access_token']))
        return user, result['access_token'], result['refresh_token'], min(lifetime, 3600)

    def _remove(self, key, entry):
        with self._lock:
            if self._sessions.get(key) is entry:
                self._sessions.pop(key)
        entry.access_token = ''
        entry.refresh_token = ''

    def _current(self, key, entry):
        with self._lock:
            return self._sessions.get(key) is entry

    def sign_in(self, email, password):
        email, password = _credentials(email, password)
        response = _auth_request(self.settings, 'POST', '/auth/v1/token?grant_type=password', {'email': email, 'password': password})
        user, access, refresh, lifetime = self._verified_tokens(response)
        now = self._clock()
        session_id = secrets.token_urlsafe(32)
        entry = _Session(user, access, refresh, now + lifetime, now + self._absolute_ttl, now + self._idle_ttl)
        with self._lock:
            # Expired entries are inaccessible immediately; no provider reads here.
            expired = [key for key, session in self._sessions.items() if min(session.absolute_expires, session.idle_expires) <= now]
            for key in expired:
                self._sessions.pop(key, None)
            if len(self._sessions) >= self._max_sessions:
                raise AuthError('The server session capacity is full. Try again later.', 503, 'session_capacity')
            self._sessions[self._session_key(session_id)] = entry
        return {'session_id': session_id, 'user': dict(user)}

    def resolve(self, session_id):
        key = self._session_key(session_id)
        if key is None:
            return None
        with self._lock:
            entry = self._sessions.get(key)
        if entry is None:
            return None
        with entry.lock:
            if not self._current(key, entry):
                return None
            now = self._clock()
            if now >= min(entry.absolute_expires, entry.idle_expires):
                self._remove(key, entry)
                return None
            if now + self._leeway >= entry.access_expires:
                try:
                    response = _auth_request(self.settings, 'POST', '/auth/v1/token?grant_type=refresh_token',
                                             {'refresh_token': entry.refresh_token})
                    user, access, refresh, lifetime = self._verified_tokens(response)
                    if user['id'] != entry.user['id']:
                        raise AuthError('The refreshed session did not match this account.', 401)
                except AuthError as exc:
                    self._remove(key, entry)
                    if exc.status == 401:
                        return None
                    raise
                entry.user, entry.access_token, entry.refresh_token = user, access, refresh
                entry.access_expires = self._clock() + lifetime
            else:
                try:
                    user = _public_user(_auth_request(self.settings, 'GET', '/auth/v1/user', access_token=entry.access_token))
                    if user['id'] != entry.user['id']:
                        raise AuthError('The authenticated session did not match this account.', 401)
                except AuthError as exc:
                    if exc.status == 401:
                        self._remove(key, entry)
                        return None
                    raise
                entry.user = user
            now = self._clock()
            if not self._current(key, entry):
                return None
            if now >= min(entry.absolute_expires, entry.idle_expires):
                self._remove(key, entry)
                return None
            entry.idle_expires = min(now + self._idle_ttl, entry.absolute_expires)
            return CloudSession(self.settings, entry.access_token)

    def public_user(self, session_id):
        """Return safe user fields after resolving; useful for /api/auth/session."""
        scope = self.resolve(session_id)
        if scope is None:
            return None
        key = self._session_key(session_id)
        with self._lock:
            entry = self._sessions.get(key)
            return dict(entry.user) if entry else None

    def sign_out(self, session_id):
        """Always forget locally; local provider scope preserves other devices.

        Return public revocation status; a provider failure never restores the
        local session and must not be described as remote revocation success.
        """
        key = self._session_key(session_id)
        with self._lock:
            entry = self._sessions.pop(key, None) if key else None
        if entry is None:
            return {'signed_out': True, 'provider_revoked': None}
        with entry.lock:
            access = entry.access_token
            entry.access_token = ''
            entry.refresh_token = ''
            try:
                _auth_request(self.settings, 'POST', '/auth/v1/logout?scope=local', access_token=access)
                revoked = True
            except AuthError:
                revoked = False
        return {'signed_out': True, 'provider_revoked': revoked}

    def sign_up(self, email, password):
        """Explicit caller action only; may send confirmation email. Never called
        by tests against a live provider, and never signs an account in implicitly.
        """
        email, password = _credentials(email, password)
        response = _auth_request(self.settings, 'POST', '/auth/v1/signup', {'email': email, 'password': password})
        if _token(response.get('access_token')):
            # If project email confirmation is disabled, avoid retaining an
            # unrequested login; caller must sign in via the normal entry point.
            try:
                _auth_request(self.settings, 'POST', '/auth/v1/logout?scope=local', access_token=response['access_token'])
            except AuthError:
                pass
            return {'email_confirmation_required': False, 'sign_in_required': True,
                    'message': 'Sign in with your email and password to continue.'}
        return {'email_confirmation_required': True, 'sign_in_required': True,
                'message': 'If confirmation is required for this address, follow the email instructions, then sign in.'}

    def recover(self, email):
        email, _ = _credentials(email, 'validation-only')
        _auth_request(self.settings, 'POST', '/auth/v1/recover', {'email': email})
        return {'message': 'If this address is eligible, check your email. Copy the unopened recovery link into Have a recovery email? in Homely.'}

    def resend(self, email):
        email, _ = _credentials(email, 'validation-only')
        _auth_request(self.settings, 'POST', '/auth/v1/resend', {'email': email, 'type': 'signup'})
        return {'message': 'If confirmation is needed for this address, check your email.'}

    def reset_password(self, token_hash, new_password):
        if not isinstance(token_hash, str) or not re.fullmatch(r'[A-Za-z0-9_-]{20,2048}', token_hash):
            raise AuthError('Enter a valid recovery token hash.', 400, 'invalid_input')
        if not isinstance(new_password, str) or not 8 <= len(new_password) <= 1024 or '\x00' in new_password:
            raise AuthError('Use a password between 8 and 1,024 characters.', 400, 'invalid_input')
        # Only a provider-verified recovery token can authorize this update.
        result = _auth_request(self.settings, 'POST', '/auth/v1/verify', {'token_hash': token_hash, 'type': 'recovery'})
        access = result.get('access_token')
        if not _token(access):
            raise AuthError('Recovery did not return a usable session. Request a new email.', 401, 'recovery_failed')
        try:
            user, access, refresh, lifetime = self._verified_tokens(result)
            updated = _public_user(_auth_request(self.settings, 'PUT', '/auth/v1/user', {'password': new_password}, access_token=access))
            if updated['id'] != user['id']:
                raise AuthError('Recovery account verification failed.', 401, 'recovery_failed')
            with self._lock:
                keys = [key for key, entry in self._sessions.items() if entry.user['id'] == user['id']]
                for key in keys:
                    entry = self._sessions.pop(key)
                    entry.access_token = ''
                    entry.refresh_token = ''
        finally:
            try:
                _auth_request(self.settings, 'POST', '/auth/v1/logout?scope=local', access_token=access)
            except AuthError:
                pass
        return {'message': 'Password updated. Sign in with your new password.', 'sign_in_required': True}
