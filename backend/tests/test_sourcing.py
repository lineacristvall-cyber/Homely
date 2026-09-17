import copy
import json
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock
from urllib.error import HTTPError
from backend import sourcing as s

NOW = datetime(2026, 9, 13, 12, tzinfo=timezone.utc)

class VerificationTests(unittest.TestCase):
    def setUp(self):
        self.brief = dict(quantity=6, location='94110', hardCap=700)
        self.obs = dict(sourceId='fixture', method='fixture_inventory', recordId='stock-1',
                        url='https://shop.example/chair', exactSku='SKU-1', variant='oak',
                        observedAt=NOW.isoformat(), region='94110', availableQuantity=6,
                        unitPrice=100, shipping=20, tax=50, currency='USD', costComplete=True)
        self.candidate = dict(self.obs, status='ready', sourceRefs=[self.obs])
        self.registration = patch.dict(s.STOCK_ADAPTERS, {'fixture': {'method': 'fixture_inventory'}})
        self.registration.start()
        self.addCleanup(self.registration.stop)

    def verify(self):
        return s.verify_candidate(self.candidate, self.brief, NOW)

    def test_complete_registered_evidence(self):
        result = self.verify()
        self.assertEqual(result['status'], 'ready')
        self.assertEqual(result['deliveredTotal'], 670)

    def test_search_cannot_be_ready_even_with_complete_claims(self):
        self.candidate['method'] = 'openai_web_search'
        self.assertEqual(self.verify()['status'], 'lead')

    def test_unregistered_source_cannot_be_ready(self):
        self.candidate['sourceId'] = 'unregistered'
        self.assertEqual(self.verify()['status'], 'lead')

    def test_quantity_is_exact_and_numeric(self):
        for quantity in (None, '6', True, 5.5):
            with self.subTest(quantity=quantity):
                self.obs['availableQuantity'] = quantity
                self.assertEqual(self.verify()['status'], 'lead')
        self.obs['availableQuantity'] = 5
        self.assertEqual(self.verify()['status'], 'unavailable')
        self.obs['availableQuantity'] = 0
        self.assertEqual(self.verify()['status'], 'unavailable')

    def test_wrong_variant_or_sku_or_region(self):
        for field in ('variant', 'exactSku', 'region', 'url', 'recordId'):
            with self.subTest(field=field):
                previous = self.obs[field]
                self.obs[field] = 'mismatch'
                if field == 'recordId':
                    self.obs[field] = None
                self.assertEqual(self.verify()['status'], 'lead')
                self.obs[field] = previous

    def test_freshness_and_future(self):
        self.obs['observedAt'] = (NOW - timedelta(seconds=901)).isoformat()
        self.assertEqual(self.verify()['status'], 'stale')
        self.obs['observedAt'] = (NOW + timedelta(seconds=1)).isoformat()
        self.assertEqual(self.verify()['status'], 'lead')
        self.obs['observedAt'] = '2026-09-13T12:00:00'
        self.assertEqual(self.verify()['status'], 'lead')

    def test_cost_currency_cap_and_unknown(self):
        self.brief['hardCap'] = 669.99
        self.assertEqual(self.verify()['status'], 'lead')
        self.brief['hardCap'] = 670
        self.assertEqual(self.verify()['status'], 'ready')
        for field, value in [('tax', None), ('currency', 'EUR'), ('unitPrice', 101), ('costComplete', False)]:
            old = self.obs[field]
            self.obs[field] = value
            self.assertEqual(self.verify()['status'], 'lead')
            self.obs[field] = old

    def test_does_not_mutate_input(self):
        original = copy.deepcopy(self.candidate)
        self.verify()
        self.assertEqual(self.candidate, original)


