import copy
import unittest
from backend.fit import assess_candidate, gate_requirements, validate_fit_config, validate_candidate_evidence


def measure(value, **changes):
    return dict(value=value, unit='in', source='measured', status='confirmed', **changes)


def dining():
    brief = dict(itemType='Dining chairs', quantity=4, furnishingMode='keep', fit=dict(
        schemaVersion=1, scenario='retained_dining_table',
        retainedObject=dict(identity='Retained table', variant='72 inch oak', confirmed=True,
                            dimensions=dict(lowestApronHeight=measure(26), tabletopHeight=measure(30))),
        arrangement=dict(type='parallel_rows', confirmed=True, rows=[
            dict(count=2, legSpacing=measure(50), availableDepth=measure(50)),
            dict(count=2, legSpacing=measure(50), availableDepth=measure(50))]),
        tolerances=dict(confirmed=True, armClearance=measure(1), seatGapMin=measure(10),
                        seatGapMax=measure(13), chairGap=measure(3), edgeClearance=measure(2), pullOutClearance=measure(20))))
    candidate = dict(exactSku='chair-1', variant='oak', fitEvidence=dict(exactSku='chair-1', variant='oak',
        dimensions=dict(armHeight=measure(24), seatHeight=measure(18), width=measure(20), depth=measure(23))))
    return brief, candidate


