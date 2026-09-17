"""Pure, conservative geometry checks. No photo inference or default tolerances.

Evidence: {value, unit: in|cm, source: measured|product_source,
status: confirmed|unknown|conflicting, url?: http(s)}. Partial configs can be
saved, but never pass. Candidate fitEvidence pins exactSku and variant.
"""
from copy import deepcopy
import math
from urllib.parse import urlsplit

SCOPE = ('Only the declared measured constraints and exact variant are checked. '
         'This is not a guarantee of comfort, access, stability, stock or overall room fit.')


def _number(value):
    return type(value) in (int, float) and math.isfinite(value) and 0 <= value <= 100000


def _url(value):
    if not isinstance(value, str) or len(value) > 2048:
        return False
    try:
        parsed = urlsplit(value)
        return parsed.scheme in ('https', 'http') and bool(parsed.hostname) and not parsed.username and not parsed.password
    except ValueError:
        return False


def _object(value, allowed, path):
    if not isinstance(value, dict) or set(value) - set(allowed):
        raise ValueError(f'{path}: expected an object with supported fields')


def _evidence(value, path):
    if value is None:
        return
    _object(value, ('value', 'unit', 'source', 'status', 'url'), path)
    if value.get('value') is not None and not _number(value['value']):
        raise ValueError(f'{path}: measurement must be a finite nonnegative number')
    for key, choices in [('unit', ('in', 'cm')), ('source', ('measured', 'product_source')),
                         ('status', ('confirmed', 'unknown', 'conflicting'))]:
        if key in value and value[key] not in choices:
            raise ValueError(f'{path}: invalid {key}')
    if 'url' in value and value['url'] is not None and not _url(value['url']):
        raise ValueError(f'{path}: source URL must be a traceable http(s) URL')


def _dims(value, fields, path):
    _object(value, fields, path)
    for key, item in value.items():
        _evidence(item, f'{path}.{key}')


def validate_fit_config(value):
    """Validate bounded saveable data; completeness is checked independently."""
    if value is None:
        return None
    _object(value, ('schemaVersion', 'scenario', 'retainedObject', 'room', 'arrangement', 'tolerances'), 'fit')
    if 'schemaVersion' in value and (type(value['schemaVersion']) is not int or value['schemaVersion'] != 1):
        raise ValueError('fit.schemaVersion must be 1')
    if 'scenario' in value and value['scenario'] not in ('retained_dining_table', 'room_layout'):
        raise ValueError('Unsupported fit scenario')
    for key, fields in [('retainedObject', ('lowestApronHeight', 'tabletopHeight')),
                        ('room', ('width', 'depth', 'heightLimit'))]:
        if key not in value:
            continue
        obj = value[key]
        _object(obj, ('identity', 'variant', 'confirmed', 'dimensions') if key == 'retainedObject' else ('confirmed', 'dimensions'), key)
        for name in ('identity', 'variant'):
            if name in obj and (not isinstance(obj[name], str) or len(obj[name]) > 200):
                raise ValueError(f'{key}.{name}: expected text up to 200 characters')
        if 'confirmed' in obj and type(obj['confirmed']) is not bool:
            raise ValueError(f'{key}.confirmed must be boolean')
        if 'dimensions' in obj:
            _dims(obj['dimensions'], fields, f'{key}.dimensions')
    if 'tolerances' in value:
        tolerances = value['tolerances']
        fields = ('armClearance', 'seatGapMin', 'seatGapMax', 'chairGap', 'edgeClearance', 'pullOutClearance')
        _object(tolerances, (*fields, 'confirmed'), 'tolerances')
        if 'confirmed' in tolerances and type(tolerances['confirmed']) is not bool:
            raise ValueError('tolerances.confirmed must be boolean')
        for key in fields:
            if key in tolerances:
                _evidence(tolerances[key], f'tolerances.{key}')
    if 'arrangement' in value:
        arrangement = value['arrangement']
        _object(arrangement, ('type', 'confirmed', 'rows', 'columns'), 'arrangement')
        if 'confirmed' in arrangement and type(arrangement['confirmed']) is not bool:
            raise ValueError('arrangement.confirmed must be boolean')
        if 'type' in arrangement and arrangement['type'] not in ('grid', 'parallel_rows'):
            raise ValueError('Unsupported arrangement; end chairs and nonrectangular layouts require additional geometry')
        if 'columns' in arrangement and (type(arrangement['columns']) is not int or not 1 <= arrangement['columns'] <= 100):
            raise ValueError('Grid columns must be 1–100')
        if 'rows' in arrangement:
            rows = arrangement['rows']
            if arrangement.get('type') == 'grid':
                if type(rows) is not int or not 1 <= rows <= 100:
                    raise ValueError('Grid rows must be 1–100')
            else:
                if not isinstance(rows, list) or len(rows) > 2:
                    raise ValueError('Dining arrangement supports at most two opposing parallel rows')
                for row in rows:
                    _object(row, ('count', 'legSpacing', 'availableDepth'), 'arrangement row')
                    if 'count' in row and (type(row['count']) is not int or not 1 <= row['count'] <= 100):
                        raise ValueError('Row count must be 1–100')
                    for key in ('legSpacing', 'availableDepth'):
                        if key in row:
                            _evidence(row[key], f'row.{key}')
    return deepcopy(value)


