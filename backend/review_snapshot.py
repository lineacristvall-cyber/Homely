"""Pure owner-selected client preview; does not authenticate or grant access.

Caller supplies an owner-authorized project and asset metadata. Scope keys are
candidateIds, noteFields (brief notes only), measurementFields, and imageIds.
Image IDs are references for a later authorized review-asset service, never URLs.
"""
import hashlib
import json
import math
import re

SCHEMA_VERSION = 'homely.review-preview.v1'
MEASUREMENTS = {'tableUndersideIn', 'chairArmIn', 'roomWidthIn', 'roomDepthIn'}
KINDS = {'room_original', 'product_source', 'illustrative_render'}
VARIANT_FIELDS = {'color', 'size', 'material', 'finish', 'name', 'id'}
DIMENSION_FIELDS = {'widthIn', 'depthIn', 'heightIn', 'armHeightIn'}
SCOPE_FIELDS = {'candidateIds', 'noteFields', 'measurementFields', 'imageIds'}


class ReviewSnapshotError(ValueError):
    """Safe validation error without private input values."""


def _identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,100}', value):
        raise ReviewSnapshotError('Invalid review object identifier.')
    return value


def _text(value):
    if value is None:
        return None
    if not isinstance(value, str) or len(value) > 10000:
        raise ReviewSnapshotError('Invalid review text.')
    # Reuse the export sanitizer for known credentials, private paths and URLs;
    # it receives scalar text only, never project or provider objects.
    from backend.privacy import _Builder, PrivacyExportError
    try:
        cleaned = _Builder().scalar(value)
        return re.sub(r'/(?:api/(?:assets|cloud-assets)|storage/v1)/[^\s<>"\']+', '[redacted private asset]', cleaned)
    except PrivacyExportError:
        raise ReviewSnapshotError('Review text could not be sanitized.') from None


def _number(value):
    if value is None:
        return None
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or (isinstance(value, float) and not math.isfinite(value)) or value < 0):
        raise ReviewSnapshotError('Invalid review numeric value.')
    return value


def _variant(value):
    if isinstance(value, dict):
        return {key: _text(value[key]) for key in sorted(VARIANT_FIELDS & value.keys())}
    return _text(value)


def _candidate(value):
    if not isinstance(value, dict):
        raise ReviewSnapshotError('Invalid candidate record.')
    dimensions = value.get('dimensions') or {}
    if not isinstance(dimensions, dict):
        raise ReviewSnapshotError('Invalid candidate measurements.')
    # A snapshot is historical evidence, never fresh stock or a fit assertion.
    return {'id': _identifier(value.get('id')), 'title': _text(value.get('title')),
            'seller': _text(value.get('seller')), 'exactSku': _text(value.get('exactSku')),
            'variant': _variant(value.get('variant')),
            'availability': {'sourceStatus': _text(value.get('status')), 'currentStatus': 'unverified',
                             'observedAt': _text(value.get('observedAt')),
                             'availableQuantity': _number(value.get('availableQuantity'))},
            'cost': {key: _number(value.get(key)) for key in ('unitPrice', 'shipping', 'tax', 'deliveredTotal')},
            'dimensions': {key: _number(dimensions[key]) for key in sorted(DIMENSION_FIELDS & dimensions.keys())},
            'fitStatus': 'fail' if value.get('fitStatus') == 'fail' else 'unverified'}


def build_review_snapshot(project, scope=None, *, assets=None):
    """Return a detached JSON preview with an immutable-content hash.

    Missing scope means no selected content. Supplied asset records use
    {id, projectId, kind}; metadata ownership must already be checked by caller.
    This function cannot grant recipients access or prove stock/image fidelity.
    """
    if not isinstance(project, dict):
        raise ReviewSnapshotError('An authorized project is required.')
    project_id = _identifier(project.get('id'))
    version = project.get('version')
    if type(version) is not int or version < 1:
        raise ReviewSnapshotError('A positive project version is required.')
    scope = {} if scope is None else scope
    if not isinstance(scope, dict) or set(scope) - SCOPE_FIELDS:
        raise ReviewSnapshotError('Unsupported disclosure scope.')
    selected = {}
    for key in sorted(SCOPE_FIELDS):
        items = scope.get(key, [])
        if not isinstance(items, list) or len(items) > 100 or any(not isinstance(item, str) for item in items):
            raise ReviewSnapshotError('Disclosure selections must be bounded string lists.')
        if len(set(items)) != len(items):
            raise ReviewSnapshotError('Duplicate disclosure selections.')
        selected[key] = sorted(items)
    if set(selected['noteFields']) - {'notes'} or set(selected['measurementFields']) - MEASUREMENTS:
        raise ReviewSnapshotError('Unsupported note or measurement selection.')
    brief = project.get('brief', {})
    candidates = project.get('candidates', [])
    assets = [] if assets is None else assets
    if not isinstance(brief, dict) or not isinstance(candidates, list) or not isinstance(assets, list):
        raise ReviewSnapshotError('Invalid project or asset records.')
    def records_by_id(records):
        result = {}
        for record in records:
            if not isinstance(record, dict):
                raise ReviewSnapshotError('Invalid selectable record.')
            key = _identifier(record.get('id'))
            if key in result:
                raise ReviewSnapshotError('Ambiguous selectable identifier.')
            result[key] = record
        return result
    candidate_map, asset_map = records_by_id(candidates), records_by_id(assets)
    if set(selected['candidateIds']) - candidate_map.keys() or set(selected['imageIds']) - asset_map.keys():
        raise ReviewSnapshotError('Selection is not in the authorized project.')
    image_previews = []
    for image_id in selected['imageIds']:
        asset = asset_map[image_id]
        if asset.get('projectId') != project_id or asset.get('kind') not in KINDS:
            raise ReviewSnapshotError('Image does not belong to this project or has an unsupported kind.')
        image_previews.append({'id': image_id, 'kind': asset['kind'],
                               'illustrative': asset['kind'] == 'illustrative_render',
                               'identityStatus': 'unverified', 'fitStatus': 'unverified'})
    measurements = brief.get('measurements') or {}
    if not isinstance(measurements, dict):
        raise ReviewSnapshotError('Invalid brief measurements.')
    result = {'schemaVersion': SCHEMA_VERSION, 'projectVersion': version,
              'disclosure': selected,
              'candidates': [_candidate(candidate_map[key]) for key in selected['candidateIds']],
              'notes': {key: _text(brief.get(key)) for key in selected['noteFields']},
              'measurements': {key: _number(measurements.get(key)) for key in selected['measurementFields']},
              'images': image_previews,
              'limitations': ['Preview only; no access or sharing link has been created.',
                             'Stock, cost and measurements are historical; unknown values remain unknown.',
                             'Images do not prove product identity or physical fit.',
                             'Approval records a selection only; it does not reserve stock, authorize purchase or place an order.']}
    try:
        encoded = json.dumps(result, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(',', ':')).encode()
    except (ValueError, TypeError, UnicodeError):
        raise ReviewSnapshotError('Preview cannot be represented as safe JSON.') from None
    if len(encoded) > 1024 * 1024:
        raise ReviewSnapshotError('Preview exceeds its size limit.')
    result['disclosureHash'] = hashlib.sha256(encoded).hexdigest()
    return result
