"""Opt-in mapping between Homely documents and authenticated Supabase storage.

No local migration, service-role use, job writes or source verification. Caller
must keep the returned canonical document; database UUID/version/times win over
submitted envelope fields. Project mode is fixed at creation in this adapter.
"""
from __future__ import annotations
import copy
from datetime import datetime, timezone
import io
import json
import uuid
import warnings
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, unquote
from urllib.request import Request, build_opener, HTTPRedirectHandler
from PIL import Image, UnidentifiedImageError
from .supabase import CloudSession, CloudError, PROJECT_URL, BUCKET

MAX_IMAGE_BYTES = 10 * 1024 * 1024
MAX_IMAGE_PIXELS = 25_000_000
MAX_DOCUMENT_BYTES = 2 * 1024 * 1024
DOCUMENT_FIELDS = ('brief', 'room', 'candidates', 'decisions', 'sourceCoverage', 'sourceCoverageComplete')
DOCUMENT_DEFAULTS = {'brief': {}, 'room': None, 'candidates': [], 'decisions': [],
                     'sourceCoverage': [], 'sourceCoverageComplete': False}
MIMES = {'PNG': 'image/png', 'JPEG': 'image/jpeg', 'WEBP': 'image/webp'}


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, newurl):
        return None


def _id(value):
    try:
        return str(uuid.UUID(str(value)))
    except (ValueError, TypeError, AttributeError):
        raise CloudError('Invalid cloud resource identifier.', 400) from None


def _mode(value):
    if value not in ('pro', 'diy'):
        raise CloudError('Project mode must be pro or diy.', 400)
    return 'designer' if value == 'pro' else 'diy'


def _document(value):
    if not isinstance(value, dict):
        raise CloudError('Project must be an object.', 400)
    data = {key: copy.deepcopy(value.get(key, DOCUMENT_DEFAULTS[key])) for key in DOCUMENT_FIELDS}
    if not isinstance(data['brief'], dict) or (data['room'] is not None and not isinstance(data['room'], dict)) or not isinstance(data['candidates'], list) or not isinstance(data['decisions'], list):
        raise CloudError('Project document fields have invalid types.', 400)
    if (not isinstance(data['sourceCoverage'], list)
            or any(not isinstance(record, dict) for record in data['sourceCoverage'])
            or not isinstance(data['sourceCoverageComplete'], bool)):
        raise CloudError('Source coverage must be a record list and a boolean completeness flag.', 400)
    try:
        encoded = json.dumps(data, allow_nan=False).encode()
    except (ValueError, TypeError, RecursionError):
        raise CloudError('Project document must contain finite JSON data.', 400) from None
    if len(encoded) > MAX_DOCUMENT_BYTES:
        raise CloudError('Project document exceeds the cloud size limit.', 413)
    return data


def _validated_image(raw, mime):
    if not isinstance(raw, bytes) or not 1 <= len(raw) <= MAX_IMAGE_BYTES:
        raise CloudError('A nonempty image up to 10 MiB is required.', 413)
    if mime not in MIMES.values():
        raise CloudError('Only JPEG, PNG and WebP images are supported.', 415)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(raw)) as image:
                if image.width <= 0 or image.height <= 0 or image.width * image.height > MAX_IMAGE_PIXELS:
                    raise CloudError('The image exceeds the pixel limit.', 413)
                if MIMES.get(image.format) != mime:
                    raise CloudError('Decoded image format does not match its MIME type.', 415)
                if getattr(image, 'n_frames', 1) != 1:
                    raise CloudError('Use a still image for room and product assets.', 415)
                image.verify()
            with Image.open(io.BytesIO(raw)) as image:
                image.load()
    except CloudError:
        raise
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError, EOFError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise CloudError('Image bytes could not be decoded safely.', 415) from None
    return mime