def _check(checks, name, valid, reason, evidence=None, **values):
    checks.append(dict(id=name, status='passed' if valid else 'blocked', reason=reason,
                       evidence=deepcopy(evidence), **values))


def _read(checks, name, item, positive=True):
    try:
        _evidence(item, name)
        valid = (isinstance(item, dict) and item.get('status') == 'confirmed' and
                 _number(item.get('value')) and (not positive or item['value'] > 0) and
                 item.get('unit') in ('in', 'cm') and item.get('source') in ('measured', 'product_source') and
                 (item['source'] != 'product_source' or _url(item.get('url'))))
    except ValueError:
        valid = False
    _check(checks, name, valid, f'{name}: confirmed measurement with unit and provenance recorded' if valid else
           f'{name}: missing, conflicting, unknown or unsupported measurement; confirm value, unit and source', item)
    return item['value'] / (2.54 if item['unit'] == 'cm' else 1) if valid else None


def _result(checks, scope=SCOPE):
    status = 'blocked' if any(c['status'] == 'blocked' for c in checks) else 'failed' if any(c['status'] == 'failed' for c in checks) else 'passed'
    reasons = [c['reason'] for c in checks if c['status'] != 'passed']
    return dict(status=status, checks=checks, reason='; '.join(reasons) if reasons else 'Declared measured constraints passed.', scope=scope)


