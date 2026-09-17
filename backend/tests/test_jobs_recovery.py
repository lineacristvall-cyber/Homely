"""Deterministic recovery regressions; temporary files and mocked providers only."""
import base64
import copy
from concurrent.futures import ThreadPoolExecutor
import http.client
import io
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch, MagicMock
from PIL import Image
from backend import server

PID = 'aaaaaaaa-1111-4111-8111-111111111111'
ROOM = 'bbbbbbbb-2222-4222-8222-222222222222.png'
PRODUCT = 'cccccccc-3333-4333-8333-333333333333.png'


class JobRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.project = {'id': PID, 'name': 'Recovery fixture', 'mode': 'pro', 'version': 1,
                        'createdAt': '2026-09-13T00:00:00Z', 'updatedAt': '2026-09-13T00:00:00Z',
                        'brief': {'quantity': 6, 'itemType': 'chairs', 'location': 'Fixture city', 'style': 'original style',
                                  'flexibleTarget': 1000, 'hardCap': 2000, 'notes': '', 'measurements': {'tableUndersideIn': 28}},
                        'room': {'imageUrl': '/api/assets/' + ROOM, 'consent': True},
                        'candidates': [{'id': 'chair-original', 'title': 'Original chair', 'variant': 'Oak', 'status': 'lead'}],
                        'decisions': []}
        values = {'ROOT': self.base, 'DATA': self.base, 'PROJECTS': self.base / 'projects',
                  'ASSETS': self.base / 'assets', 'JOBS': self.base / 'jobs', 'WEB': self.base / 'web'}
        for name, value in values.items():
            patcher = patch.object(server, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        for patcher in (patch.object(server, 'cloud_enabled', return_value=False), patch.object(server, 'api_key', return_value=None)):
            patcher.start()
            self.addCleanup(patcher.stop)
        server.ensure_dirs()
        server.save_project(copy.deepcopy(self.project))
        image = io.BytesIO()
        Image.new('RGB', (3, 3), 'white').save(image, 'PNG')
        self.image = image.getvalue()
        self.data_url = 'data:image/png;base64,' + base64.b64encode(self.image).decode()
        self.product_path = server.ASSETS / PRODUCT
        (server.ASSETS / ROOM).write_bytes(self.image)
        self.product_path.write_bytes(self.image)
        self.output_path = server.ASSETS / 'output.png'
        self.http = server.ThreadingHTTPServer(('127.0.0.1', 0), server.Handler)
        self.thread = threading.Thread(target=self.http.serve_forever, kwargs={'poll_interval': .01}, daemon=True)
        self.thread.start()
        self.addCleanup(self.stop_http)

    def stop_http(self):
        self.http.shutdown()
        self.http.server_close()
        self.thread.join(timeout=3)

    def request(self, method, path, body):
        connection = http.client.HTTPConnection('127.0.0.1', self.http.server_port, timeout=5)
        try:
            connection.request(method, path, body=json.dumps(body).encode(), headers={'Content-Type': 'application/json'})
            response = connection.getresponse()
            return response.status, json.loads(response.read())
        finally:
            connection.close()

    def render(self, job, snapshot=None):
        server.visualization_worker(job['id'], PID, 'chair-original', self.product_path, self.output_path, True,
                                    '/api/assets/' + PRODUCT, copy.deepcopy(snapshot or self.project))

    def test_concurrent_brief_patch_during_room_upload_cannot_overwrite_new_state(self):
        entered, release = threading.Event(), threading.Event()
        def blocked_upload(*args):
            entered.set()
            if not release.wait(3):
                raise AssertionError('Fixture upload was not released')
            return self.product_path, '/api/assets/new-room.png'
        with patch.object(server, 'save_asset', side_effect=blocked_upload), ThreadPoolExecutor(max_workers=1) as pool:
            uploading = pool.submit(self.request, 'POST', '/api/projects/' + PID + '/room',
                                    {'expectedVersion': 1, 'dataUrl': self.data_url, 'consent': True})
            self.assertTrue(entered.wait(2))
            try:
                status, _ = self.request('PATCH', '/api/projects/' + PID + '/brief', {'expectedVersion': 1, 'brief': {'style': 'new style'}})
                self.assertEqual(status, 200)
            finally:
                release.set()
            self.assertEqual(uploading.result(timeout=4)[0], 409)
        current = server.get_project(PID)
        self.assertEqual(current['version'], 2)
        self.assertEqual(current['brief']['style'], 'new style')
        self.assertEqual(current['room'], self.project['room'])

    def test_stale_room_version_rejected_before_asset_upload(self):
        server.patch_brief(PID, 1, {'style': 'new style'})
        with patch.object(server, 'save_asset') as save:
            status, _ = self.request('POST', '/api/projects/' + PID + '/room', {'expectedVersion': 1, 'dataUrl': self.data_url, 'consent': True})
        self.assertEqual(status, 409)
        save.assert_not_called()

    def test_pre_render_version_conflict_has_no_provider_call(self):
        job = server.new_job(PID, 'visualization')
        server.patch_brief(PID, 1, {'quantity': 8})
        with patch('backend.visualization.create_visualization') as provider:
            self.render(job)
        provider.assert_not_called()
        self.assertEqual(server.get_job(job['id'])['status'], 'cancelled')
        self.assertEqual(server.get_project(PID)['brief']['quantity'], 8)

    def test_during_render_version_change_marks_output_stale_and_cancelled(self):
        job = server.new_job(PID, 'visualization')
        entered, release = threading.Event(), threading.Event()
        def provider(*args):
            entered.set()
            if not release.wait(3):
                raise AssertionError('Fixture render was not released')
            self.output_path.write_bytes(self.image)
            return {'status': 'generated', 'illustrative': True}
        with patch('backend.visualization.create_visualization', side_effect=provider), ThreadPoolExecutor(max_workers=1) as pool:
            rendering = pool.submit(self.render, job)
            self.assertTrue(entered.wait(2))
            try:
                server.patch_brief(PID, 1, {'style': 'changed during render'})
            finally:
                release.set()
            rendering.result(timeout=4)
        result = server.get_job(job['id'])
        self.assertEqual(result['status'], 'cancelled')
        self.assertTrue(result['result']['stale'])
        self.assertEqual(result['result']['projectVersion'], 1)
        self.assertNotIn('imageUrl', result['result'])
        self.assertEqual(server.get_project(PID)['brief']['style'], 'changed during render')

    def test_enqueue_captures_deep_original_snapshot(self):
        shared = copy.deepcopy(self.project)
        with patch.object(server, 'current_version', return_value=shared), patch.object(server, 'background') as enqueue:
            status, body = self.request('POST', '/api/projects/' + PID + '/visualizations',
                                       {'expectedVersion': 1, 'candidateId': 'chair-original', 'productImageDataUrl': self.data_url,
                                        'productImageRightsConfirmed': True})
        self.assertEqual(status, 202)
        args = enqueue.call_args.args
        self.assertIs(args[0], server.visualization_worker)
        snapshot = args[-1]
        shared['brief']['style'] = 'mutated after enqueue'
        shared['room']['imageUrl'] = '/api/assets/not-original.png'
        shared['candidates'][0]['variant'] = 'different variant'
        self.assertEqual(snapshot, self.project)
        self.assertEqual(body['job']['projectVersion'], 1)
        with patch('backend.visualization.create_visualization', return_value={'status': 'unavailable', 'reason': 'mocked'}) as provider:
            args[0](*args[1:])
        room_path, product_path, candidate, brief = provider.call_args.args[:4]
        self.assertEqual(room_path, server.ASSETS / ROOM)
        self.assertEqual(candidate['variant'], 'Oak')
        self.assertEqual(brief['style'], 'original style')
        self.assertEqual(brief['measurements'], {'tableUndersideIn': 28})
        self.assertEqual(brief['roomImageUrl'], '/api/assets/' + ROOM)

    def test_cancel_during_research_discards_results_and_preserves_project(self):
        job = server.new_job(PID, 'research')
        entered, release = threading.Event(), threading.Event()
        def research(*args):
            entered.set()
            if not release.wait(3):
                raise AssertionError('Fixture research was not released')
            return {'candidates': [{'id': 'late-result', 'title': 'Late chair', 'status': 'ready'}], 'coverage': [], 'coverageComplete': False}
        with patch('backend.sourcing.search_products_with_coverage', side_effect=research), ThreadPoolExecutor(max_workers=1) as pool:
            researching = pool.submit(server.research_worker, job['id'], PID, 1)
            self.assertTrue(entered.wait(2))
            try:
                status, body = self.request('POST', '/api/jobs/' + job['id'] + '/cancel', {})
                self.assertEqual(status, 200)
                self.assertEqual(body['job']['status'], 'cancelled')
            finally:
                release.set()
            researching.result(timeout=4)
        self.assertEqual(server.get_project(PID), self.project)
        self.assertEqual(server.get_job(job['id'])['status'], 'cancelled')
        self.assertIsNone(server.get_job(job['id'])['result'])

    def test_version_change_during_cloud_upload_prevents_current_publication(self):
        current = copy.deepcopy(self.project)
        current['room']['imageUrl'] = '/api/cloud-assets/bbbbbbbb-2222-4222-8222-222222222222'
        snapshot = copy.deepcopy(current)
        store = MagicMock()
        store.read.return_value = (self.image, 'image/png')
        def uploading(*args, **kwargs):
            # Represents another request committing after provider generation,
            # while the result bytes are still being uploaded to cloud storage.
            current['version'] = 2
            current['brief']['style'] = 'changed during cloud upload'
            return {'imageUrl': '/api/cloud-assets/dddddddd-4444-4444-8444-444444444444'}
        store.upload.side_effect = uploading
        def provider(*args):
            args[-1].write_bytes(self.image)
            return {'status': 'generated', 'illustrative': True}
        owner_token = server.CURRENT_OWNER.set('fixture-owner')
        try:
            with patch.object(server, 'cloud_enabled', return_value=True), patch.object(server, 'cloud_store', return_value=store), \
                 patch.object(server, 'get_project', side_effect=lambda project_id: copy.deepcopy(current)), \
                 patch('backend.visualization.create_visualization', side_effect=provider):
                server.ensure_dirs()
                job = server.new_job(PID, 'visualization')
                server.visualization_worker(job['id'], PID, 'chair-original', self.product_path,
                                            server.asset_directory() / 'cloud-output.png', True,
                                            '/api/cloud-assets/cccccccc-3333-4333-8333-333333333333', snapshot)
                saved = server.get_job(job['id'])
        finally:
            server.CURRENT_OWNER.reset(owner_token)
        store.upload.assert_called_once()
        self.assertEqual(saved['status'], 'cancelled')
        self.assertTrue(saved['result']['stale'])
        self.assertEqual(saved['result']['projectVersion'], 1)
        self.assertEqual(current['version'], 2)
        self.assertEqual(current['brief']['style'], 'changed during cloud upload')

    def test_historical_completed_render_get_becomes_stale_after_project_change(self):
        job = server.new_job(PID, 'visualization')
        job['projectVersion'] = 1
        server.save_job(job)
        def provider(*args):
            self.output_path.write_bytes(self.image)
            return {'status': 'generated', 'illustrative': True}
        with patch('backend.visualization.create_visualization', side_effect=provider):
            self.render(job)
        status, before = self.request('GET', '/api/jobs/' + job['id'], {})
        self.assertEqual(status, 200)
        self.assertEqual(before['job']['status'], 'completed')
        self.assertFalse(before['job']['result'].get('stale', False))
        server.patch_brief(PID, 1, {'style': 'later project change'})
        status, after = self.request('GET', '/api/jobs/' + job['id'], {})
        self.assertEqual(status, 200)
        self.assertEqual(after['job']['status'], 'cancelled')
        self.assertTrue(after['job']['result']['stale'])
        self.assertEqual(after['job']['result']['projectVersion'], 1)
        self.assertEqual(server.get_project(PID)['version'], 2)
        self.assertEqual(self.output_path.read_bytes(), self.image)
        # Serving the history should not erase the originally completed record.
        self.assertEqual(server.get_job(job['id'])['status'], 'completed')

    def test_queued_cancellation_skips_both_providers_and_cannot_resurrect(self):
        for kind in ('research', 'visualization'):
            job = server.new_job(PID, kind)
            server.update_job(job['id'], status='cancelled')
            with patch('backend.sourcing.search_products_with_coverage') as research, patch('backend.visualization.create_visualization') as render:
                if kind == 'research':
                    server.research_worker(job['id'], PID, 1)
                else:
                    self.render(job)
            research.assert_not_called()
            render.assert_not_called()
            for status in ('running', 'completed', 'failed'):
                server.update_job(job['id'], status=status, result={'late': True})
                self.assertEqual(server.get_job(job['id'])['status'], 'cancelled')
                self.assertIsNone(server.get_job(job['id'])['result'])

    def test_research_success_saves_actual_coverage_on_project_and_job(self):
        job = server.new_job(PID, 'research')
        coverage = [{'sourceId': 'fixture', 'stage': 'enrichment', 'status': 'blocked',
                     'url': 'https://fixture.invalid/chair', 'reason': 'Fixture robots denial'}]
        envelope = {'candidates': [], 'coverage': coverage, 'coverageComplete': False}
        with patch('backend.sourcing.search_products_with_coverage', return_value=envelope):
            server.research_worker(job['id'], PID, 1)
        current, saved = server.get_project(PID), server.get_job(job['id'])
        self.assertEqual(current['version'], 2)
        self.assertEqual(current['sourceCoverage'], coverage)
        self.assertFalse(current['sourceCoverageComplete'])
        self.assertEqual(saved['status'], 'completed')
        self.assertEqual(saved['result']['sourceCoverage'], coverage)
        self.assertFalse(saved['result']['sourceCoverageComplete'])

    def test_brief_change_clears_prior_coverage_and_findings(self):
        project = copy.deepcopy(self.project)
        project['sourceCoverage'] = [{'sourceId': 'old-source', 'status': 'checked'}]
        project['sourceCoverageComplete'] = False
        server.save_project(project)
        changed = server.patch_brief(PID, 1, {'style': 'new direction'})
        self.assertEqual(changed['version'], 2)
        self.assertEqual(changed['candidates'], [])
        self.assertEqual(changed['sourceCoverage'], [])
        self.assertIs(changed['sourceCoverageComplete'], False)
        self.assertEqual(server.get_project(PID), changed)

    def test_research_failure_retains_ledger_without_overwriting_project(self):
        from backend.sourcing import SourcingError
        job = server.new_job(PID, 'research')
        coverage = [{'sourceId': 'fixture', 'stage': 'discovery', 'status': 'failed', 'reason': 'Fixture timeout'}]
        with patch('backend.sourcing.search_products_with_coverage', side_effect=SourcingError('Fixture unavailable', coverage=coverage)):
            server.research_worker(job['id'], PID, 1)
        saved = server.get_job(job['id'])
        self.assertEqual(saved['status'], 'failed')
        self.assertEqual(saved['result']['sourceCoverage'], coverage)
        self.assertFalse(saved['result']['sourceCoverageComplete'])
        self.assertEqual(server.get_project(PID), self.project)

    def test_research_failure_after_brief_change_stays_cancelled(self):
        from backend.sourcing import SourcingError
        job = server.new_job(PID, 'research')
        def fail_after_change(*args):
            server.patch_brief(PID, 1, {'style': 'newer brief'})
            raise SourcingError('Old failure', coverage=[{'status': 'failed'}])
        with patch('backend.sourcing.search_products_with_coverage', side_effect=fail_after_change):
            server.research_worker(job['id'], PID, 1)
        self.assertEqual(server.get_job(job['id'])['status'], 'cancelled')
        self.assertIsNone(server.get_job(job['id'])['result'])
        self.assertEqual(server.get_project(PID)['brief']['style'], 'newer brief')

if __name__ == '__main__':
    unittest.main()
