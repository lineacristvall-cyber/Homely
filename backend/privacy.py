"""Pure project JSON export. Caller must supply already owner-authorized projects.

No files, database, environment, image bytes or network are read. This module
cannot infer ownership from an ownerless canonical project or an owner_id field.
"""
from datetime import datetime, timezone
import ipaddress
import json
import math
import re
from urllib.parse import urlsplit, urlunsplit

SCHEMA_VERSION = 'homely.project-export.v1'
MAX_PROJECTS = 1000
MAX_EXPORT_BYTES = 20 * 1024 * 1024


class PrivacyExportError(ValueError):
    """Safe error without private source values."""


def fields(names):
    return dict.fromkeys(names.split(), 'scalar')


BRIEF = fields('itemType quantity style location flexibleTarget hardCap notes roomType roomLabel furnishingMode')
BRIEF['retainedItems'] = 'room-items'
FIT_MEASUREMENT = fields('value unit source status')
FIT_MEASUREMENT['url'] = 'url'
FIT_DIMENSIONS = {k: FIT_MEASUREMENT for k in ('lowestApronHeight','tabletopHeight','width','depth','height','heightLimit','armHeight','seatHeight')}
FIT_OBJECT = fields('identity variant confirmed')
FIT_OBJECT['dimensions'] = FIT_DIMENSIONS
FIT_TOLERANCES = {'confirmed': 'scalar', **{k: FIT_MEASUREMENT for k in ('armClearance','seatGapMin','seatGapMax','chairGap','edgeClearance','pullOutClearance')}}
FIT_ROW = {'count': 'scalar', 'legSpacing': FIT_MEASUREMENT, 'availableDepth': FIT_MEASUREMENT}
FIT_CONFIG = {'schemaVersion':'scalar','scenario':'scalar','retainedObject':FIT_OBJECT,
              'room': {'confirmed':'scalar','dimensions':FIT_DIMENSIONS},
              'arrangement': {'type':'scalar','confirmed':'scalar','rows':('fit-rows',FIT_ROW),'columns':'scalar'},
              'tolerances':FIT_TOLERANCES}
BRIEF['fit'] = FIT_CONFIG
RETAINED_OBJECT = fields('id label variant confirmed')
RETAINED_OBJECT['anchor'] = {'x':'scalar','y':'scalar','imageUrl':'url'}
BRIEF['journey'] = {**fields('step keepingDecision categoryOther categoryGuideIndex resultMode'),
                    'selectedCategories':'room-items','retainedObjects':[RETAINED_OBJECT],
                    'roomMeasurements':fields('width depth height unit')}
DIMENSIONS = fields('widthIn depthIn heightIn armHeightIn')
BRIEF['measurements'] = fields('tableUndersideIn chairArmIn roomWidthIn roomDepthIn')
VARIANT = fields('color size material finish name id')
CONSENT = fields('upload generation uploadAt generationAt observedAt updatedAt')
EVIDENCE = fields('title sourceId observedAt expiresAt method recordId rightsScope exactSku availableQuantity region currency unitPrice shipping tax costComplete path')
EVIDENCE.update(url='url', variant=('scalar-or-map', VARIANT), rawValue=('scalar-or-map', DIMENSIONS))
COVERAGE = fields('sourceId stage status observedAt reason')
COVERAGE['url'] = 'url'
CANDIDATE = fields('id title seller sourceId exactSku unitPrice listedPrice listedAvailability shipping tax availableQuantity observedAt method status reason imageRights deliveredTotal currency productImageRightsConfirmed')
CANDIDATE.update(dict.fromkeys('url imageUrl sourceImageUrl merchantImageUrl'.split(), 'url'))
CANDIDATE.update(variant=('scalar-or-map', VARIANT), dimensions=DIMENSIONS, sourceRefs=[EVIDENCE])
CANDIDATE['fieldEvidence'] = dict.fromkeys('title seller exactSku variant unitPrice listedPrice listedAvailability dimensions sourceImageUrl'.split(), EVIDENCE)
LINEAGE = fields('candidateId exactSku roomSha256 productSha256 outputSha256')
LINEAGE.update(variant=('scalar-or-map', VARIANT), sourceUrl='url', sourceRefs=[EVIDENCE])
CANDIDATE['lineage'] = LINEAGE
CANDIDATE['fitEvidence'] = {**fields('exactSku variant'), 'dimensions': FIT_DIMENSIONS}
ROOM = {'imageUrl': 'url', 'uploadedAt': 'scalar', 'uploadConsent': 'scalar', 'consent': ('scalar-or-map', CONSENT), 'lineage': LINEAGE}
DECISION = fields('id candidateId projectVersion createdAt deliveredTotal withinHardCap status readyForHandoff notes')
DECISION.update(candidateSnapshot=CANDIDATE, briefSnapshot=BRIEF)
PROJECT = fields('id name mode version createdAt updatedAt sourceCoverageComplete')
PROJECT.update(brief=BRIEF, room=ROOM, candidates=[CANDIDATE], decisions=[DECISION], sourceCoverage=[COVERAGE])