class SearchTests(unittest.TestCase):
    def setUp(self):
        self.url = 'https://shop.example/chair'
        self.raw = dict(title='Oak chair', seller='Shop', url=self.url, exactSku='OAK', variant='oak',
                        unitPrice=120, currency='USD', availableQuantity=99, status='ready')

    def response(self, rows=None, sources=None):
        return dict(id='response-fixture', status='completed', output=[
            dict(type='web_search_call', action=dict(sources=sources if sources is not None else [dict(url=self.url, title='Chair')])),
            dict(type='message', content=[dict(type='output_text', text=json.dumps(dict(candidates=rows if rows is not None else [self.raw])))])])

    def run_search(self, response):
        context = MagicMock()
        context.__enter__.return_value.read.return_value = json.dumps(response).encode()
        with patch.object(s, 'urlopen', return_value=context) as mocked, patch.object(s, 'enrich_product_url', side_effect=s.SourcingError('Fixture skips page fetch')):
            result = s.search_products({'itemType': 'chair', 'quantity': 6}, 'test-placeholder')
        payload = json.loads(mocked.call_args.args[0].data)
        self.assertEqual(payload['max_tool_calls'], 6)
        self.assertFalse(payload['store'])
        self.assertEqual(mocked.call_count, 1)
        self.assertEqual(mocked.call_args.kwargs['timeout'], 80)
        return result

    def test_normalization_never_invents_stock_or_rights(self):
        candidate = self.run_search(self.response())[0]
        self.assertEqual(candidate['status'], 'lead')
        self.assertEqual(candidate['unitPrice'], 120)
        for field in ('availableQuantity', 'shipping', 'tax', 'imageUrl'):
            self.assertIsNone(candidate[field])
        self.assertEqual(candidate['sourceRefs'][0]['recordId'], 'response-fixture')

    def test_uncited_and_blocked_sources_rejected(self):
        with self.assertRaises(s.SourcingError):
            self.run_search(self.response(sources=[]))
        self.raw['url'] = 'https://www.ebay.com/itm/123'
        with self.assertRaises(s.SourcingError):
            self.run_search(self.response(sources=[dict(url=self.raw['url'])]))

    def test_duplicates_and_invalid_price(self):
        self.raw['unitPrice'] = '120'
        result = self.run_search(self.response(rows=[self.raw, self.raw]))
        self.assertEqual(len(result), 1)
        self.assertIsNone(result[0]['unitPrice'])

    def test_unsafe_urls(self):
        for url in ('javascript:alert(1)', 'http://127.0.0.1/a', 'http://localhost/x', 'https://a:b@shop.example/x'):
            self.assertIsNone(s._url(url))

    def test_missing_configuration_and_provider_errors(self):
        with self.assertRaisesRegex(s.SourcingError, 'server-side'):
            s.search_products({'itemType': 'chair'}, None)
        with patch.object(s, 'urlopen', side_effect=HTTPError('https://api.openai.com', 429, 'sensitive body', {}, None)):
            with self.assertRaises(s.SourcingError) as caught:
                s.search_products({'itemType': 'chair'}, 'test-placeholder')
        self.assertNotIn('sensitive', str(caught.exception))
        self.assertIn('rate limited', str(caught.exception))

    def test_incomplete_and_empty_result(self):
        with self.assertRaises(s.SourcingError):
            self.run_search(dict(status='incomplete', output=[]))
        self.assertEqual(self.run_search(self.response(rows=[])), [])



class PublicPageTests(unittest.TestCase):
    def page(self, data):
        return '<html><script type="application/ld+json">' + json.dumps(data) + '</script></html>'

    def test_jsonld_graph_product_offer_reference(self):
        data = {'@graph': [{'@type': 'Product', 'name': 'Oak chair', 'sku': 'A1', 'color': 'Natural',
                            'image': '/chair.jpg', 'offers': {'@id': '#offer'}},
                           {'@id': '#offer', '@type': 'Offer', 'price': '199.50', 'priceCurrency': 'USD',
                            'availability': 'https://schema.org/InStock', 'inventoryLevel': 6}]}
        result = s._extract_page(self.page(data), 'https://shop.example/p', NOW.isoformat())
        self.assertEqual(result['unitPrice'], 199.5)
        self.assertEqual(result['exactSku'], 'A1')
        self.assertEqual(result['sourceImageUrl'], 'https://shop.example/chair.jpg')
        self.assertIsNone(result['availableQuantity'])
        self.assertIsNone(result['imageUrl'])
        self.assertEqual(result['status'], 'lead')
        self.assertIn('unitPrice', result['fieldEvidence'])

    def test_multiple_variants_do_not_pick_arbitrary_price(self):
        data = [{'@type': 'Product', 'name': 'Oak', 'offers': {'price': 20, 'priceCurrency': 'USD'}},
                {'@type': 'Product', 'name': 'Walnut', 'offers': {'price': 40, 'priceCurrency': 'USD'}}]
        result = s._extract_page('<title>Chairs</title>' + self.page(data), 'https://shop.example/p', NOW.isoformat())
        self.assertIsNone(result['unitPrice'])
        self.assertIsNone(result['exactSku'])
        self.assertIn('Multiple products', result['reason'])

    def test_metadata_and_challenge(self):
        html = '<title>Chair</title><meta property="product:price:amount" content="125"><meta property="product:price:currency" content="USD">'
        self.assertEqual(s._extract_page(html, 'https://shop.example/p', NOW.isoformat())['unitPrice'], 125)
        with self.assertRaisesRegex(s.SourcingError, 'challenge'):
            s._extract_page('<title>Verify you are human</title>', 'https://shop.example/p', NOW.isoformat())

    def test_dns_private_and_mixed_addresses_blocked(self):
        for addresses in [('127.0.0.1',), ('93.184.216.34', '10.0.0.1'), ('169.254.169.254',)]:
            response = [(2, 1, 6, '', (ip, 443)) for ip in addresses]
            with patch.object(s.socket, 'getaddrinfo', return_value=response):
                with self.assertRaisesRegex(s.SourcingError, 'private or reserved'):
                    s._public_target('https://shop.example/p')

    def test_robots_disallow_and_403(self):
        for status, body in [(200, b'User-agent: *\nDisallow: /'), (403, b'')]:
            with patch.object(s, '_fetch_redirects', return_value=('https://shop.example/robots.txt', status, {'content-type': 'text/plain'}, body)):
                with self.assertRaises(s.SourcingError):
                    s._check_robots('https://shop.example/p', 100)

    def test_redirect_private_target_blocked(self):
        with patch.object(s.socket, 'getaddrinfo', return_value=[(2, 1, 6, '', ('93.184.216.34', 443))]), patch.object(s, '_fetch_once', return_value=('https://shop.example/p', 302, {'location': 'https://127.0.0.1/private'}, b'')):
            with self.assertRaises(s.SourcingError):
                s._fetch_redirects('https://shop.example/p', 100)

    def test_import_status_and_page_provenance(self):
        body = self.page({'@type': 'Product', 'name': 'Public chair', 'sku': '1'}).encode()
        with patch.object(s, '_fetch_redirects', return_value=('https://shop.example/p', 200, {'content-type': 'text/html'}, body)) as fetched:
            result = s.enrich_product_url('https://shop.example/p')
        self.assertEqual(result['status'], 'lead')
        self.assertEqual(result['sourceRefs'][0]['method'], 'public_product_page')
        self.assertTrue(fetched.call_args.kwargs['check_robots'])


