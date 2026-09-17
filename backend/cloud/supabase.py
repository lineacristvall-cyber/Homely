"""Dependency-free, user-JWT-scoped Supabase REST/Auth/Storage adapter.

No service key accepted. Auth validates the JWT remotely; Postgres and Storage
RLS remain authoritative. This module does not replace or migrate the local store.
"""
from dataclasses import dataclass, field
import json
import os
import uuid
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, quote
from urllib.request import Request, build_opener, HTTPRedirectHandler

PROJECT_REF = 'bbwmwwupvqajidqznsly'
PROJECT_URL = 'https://' + PROJECT_REF + '.supabase.co'
BUCKET = 'homely-private-assets'


class CloudError(RuntimeError):
    def __init__(self, message, status=502):
        super().__init__(message)
        self.status = status


@dataclass(frozen=True)
class CloudSettings:
    url: str = PROJECT_URL
    publishable_key: str = field(default='', repr=False)

    def __post_init__(self):
        if self.url.rstrip('/') != PROJECT_URL:
            raise CloudError('Cloud configuration must target the approved Homely project.', 400)
        # New low-privilege key only: never accidentally use a bypass-RLS secret.
        if not self.publishable_key.startswith('sb_publishable_') or any(c.isspace() for c in self.publishable_key):
            raise CloudError('Configure the approved project publishable key; secret/service-role keys are not accepted.', 503)

    @classmethod
    def from_environment(cls):
        return cls(url=os.environ.get('SUPABASE_URL', PROJECT_URL),
                   publishable_key=os.environ.get('SUPABASE_PUBLISHABLE_KEY', ''))


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, newurl):
        return None


def _uuid(value):
    try:
        return str(uuid.UUID(str(value)))
    except (ValueError, TypeError, AttributeError):
        raise CloudError('Invalid cloud resource identifier.', 400) from None


def _request(settings, token, method, path, payload=None, headers=None, binary=False):
    if not path.startswith(('/auth/v1/', '/rest/v1/', '/storage/v1/')) or '://' in path:
        raise CloudError('Unsupported cloud operation.', 400)
    request_headers = {'apikey': settings.publishable_key, 'Authorization': 'Bearer ' + token,
                       'Accept': 'application/json'}
    if headers:
        request_headers.update(headers)
    if binary:
        data = payload
    else:
        data = json.dumps(payload, allow_nan=False).encode() if payload is not None else None
        request_headers['Content-Type'] = 'application/json'
    request = Request(settings.url.rstrip('/') + path, data=data, headers=request_headers, method=method)
    try:
        with build_opener(_NoRedirect()).open(request, timeout=15) as response:
            body = response.read(12_000_001)
        if len(body) > 12_000_000:
            raise CloudError('Cloud response exceeded the size limit.')
        return json.loads(body) if body else None
    except HTTPError as exc:
        status = exc.code
        messages = {401: 'Sign in again to access your cloud workspace.', 403: 'This cloud operation is not permitted.',
                    404: 'Cloud resource was not found.', 409: 'Cloud resource conflict; refresh before retrying.',
                    429: 'Cloud request limit reached; retry later.'}
        raise CloudError(messages.get(status, 'Cloud request failed; no local data was changed.'), status) from None
    except (URLError, OSError, ValueError):
        raise CloudError('Cloud could not be reached or returned an invalid response; local data is preserved.') from None


