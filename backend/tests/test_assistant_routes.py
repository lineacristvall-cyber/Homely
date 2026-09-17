"""Service integration tests: plans cannot bypass version/confirmation gates."""
import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from backend import server


class AssistantServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        base = Path(self.temp.name)
        self.locations = (server.DATA, server.PROJECTS, server.ASSETS, server.JOBS)
        server.DATA, server.PROJECTS, server.ASSETS, server.JOBS = base, base/'projects', base/'assets', base/'jobs'
        server.PENDING_ACTIONS.clear()
        self.project = {'id':'11111111-1111-4111-8111-111111111111','name':'Fixture only','mode':'pro',
            'version':1,'createdAt':server.now_iso(),'brief':{'itemType':'chairs','quantity':6,'style':'oak','location':'',
            'flexibleTarget':2000,'hardCap':3000,'notes':'','measurements':{'roomWidthIn':120,'tableUndersideIn':28}},
            'room':None,'candidates':[{'id':'fixture-chair','title':'Fixture chair','unitPrice':100,'shipping':0,'tax':0,'status':'ready'}], 'decisions':[]}
        server.save_project(self.project)
        self.key = patch.object(server, 'api_key', return_value='test-only-not-a-key'); self.key.start()

    def tearDown(self):
        self.key.stop()
        server.DATA, server.PROJECTS, server.ASSETS, server.JOBS = self.locations
        server.PENDING_ACTIONS.clear()
        self.temp.cleanup()

    def propose(self, action, session='browser-a'):
        with patch('backend.assistant.plan_message',return_value={'reply':'ignored success claim','action':action}):
            return server.assistant_request(self.project['id'],{'expectedVersion':1,'message':'fixture instruction'},session)

    def confirm(self, proposal, session='browser-a', version=1):
        return server.assistant_request(self.project['id'],{'expectedVersion':version,'confirmationId':proposal['confirmation']['id']},session)

    def test_brief_waits_for_confirm_then_versioned_and_clears_results(self):
        out=self.propose({'type':'update_brief','patch':{'quantity':4}})
        self.assertEqual(server.get_project(self.project['id'])['brief']['quantity'],6)
        self.assertNotIn('ignored success',out['reply'])
        done=self.confirm(out)
        self.assertEqual(done['project']['brief']['quantity'],4)
        self.assertEqual(done['project']['version'],2)
        self.assertEqual(done['project']['candidates'],[])
        with self.assertRaises(ValueError): self.confirm(out,version=2)

    def test_browser_cannot_confirm_another_browsers_proposal(self):
        out=self.propose({'type':'update_brief','patch':{'style':'linen'}})
        with self.assertRaises(ValueError): self.confirm(out,session='browser-b')
        self.assertEqual(self.confirm(out)['project']['brief']['style'],'linen')

    def test_confirmation_cannot_cross_project(self):
        out=self.propose({'type':'update_brief','patch':{'style':'linen'}})
        other=copy.deepcopy(self.project); other['id']='22222222-2222-4222-8222-222222222222'; server.save_project(other)
        with self.assertRaises(ValueError):
            server.assistant_request(other['id'],{'expectedVersion':1,'confirmationId':out['confirmation']['id']},'browser-a')

    def test_changed_project_rejects_stale_proposal(self):
        out=self.propose({'type':'update_brief','patch':{'quantity':4}})
        server.patch_brief(self.project['id'],1,{'style':'new style'})
        with self.assertRaises(server.ConflictError): self.confirm(out,version=2)
        self.assertEqual(server.get_project(self.project['id'])['brief']['quantity'],6)

    def test_version_change_during_provider_call_discards_plan(self):
        def planning(*args):
            server.patch_brief(self.project['id'],1,{'style':'changed elsewhere'})
            return {'reply':'Done','action':{'type':'start_research'}}
        with patch('backend.assistant.plan_message',side_effect=planning):
            with self.assertRaises(server.ConflictError):
                server.assistant_request(self.project['id'],{'expectedVersion':1,'message':'research'},'browser-a')
        self.assertEqual(server.PENDING_ACTIONS,{})

    def test_nested_measurement_patch_keeps_other_measurements(self):
        out=self.propose({'type':'update_brief','patch':{'measurements':{'tableUndersideIn':29}}})
        done=self.confirm(out)
        self.assertEqual(done['project']['brief']['measurements'],{'roomWidthIn':120,'tableUndersideIn':29})

    def test_invalid_patch_and_foreign_candidate_rejected_before_proposal(self):
        for patch_value in ({'quantity':True},{'quantity':101},{'hardCap':float('nan')},{'hardCap':100}):
            with self.subTest(patch_value=patch_value), self.assertRaises(ValueError):
                self.propose({'type':'update_brief','patch':patch_value})
        with self.assertRaises(ValueError): self.propose({'type':'save_decision','candidateId':'another-project'})
        self.assertEqual(server.PENDING_ACTIONS,{})

    def test_save_snapshot_never_claims_ready_handoff(self):
        out=self.propose({'type':'save_decision','candidateId':'fixture-chair'})
        self.assertEqual(server.get_project(self.project['id'])['decisions'],[])
        done=self.confirm(out)
        self.assertFalse(done['decision']['readyForHandoff'])
        self.assertEqual(done['decision']['candidateSnapshot']['title'],'Fixture chair')
        self.assertEqual(len(done['project']['decisions']),1)

    def test_research_only_starts_once_after_confirmation(self):
        with patch.object(server,'start_research',return_value={'id':'fixture-job','status':'queued'}) as start:
            out=self.propose({'type':'start_research'}); start.assert_not_called()
            self.assertEqual(self.confirm(out)['job']['id'],'fixture-job'); start.assert_called_once()
            with self.assertRaises(ValueError): self.confirm(out)
            start.assert_called_once()

    def test_visualization_requests_setup_and_never_starts_render(self):
        with patch.object(server,'new_job') as job:
            out=self.propose({'type':'request_visualization','candidateId':'fixture-chair'})
            self.assertEqual(out['command']['type'],'request_visualization')
            job.assert_not_called()
            self.assertIn('confirm image use',out['reply'])

    def test_expired_and_superseded_proposals_unusable(self):
        old=self.propose({'type':'update_brief','patch':{'style':'old'}})
        fresh=self.propose({'type':'update_brief','patch':{'style':'fresh'}})
        with self.assertRaises(ValueError):self.confirm(old)
        server.PENDING_ACTIONS[fresh['confirmation']['id']]['at']-=server.CONFIRM_TTL+1
        with self.assertRaises(ValueError):self.confirm(fresh)

if __name__=='__main__': unittest.main()