# Closed shapes exclude arbitrary session/provider objects at every nesting level.
# Recognizable credentials in user text receive defense-in-depth redaction; no
# general detector can identify every arbitrary secret pasted into natural prose.
_CREDENTIAL = re.compile(r'(?i)\b(?:sk-[a-z0-9_-]{8,}|sb_(?:secret|publishable)_[a-z0-9_-]+|eyJ[a-z0-9_-]+\.[a-z0-9_-]+\.[a-z0-9_-]+)\b|\bBearer\s+[^\s,;]+|\b(?:access[_-]?token|refresh[_-]?token|api[_-]?key|authorization|cookie|homely_auth|homely_session|session[_-]?id|password)\s*[=:]\s*[^\s,;]+')
_INTERNAL = re.compile(r'(?i)(?:file://[^\s]+|/(?:Users|home|private|tmp|var|data)/[^\s]+|[a-z]:\\[^\s]+|[^\s]*private-cloud-(?:cache|jobs)[^\s]*)')
_EMBEDDED_URL = re.compile(r'https?://[^\s<>"\']+', re.I)
_APP_ASSET = re.compile(r'/api/(?:cloud-assets/[a-f0-9-]{36}|assets/[a-f0-9-]{36}\.(?:png|jpg|jpeg|webp))\Z')


class _Builder:
    def __init__(self):
        self.redacted = 0
        self.visited = 0

    def url(self, value):
        if value is None:
            return None
        if not isinstance(value, str):
            raise PrivacyExportError('An export URL has an invalid type.')
        if _APP_ASSET.fullmatch(value):
            return value
        try:
            parts = urlsplit(value)
            host = parts.hostname or ''
            unsafe = (parts.scheme not in ('http', 'https') or not host or parts.username is not None
                      or parts.password is not None or parts.port not in (None, 80, 443)
                      or host.lower() in ('localhost', 'metadata.google.internal')
                      or host.lower().endswith(('.local', '.internal', '.supabase.co', '.supabase.in'))
                      or '/storage/v1/' in parts.path.lower() or _CREDENTIAL.search(value)
                      or any(ord(c) < 32 for c in value) or '\\' in value)
            try:
                unsafe = unsafe or not ipaddress.ip_address(host).is_global
            except ValueError:
                pass
            if unsafe:
                raise ValueError()
            cleaned = urlunsplit((parts.scheme, parts.netloc, parts.path, '', ''))
        except ValueError:
            self.redacted += 1
            return None
        if cleaned != value:
            self.redacted += 1
        return cleaned

    def scalar(self, value):
        if value is None or isinstance(value, (bool, int)):
            return value
        if isinstance(value, float) and math.isfinite(value):
            return value
        if not isinstance(value, str) or len(value) > 100_000:
            raise PrivacyExportError('An export field has an invalid type or size.')
        cleaned = _EMBEDDED_URL.sub(lambda m: self.url(m.group()) or '[redacted URL]', value)
        cleaned = _CREDENTIAL.sub('[redacted credential]', cleaned)
        cleaned = _INTERNAL.sub('[redacted private path]', cleaned)
        if cleaned != value:
            self.redacted += 1
        return cleaned

    def select(self, value, shape, depth=0):
        self.visited += 1
        if depth > 20 or self.visited > 100_000:
            raise PrivacyExportError('The project export exceeds its structural limit.')
        if value is None:
            return None
        if shape == 'scalar':
            return self.scalar(value)
        if shape == 'room-items':
            if not isinstance(value, list) or len(value) > 20 or any(not isinstance(item, str) or len(item) > 100 for item in value):
                raise PrivacyExportError('Room items have an invalid type or size.')
            return [self.scalar(item) for item in value]
        if shape == 'url':
            return self.url(value)
        if isinstance(shape, tuple):
            if shape[0] == 'fit-rows':
                return self.select(value, [shape[1]] if isinstance(value, list) else 'scalar', depth + 1)
            return self.select(value, shape[1] if isinstance(value, dict) else 'scalar', depth + 1)
        if isinstance(shape, list):
            if not isinstance(value, list) or len(value) > 5000:
                raise PrivacyExportError('An export collection has an invalid type or size.')
            if any(not isinstance(item, dict) for item in value):
                raise PrivacyExportError('An export collection contains an invalid record.')
            return [self.select(item, shape[0], depth + 1) for item in value]
        if not isinstance(value, dict):
            raise PrivacyExportError('An export record has an invalid type.')
        return {key: self.select(value[key], spec, depth + 1) for key, spec in shape.items() if key in value}