def _requirements(brief):
    checks, values = [], {}
    try:
        fit = validate_fit_config(brief.get('fit')) or {}
    except ValueError as exc:
        _check(checks, 'config', False, str(exc))
        return checks, values, {}
    scenario = fit.get('scenario')
    _check(checks, 'scenario', fit.get('schemaVersion') == 1 and scenario in ('retained_dining_table', 'room_layout'),
           'A supported fit scenario and schema version 1 are required.')
    journey = brief.get('journey') or {}
    keeping_decision = journey.get('keepingDecision') if isinstance(journey, dict) else None
    expected_mode = {'retained_dining_table': 'keep', 'room_layout': 'from_scratch'}.get(scenario)
    expected_decision = {'retained_dining_table': 'keep', 'room_layout': 'fresh'}.get(scenario)
    _check(checks, 'furnishingMode', expected_mode is not None and brief.get('furnishingMode') == expected_mode
           and keeping_decision in (None, expected_decision),
           'The current keep/start-fresh decision must match the measured fit scenario; deciding later or switching modes requires a matching fit setup.',
           {'furnishingMode': brief.get('furnishingMode'), 'keepingDecision': keeping_decision, 'scenario': scenario})
    arrangement, tolerances = fit.get('arrangement', {}), fit.get('tolerances', {})
    _check(checks, 'arrangement.confirmed', arrangement.get('confirmed') is True, 'Confirm the exact chair count and arrangement, or the complete room grid.')
    _check(checks, 'tolerances.confirmed', tolerances.get('confirmed') is True, 'Confirm all applicable clearance tolerances; none are assumed.')
    quantity = brief.get('quantity')
    _check(checks, 'quantity', type(quantity) is int and 1 <= quantity <= 100, 'Requested quantity must be an integer from 1 to 100.')
    if scenario == 'retained_dining_table':
        obj = fit.get('retainedObject', {})
        _check(checks, 'retainedObject', obj.get('confirmed') is True and all(isinstance(obj.get(k), str) and obj[k].strip() for k in ('identity', 'variant')),
               'Confirm the retained table identity and exact variant.', obj)
        if isinstance(journey, dict) and 'retainedObjects' in journey:
            retained_objects = journey['retainedObjects']
            matching_object = isinstance(retained_objects, list) and any(
                isinstance(current, dict) and current.get('confirmed') is True
                and isinstance(current.get('label'), str) and isinstance(current.get('variant'), str)
                and current['label'].strip() == str(obj.get('identity', '')).strip()
                and current['variant'].strip() == str(obj.get('variant', '')).strip()
                for current in retained_objects)
            _check(checks, 'retainedObject.current', matching_object,
                   'The measured table identity and variant must match a currently confirmed retained object; changes or undo require confirming the matching table again.',
                   {'identity': obj.get('identity'), 'variant': obj.get('variant'),
                    'retainedObjects': retained_objects})
        _check(checks, 'category', brief.get('itemType', '').strip().lower() in ('dining chairs', 'dining chair', 'chairs', 'chair'),
               'The retained-table engine supports dining chairs only.')
        fields = ('lowestApronHeight', 'tabletopHeight')
        dims = obj.get('dimensions', {})
        for key in fields:
            values[key] = _read(checks, key, dims.get(key))
        rows = arrangement.get('rows', [])
        valid_rows = arrangement.get('type') == 'parallel_rows' and isinstance(rows, list) and 1 <= len(rows) <= 2
        _check(checks, 'arrangement.type', valid_rows, 'Only one or two opposing parallel rows are supported; end chairs need more geometry.')
        rows = rows if valid_rows else []
        _check(checks, 'arrangement.count', bool(rows) and all(type(r.get('count')) is int for r in rows) and sum(r.get('count', 0) for r in rows) == quantity,
               'The sum of row counts must equal the requested quantity.')
        values['rows'] = []
        for index, row in enumerate(rows):
            values['rows'].append({key: _read(checks, f'row.{index}.{key}', row.get(key)) for key in ('legSpacing', 'availableDepth')})
        needed = ('armClearance', 'seatGapMin', 'seatGapMax', 'chairGap', 'edgeClearance', 'pullOutClearance')
    elif scenario == 'room_layout':
        room = fit.get('room', {})
        _check(checks, 'room.confirmed', room.get('confirmed') is True and brief.get('furnishingMode') == 'from_scratch',
               'Confirm an unobstructed usable rectangular space in a room furnished from scratch.', room)
        for key in ('width', 'depth', 'heightLimit'):
            values['room.' + key] = _read(checks, 'room.' + key, room.get('dimensions', {}).get(key))
        rows, columns = arrangement.get('rows'), arrangement.get('columns')
        _check(checks, 'arrangement.grid', arrangement.get('type') == 'grid' and type(rows) is int and type(columns) is int and rows * columns == quantity,
               'Confirm a full rectangular grid whose rows × columns equal the requested quantity.')
        needed = ('chairGap', 'edgeClearance')
    else:
        needed = ()
    for key in needed:
        values[key] = _read(checks, key, tolerances.get(key), positive=False)
    if scenario == 'retained_dining_table':
        low, high = values.get('seatGapMin'), values.get('seatGapMax')
        _check(checks, 'seatGap.range', low is not None and high is not None and 0 < low <= high,
               'Seat-to-table gap minimum must be positive and no greater than the maximum.')
        apron, top = values.get('lowestApronHeight'), values.get('tabletopHeight')
        _check(checks, 'table.geometry', apron is not None and top is not None and apron < top,
               'Lowest apron height must be below the tabletop height.')
    return checks, values, fit


def gate_requirements(brief):
    """Check only project inputs; a pass here does not qualify any candidate."""
    checks, _, _ = _requirements(brief)
    result = _result(checks)
    if result['status'] == 'passed':
        result['reason'] = 'Project measurements recorded. Each exact candidate still requires independent fit checks.'
    return result