class CloudProjectStore:
    def __init__(self, session: CloudSession):
        if not isinstance(session, CloudSession):
            raise CloudError('An authenticated cloud session is required.', 401)
        self._session = session

    def __repr__(self):
        return 'CloudProjectStore(session=<private>)'

    def _owner(self):
        return _id(self._session.user()['id'])

    def _canonical(self, row, owner):
        if not isinstance(row, dict) or row.get('owner_id') != owner:
            raise CloudError('Cloud project ownership did not match the authenticated account.', 403)
        if row.get('mode') not in ('designer', 'diy') or isinstance(row.get('version'), bool) or not isinstance(row.get('version'), int) or row['version'] < 1:
            raise CloudError('Cloud returned an invalid project envelope.', 502)
        if not isinstance(row.get('name'), str) or not isinstance(row.get('created_at'), str) or not isinstance(row.get('updated_at'), str):
            raise CloudError('Cloud returned incomplete project metadata.', 502)
        data = _document(row.get('data', {}))
        return {'id': _id(row.get('id')), 'name': row['name'], 'mode': 'pro' if row['mode'] == 'designer' else 'diy',
                'version': row['version'], 'createdAt': row['created_at'], 'updatedAt': row['updated_at'], **data}

    def list(self):
        owner = self._owner()
        rows = self._session.list_projects()
        if not isinstance(rows, list):
            raise CloudError('Cloud returned an invalid project list.', 502)
        return [self._canonical(row, owner) for row in rows]

    def list_for_export(self):
        """Enumerate up to 1000 owned projects; overflow/failure never truncates."""
        owner = self._owner()
        rows = self._session.list_projects_for_export()
        if not isinstance(rows, list):
            raise CloudError('Cloud returned an invalid project export.', 502)
        if len(rows) > 1000:
            raise CloudError('Project export exceeds the 1000-project limit.', 413)
        return [self._canonical(row, owner) for row in rows]

    def get(self, project_id):
        project_id = _id(project_id)
        owner = self._owner()
        try:
            row = self._session.get_project(project_id)
        except CloudError as exc:
            if exc.status == 404:
                return None
            raise
        if not isinstance(row, dict) or row.get('id') != project_id:
            raise CloudError('Cloud returned a different project.', 502)
        return self._canonical(row, owner)

    def create(self, project):
        data = _document(project)
        mode = _mode(project.get('mode', 'pro'))
        owner = self._owner()
        row = self._session.create_project(project.get('name'), mode=mode, data=data)
        return self._canonical(row, owner)

    def save(self, project):
        data = _document(project)
        project_id = _id(project.get('id'))
        version = project.get('version')
        if isinstance(version, bool) or not isinstance(version, int) or version < 2:
            raise CloudError('Save requires an incremented project version.', 409)
        expected = version - 1
        mode = _mode(project.get('mode'))
        owner = self._owner()
        # No upsert: preserve both ownership and the creation-time mode.
        current = self._session.get_project(project_id)
        self._canonical(current, owner)
        if current.get('id') != project_id or current.get('version') != expected:
            raise CloudError('Cloud project changed; refresh before saving.', 409)
        if current.get('mode') != mode:
            raise CloudError('Project mode cannot be changed by saving its document.', 400)
        row = self._session.update_project(project_id, expected, data=data, name=project.get('name'))
        if not isinstance(row, dict) or row.get('id') != project_id or row.get('version') != version:
            raise CloudError('Cloud save returned an unexpected project version.', 502)
        return self._canonical(row, owner)

    def upload(self, project_id, kind, raw, mime, consent, lineage=None):
        project_id = _id(project_id)
        _validated_image(raw, mime)
        if not isinstance(consent, dict) or consent.get('upload') is not True:
            raise CloudError('Explicit consent is required before cloud image upload.', 400)
        owner = self._owner()
        row = self._session.upload_asset(project_id, kind, raw, mime, consent, lineage)
        if not isinstance(row, dict) or row.get('owner_id') != owner or row.get('project_id') != project_id:
            raise CloudError('Cloud asset ownership did not match the authenticated project.', 403)
        asset_id = _id(row.get('id'))
        return {'assetId': asset_id, 'imageUrl': '/api/cloud-assets/' + asset_id, 'kind': row.get('kind'),
                'mimeType': mime, 'byteSize': len(raw), 'uploadedAt': datetime.now(timezone.utc).isoformat()}

    def read(self, asset_id):
        asset_id = _id(asset_id)
        owner = self._owner()
        signed = self._session.signed_asset_url(asset_id, expires_in=60)
        try:
            parts = urlsplit(signed)
            origin = urlsplit(PROJECT_URL)
            path = unquote(parts.path)
            prefix = '/storage/v1/object/sign/' + BUCKET + '/'
            segments = path[len(prefix):].split('/') if path.startswith(prefix) else []
            if (parts.scheme != 'https' or parts.netloc != origin.netloc or parts.username or parts.password or parts.fragment
                    or len(segments) != 3 or segments[0] != owner or segments[2] != asset_id
                    or _id(segments[1]) != segments[1] or not parts.query):
                raise ValueError()
        except (ValueError, TypeError, CloudError):
            raise CloudError('Cloud returned an invalid private image location.', 502) from None
        # No Authorization header: this short-lived URL is already signed. Never
        # return it publicly, follow redirects, or include it in an error message.
        request = Request(signed, headers={'Accept': 'image/png,image/jpeg,image/webp'}, method='GET')
        try:
            with build_opener(_NoRedirect()).open(request, timeout=15) as response:
                mime = response.headers.get('Content-Type', '').split(';', 1)[0].strip().lower()
                length = response.headers.get('Content-Length', '')
                if length.isdigit() and int(length) > MAX_IMAGE_BYTES:
                    raise CloudError('Cloud image exceeds the size limit.', 413)
                raw = response.read(MAX_IMAGE_BYTES + 1)
        except HTTPError as exc:
            status = 404 if exc.code in (401, 403, 404) else 502
            raise CloudError('Private image is unavailable or its access expired.', status) from None
        except (URLError, OSError):
            raise CloudError('Private image could not be reached. Try again.', 502) from None
        return raw, _validated_image(raw, mime)