def build_project_export(projects: list[dict], *, now: datetime | None = None) -> dict:
    """Return a detached, versioned export of only the supplied scoped projects.

    Authenticate in HTTP and pass CloudProjectStore(current_session).list_for_export() or an
    owned subset; never pass a global store or request-supplied project documents.
    Missing consent/state stays missing. Evidence is copied, never reverified.
    Redaction is for known credential formats, not arbitrary secrets in prose.
    """
    if not isinstance(projects, list) or len(projects) > MAX_PROJECTS:
        raise PrivacyExportError('Supply an owner-scoped project list within the export limit.')
    seen = set()
    for project in projects:
        if not isinstance(project, dict) or not isinstance(project.get('id'), str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,100}', project['id']):
            raise PrivacyExportError('An export project has an invalid identifier.')
        if project['id'] in seen:
            raise PrivacyExportError('The export contains duplicate project identifiers.')
        seen.add(project['id'])
    stamp = now if now is not None else datetime.now(timezone.utc)
    if not isinstance(stamp, datetime) or stamp.tzinfo is None or stamp.utcoffset() is None:
        raise PrivacyExportError('Export time must be a timezone-aware datetime.')
    builder = _Builder()
    documents = [builder.select(project, PROJECT) for project in projects]
    result = {'schemaVersion': SCHEMA_VERSION, 'exportedAt': stamp.astimezone(timezone.utc).isoformat(),
              'scope': 'caller-authorized-projects', 'projectCount': len(documents), 'projects': documents,
              'redactionCount': builder.redacted,
              'limitations': ['Project JSON only; original image bytes, account settings, jobs and voice recordings are not included.',
                  'App asset references require the owning account in cloud mode and the running application; this is not a portable image backup.',
                  'Private storage URLs and recognizable credentials are redacted; public URL queries/fragments are omitted.',
                  'Live project enumeration is not a transactionally frozen database snapshot.',
                  'Source observations and consent fields are copied history, not new verification, permission or stock claims.']}
    try:
        encoded = json.dumps(result, ensure_ascii=False, allow_nan=False).encode('utf-8')
    except (ValueError, TypeError, UnicodeError, OverflowError):
        raise PrivacyExportError('Project data cannot be represented as safe JSON.') from None
    if len(encoded) > MAX_EXPORT_BYTES:
        raise PrivacyExportError('The project export exceeds its byte limit.')
    return result