class CloudSession:
    """One authenticated user's scope; never share an instance between users."""
    def __init__(self, settings: CloudSettings, access_token: str):
        if not isinstance(access_token, str) or not access_token or any(c.isspace() for c in access_token):
            raise CloudError('A signed-in user session is required.', 401)
        self.settings = settings
        self._token = access_token

    def __repr__(self):
        return 'CloudSession(project=' + PROJECT_REF + ', credentials=<redacted>)'

    def user(self):
        # Server response is authentic; no unverified JWT payload authorization.
        data = _request(self.settings, self._token, 'GET', '/auth/v1/user')
        if not isinstance(data, dict) or not data.get('id'):
            raise CloudError('Supabase did not validate the signed-in user.', 401)
        if data.get('is_anonymous') is True:
            raise CloudError('A permanent signed-in account is required for cloud persistence.', 403)
        return {'id': _uuid(data['id'])}

    def _rows(self, method, table, filters=None, payload=None):
        if table not in ('homely_projects', 'homely_jobs', 'homely_assets'):
            raise CloudError('Unsupported cloud table.', 400)
        query = urlencode(filters or {}, safe='(),.*')
        return _request(self.settings, self._token, method, '/rest/v1/' + table + ('?' + query if query else ''),
                        payload, {'Prefer': 'return=representation'})

    def list_projects(self):
        owner = self.user()['id']
        return self._rows('GET', 'homely_projects', {'owner_id': 'eq.' + owner, 'order': 'updated_at.desc', 'limit': '100'})

    def list_projects_for_export(self, max_projects=1000):
        """Bounded owner-only keyset enumeration; never return a truncated export.

        UI list_projects retains its 100-row limit. Export uses immutable UUID
        order, not changing updated_at offsets, and requires a terminal empty
        page. This is live enumeration, not a transactional database snapshot.
        """
        if isinstance(max_projects, bool) or not isinstance(max_projects, int) or not 1 <= max_projects <= 1000:
            raise CloudError('Export project limit must be between 1 and 1000.', 400)
        owner = self.user()['id']
        records, cursor = [], None
        for _ in range(11):
            limit = min(100, max_projects - len(records) + 1)
            filters = {'owner_id': 'eq.' + owner, 'order': 'id.asc', 'limit': str(limit)}
            if cursor is not None:
                filters['id'] = 'gt.' + cursor
            page = self._rows('GET', 'homely_projects', filters)
            if not isinstance(page, list) or len(page) > limit:
                raise CloudError('Cloud returned an invalid export page.', 502)
            if not page:
                return records
            for row in page:
                if not isinstance(row, dict) or row.get('owner_id') != owner:
                    raise CloudError('Cloud export ownership did not match this account.', 403)
                identifier = _uuid(row.get('id'))
                if cursor is not None and identifier <= cursor:
                    raise CloudError('Cloud export pagination did not advance safely.', 502)
                cursor = identifier
                records.append(row)
                if len(records) > max_projects:
                    raise CloudError('Project export exceeds its configured project limit; no partial export was returned.', 413)
        raise CloudError('Project export could not finish within its page limit; no partial export was returned.', 413)

    def get_project(self, project_id):
        owner = self.user()['id']
        rows = self._rows('GET', 'homely_projects', {'id': 'eq.' + _uuid(project_id), 'owner_id': 'eq.' + owner, 'limit': '1'})
        if not rows:
            raise CloudError('Cloud project was not found or is outside this account.', 404)
        return rows[0]

    def create_project(self, name, mode='designer', data=None):
        owner = self.user()['id']
        if not isinstance(name, str) or not 1 <= len(name.strip()) <= 200 or mode not in ('designer', 'diy'):
            raise CloudError('A valid project name and mode are required.', 400)
        if data is not None and not isinstance(data, dict):
            raise CloudError('Project data must be an object.', 400)
        rows = self._rows('POST', 'homely_projects', payload={'owner_id': owner, 'name': name.strip(), 'mode': mode, 'data': data or {}})
        return rows[0]

    def update_project(self, project_id, expected_version, *, data, name=None):
        owner = self.user()['id']
        if isinstance(expected_version, bool) or not isinstance(expected_version, int) or expected_version < 1 or not isinstance(data, dict):
            raise CloudError('Project update requires data and its current version.', 400)
        payload = {'data': data}
        if name is not None:
            if not isinstance(name, str) or not 1 <= len(name.strip()) <= 200:
                raise CloudError('A valid project name is required.', 400)
            payload['name'] = name.strip()
        rows = self._rows('PATCH', 'homely_projects', {'id': 'eq.' + _uuid(project_id), 'owner_id': 'eq.' + owner,
                                                     'version': 'eq.' + str(expected_version)}, payload)
        if not rows:
            raise CloudError('Project changed or is not accessible; refresh before retrying.', 409)
        return rows[0]

    def list_jobs(self, project_id):
        project = self.get_project(project_id)
        return self._rows('GET', 'homely_jobs', {'project_id': 'eq.' + project['id'], 'owner_id': 'eq.' + project['owner_id'],
                                               'order': 'created_at.desc', 'limit': '100'})

    def upload_asset(self, project_id, kind, content, mime_type, consent, lineage=None):
        project = self.get_project(project_id)
        if kind not in ('room_original', 'product_source', 'illustrative_render') or not isinstance(content, bytes) or not 1 <= len(content) <= 10_485_760:
            raise CloudError('A supported image up to 10 MiB is required.', 400)
        valid = {'image/png': content.startswith(b'\x89PNG\r\n\x1a\n'),
                 'image/jpeg': content.startswith(b'\xff\xd8\xff'),
                 'image/webp': content[:4] == b'RIFF' and content[8:12] == b'WEBP'}
        if not valid.get(mime_type):
            raise CloudError('Image bytes do not match an allowed MIME type.', 400)
        if not isinstance(consent, dict) or consent.get('upload') is not True:
            raise CloudError('Explicit cloud upload consent is required.', 400)
        if lineage is not None and not isinstance(lineage, dict):
            raise CloudError('Asset lineage must be an object.', 400)
        asset_id = str(uuid.uuid4())
        path = project['owner_id'] + '/' + project['id'] + '/' + asset_id
        row = {'id': asset_id, 'owner_id': project['owner_id'], 'project_id': project['id'], 'kind': kind,
               'object_path': path, 'mime_type': mime_type, 'byte_size': len(content), 'consent': consent, 'lineage': lineage or {}}
        self._rows('POST', 'homely_assets', payload=row)
        # Metadata precedes bytes so RLS can require consent and project lineage.
        # A failed upload leaves metadata only; reconcile explicitly, never retry
        # a write blindly or delete an original to make an upload succeed.
        _request(self.settings, self._token, 'POST', '/storage/v1/object/' + BUCKET + '/' + quote(path, safe='/'),
                 content, {'Content-Type': mime_type, 'x-upsert': 'false'}, binary=True)
        return row

    def signed_asset_url(self, asset_id, expires_in=60):
        owner = self.user()['id']
        if isinstance(expires_in, bool) or not isinstance(expires_in, int) or not 1 <= expires_in <= 300:
            raise CloudError('Private image links must expire within five minutes.', 400)
        rows = self._rows('GET', 'homely_assets', {'id': 'eq.' + _uuid(asset_id), 'owner_id': 'eq.' + owner, 'limit': '1'})
        if not rows:
            raise CloudError('Asset was not found or is outside this account.', 404)
        path = rows[0]['object_path']
        if not path.startswith(owner + '/'):
            raise CloudError('Asset ownership did not match.', 403)
        result = _request(self.settings, self._token, 'POST', '/storage/v1/object/sign/' + BUCKET + '/' + quote(path, safe='/'),
                          {'expiresIn': expires_in})
        signed = result.get('signedURL') if isinstance(result, dict) else None
        if not isinstance(signed, str) or not signed.startswith('/object/sign/'):
            raise CloudError('Cloud did not return an expected private asset URL.')
        return self.settings.url + '/storage/v1' + signed
