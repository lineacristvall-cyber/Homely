"""Owner-only review previews via temporary HTTP; no disclosure or provider calls."""
import copy
import json
import unittest
from unittest.mock import patch
from backend import server
from backend.review_snapshot import ReviewSnapshotError
from backend.tests import test_cloud_routes as fixtures

A, B, PA, PB, LOCAL, SA, SB = (getattr(fixtures, key) for key in ('A', 'B', 'PA', 'PB', 'LOCAL', 'SA', 'SB'))


class ReviewRouteTests(unittest.TestCase):
    stop_http = fixtures.CloudRouteTests.stop_http
    request = fixtures.CloudRouteTests.request

    def setUp(self):
        fixtures.CloudRouteTests.setUp(self)
        case = self
        base_store = server.CloudProjectStore
        self.documents = {}
        for identifier, owner in ((PA, A), (PB, B)):
            document = fixtures.project(identifier, 'PRIVATE project name')
            document['brief'].update(notes='Selected note ' + owner, location='PRIVATE location',
                measurements={'tableUndersideIn': 27, 'roomWidthIn': 120})
            document['candidates'] = [{'id': 'chair-a', 'title': 'Selected chair ' + owner, 'status': 'ready',
                'availableQuantity': 6, 'unitPrice': 100, 'shipping': None, 'tax': None,
                'imageUrl': '/api/cloud-assets/PRIVATE', 'sourceRefs': [{'private': 'PRIVATE provenance'}]},
                {'id': 'chair-b', 'title': 'UNSELECTED chair'}]
            document['room'] = {'imageUrl': '/api/cloud-assets/PRIVATE', 'consent': True}
            self.documents[identifier] = document

        class Store(base_store):
            def get(self, project_id):
                scoped = super().get(project_id)
                return case.documents[project_id] if scoped else None

        patcher = patch.object(server, 'CloudProjectStore', Store)
        patcher.start()
        self.addCleanup(patcher.stop)

    def preview(self, scope=None, version=1, session=SA, project_id=PA, extra=None):
        body = {'expectedVersion': version, 'scope': {} if scope is None else scope}
        body.update(extra or {})
        return self.request('POST', '/api/projects/' + project_id + '/review-preview', body, session=session)

    def test_anonymous_and_cross_owner_denied_before_disclosure(self):
        self.assertEqual(self.preview(session=None)[0], 401)
        self.assertEqual(self.preview(session=SA, project_id=PB)[0], 404)
        self.assertEqual(self.preview(session=SB, project_id=PA)[0], 404)
        for session, identifier, owner in ((SA, PA, A), (SB, PB, B)):
            status, body, _ = self.preview({'candidateIds': ['chair-a']}, session=session, project_id=identifier)
            self.assertEqual(status, 200)
            self.assertEqual(body['preview']['candidates'][0]['title'], 'Selected chair ' + owner)

    def test_empty_scope_discloses_no_content_and_no_access_grant(self):
        status, body, headers = self.preview()
        self.assertEqual(status, 200)
        preview = body['preview']
        self.assertIs(body['canCreateReview'], False)
        self.assertNotIn('previewToken', body)
        self.assertEqual(preview['schemaVersion'], 'homely.review-preview.v1')
        self.assertEqual((preview['candidates'], preview['images'], preview['notes'], preview['measurements']), ([], [], {}, {}))
        text = json.dumps(body)
        self.assertNotIn('PRIVATE', text)
        self.assertNotIn('Selected note', text)
        self.assertNotIn('shareUrl', text)
        self.assertIn('no access', preview['limitations'][0])
        self.assertEqual(headers['Cache-Control'], 'no-store')

    def test_selected_fields_only_and_stored_ready_does_not_claim_current_stock(self):
        scope = {'candidateIds': ['chair-a'], 'noteFields': ['notes'], 'measurementFields': ['tableUndersideIn'], 'imageIds': []}
        status, body, _ = self.preview(scope)
        self.assertEqual(status, 200)
        preview = body['preview']
        self.assertEqual(preview['notes'], {'notes': 'Selected note ' + A})
        self.assertEqual(preview['measurements'], {'tableUndersideIn': 27})
        self.assertEqual(preview['candidates'][0]['availability']['currentStatus'], 'unverified')
        self.assertEqual(preview['candidates'][0]['availability']['sourceStatus'], 'ready')
        self.assertEqual(len(preview['disclosureHash']), 64)
        for forbidden in ('PRIVATE', 'UNSELECTED', 'sourceRefs', 'roomWidthIn', '/api/cloud-assets/'):
            self.assertNotIn(forbidden, json.dumps(body))

    def test_stale_version_conflicts_and_malformed_version_rejected(self):
        self.documents[PA]['version'] = 2
        with patch('backend.review_snapshot.build_review_snapshot') as builder:
            self.assertEqual(self.preview(version=1)[0], 409)
        builder.assert_not_called()
        for version in (None, True, 1.0, '2', 0, -1):
            with self.subTest(version=version):
                self.assertEqual(self.preview(version=version)[0], 400)
        self.assertEqual(self.preview(version=2)[0], 200)

    def test_unknown_or_duplicate_selections_and_all_images_rejected(self):
        scopes = [{'candidateIds': ['foreign']}, {'candidateIds': ['chair-a', 'chair-a']},
                  {'noteFields': ['location']}, {'measurementFields': ['unknown']}, {'all': True},
                  {'candidateIds': 'chair-a'}, {'imageIds': ['PRIVATE']},
                  {'imageIds': ['/api/cloud-assets/PRIVATE']}, {'imageIds': None}]
        for scope in scopes:
            with self.subTest(scope=scope):
                self.assertEqual(self.preview(scope)[0], 400)
        self.assertEqual(self.preview(extra={'assets': [{'id': 'PRIVATE', 'projectId': PA}]})[0], 400)

    def test_preview_never_mutates_store_files_or_enqueues(self):
        documents = copy.deepcopy(self.documents)
        files = {path: path.read_bytes() for path in self.base.rglob('*') if path.is_file()}
        with patch.object(server, 'save_project') as save, patch.object(server, 'save_asset') as asset, patch.object(server, 'background') as background:
            self.assertEqual(self.preview({'candidateIds': ['chair-a'], 'noteFields': ['notes']})[0], 200)
        save.assert_not_called()
        asset.assert_not_called()
        background.assert_not_called()
        self.assertEqual(self.documents, documents)
        self.assertEqual({path: path.read_bytes() for path in self.base.rglob('*') if path.is_file()}, files)

    def test_safe_builder_error_and_request_context_reset(self):
        with patch('backend.review_snapshot.build_review_snapshot', side_effect=ReviewSnapshotError('PRIVATE_TOKEN /Users/private')):
            status, body, _ = self.preview()
        self.assertEqual(status, 400)
        self.assertNotIn('PRIVATE', json.dumps(body))
        self.assertNotIn('/Users/', json.dumps(body))
        self.assertEqual(self.preview(session=SB, project_id=PB)[0], 200)
        self.assertTrue(all(pair == (None, None) for pair in self.context_records))

    def test_explicit_local_mode_has_no_cloud_fallback_or_share_creation(self):
        self.cloud_mode = False
        status, body, _ = self.preview(project_id=LOCAL, session=None)
        self.assertEqual(status, 200)
        self.assertEqual(body['preview']['projectVersion'], 1)
        self.assertEqual(self.preview(project_id=PA, session=None)[0], 404)


if __name__ == '__main__':
    unittest.main()
