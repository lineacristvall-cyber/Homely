"""Temporary HTTP/files only; no provider or live user requests."""
from datetime import datetime, timedelta, timezone
import json
import unittest
from unittest.mock import patch
from backend import server
from backend.tests import test_cloud_routes as fixtures

A, B, PA, PB, LOCAL, SA, SB = (getattr(fixtures, key) for key in ("A", "B", "PA", "PB", "LOCAL", "SA", "SB"))


class VisualizationHistoryTests(unittest.TestCase):
    # Reuse only the temporary-server fixture, not its unrelated test methods.
    setUp = fixtures.CloudRouteTests.setUp
    stop_http = fixtures.CloudRouteTests.stop_http
    request = fixtures.CloudRouteTests.request

    def write_render(self, n=1, owner=A, project_id=PA, version=1, status='completed', directory=None):
        identifier = '%08x-1234-4234-8234-123456789abc' % n
        stamp = datetime(2026, 9, 1, tzinfo=timezone.utc) + timedelta(minutes=n)
        job = {'id': identifier, 'ownerId': owner, 'projectId': project_id, 'projectVersion': version,
               'candidateId': 'chair-1', 'kind': 'visualization', 'status': status,
               'createdAt': stamp.isoformat(), 'updatedAt': stamp.isoformat(),
               'result': {'imageUrl': '/api/cloud-assets/' + identifier, 'illustrative': True,
                          'lineage': {'candidateId': 'chair-1'}} if status == 'completed' else None}
        path = (directory or self.base / 'private-cloud-jobs') / (identifier + '.json')
        path.write_text(json.dumps(job))
        return job, path

    def history(self, project_id=PA, session=SA):
        return self.request('GET', '/api/projects/' + project_id + '/visualizations', session=session)

    def test_requires_project_auth_and_never_lists_other_owner_or_project(self):
        own, _ = self.write_render()
        self.write_render(2, owner=B)  # Foreign owner even with A's project UUID.
        self.write_render(3, owner=A, project_id=PB)  # Same owner wrong project.
        other, _ = self.write_render(4, owner=B, project_id=PB)
        self.assertEqual(self.history(session=None)[0], 401)
        self.assertEqual(self.history(PB, SA)[0], 404)
        status, value, headers = self.history()
        self.assertEqual(status, 200)
        self.assertEqual([j['id'] for j in value['jobs']], [own['id']])
        self.assertEqual(headers['Cache-Control'], 'no-store')
        self.assertEqual([j['id'] for j in self.history(PB, SB)[1]['jobs']], [other['id']])

    def test_current_and_stale_results_match_individual_get_without_changing_disk(self):
        current, _ = self.write_render()
        old, path = self.write_render(2, version=0)
        before = path.read_bytes()
        jobs = self.history()[1]['jobs']
        for expected in (old, current):
            listed = next(j for j in jobs if j['id'] == expected['id'])
            single = self.request('GET', '/api/jobs/' + expected['id'], session=SA)[1]['job']
            self.assertEqual(listed, single)
        self.assertEqual(jobs[0]['status'], 'cancelled')
        self.assertTrue(jobs[0]['result']['stale'])
        self.assertEqual(jobs[1]['status'], 'completed')
        self.assertNotIn('stale', jobs[1]['result'])
        self.assertEqual(path.read_bytes(), before)

    def test_all_job_states_included_but_research_excluded(self):
        for n, status in enumerate(('queued', 'running', 'completed', 'failed', 'cancelled'), 1):
            self.write_render(n, status=status)
        research, path = self.write_render(6)
        research['kind'] = 'research'
        path.write_text(json.dumps(research))
        jobs = self.history()[1]['jobs']
        self.assertEqual(len(jobs), 5)
        self.assertEqual({j['status'] for j in jobs}, {'queued', 'running', 'completed', 'failed', 'cancelled'})
        self.assertTrue(all(j['candidateId'] == 'chair-1' for j in jobs))

    def test_fifty_newest_by_created_time_not_filename_or_mtime(self):
        entries = [self.write_render(n)[0] for n in range(1, 56)]
        jobs = self.history()[1]['jobs']
        self.assertEqual([j['id'] for j in jobs], [j['id'] for j in reversed(entries[-50:])])

    def test_malformed_files_mismatched_ids_and_symlinks_ignored(self):
        expected, _ = self.write_render()
        directory = self.base / 'private-cloud-jobs'
        for n, change in ((2, {'createdAt': 'not-a-date'}), (3, {'id': expected['id']}),
                          (4, {'result': ['invalid']}), (5, {'createdAt': '2026-09-13T00:00:00'}),
                          (6, {'status': 'invented'})):
            job, path = self.write_render(n)
            job.update(change)
            path.write_text(json.dumps(job))
        for n, raw in ((7, '{bad json'), (8, '[]'), (9, 'null')):
            (directory / ('%08x-1234-4234-8234-123456789abc.json' % n)).write_text(raw)
        (directory / 'not-a-job.json').write_text(json.dumps(expected))
        external = self.base / 'external.json'
        external.write_text(json.dumps(expected))
        (directory / '00000010-1234-4234-8234-123456789abc.json').symlink_to(external)
        self.assertEqual([j['id'] for j in self.history()[1]['jobs']], [expected['id']])

    def test_local_and_cloud_history_use_separate_directories(self):
        cloud, _ = self.write_render()
        local, _ = self.write_render(2, owner=None, project_id=LOCAL, directory=self.base / 'jobs')
        self.write_render(3, owner=A, project_id=LOCAL, directory=self.base / 'jobs')
        self.assertEqual([j['id'] for j in self.history()[1]['jobs']], [cloud['id']])
        self.cloud_mode = False
        status, value, _ = self.history(LOCAL, None)
        self.assertEqual(status, 200)
        self.assertEqual([j['id'] for j in value['jobs']], [local['id']])
        self.assertEqual(self.history(PA, None)[0], 404)
        self.cloud_mode = True
        self.assertEqual(self.history(LOCAL)[0], 404)

    def test_enqueued_candidate_identity_is_persisted_and_reopened_without_provider(self):
        self.cloud_mode = False
        path = self.base / 'projects' / (LOCAL + '.json')
        project = json.loads(path.read_text())
        project.update(candidates=[{'id': 'chair-queued'}], room={'imageUrl': '/api/assets/room.png', 'consent': True})
        path.write_text(json.dumps(project))
        product_path = self.base / 'assets' / 'fixture.png'
        with patch.object(server, 'save_asset', return_value=(product_path, '/api/assets/fixture.png')), patch.object(server, 'background') as background:
            status, value, _ = self.request('POST', '/api/projects/' + LOCAL + '/visualizations',
                {'candidateId': 'chair-queued', 'expectedVersion': 1, 'productImageRightsConfirmed': True, 'productImageDataUrl': 'mocked-input'})
        self.assertEqual(status, 202)
        self.assertEqual(value['job']['candidateId'], 'chair-queued')
        saved = json.loads((self.base / 'jobs' / (value['job']['id'] + '.json')).read_text())
        self.assertEqual(saved['candidateId'], 'chair-queued')
        listed = self.history(LOCAL, None)[1]['jobs'][0]
        self.assertEqual((listed['candidateId'], listed['status']), ('chair-queued', 'queued'))
        background.assert_called_once()

    def test_history_does_not_enqueue_or_call_render_provider(self):
        self.write_render()
        with patch.object(server, 'background') as background, patch('backend.visualization.create_visualization') as render:
            self.assertEqual(self.history()[0], 200)
        background.assert_not_called()
        render.assert_not_called()


if __name__ == '__main__':
    unittest.main()
