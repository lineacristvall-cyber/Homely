import copy
import json
import tempfile
import unittest
from pathlib import Path
from datetime import datetime, timezone
from backend.price_watch import PriceWatchStore, PriceWatchError


def product(price=100):
    p = dict(url='https://example.invalid/chair', exactSku='chair-1', variant='oak', unitPrice=price, title='Chair')
    p['fieldEvidence'] = {k: dict(url=p['url'], rawValue=p[k], method='public_product_page', path='jsonld.Product',
                               observedAt='2026-09-17T10:00:00+00:00') for k in ('unitPrice', 'exactSku', 'variant')}
    return p


class PriceWatchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'watches.json'
        self.now = [datetime(2026, 9, 17, 10, tzinfo=timezone.utc).timestamp()]
        self.answer = product(90)
        self.calls = []
        def checker(url, brief):
            self.calls.append(url)
            if isinstance(self.answer, Exception):
                raise self.answer
            return copy.deepcopy(self.answer)
        self.checker = checker
        self.store = PriceWatchStore(self.path, checker=checker, clock=lambda: self.now[0])
        self.addCleanup(self.store.stop)

    def subscribe(self, owner='A'):
        return self.store.subscribe(owner, product(), consent=True, interval_seconds=60)

    def test_real_scheduler_thread_publishes_fixture_notification(self):
        import threading
        import time
        called = threading.Event()
        original = self.store.checker
        def checked(url, brief):
            answer = original(url, brief)
            called.set()
            return answer
        self.store.checker = checked
        self.subscribe()
        self.now[0] += 60
        self.store.start()
        self.assertTrue(called.wait(4), 'Scheduler did not run the due check')
        deadline = time.monotonic() + 2
        while not self.store.notifications('A') and time.monotonic() < deadline:
            time.sleep(.01)
        self.assertEqual(self.store.notifications('A')[0]['currentPrice'], 90)

    def test_optin_required_no_network_or_storage_until_subscribe(self):
        for consent in (False, 1, 'true', None):
            with self.assertRaises(PriceWatchError):
                self.store.subscribe('A', product(), consent=consent)
        self.store.run_due()
        self.assertEqual(self.calls, [])
        self.assertFalse(self.path.exists())

    def test_paused_until_daemon_started_and_after_stop(self):
        self.assertEqual(self.subscribe()['status'], 'paused')
        self.store.start()
        self.assertEqual(self.store.list('A')[0]['status'], 'active')
        self.store.stop()
        self.assertEqual(self.store.list('A')[0]['status'], 'paused')

    def test_owner_privacy_and_restart(self):
        watch = self.subscribe()
        self.assertEqual(self.store.list('B'), [])
        with self.assertRaises(PriceWatchError):
            self.store.cancel('B', watch['id'])
        loaded = PriceWatchStore(self.path, checker=self.checker, clock=lambda: self.now[0])
        self.assertEqual(loaded.list('A')[0]['id'], watch['id'])
        self.assertEqual(loaded.list('A')[0]['status'], 'paused')
        self.assertNotIn('owner', loaded.list('A')[0])
        self.assertEqual(self.path.stat().st_mode & 0o777, 0o600)

    def test_notifications_dedup_and_mark_read_are_owner_scoped(self):
        self.subscribe()
        self.store.run_due()
        self.assertEqual(self.calls, [])
        self.now[0] += 60
        self.store.run_due()
        notes = self.store.notifications('A')
        self.assertEqual(len(notes), 1)
        self.assertEqual(notes[0]['previousPrice'], 100)
        self.assertEqual(notes[0]['currentPrice'], 90)
        self.assertEqual(notes[0]['delivery'], 'in_app')
        self.assertEqual(self.store.notifications('B'), [])
        with self.assertRaises(PriceWatchError):
            self.store.mark_read('B', notes[0]['id'])
        self.assertTrue(self.store.mark_read('A', notes[0]['id'])['read'])
        self.now[0] += 60
        self.store.run_due()
        self.assertEqual(len(self.store.notifications('A')), 1)

    def test_unknown_mismatched_or_failed_source_never_alerts(self):
        self.subscribe()
        values = [product(None), product(80), RuntimeError('PRIVATE source text')]
        values[1]['exactSku'] = 'other'
        values[1]['fieldEvidence']['exactSku']['rawValue'] = 'other'
        for value in values:
            self.answer = value
            self.now[0] += 60
            self.store.run_due()
            self.assertEqual(self.store.notifications('A'), [])
            self.assertIsNotNone(self.store.list('A')[0]['error'])
            self.assertNotIn('PRIVATE', json.dumps(self.store.list('A')))
        self.assertEqual(self.store.list('A')[0]['product']['unitPrice'], 100)

    def test_cancel_prevents_fetch_and_inflight_alert(self):
        watch = self.subscribe()
        self.store.cancel('A', watch['id'])
        self.now[0] += 60
        self.store.run_due()
        self.assertEqual(self.calls, [])
        watch = self.subscribe()
        def cancel_during_fetch(url, brief):
            self.store.cancel('A', watch['id'])
            return product(80)
        self.store.checker = cancel_during_fetch
        self.now[0] += 60
        self.store.run_due()
        self.assertEqual(self.store.notifications('A'), [])

    def test_reject_bad_evidence_and_identity(self):
        bad = [product(float('nan')), product(True), product(-1), product()]
        bad[-1]['fieldEvidence']['variant']['rawValue'] = 'other'
        for value in bad:
            with self.assertRaises(PriceWatchError):
                self.store.subscribe('A', value, consent=True)
        self.assertEqual(self.calls, [])

    def test_all_identity_mismatches_do_not_replace_baseline(self):
        self.subscribe()
        for key, value in (('exactSku', 'other'), ('variant', 'blue'), ('url', 'https://example.invalid/other')):
            self.answer = product(50)
            self.answer[key] = value
            if key == 'url':
                for evidence in self.answer['fieldEvidence'].values():
                    evidence['url'] = value
            else:
                self.answer['fieldEvidence'][key]['rawValue'] = value
            self.now[0] += 60
            self.store.run_due()
            self.assertEqual(self.store.notifications('A'), [])
            self.assertEqual(self.store.list('A')[0]['product']['unitPrice'], 100)
            self.assertEqual(self.store.list('A')[0]['product']['exactSku'], 'chair-1')

    def test_stale_and_future_evidence_rejected(self):
        for stamp in ('2020-01-01T00:00:00Z', '2099-01-01T00:00:00Z'):
            p = product()
            p['fieldEvidence']['unitPrice']['observedAt'] = stamp
            with self.assertRaises(PriceWatchError):
                self.store.subscribe('A', p, consent=True)
        self.subscribe()
        self.now[0] += 90000
        self.store.run_due()
        self.assertEqual(self.store.notifications('A'), [])
        self.assertIsNotNone(self.store.list('A')[0]['error'])

    def test_duplicate_subscription_and_corrupt_storage(self):
        a = self.subscribe()
        self.assertEqual(self.subscribe()['id'], a['id'])
        self.path.write_text('{broken')
        with self.assertRaises(PriceWatchError):
            PriceWatchStore(self.path, checker=self.checker)

if __name__ == '__main__':
    unittest.main()