class FitTests(unittest.TestCase):
    def test_complete_dining_and_no_mutation(self):
        brief, candidate = dining()
        original = copy.deepcopy((brief, candidate))
        self.assertEqual(assess_candidate(brief, candidate)['status'], 'passed')
        self.assertEqual((brief, candidate), original)
        self.assertEqual(gate_requirements(brief)['status'], 'passed')

    def test_height_alone_never_qualifies(self):
        brief, candidate = dining()
        candidate['fitEvidence']['dimensions'] = dict(armHeight=measure(24))
        self.assertEqual(assess_candidate(brief, candidate)['status'], 'blocked')

    def test_every_applicable_dimension_blocks_unknown_or_conflicting(self):
        for status in ('unknown', 'conflicting'):
            brief, candidate = dining()
            candidate['fitEvidence']['dimensions']['width']['status'] = status
            self.assertEqual(assess_candidate(brief, candidate)['status'], 'blocked')
            self.assertIn('candidate.width', assess_candidate(brief, candidate)['reason'])

    def test_exact_variant_binding(self):
        for key in ('variant', 'exactSku'):
            brief, candidate = dining()
            candidate['fitEvidence'][key] = 'different'
            self.assertEqual(assess_candidate(brief, candidate)['status'], 'blocked')
            with self.assertRaises(ValueError):
                validate_candidate_evidence(candidate['fitEvidence'], candidate)

    def test_units_convert_equally(self):
        brief, candidate = dining()
        for item in candidate['fitEvidence']['dimensions'].values():
            item['value'] *= 2.54
            item['unit'] = 'cm'
        self.assertEqual(assess_candidate(brief, candidate)['status'], 'passed')

    def test_product_source_requires_traceable_url(self):
        brief, candidate = dining()
        width = candidate['fitEvidence']['dimensions']['width']
        width['source'] = 'product_source'
        self.assertEqual(assess_candidate(brief, candidate)['status'], 'blocked')
        width['url'] = 'https://merchant.example/chair-1/oak'
        self.assertEqual(assess_candidate(brief, candidate)['status'], 'passed')

    def test_geometry_failures_are_independent(self):
        for field, value, check in [('armHeight', 26, 'arm.apron'), ('seatHeight', 25, 'seat.minimumGap'),
                                     ('seatHeight', 10, 'seat.maximumGap'), ('width', 24, 'row.0.width'),
                                     ('depth', 31, 'row.0.depth')]:
            with self.subTest(field=field, value=value):
                brief, candidate = dining()
                candidate['fitEvidence']['dimensions'][field]['value'] = value
                result = assess_candidate(brief, candidate)
                self.assertEqual(result['status'], 'failed')
                found = next(c for c in result['checks'] if c['id'] == check)
                self.assertEqual(found['status'], 'failed')
                self.assertIn('candidate', found['evidence'])

    def test_zero_arm_height_is_explicit_armless(self):
        brief, candidate = dining()
        candidate['fitEvidence']['dimensions']['armHeight']['value'] = 0
        self.assertEqual(assess_candidate(brief, candidate)['status'], 'passed')

    def test_quantity_and_confirmation_required(self):
        brief, candidate = dining()
        brief['quantity'] = 6
        self.assertEqual(assess_candidate(brief, candidate)['status'], 'blocked')
        brief['quantity'] = 4
        brief['fit']['retainedObject']['confirmed'] = False
        self.assertEqual(assess_candidate(brief, candidate)['status'], 'blocked')

    def test_partial_configs_save_without_qualification(self):
        for value in (None, {}, {'schemaVersion': 1}, {'retainedObject': {'identity': 'Table'}}):
            self.assertEqual(validate_fit_config(value), value)
            self.assertEqual(gate_requirements({'fit': value})['status'], 'blocked')

    def test_invalid_values_and_unknown_fields_rejected(self):
        for value in (True, float('nan'), float('inf'), -1, '20'):
            brief, _ = dining()
            brief['fit']['tolerances']['chairGap']['value'] = value
            with self.assertRaises(ValueError):
                validate_fit_config(brief['fit'])
        with self.assertRaises(ValueError):
            validate_fit_config({'guaranteed': True})

    def test_unsupported_arrangements_block(self):
        brief, candidate = dining()
        brief['fit']['arrangement']['type'] = 'round_table'
        self.assertEqual(assess_candidate(brief, candidate)['status'], 'blocked')

    def test_missing_tolerance_and_inconsistent_table_block(self):
        brief, candidate = dining()
        del brief['fit']['tolerances']['pullOutClearance']
        self.assertEqual(assess_candidate(brief, candidate)['status'], 'blocked')
        brief, candidate = dining()
        brief['fit']['retainedObject']['dimensions']['lowestApronHeight']['value'] = 35
        self.assertEqual(assess_candidate(brief, candidate)['status'], 'blocked')

    def test_fresh_room_grid_checks_width_depth_and_height(self):
        brief = dict(quantity=4, furnishingMode='from_scratch', fit=dict(schemaVersion=1, scenario='room_layout',
            room=dict(confirmed=True, dimensions=dict(width=measure(60), depth=measure(60), heightLimit=measure(90))),
            arrangement=dict(type='grid', confirmed=True, rows=2, columns=2),
            tolerances=dict(confirmed=True, chairGap=measure(5), edgeClearance=measure(5))))
        candidate = dict(exactSku='c1', variant='v1', fitEvidence=dict(exactSku='c1', variant='v1',
            dimensions=dict(width=measure(20), depth=measure(20), height=measure(40))))
        self.assertEqual(assess_candidate(brief, candidate)['status'], 'passed')
        for field in ('width', 'depth', 'height'):
            changed = copy.deepcopy(candidate)
            changed['fitEvidence']['dimensions'][field]['value'] = 100
            self.assertEqual(assess_candidate(brief, changed)['status'], 'failed')
        brief['furnishingMode'] = 'keep'
        self.assertEqual(assess_candidate(brief, candidate)['status'], 'blocked')

    def test_saved_dining_fit_invalidated_by_mode_or_later_decision(self):
        brief, candidate = dining()
        brief['journey'] = {'keepingDecision': 'keep'}
        self.assertEqual(assess_candidate(brief, candidate)['status'], 'passed')
        original_fit = copy.deepcopy(brief['fit'])
        for mode, decision in [('from_scratch', 'fresh'), ('keep', 'fresh'),
                               ('keep', 'later'), (None, 'keep')]:
            with self.subTest(mode=mode, decision=decision):
                brief['furnishingMode'] = mode
                brief['journey']['keepingDecision'] = decision
                self.assertEqual(assess_candidate(brief, candidate)['status'], 'blocked')
                self.assertEqual(gate_requirements(brief)['status'], 'blocked')
                self.assertEqual(brief['fit'], original_fit)
        brief['furnishingMode'] = 'keep'
        brief['journey']['keepingDecision'] = 'keep'
        self.assertEqual(assess_candidate(brief, candidate)['status'], 'passed')

    def test_saved_room_fit_invalidated_by_keep_or_later_decision(self):
        brief = dict(quantity=1, furnishingMode='from_scratch', journey={'keepingDecision': 'fresh'},
            fit=dict(schemaVersion=1, scenario='room_layout',
                room=dict(confirmed=True, dimensions=dict(width=measure(60), depth=measure(60), heightLimit=measure(90))),
                arrangement=dict(type='grid', confirmed=True, rows=1, columns=1),
                tolerances=dict(confirmed=True, chairGap=measure(5), edgeClearance=measure(5))))
        candidate = dict(exactSku='c1', variant='v1', fitEvidence=dict(exactSku='c1', variant='v1',
            dimensions=dict(width=measure(20), depth=measure(20), height=measure(40))))
        self.assertEqual(assess_candidate(brief, candidate)['status'], 'passed')
        for decision in ('keep', 'later'):
            brief['journey']['keepingDecision'] = decision
            self.assertEqual(assess_candidate(brief, candidate)['status'], 'blocked')
            self.assertEqual(gate_requirements(brief)['status'], 'blocked')
        brief['journey']['keepingDecision'] = 'fresh'
        brief['furnishingMode'] = 'keep'
        self.assertEqual(assess_candidate(brief, candidate)['status'], 'blocked')

    def test_current_retained_objects_invalidate_removed_or_corrected_table(self):
        brief, candidate = dining()
        table = {'id': 'table-1', 'label': 'Retained table', 'variant': '72 inch oak', 'confirmed': True}
        brief['journey'] = {'keepingDecision': 'keep', 'retainedObjects': [table]}
        self.assertEqual(assess_candidate(brief, candidate)['status'], 'passed')
        for change in ({'variant': '60 inch oak'}, {'label': 'Different table'}, {'confirmed': False}):
            with self.subTest(change=change):
                brief['journey']['retainedObjects'] = [{**table, **change}]
                self.assertEqual(assess_candidate(brief, candidate)['status'], 'blocked')
                self.assertEqual(gate_requirements(brief)['status'], 'blocked')
        brief['journey']['retainedObjects'] = []
        self.assertEqual(assess_candidate(brief, candidate)['status'], 'blocked')
        brief['journey']['retainedObjects'] = [
            {'id': 'other', 'label': 'Sofa', 'variant': 'Blue', 'confirmed': True}]
        self.assertEqual(assess_candidate(brief, candidate)['status'], 'blocked')
        brief['journey']['retainedObjects'].append(table)
        self.assertEqual(assess_candidate(brief, candidate)['status'], 'passed')
        del brief['journey']['retainedObjects']
        self.assertEqual(assess_candidate(brief, candidate)['status'], 'passed')

    def test_candidate_evidence_is_bounded(self):
        _, candidate = dining()
        evidence = candidate['fitEvidence']
        self.assertEqual(validate_candidate_evidence(evidence, candidate), evidence)
        evidence['dimensions']['extra'] = measure(1)
        with self.assertRaises(ValueError):
            validate_candidate_evidence(evidence, candidate)


if __name__ == '__main__':
    unittest.main()
