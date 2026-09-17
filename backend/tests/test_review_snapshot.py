"""Pure fixtures only: no storage, provider calls or access grants."""
import copy
import json
import unittest
from backend.review_snapshot import build_review_snapshot, ReviewSnapshotError


class ReviewSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.project = {'id': 'project-a', 'version': 7, 'name': 'PRIVATE PROJECT NAME',
                        'brief': {'location': 'PRIVATE LOCATION', 'notes': 'Selected note', 'hardCap': 3000,
                                  'measurements': {'tableUndersideIn': 27, 'roomWidthIn': 120}},
                        'room': {'imageUrl': '/api/cloud-assets/SECRET', 'lineage': {'private': 'SECRET'}},
                        'candidates': [{'id': 'chair-a', 'title': 'Oak chair', 'status': 'lead',
                                        'variant': {'finish': 'oak', 'private': 'SECRET'},
                                        'unitPrice': 100, 'shipping': None, 'tax': None,
                                        'availableQuantity': None, 'dimensions': {'widthIn': 20, 'private': 'SECRET'},
                                        'imageUrl': '/api/assets/SECRET', 'sourceRefs': [{'secret': 'SECRET'}],
                                        'lineage': {'private': 'SECRET'}, 'notes': 'PRIVATE CANDIDATE NOTE'},
                                       {'id': 'chair-b', 'title': 'UNRELATED CHAIR'}],
                        'decisions': [{'private': 'SECRET'}]}
        self.assets = [{'id': 'image-a', 'projectId': 'project-a', 'kind': 'illustrative_render',
                        'object_path': 'PRIVATE STORAGE PATH', 'imageUrl': '/api/cloud-assets/SECRET',
                        'lineage': {'private': 'SECRET'}}]

    def test_default_discloses_no_content_or_access(self):
        result = build_review_snapshot(self.project)
        for key in ('candidates', 'images'):
            self.assertEqual(result[key], [])
        for key in ('notes', 'measurements'):
            self.assertEqual(result[key], {})
        self.assertEqual(result['projectVersion'], 7)
        for value in ('Oak chair', 'PRIVATE', 'SECRET', 'project-a'):
            self.assertNotIn(value, json.dumps(result))
        self.assertIn('no access', result['limitations'][0])

    def test_selected_only_nested_allowlist_and_uncertainty(self):
        scope = {'candidateIds': ['chair-a'], 'noteFields': ['notes'],
                 'measurementFields': ['tableUndersideIn'], 'imageIds': ['image-a']}
        result = build_review_snapshot(self.project, scope, assets=self.assets)
        rendered = json.dumps(result)
        for value in ('SECRET', 'PRIVATE', 'UNRELATED', '/api/', 'sourceRefs', 'lineage', 'hardCap', 'roomWidthIn'):
            self.assertNotIn(value, rendered)
        self.assertEqual(result['notes'], {'notes': 'Selected note'})
        self.assertEqual(result['measurements'], {'tableUndersideIn': 27})
        candidate = result['candidates'][0]
        self.assertEqual(candidate['variant'], {'finish': 'oak'})
        self.assertEqual(candidate['availability']['sourceStatus'], 'lead')
        self.assertEqual(candidate['availability']['currentStatus'], 'unverified')
        self.assertIsNone(candidate['availability']['availableQuantity'])
        self.assertIsNone(candidate['cost']['deliveredTotal'])
        self.assertTrue(result['images'][0]['illustrative'])

    def test_detached_content_and_canonical_hash_version(self):
        scope = {'candidateIds': ['chair-b', 'chair-a'], 'measurementFields': ['roomWidthIn', 'tableUndersideIn']}
        before = copy.deepcopy(self.project)
        first = build_review_snapshot(self.project, scope)
        reverse = {'measurementFields': list(reversed(scope['measurementFields'])), 'candidateIds': ['chair-a', 'chair-b']}
        self.assertEqual(first, build_review_snapshot(self.project, reverse))
        first['candidates'][0]['title'] = 'mutated preview'
        self.assertEqual(self.project, before)
        old_hash = build_review_snapshot(self.project, scope)['disclosureHash']
        self.project['version'] += 1
        self.assertNotEqual(old_hash, build_review_snapshot(self.project, scope)['disclosureHash'])
        self.project['version'] -= 1
        self.project['candidates'][0]['unitPrice'] = 101
        self.assertNotEqual(old_hash, build_review_snapshot(self.project, scope)['disclosureHash'])

    def test_malformed_or_unknown_scope_fails_closed(self):
        scopes = [[], {'all': True}, {'candidateIds': 'chair-a'}, {'candidateIds': [1]},
                  {'candidateIds': ['missing']}, {'candidateIds': ['chair-a', 'chair-a']},
                  {'noteFields': ['location']}, {'measurementFields': ['private']}, {'imageIds': ['missing']}]
        for scope in scopes:
            with self.subTest(scope=scope), self.assertRaises(ReviewSnapshotError):
                build_review_snapshot(self.project, scope, assets=self.assets)

    def test_foreign_image_and_invalid_numeric_data_fail_closed(self):
        self.assets[0]['projectId'] = 'other-project'
        with self.assertRaises(ReviewSnapshotError):
            build_review_snapshot(self.project, {'imageIds': ['image-a']}, assets=self.assets)
        for value in (True, -1, float('nan'), float('inf'), '100'):
            self.project['candidates'][0]['unitPrice'] = value
            with self.subTest(value=value), self.assertRaises(ReviewSnapshotError):
                build_review_snapshot(self.project, {'candidateIds': ['chair-a']})

    def test_selected_text_redacts_credentials_and_private_asset_routes(self):
        self.project['brief']['notes'] = 'Keep oak. sk-testsecret123456 /api/assets/private.png /api/cloud-assets/private /storage/v1/object/private'
        result = build_review_snapshot(self.project, {'noteFields': ['notes']})
        self.assertIn('Keep oak.', result['notes']['notes'])
        for value in ('sk-testsecret', '/api/', '/storage/'):
            self.assertNotIn(value, json.dumps(result))

    def test_known_fit_failure_is_not_erased_or_promoted(self):
        self.project['candidates'][0]['fitStatus'] = 'fail'
        result = build_review_snapshot(self.project, {'candidateIds': ['chair-a']})
        self.assertEqual(result['candidates'][0]['fitStatus'], 'fail')
        self.project['candidates'][0]['fitStatus'] = 'pass'
        result = build_review_snapshot(self.project, {'candidateIds': ['chair-a']})
        self.assertEqual(result['candidates'][0]['fitStatus'], 'unverified')


if __name__ == '__main__':
    unittest.main()