def assess_candidate(brief, candidate):
    checks, values, fit = _requirements(brief)
    evidence = candidate.get('fitEvidence')
    evidence = evidence if isinstance(evidence, dict) else {}
    identity_ok = all(isinstance(candidate.get(k), str) and candidate[k].strip() and evidence.get(k) == candidate[k] for k in ('exactSku', 'variant'))
    _check(checks, 'candidate.variant', identity_ok, 'Candidate measurements must name the same exact SKU and variant as this product.',
           {k: evidence.get(k) for k in ('exactSku', 'variant')})
    fields = ('armHeight', 'seatHeight', 'width', 'depth') if fit.get('scenario') == 'retained_dining_table' else ('width', 'depth', 'height')
    dimensions = evidence.get('dimensions', {})
    dimensions = dimensions if isinstance(dimensions, dict) else {}
    for key in fields:
        values['candidate.' + key] = _read(checks, 'candidate.' + key, dimensions.get(key), positive=key != 'armHeight')
    if any(c['status'] == 'blocked' for c in checks):
        return _result(checks)

    def compare(name, actual, limit, reason):
        ok = actual <= limit + 1e-9
        checks.append(dict(id=name, status='passed' if ok else 'failed', reason=reason,
                           actualIn=round(actual, 6), limitIn=round(limit, 6),
                           evidence={'project': deepcopy(fit), 'candidate': deepcopy(evidence)}))

    arrangement = fit['arrangement']
    if fit['scenario'] == 'retained_dining_table':
        compare('arm.apron', values['candidate.armHeight'] + values['armClearance'], values['lowestApronHeight'],
                'Chair arm height plus confirmed clearance must fit beneath the lowest apron; zero arm height denotes confirmed armless construction.')
        gap = values['tabletopHeight'] - values['candidate.seatHeight']
        compare('seat.minimumGap', values['seatGapMin'], gap, 'Tabletop minus seat height must meet the confirmed minimum gap.')
        compare('seat.maximumGap', gap, values['seatGapMax'], 'Tabletop minus seat height must stay within the confirmed maximum gap.')
        for index, row in enumerate(arrangement['rows']):
            required = row['count'] * values['candidate.width'] + (row['count'] - 1) * values['chairGap'] + 2 * values['edgeClearance']
            compare(f'row.{index}.width', required, values['rows'][index]['legSpacing'], 'Chairs, inter-chair gaps and both edge clearances must fit between the table legs.')
            compare(f'row.{index}.depth', values['candidate.depth'] + values['pullOutClearance'], values['rows'][index]['availableDepth'],
                    'Chair depth plus confirmed pull-out clearance must fit the measured unobstructed space from the table edge.')
    else:
        for axis, count in [('width', arrangement['columns']), ('depth', arrangement['rows'])]:
            required = count * values['candidate.' + axis] + (count - 1) * values['chairGap'] + 2 * values['edgeClearance']
            compare('room.' + axis, required, values['room.' + axis], 'Axis-aligned item envelopes, inter-item gaps and edge clearances must fit the confirmed usable room rectangle.')
        compare('room.height', values['candidate.height'], values['room.heightLimit'], 'Item height must not exceed the confirmed room height limit.')
    return _result(checks)


def validate_candidate_evidence(evidence, candidate):
    """Bound owner-recorded evidence and pin it to an existing exact variant."""
    _object(evidence, ('exactSku', 'variant', 'dimensions'), 'fitEvidence')
    for key in ('exactSku', 'variant'):
        if not isinstance(evidence.get(key), str) or not evidence[key].strip() or len(evidence[key]) > 200:
            raise ValueError(f'fitEvidence.{key}: exact identity is required (up to 200 characters)')
        if evidence[key] != candidate.get(key):
            raise ValueError(f'fitEvidence.{key} must match the candidate exact variant')
    _dims(evidence.get('dimensions', {}), ('armHeight', 'seatHeight', 'width', 'depth', 'height'), 'fitEvidence.dimensions')
    return deepcopy(evidence)