class ExtractionEdgeTests(unittest.TestCase):
    def test_bundle_price_and_dimension_unit(self):
        data = {'@type': 'Product', 'name': 'Set of 2 chairs', 'offers': {'@type': 'Offer', 'price': '200', 'priceCurrency': 'USD'},
                'width': {'value': 50.8, 'unitCode': 'CMT'}, 'depth': {'value': 18}, 'height': {'value': 32, 'unitCode': 'INH'}}
        html = '<script type="application/ld+json">' + json.dumps(data) + '</script>'
        result = s._extract_page(html, 'https://shop.example/p', NOW.isoformat())
        self.assertIsNone(result['unitPrice'])
        self.assertEqual(result['listedPrice'], 200)
        self.assertEqual(result['dimensions'], {'widthIn': 20, 'heightIn': 32})

    def test_metadata_provenance_path(self):
        result = s._extract_page('<title>Chair title</title>', 'https://shop.example/p', NOW.isoformat())
        self.assertEqual(result['fieldEvidence']['title']['path'], 'html.title')



class CoverageTests(unittest.TestCase):
    def response(self, count=3):
        urls = [f'https://shop.example/chair-{i}' for i in range(count)]
        rows = [{'title': f'Chair {i}', 'url': url, 'currency': 'USD', 'unitPrice': 100} for i, url in enumerate(urls)]
        return {'id': 'coverage-fixture', 'status': 'completed', 'output': [
            {'type': 'web_search_call', 'action': {'sources': [{'url': url} for url in urls]}},
            {'type': 'message', 'content': [{'type': 'output_text', 'text': json.dumps({'candidates': rows})}]}]}

    def run_response(self, response, side_effect, compatibility=False):
        context = MagicMock()
        context.__enter__.return_value.read.return_value = json.dumps(response).encode()
        with patch.object(s, 'urlopen', return_value=context) as provider, patch.object(s, 'enrich_product_url', side_effect=side_effect) as enrich:
            fn = s.search_products if compatibility else s.search_products_with_coverage
            result = fn({'itemType': 'chair'}, 'fixture-key-not-real')
        return result, provider, enrich

    def test_actual_attempts_record_robot_block_and_timeout_with_leads_retained(self):
        result, provider, enrich = self.run_response(self.response(), [
            s.SourcingError('Source robots policy disallows this page; import is blocked.'),
            s.SourcingError('Source could not be reached securely or timed out.')])
        self.assertEqual(provider.call_count, 1)
        self.assertEqual(enrich.call_count, 2)
        self.assertEqual(len(result['candidates']), 3)
        self.assertEqual([record['status'] for record in result['coverage']], ['completed', 'blocked', 'failed'])
        self.assertEqual([record['stage'] for record in result['coverage']], ['discovery', 'enrichment', 'enrichment'])
        self.assertEqual(result['coverage'][1]['url'], 'https://shop.example/chair-0')
        self.assertIn('robots', result['coverage'][1]['reason'])
        self.assertIn('timed out', result['candidates'][1]['enrichmentError'])
        self.assertNotIn('enrichmentStatus', result['candidates'][2])
        self.assertFalse(result['coverageComplete'])
        self.assertIn('internal attempted sites are unavailable', result['coverage'][0]['reason'])
        for candidate in result['candidates']:
            self.assertEqual(candidate['status'], 'lead')
            self.assertIsNone(candidate['availableQuantity'])
            self.assertIsNone(candidate['imageUrl'])
        for record in result['coverage']:
            self.assertIsNotNone(s._time(record['observedAt']))

    def test_unsupported_enrichment_remains_visible_without_fabricated_site_attempts(self):
        diagnostic = 'This source is not supported; integration rights are unvalidated.'
        result, _, _ = self.run_response(self.response(1), [s.SourcingError(diagnostic)])
        self.assertEqual(len(result['coverage']), 2)
        self.assertEqual(result['coverage'][1]['status'], 'blocked')
        self.assertEqual(result['coverage'][1]['reason'], diagnostic)
        self.assertEqual(result['candidates'][0]['enrichmentError'], diagnostic)
        self.assertFalse(any(record['sourceId'] in s.BLOCKED_DOMAINS for record in result['coverage']))

    def test_completed_enrichment_preserves_image_provenance_not_rights(self):
        source_image = 'https://shop.example/reference.jpg'
        page = {'sourceRefs': [{'url': 'https://shop.example/chair-0', 'method': 'public_product_page'}],
                'reason': 'Public-page lead.', 'sourceImageUrl': source_image,
                'fieldEvidence': {'sourceImageUrl': {'path': 'jsonld.Product.image'}}}
        result, _, _ = self.run_response(self.response(1), [page])
        self.assertEqual(result['coverage'][1]['status'], 'completed')
        self.assertEqual(result['candidates'][0]['sourceImageUrl'], source_image)
        self.assertIsNone(result['candidates'][0]['imageUrl'])
        self.assertIn('rights remain unverified', result['coverage'][1]['reason'])

    def test_unexpected_enrichment_failure_does_not_echo_arbitrary_exception(self):
        result, _, _ = self.run_response(self.response(1), [RuntimeError('secret-provider-body fixture-key-not-real')])
        self.assertEqual(result['coverage'][1]['status'], 'failed')
        serialized = json.dumps(result)
        self.assertNotIn('secret-provider-body', serialized)
        self.assertNotIn('fixture-key-not-real', serialized)
        self.assertEqual(len(result['candidates']), 1)

    def test_provider_failure_preserves_safe_discovery_diagnostic(self):
        error = HTTPError('https://api.openai.com', 429, 'secret-response-body', {}, None)
        with patch.object(s, 'urlopen', side_effect=error) as provider, patch.object(s, 'enrich_product_url') as enrich:
            with self.assertRaises(s.SourcingError) as caught:
                s.search_products_with_coverage({'itemType': 'chair'}, 'fixture-key-not-real')
        failure = caught.exception
        self.assertEqual(len(failure.coverage), 1)
        self.assertEqual(failure.coverage[0]['status'], 'failed')
        self.assertEqual(failure.coverage[0]['sourceId'], 'openai.web_search')
        self.assertFalse(failure.coverageComplete)
        self.assertIn('rate limited', failure.coverage[0]['reason'])
        self.assertNotIn('secret-response-body', json.dumps(failure.coverage))
        self.assertEqual(provider.call_count, 1)
        enrich.assert_not_called()

    def test_preflight_failure_has_no_invented_operation(self):
        with patch.object(s, 'urlopen') as provider:
            with self.assertRaises(s.SourcingError) as caught:
                s.search_products_with_coverage({'itemType': 'chair'}, None)
        self.assertEqual(caught.exception.coverage, [])
        self.assertFalse(caught.exception.coverageComplete)
        provider.assert_not_called()

    def test_empty_search_and_malformed_response_have_honest_ledgers(self):
        result, _, enrich = self.run_response(self.response(0), [])
        self.assertEqual(result['candidates'], [])
        self.assertEqual(len(result['coverage']), 1)
        self.assertEqual(result['coverage'][0]['status'], 'completed')
        enrich.assert_not_called()
        with self.assertRaises(s.SourcingError) as caught:
            self.run_response({'status': 'completed', 'output': [None]}, [])
        self.assertEqual(caught.exception.coverage[0]['status'], 'failed')
        self.assertIn('unexpected response', str(caught.exception))

    def test_compatibility_interface_still_returns_list_from_same_bounded_pipeline(self):
        result, provider, enrich = self.run_response(self.response(1), [s.SourcingError('Source is blocked.')], compatibility=True)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(provider.call_count, 1)
        self.assertEqual(enrich.call_count, 1)

if __name__ == '__main__':
    unittest.main()
