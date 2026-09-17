import base64
import io
import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from backend import server


class ServerContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.base = Path(cls.temp.name)
        cls.old = (server.DATA, server.PROJECTS, server.ASSETS, server.JOBS, server.WEB)
        server.DATA = cls.base / "data"
        server.PROJECTS = server.DATA / "projects"
        server.ASSETS = server.DATA / "assets"
        server.JOBS = server.DATA / "jobs"
        server.WEB = cls.base / "web"
        server.WEB.mkdir()
        (server.WEB / "index.html").write_text("<h1>Homely test</h1>")
        cls.http = server.ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        cls.url = "http://127.0.0.1:%d" % cls.http.server_address[1]
        cls.thread = threading.Thread(target=cls.http.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown()
        cls.http.server_close()
        cls.thread.join(timeout=3)
        server.DATA, server.PROJECTS, server.ASSETS, server.JOBS, server.WEB = cls.old
        cls.temp.cleanup()

    def request(self, method, path, body=None):
        data = None if body is None else json.dumps(body).encode()
        request = urllib.request.Request(self.url + path, data=data, method=method,
                                         headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                return response.status, json.load(response)
        except urllib.error.HTTPError as exc:
            return exc.code, json.load(exc)

    def create_project(self):
        status, result = self.request("POST", "/api/projects", {"name": "Test room", "mode": "pro"})
        self.assertEqual(status, 201)
        return result["project"]

    def test_optin_watch_routes_scheduler_notification_and_cancel(self):
        from backend.price_watch import PriceWatchStore
        from datetime import datetime, timezone
        project = self.create_project()
        now = [datetime.now(timezone.utc).timestamp()]
        product = dict(id='watch-fixture', title='Synthetic test chair', url='https://example.invalid/chair', exactSku='QA-1', variant='oak', unitPrice=100)
        product['fieldEvidence'] = {key: dict(url=product['url'], rawValue=product[key], observedAt=datetime.fromtimestamp(now[0], timezone.utc).isoformat(), method='test_fixture', path='fixture') for key in ('unitPrice', 'exactSku', 'variant')}
        project['candidates'] = [product]
        server.save_project(project)
        answer = json.loads(json.dumps(product))
        answer['unitPrice'] = 90
        answer['fieldEvidence']['unitPrice']['rawValue'] = 90
        store = PriceWatchStore(self.base / 'route-watch.json', checker=lambda url, brief: answer, clock=lambda: now[0])
        self.addCleanup(store.stop)
        path = '/api/projects/' + project['id'] + '/watches'
        with patch.object(server, 'price_watch_store', return_value=store):
            self.assertEqual(self.request('GET', '/api/watches')[1]['watches'], [])
            body = dict(candidateId=product['id'], expectedVersion=project['version'])
            self.assertEqual(self.request('POST', path, body)[0], 400)
            body['enabled'] = True
            body['expectedVersion'] = 999
            self.assertEqual(self.request('POST', path, body)[0], 409)
            body['expectedVersion'] = project['version']
            status, out = self.request('POST', path, body)
            self.assertEqual(status, 201)
            self.assertEqual(out['watch']['status'], 'paused')
            watch_id = out['watch']['id']
            now[0] += 3601
            store.run_due()
            status, out = self.request('GET', '/api/watches')
            self.assertEqual(status, 200)
            self.assertEqual(out['notifications'][0]['currentPrice'], 90)
            note_id = out['notifications'][0]['id']
            self.assertTrue(self.request('POST', '/api/notifications/' + note_id + '/read', {})[1]['notification']['read'])
            self.assertEqual(self.request('POST', '/api/watches/' + watch_id + '/cancel', {})[1]['watch']['status'], 'cancelled')
            with patch.object(server, 'watch_owner', return_value='other-owner'):
                self.assertEqual(self.request('GET', '/api/watches')[1]['watches'], [])
                self.assertEqual(self.request('POST', '/api/watches/' + watch_id + '/cancel', {})[0], 400)

    def test_project_brief_version_and_hard_cap(self):
        project = self.create_project()
        path = "/api/projects/" + project["id"] + "/brief"
        brief = dict(project["brief"], quantity=6, flexibleTarget=3000, hardCap=2800)
        status, out = self.request("PATCH", path, {"expectedVersion": project["version"], "brief": brief})
        self.assertEqual(status, 400)
        self.assertIn("hard cap", out["error"])
        brief["flexibleTarget"] = 2400
        status, out = self.request("PATCH", path, {"expectedVersion": project["version"], "brief": brief})
        self.assertEqual(status, 200)
        self.assertEqual(out["project"]["version"], project["version"] + 1)
        status, _ = self.request("PATCH", path, {"expectedVersion": project["version"], "brief": brief})
        self.assertEqual(status, 409)

    def test_room_setup_round_trip_preserves_brief_and_version(self):
        project = self.create_project()
        path = "/api/projects/" + project["id"] + "/brief"
        setup = {"roomType": "other", "roomLabel": " Study ",
                 "furnishingMode": "keep", "retainedItems": ["Desk", " Bookcase "],
                 "flexibleTarget": 1200, "hardCap": 1500}
        status, out = self.request("PATCH", path, {"expectedVersion": project["version"], "brief": setup})
        self.assertEqual(status, 200)
        saved = out["project"]
        self.assertEqual(saved["brief"]["roomLabel"], "Study")
        self.assertEqual(saved["brief"]["retainedItems"], ["Desk", "Bookcase"])
        self.assertEqual(saved["brief"]["itemType"], project["brief"]["itemType"])
        self.assertEqual(server.get_project(project["id"])["brief"], saved["brief"])
        status, out = self.request("PATCH", path, {"expectedVersion": saved["version"], "brief": {"style": "Warm"}})
        self.assertEqual(status, 200)
        self.assertEqual(out["project"]["brief"]["retainedItems"], ["Desk", "Bookcase"])
        status, _ = self.request("PATCH", path, {"expectedVersion": saved["version"], "brief": setup})
        self.assertEqual(status, 409)

    def test_room_setup_rejects_invalid_values(self):
        project = self.create_project()
        invalid = [{"roomType": "garage"}, {"furnishingMode": "maybe"},
                   {"roomLabel": 9}, {"roomLabel": "x" * 101},
                   {"retainedItems": "Table"}, {"retainedItems": [""]},
                   {"retainedItems": ["x"] * 21}, {"retainedItems": [True]}]
        for brief in invalid:
            with self.subTest(brief=brief):
                with self.assertRaises(ValueError):
                    server.validate_brief(project["brief"], brief)

    def test_fit_route_blocks_missing_geometry_before_research(self):
        project = self.create_project()
        base = '/api/projects/' + project['id']
        status, out = self.request('GET', base + '/fit')
        self.assertEqual(status, 200)
        self.assertEqual(out['gate']['status'], 'blocked')
        with patch.object(server, 'background') as worker:
            status, out = self.request('POST', base + '/research', {'expectedVersion':project['version']})
            self.assertEqual(status,400)
            worker.assert_not_called()
            status, out = self.request('POST', base + '/research', {'expectedVersion':project['version'], 'mode':'inspiration'})
            self.assertEqual(status,202)
            self.assertEqual(out['job']['resultMode'],'inspiration')
            worker.assert_called_once()

    def test_fit_candidate_evidence_is_bound_and_recomputed(self):
        from backend.tests.test_fit import dining
        brief, candidate = dining()
        project = self.create_project()
        project['brief'].update(brief)
        evidence = candidate.pop('fitEvidence')
        candidate['id'] = 'chair-fit'
        project['candidates'] = [candidate]
        server.save_project(project)
        base = '/api/projects/' + project['id']
        status, out = self.request('GET', base + '/fit')
        self.assertEqual(out['gate']['status'],'passed')
        self.assertEqual(out['candidates'][0]['status'],'blocked')
        status, out = self.request('POST',base+'/fit-evidence',{'expectedVersion':1,'candidateId':'chair-fit','fitEvidence':evidence})
        self.assertEqual(status,200)
        status, out = self.request('GET',base+'/fit')
        self.assertEqual(out['candidates'][0]['status'],'passed')
        status, out = self.request('POST',base+'/fit-evidence',{'expectedVersion':1,'candidateId':'chair-fit','fitEvidence':evidence})
        self.assertEqual(status,409)
        evidence['dimensions']['width']['status']='conflicting'
        status, out = self.request('POST',base+'/fit-evidence',{'expectedVersion':2,'candidateId':'chair-fit','fitEvidence':evidence})
        self.assertEqual(status,200)
        status, out = self.request('GET',base+'/fit')
        self.assertEqual(out['candidates'][0]['status'],'blocked')

    def test_progress_and_photo_confirmation_preserve_candidates(self):
        project = self.create_project()
        project['candidates'] = [{'id': 'chair', 'title': 'Original lead'}]
        server.save_project(project)
        path = '/api/projects/' + project['id'] + '/brief'
        status, out = self.request('PATCH', path, {'expectedVersion': project['version'], 'brief': {
            'journey': {'step': 'keep', 'keepingDecision': 'later', 'retainedObjects': []}}})
        self.assertEqual(status, 200)
        self.assertEqual(out['project']['candidates'], project['candidates'])
        invalid = {'step':'keep','retainedObjects':[{'id':'t','label':'Table','variant':'Oak','confirmed':True,
                   'anchor':{'x':.5,'y':.5,'imageUrl':'/api/assets/another-owner.png'}}]}
        status, _ = self.request('PATCH', path, {'expectedVersion':out['project']['version'], 'brief':{'journey':invalid}})
        self.assertEqual(status,400)
        self.assertEqual(server.get_project(project['id'])['brief']['journey']['keepingDecision'],'later')

    def test_room_upload_requires_consent_and_stores_original(self):
        project = self.create_project()
        image = Image.new("RGB", (5, 5), "#d9cdbb")
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        data_url = "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode()
        path = "/api/projects/" + project["id"] + "/room"
        status, out = self.request("POST", path, {"dataUrl": data_url, "consent": False})
        self.assertEqual(status, 400)
        status, out = self.request("POST", path, {"dataUrl": data_url, "consent": True})
        self.assertEqual(status, 200)
        self.assertTrue(out["project"]["room"]["consent"])
        with urllib.request.urlopen(self.url + out["project"]["room"]["imageUrl"]) as response:
            self.assertEqual(response.read(), buffer.getvalue())

    def test_upload_permission_does_not_grant_provider_permission(self):
        project=self.create_project()
        image=Image.new('RGB',(5,5),'#d9cdbb'); buffer=io.BytesIO(); image.save(buffer,format='PNG')
        data_url='data:image/png;base64,'+base64.b64encode(buffer.getvalue()).decode()
        status,out=self.request('POST','/api/projects/'+project['id']+'/room',
            {'dataUrl':data_url,'uploadConsent':True,'consent':False,'expectedVersion':project['version']})
        self.assertEqual(status,200)
        self.assertTrue(out['project']['room']['uploadConsent'])
        self.assertFalse(out['project']['room']['consent'])

    def test_imported_product_is_lead_and_handoff_blocked(self):
        project = self.create_project()
        candidate = {
            "id": "lead-1", "title": "Sample chair", "seller": "Example",
            "url": "https://example.com/chair", "sourceId": "example.com",
            "exactSku": "CHAIR-1", "variant": "Walnut", "unitPrice": 100,
            "shipping": 0, "tax": 0, "availableQuantity": None,
            "sourceRefs": [{"url": "https://example.com/chair", "method": "public_html"}],
            "status": "ready",
        }
        with patch("backend.sourcing.enrich_product_url", return_value=candidate):
            status, out = self.request("POST", "/api/projects/" + project["id"] + "/product-urls",
                                       {"url": "https://example.com/chair"})
        self.assertEqual(status, 201)
        self.assertEqual(out["candidate"]["status"], "lead")
        self.assertIsNone(out["candidate"]["availableQuantity"])
        status, out = self.request("POST", "/api/projects/" + project["id"] + "/decisions",
                                   {"candidateId": "lead-1"})
        self.assertEqual(status, 201)
        self.assertFalse(out["decision"]["readyForHandoff"])
        status, out = self.request("POST", "/api/projects/" + project["id"] + "/handoff",
                                   {"candidateId": "lead-1"})
        self.assertEqual(status, 200)
        self.assertEqual(out["status"], "blocked")
        self.assertIsNone(out["url"])

    def test_static_and_asset_path_constraints(self):
        with urllib.request.urlopen(self.url + "/") as response:
            self.assertIn(b"Homely test", response.read())
        status, _ = self.request("GET", "/api/assets/not-an-asset")
        self.assertEqual(status, 404)


if __name__ == "__main__":
    unittest.main()
