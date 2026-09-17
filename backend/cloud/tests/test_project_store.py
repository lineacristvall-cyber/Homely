import copy
import io
import json
import unittest
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError
from PIL import Image
from backend.cloud.supabase import CloudSession, CloudSettings, CloudError, PROJECT_URL, BUCKET
from backend.cloud import project_store as m

OWNER = 'aaaaaaaa-1111-4111-8111-111111111111'
OTHER = 'bbbbbbbb-2222-4222-8222-222222222222'
PROJECT = 'cccccccc-3333-4333-8333-333333333333'
ASSET = 'dddddddd-4444-4444-8444-444444444444'
SIGNED = PROJECT_URL + '/storage/v1/object/sign/' + BUCKET + '/' + OWNER + '/' + PROJECT + '/' + ASSET + '?token=fixture-secret-signature'


def row(version=1):
    return {'id': PROJECT, 'owner_id': OWNER, 'name': 'Dining room', 'mode': 'designer', 'version': version,
            'created_at': '2026-09-13T00:00:00Z', 'updated_at': '2026-09-13T01:00:00Z',
            'data': {'brief': {'quantity': 6}, 'room': None, 'candidates': [{'id': 'lead'}], 'decisions': []}}


def png():
    output = io.BytesIO()
    Image.new('RGB', (3, 4), 'white').save(output, 'PNG')
    return output.getvalue()


