"""No network, credentials or application data: pure export regression fixtures."""
import copy
from datetime import datetime, timedelta, timezone
import json
import unittest
from unittest.mock import patch
from backend.privacy import build_project_export, PrivacyExportError, SCHEMA_VERSION

NOW = datetime(2026, 9, 13, 12, 0, tzinfo=timezone(timedelta(hours=-7)))
ASSET = '/api/cloud-assets/11111111-1111-4111-8111-111111111111'


def project(identifier='project-a'):
    candidate = {'id': 'chair-1', 'title': 'Oak chair', 'exactSku': 'SKU-6', 'variant': 'Oak / natural',
        'url': 'https://shop.example/chair', 'sourceId': 'shop.example', 'status': 'lead',
        'availableQuantity': None, 'unitPrice': 150.25, 'shipping': None, 'tax': None,
        'dimensions': {'armHeightIn': 25.5}, 'imageUrl': None,
        'sourceImageUrl': 'https://shop.example/images/chair.jpg', 'imageRights': 'unknown',
        'sourceRefs': [{'url': 'https://shop.example/chair', 'recordId': 'record-1', 'observedAt': '2026-09-12T10:00:00Z',
            'method': 'public_product_page', 'rightsScope': 'Public discovery only', 'availableQuantity': None}],
        'fieldEvidence': {'unitPrice': {'url': 'https://shop.example/chair', 'path': 'jsonld.Product.offers.price',
            'rawValue': 150.25, 'method': 'public_product_page', 'observedAt': '2026-09-12T10:00:00Z'},
            'dimensions': {'rawValue': {'armHeightIn': 25.5}}},
        'lineage': {'candidateId': 'chair-1', 'productSha256': 'a' * 64, 'sourceUrl': 'https://shop.example/chair'}}
    brief = {'quantity': 6, 'hardCap': 1500, 'flexibleTarget': 1000, 'notes': 'Keep the oak table — 6 chairs.',
        'measurements': {'tableUndersideIn': 27, 'chairArmIn': None}}
    return {'id': identifier, 'name': 'Dining room', 'mode': 'pro', 'version': 4,
        'createdAt': '2026-09-10T10:00:00Z', 'updatedAt': '2026-09-12T10:00:00Z', 'brief': brief,
        'room': {'imageUrl': ASSET, 'consent': False, 'uploadedAt': '2026-09-12T10:00:00Z'},
        'candidates': [candidate], 'decisions': [{'id': 'decision-1', 'candidateId': 'chair-1',
            'createdAt': '2026-09-12T10:00:00Z', 'projectVersion': 3, 'deliveredTotal': None, 'readyForHandoff': False,
            'candidateSnapshot': copy.deepcopy(candidate), 'briefSnapshot': copy.deepcopy(brief)}],
        'sourceCoverage': [{'url': 'https://shop.example/chair', 'sourceId': 'shop.example', 'stage': 'enrichment',
            'status': 'blocked', 'reason': 'robots disallowed', 'observedAt': '2026-09-12T10:00:00Z'}],
        'sourceCoverageComplete': False}


