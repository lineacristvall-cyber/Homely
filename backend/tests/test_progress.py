"""Deterministic tracker math tests; only temporary checklist/log files are written."""
import copy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from backend import progress


def criterion(weight, checked=False, evidence=''):
    return {'label': 'Acceptance criterion', 'weight': weight, 'checked': checked, 'evidence': evidence}


def component(name, poc=None, production=None):
    return {'id': name, 'name': name, 'poc': poc or [], 'production': production or []}


class ScoreTests(unittest.TestCase):
    def test_weighted_denominator_and_earned_not_count_of_checkmarks(self):
        result = progress._score([criterion(5, True), criterion(2, False), criterion(1, True)])
        self.assertEqual((result['earned'], result['total'], result['percent']), (6, 8, 75))
        self.assertEqual([entry['met'] for entry in result['criteria']], [True, False, True])

    def test_only_literal_true_earns_weight(self):
        states = [True, False, None, 1, 'true', 'completed', [], {}]
        result = progress._score([criterion(2, state) for state in states])
        self.assertEqual(result['earned'], 2)
        self.assertEqual(result['total'], 16)
        self.assertEqual(sum(entry['met'] for entry in result['criteria']), 1)

    def test_invalid_weights_raise(self):
        for weight in (None, 0, -2, 1.5, '3', [], {}):
            with self.subTest(weight=weight):
                with self.assertRaisesRegex(ValueError, 'positive integers'):
                    progress._score([criterion(weight, True)])

    def test_boolean_weights_are_not_positive_integer_acceptance_weights(self):
        for weight in (True, False):
            with self.subTest(weight=weight):
                with self.assertRaisesRegex(ValueError, 'positive integers'):
                    progress._score([criterion(weight, True)])

    def test_empty_and_all_unchecked_are_zero(self):
        self.assertEqual(progress._score([]), {'earned': 0, 'total': 0, 'percent': 0, 'criteria': []})
        self.assertEqual(progress._score([criterion(5)])['percent'], 0)

    def test_percentage_uses_integer_rounding_not_truncation(self):
        self.assertEqual(progress._score([criterion(2, True), criterion(1)])['percent'], 67)
        self.assertEqual(progress._score([criterion(1, True), criterion(2)])['percent'], 33)
        # Current calculator uses Python round: exact .5 ties round to even.
        self.assertEqual(progress._score([criterion(1, True), criterion(7)])['percent'], 12)
        self.assertEqual(progress._score([criterion(3, True), criterion(5)])['percent'], 38)

    def test_score_does_not_mutate_input(self):
        rows = [criterion(3, True, 'verified evidence'), criterion(2)]
        original = copy.deepcopy(rows)
        progress._score(rows)
        self.assertEqual(rows, original)


class ProgressBuildTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.files = {name: self.base / (name + '.fixture') for name in ('CHECKLIST', 'PROGRESS', 'DECISIONS', 'OPEN')}
        for name, path in self.files.items():
            patcher = patch.object(progress, name, path)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.files['PROGRESS'].write_text('Fixture progress only.')
        self.files['DECISIONS'].write_text('- First decision\n- Second decision\n')
        self.files['OPEN'].write_text('- [ ] Unresolved\n- [x] Resolved\nNot an action\n')

    def build(self, components):
        self.files['CHECKLIST'].write_text(json.dumps({'schemaVersion': 1, 'planningAssumptions': 'Weighted acceptance, not time.', 'components': components}))
        return progress.build_progress()

    def test_aggregate_weights_not_average_of_component_percentages(self):
        result = self.build([component('small', [criterion(1, True)], [criterion(2, True)]),
                             component('large', [criterion(9, False)], [criterion(3, False)])])
        self.assertEqual(result['poc'], {'earned': 1, 'total': 10, 'percent': 10})
        self.assertEqual(result['production'], {'earned': 2, 'total': 5, 'percent': 40})
        self.assertEqual([entry['poc']['percent'] for entry in result['components']], [100, 0])

    def test_empty_components_and_missing_criteria_do_not_divide_by_zero(self):
        for rows in ([], [{'id': 'empty', 'name': 'Empty'}]):
            result = self.build(rows)
            for kind in ('poc', 'production'):
                self.assertEqual(result[kind], {'earned': 0, 'total': 0, 'percent': 0})

    def test_added_unchecked_scope_preserves_earned_and_changes_denominator(self):
        rows = [component('existing', [criterion(3, True), criterion(2)])]
        before = self.build(rows)
        rows.append(component('new-scope', [criterion(5)], [criterion(4)]))
        after = self.build(rows)
        self.assertEqual(before['poc'], {'earned': 3, 'total': 5, 'percent': 60})
        self.assertEqual(after['poc'], {'earned': 3, 'total': 10, 'percent': 30})
        self.assertEqual(after['production'], {'earned': 0, 'total': 4, 'percent': 0})
        self.assertEqual(after['components'][0]['poc'], before['components'][0]['poc'])

    def test_evidence_only_from_checked_criteria_and_deduplicated(self):
        result = self.build([component('one', [criterion(2, True, 'same'), criterion(1, False, 'pending')],
                                      [criterion(3, True, 'same'), criterion(1, True, 'other')])])
        self.assertEqual(result['evidence'], ['same', 'other'])
        self.assertEqual(result['openActions'], ['Unresolved'])
        self.assertEqual(result['recentDecisions'], ['First decision', 'Second decision'])

    def test_updated_time_uses_newest_existing_source_and_missing_logs_are_safe(self):
        self.build([])
        for index, path in enumerate(self.files.values()):
            stamp = 1700000000 + index * 100
            os.utime(path, (stamp, stamp))
        result = progress.build_progress()
        self.assertEqual(result['updatedAt'], datetime.fromtimestamp(1700000300, timezone.utc).isoformat())
        for name in ('PROGRESS', 'DECISIONS', 'OPEN'):
            self.files[name].unlink()
        result = progress.build_progress()
        self.assertEqual(result['openActions'], [])
        self.assertEqual(result['recentDecisions'], [])

    def test_invalid_json_missing_components_and_missing_identity_raise(self):
        self.files['CHECKLIST'].write_text('{broken')
        with self.assertRaises(json.JSONDecodeError):
            progress.build_progress()
        self.files['CHECKLIST'].write_text('{}')
        with self.assertRaises(KeyError):
            progress.build_progress()
        self.files['CHECKLIST'].write_text(json.dumps({'components': [{'name': 'missing id'}]}))
        with self.assertRaises(KeyError):
            progress.build_progress()

if __name__ == '__main__':
    unittest.main()