class ProjectStoreTests(unittest.TestCase):
    def setUp(self):
        self.session = CloudSession(CloudSettings(publishable_key='sb_publishable_fixture'), 'fixture-access')
        self.session.user = MagicMock(return_value={'id': OWNER})
        self.session.list_projects = MagicMock(return_value=[row()])
        self.session.get_project = MagicMock(return_value=row())
        self.session.create_project = MagicMock(return_value=row())
        self.session.update_project = MagicMock(return_value=row(2))
        self.session.upload_asset = MagicMock(return_value={'id': ASSET, 'owner_id': OWNER, 'project_id': PROJECT, 'kind': 'room_original'})
        self.session.signed_asset_url = MagicMock(return_value=SIGNED)
        self.store = m.CloudProjectStore(self.session)

    def test_export_uses_dedicated_enumeration_and_checks_each_owner(self):
        self.session.list_projects_for_export = MagicMock(return_value=[row()])
        exported = self.store.list_for_export()
        self.assertEqual(exported[0]['id'], PROJECT)
        self.assertNotIn('owner_id', exported[0])
        self.session.list_projects_for_export.assert_called_once_with()
        foreign = row()
        foreign['owner_id'] = OTHER
        self.session.list_projects_for_export.return_value = [row(), foreign]
        with self.assertRaises(CloudError) as caught:
            self.store.list_for_export()
        self.assertEqual(caught.exception.status, 403)

    def test_export_defensive_row_count_and_provider_failure(self):
        self.session.list_projects_for_export = MagicMock(return_value=[row()] * 1001)
        with self.assertRaises(CloudError) as caught:
            self.store.list_for_export()
        self.assertEqual(caught.exception.status, 413)
        self.session.list_projects_for_export.side_effect = CloudError('Fixture failure', 503)
        with self.assertRaises(CloudError):
            self.store.list_for_export()

    def test_list_get_canonical_mapping_and_data_cannot_override_envelope(self):
        value = row()
        value['data'].update(id='forged', version=900, mode='diy', owner_id=OTHER, name='forged', createdAt='forged')
        self.session.get_project.return_value = value
        result = self.store.get(PROJECT)
        self.assertEqual(result['id'], PROJECT)
        self.assertEqual(result['version'], 1)
        self.assertEqual(result['mode'], 'pro')
        self.assertEqual(result['createdAt'], value['created_at'])
        self.assertNotIn('owner_id', result)
        self.assertEqual(self.store.list()[0]['id'], PROJECT)

    def test_create_sends_only_document_whitelist_and_generated_id_wins(self):
        project = {'id': 'local-id', 'name': 'Dining room', 'mode': 'pro', 'version': 99, 'owner_id': OTHER,
                   'brief': {'quantity': 6}, 'room': None, 'candidates': [], 'decisions': [], 'secret': 'never-send'}
        result = self.store.create(project)
        args, kwargs = self.session.create_project.call_args
        self.assertEqual(args, ('Dining room',))
        self.assertEqual(kwargs['mode'], 'designer')
        self.assertEqual(set(kwargs['data']), set(m.DOCUMENT_FIELDS))
        self.assertNotIn('never-send', json.dumps(kwargs))
        self.assertEqual(result['id'], PROJECT)
        self.assertEqual(result['version'], 1)

    def test_diy_mapping(self):
        value = row()
        value['mode'] = 'diy'
        self.session.create_project.return_value = value
        self.assertEqual(self.store.create({'name': 'Room', 'mode': 'diy'})['mode'], 'diy')
        self.assertEqual(self.session.create_project.call_args.kwargs['mode'], 'diy')

    def test_coverage_defaults_and_roundtrip(self):
        project = self.store.get(PROJECT)
        self.assertEqual(project['sourceCoverage'], [])
        self.assertFalse(project['sourceCoverageComplete'])
        coverage = [{'url': 'https://fixture.invalid/chair', 'sourceId': 'fixture',
                     'stage': 'enrichment', 'status': 'blocked', 'reason': 'Fixture access denied'}]
        project.update(version=2, sourceCoverage=coverage, sourceCoverageComplete=False)
        saved_row = row(2)
        saved_row['data'].update(sourceCoverage=copy.deepcopy(coverage), sourceCoverageComplete=False)
        self.session.update_project.return_value = saved_row
        result = self.store.save(project)
        sent = self.session.update_project.call_args.kwargs['data']
        self.assertEqual(sent['sourceCoverage'], coverage)
        self.assertFalse(sent['sourceCoverageComplete'])
        self.assertEqual(result['sourceCoverage'], coverage)
        coverage[0]['reason'] = 'changed caller input'
        self.assertEqual(result['sourceCoverage'][0]['reason'], 'Fixture access denied')

    def test_coverage_rejects_invalid_types(self):
        for fields in ({'sourceCoverage': {}}, {'sourceCoverage': [42]},
                       {'sourceCoverageComplete': 'false'}, {'sourceCoverageComplete': 0}):
            with self.subTest(fields=fields), self.assertRaises(CloudError):
                self.store.create({'name': 'Fixture', 'mode': 'pro', **fields})
        self.session.create_project.assert_not_called()

    def test_save_uses_previous_version_and_returns_canonical(self):
        project = self.store.get(PROJECT)
        project['version'] += 1
        project['brief'].update(quantity=8, roomType='bedroom', roomLabel='Bedroom', furnishingMode='keep', retainedItems=['Oak bed'])
        result = self.store.save(project)
        self.assertEqual(self.session.update_project.call_args.args, (PROJECT, 1))
        self.assertEqual(self.session.update_project.call_args.kwargs['data']['brief']['quantity'], 8)
        self.assertEqual(self.session.update_project.call_args.kwargs['data']['brief']['retainedItems'], ['Oak bed'])
        self.assertEqual(self.session.update_project.call_args.kwargs['data']['brief']['roomType'], 'bedroom')
        self.assertEqual(result['version'], 2)
        self.session.create_project.assert_not_called()

    def test_conflict_missing_and_mode_change_never_upsert(self):
        project = self.store.get(PROJECT)
        project['version'] = 2
        self.session.get_project.return_value = row(2)
        with self.assertRaises(CloudError) as caught:
            self.store.save(project)
        self.assertEqual(caught.exception.status, 409)
        self.session.update_project.assert_not_called()
        self.session.get_project.side_effect = CloudError('missing', 404)
        self.assertIsNone(self.store.get(PROJECT))
        with self.assertRaises(CloudError):
            self.store.save(project)
        self.session.create_project.assert_not_called()
        self.session.get_project.side_effect = None
        self.session.get_project.return_value = row()
        project['mode'] = 'diy'
        with self.assertRaises(CloudError) as caught:
            self.store.save(project)
        self.assertEqual(caught.exception.status, 400)

    def test_update_race_propagates_conflict(self):
        project = self.store.get(PROJECT)
        project['version'] = 2
        self.session.update_project.side_effect = CloudError('changed', 409)
        with self.assertRaises(CloudError) as caught:
            self.store.save(project)
        self.assertEqual(caught.exception.status, 409)

    def test_foreign_owner_rows_denied(self):
        value = row()
        value['owner_id'] = OTHER
        self.session.get_project.return_value = value
        with self.assertRaises(CloudError) as caught:
            self.store.get(PROJECT)
        self.assertEqual(caught.exception.status, 403)

    def test_invalid_documents_and_versions(self):
        for project in ({'brief': []}, {'candidates': {}}, {'brief': {'bad': float('nan')}}, {'room': 'bad'}):
            with self.assertRaises(CloudError):
                self.store.create(project)
        project = self.store.get(PROJECT)
        for version in (1, True, 2.5, None):
            project['version'] = version
            with self.assertRaises(CloudError):
                self.store.save(project)

    def test_upload_validates_image_and_returns_stable_url(self):
        result = self.store.upload(PROJECT, 'room_original', png(), 'image/png', {'upload': True}, {'original': True})
        self.assertEqual(result['assetId'], ASSET)
        self.assertEqual(result['imageUrl'], '/api/cloud-assets/' + ASSET)
        self.assertNotIn('token=', json.dumps(result))
        self.assertEqual(self.session.upload_asset.call_args.args[5], {'original': True})

    def test_upload_rejects_fake_image_mime_consent_and_pixels(self):
        for raw, mime, consent in ((b'not-an-image', 'image/png', {'upload': True}), (png(), 'image/jpeg', {'upload': True}), (png(), 'image/png', {})):
            with self.assertRaises(CloudError):
                self.store.upload(PROJECT, 'room_original', raw, mime, consent)
        with patch.object(m, 'MAX_IMAGE_PIXELS', 2):
            with self.assertRaises(CloudError):
                self.store.upload(PROJECT, 'room_original', png(), 'image/png', {'upload': True})
        self.session.upload_asset.assert_not_called()

    def test_read_validates_decoding_and_keeps_signature_private(self):
        context = MagicMock()
        context.__enter__.return_value.headers = {'Content-Type': 'image/png'}
        context.__enter__.return_value.read.return_value = png()
        opener = MagicMock()
        opener.open.return_value = context
        with patch.object(m, 'build_opener', return_value=opener):
            raw, mime = self.store.read(ASSET)
        self.assertEqual((raw, mime), (png(), 'image/png'))
        self.assertIsNone(opener.open.call_args.args[0].get_header('Authorization'))
        self.session.signed_asset_url.assert_called_once_with(ASSET, expires_in=60)

    def test_read_rejects_other_origin_owner_path_or_redirect(self):
        for signed in (SIGNED.replace(PROJECT_URL, 'https://evil.invalid'), SIGNED.replace('https:', 'http:'),
                       SIGNED.replace(OWNER, OTHER), SIGNED.replace(ASSET, PROJECT), SIGNED + '#fragment'):
            self.session.signed_asset_url.return_value = signed
            with patch.object(m, 'build_opener') as opener:
                with self.assertRaises(CloudError):
                    self.store.read(ASSET)
                opener.assert_not_called()
        self.session.signed_asset_url.return_value = SIGNED
        opener = MagicMock()
        opener.open.side_effect = HTTPError(SIGNED, 302, 'sensitive signature', {}, None)
        with patch.object(m, 'build_opener', return_value=opener):
            with self.assertRaises(CloudError) as caught:
                self.store.read(ASSET)
        self.assertNotIn('fixture-secret-signature', str(caught.exception))
        self.assertEqual(opener.open.call_count, 1)

    def test_read_rejects_oversize_or_invalid_content(self):
        for headers, raw in (({'Content-Type': 'text/html'}, b'html'), ({'Content-Type': 'image/png'}, b'fake'),
                             ({'Content-Type': 'image/png', 'Content-Length': str(m.MAX_IMAGE_BYTES + 1)}, png())):
            context = MagicMock()
            context.__enter__.return_value.headers = headers
            context.__enter__.return_value.read.return_value = raw
            opener = MagicMock()
            opener.open.return_value = context
            with patch.object(m, 'build_opener', return_value=opener):
                with self.assertRaises(CloudError):
                    self.store.read(ASSET)

if __name__ == '__main__':
    unittest.main()