class PrivacyExportTests(unittest.TestCase):
    def test_valid_document_evidence_snapshots_and_unknowns_are_preserved(self):
        original = project()
        result = build_project_export([original], now=NOW)
        self.assertEqual(result['projects'], [original])
        self.assertEqual(result['schemaVersion'], SCHEMA_VERSION)
        self.assertEqual(result['exportedAt'], '2026-09-13T19:00:00+00:00')
        self.assertEqual(result['redactionCount'], 0)
        self.assertEqual(json.loads(json.dumps(result))['projects'], [original])

    def test_fit_and_photo_annotations_export_with_redaction(self):
        from backend.tests.test_fit import dining
        brief, candidate = dining()
        original = project()
        original['brief'].update(brief)
        original['brief']['journey']={'step':'fit','keepingDecision':'keep','retainedObjects':[
            {'id':'t','label':'Table','variant':'Oak','confirmed':True,'anchor':{'x':.5,'y':.5,'imageUrl':ASSET}}]}
        original['candidates'][0]['fitEvidence']=candidate['fitEvidence']
        original['brief']['fit']['retainedObject']['identity']='Table access_token=secretvalue'
        output=build_project_export([original])['projects'][0]
        self.assertEqual(output['brief']['fit']['arrangement']['rows'][0]['count'],2)
        self.assertEqual(output['brief']['journey']['retainedObjects'][0]['anchor']['imageUrl'],ASSET)
        self.assertEqual(output['candidates'][0]['fitEvidence']['dimensions']['width']['value'],20)
        self.assertNotIn('secretvalue',json.dumps(output))

    def test_room_setup_export_preserves_choices_and_redacts_private_text(self):
        original = project()
        original['brief'].update(roomType='other', roomLabel='Study', furnishingMode='keep',
                                 retainedItems=['Desk', 'access_token=opaque123'])
        brief = build_project_export([original])['projects'][0]['brief']
        self.assertEqual(brief['roomType'], 'other')
        self.assertEqual(brief['roomLabel'], 'Study')
        self.assertEqual(brief['furnishingMode'], 'keep')
        self.assertEqual(brief['retainedItems'][0], 'Desk')
        self.assertNotIn('opaque123', json.dumps(brief))

    def test_decision_project_version_is_retained_without_inference(self):
        original = project()
        original['decisions'].append({'id': 'older', 'candidateId': 'chair-1'})
        result = build_project_export([original])['projects'][0]
        self.assertEqual(result['version'], 4)
        self.assertEqual(result['decisions'][0]['projectVersion'], 3)
        self.assertNotIn('projectVersion', result['decisions'][1])

    def test_exactly_supplied_owned_subset_and_empty_export(self):
        other = project('project-b')
        self.assertEqual([p['id'] for p in build_project_export([other])['projects']], ['project-b'])
        result = build_project_export([], now=NOW)
        self.assertEqual((result['projectCount'], result['projects']), (0, []))

    def test_no_mutation_or_shared_nested_references(self):
        original = project()
        before = copy.deepcopy(original)
        result = build_project_export([original], now=NOW)
        result['projects'][0]['decisions'][0]['briefSnapshot']['quantity'] = 99
        self.assertEqual(original, before)

    def test_missing_consent_state_and_timestamps_are_not_fabricated(self):
        result = build_project_export([{'id': 'p', 'room': {}, 'brief': {}}], now=NOW)
        self.assertEqual(result['projects'], [{'id': 'p', 'room': {}, 'brief': {}}])
        self.assertIn('copied history', result['limitations'][-1])

    def test_secret_fields_removed_at_every_supported_nesting_level(self):
        doc = project()
        sensitive = {'owner_id': 'other-user', 'access_token': 'SENTINEL_ACCESS', 'refreshToken': 'SENTINEL_REFRESH',
            'cookies': 'SENTINEL_COOKIE', 'storagePath': 'SENTINEL_STORAGE', 'apiKey': 'SENTINEL_KEY'}
        for record in (doc, doc['brief'], doc['room'], doc['candidates'][0], doc['candidates'][0]['sourceRefs'][0],
                       doc['candidates'][0]['fieldEvidence']['unitPrice'], doc['candidates'][0]['lineage'],
                       doc['decisions'][0], doc['decisions'][0]['candidateSnapshot'], doc['sourceCoverage'][0]):
            record.update(sensitive)
        doc['sessions'] = sensitive
        doc['jobs'] = [{'result': sensitive}]
        rendered = json.dumps(build_project_export([doc]))
        for value in sensitive.values():
            self.assertNotIn(value, rendered)
        self.assertIn('SKU-6', rendered)

    def test_credential_values_in_allowed_free_text_are_redacted(self):
        doc = project()
        secrets = ['sk-testkey123456789', 'sb_secret_fakekey', 'eyJhbGciOiJub25lIn0.eyJzdWIiOiJhIn0.signature',
                   'access_token=opaque123', 'Bearer opaque456', 'homely_auth=opaque789']
        doc['brief']['notes'] = 'Keep table. ' + ' '.join(secrets)
        rendered = json.dumps(build_project_export([doc]))
        for secret in secrets:
            self.assertNotIn(secret, rendered)
        self.assertIn('Keep table.', rendered)

    def test_private_and_signed_urls_never_leave_builder(self):
        urls = ['https://project.supabase.co/storage/v1/object/sign/bucket/object?token=opaque',
                'https://cdn.example/storage/v1/object/sign/private?token=opaque',
                'https://user:pass@shop.example/chair', 'file:///Users/me/private.png',
                'http://127.0.0.1/secret', 'http://[::1]/secret', 'http://10.0.0.1/secret',
                '/data/private-cloud-cache/image.png', '/api/cloud-assets/../secret', 'https://shop.example:bad/chair']
        for url in urls:
            with self.subTest(url=url):
                doc = project()
                doc['room']['imageUrl'] = url
                result = build_project_export([doc])
                self.assertIsNone(result['projects'][0]['room']['imageUrl'])
                self.assertNotIn(url, json.dumps(result))

    def test_public_url_query_and_fragment_removed_but_origin_path_and_app_ref_retained(self):
        doc = project()
        doc['candidates'][0]['url'] = 'https://shop.example/chair?variant=oak&signature=opaque#private'
        result = build_project_export([doc])
        self.assertEqual(result['projects'][0]['candidates'][0]['url'], 'https://shop.example/chair')
        self.assertEqual(result['projects'][0]['room']['imageUrl'], ASSET)
        self.assertNotIn('opaque', json.dumps(result))
        self.assertGreater(result['redactionCount'], 0)

    def test_embedded_storage_links_and_filesystem_paths_are_redacted(self):
        doc = project()
        doc['brief']['notes'] = 'Compare https://p.supabase.co/storage/v1/object/sign/b/x?token=secret and /Users/alice/private.png and data/private-cloud-cache/a.png'
        doc['candidates'][0]['fieldEvidence']['unitPrice']['path'] = '/private/tmp/secret'
        text = json.dumps(build_project_export([doc]))
        for value in ('token=secret', '/Users/alice', 'data/private-cloud-cache', '/private/tmp/secret'):
            self.assertNotIn(value, text)
        self.assertIn('Compare ', text)

    def test_variant_map_consent_map_and_lineage_retained_without_extra_keys(self):
        doc = project()
        doc['room']['consent'] = {'upload': True, 'generation': False, 'access_token': 'remove-me'}
        doc['candidates'][0]['variant'] = {'color': 'oak', 'size': 'large', 'session': 'remove-me'}
        result = build_project_export([doc])['projects'][0]
        self.assertEqual(result['room']['consent'], {'upload': True, 'generation': False})
        self.assertEqual(result['candidates'][0]['variant'], {'color': 'oak', 'size': 'large'})
        self.assertEqual(result['candidates'][0]['lineage']['productSha256'], 'a' * 64)

    def test_invalid_shapes_duplicates_and_nonfinite_values_fail_safely(self):
        bad = [None, {}, [{'id': 'x'}, {'id': 'x'}], [{'id': 'x', 'candidates': ['not-record']}],
               [{'id': 'x', 'brief': {'quantity': float('nan')}}], [{'id': 'x', 'brief': []}],
               [{'id': 'x', 'room': {'imageUrl': {'access_token': 'SECRET'}}}]]
        for value in bad:
            with self.subTest(value=type(value)), self.assertRaises(PrivacyExportError) as context:
                build_project_export(value)
            self.assertNotIn('SECRET', str(context.exception))

    def test_time_and_export_bounds_are_explicit_errors(self):
        with self.assertRaises(PrivacyExportError):
            build_project_export([], now=datetime(2026, 1, 1))
        with patch('backend.privacy.MAX_PROJECTS', 1), self.assertRaises(PrivacyExportError):
            build_project_export([project('a'), project('b')])
        with patch('backend.privacy.MAX_EXPORT_BYTES', 100), self.assertRaises(PrivacyExportError):
            build_project_export([project()])


if __name__ == '__main__':
    unittest.main()
