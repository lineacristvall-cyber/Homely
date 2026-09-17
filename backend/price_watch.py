"""Opt-in local price monitoring. Notifications are in-app only.

The scheduler runs only while the local server is running. Public-page evidence
is not a stock guarantee. No paid provider, email, or push service is used.
"""
import copy
import json
import math
import os
from pathlib import Path
import tempfile
import threading
import time
import uuid
from urllib.parse import urlsplit
from datetime import datetime


class PriceWatchError(ValueError):
    pass


def _text(value, limit=500):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise PriceWatchError('Missing or invalid watch details.')
    return value.strip()


def _product(value):
    if not isinstance(value, dict):
        raise PriceWatchError('An exact product with current price evidence is required.')
    result = {key: _text(value.get(key), 2048 if key == 'url' else 500)
              for key in ('url', 'exactSku', 'variant')}
    url = urlsplit(result['url'])
    if url.scheme not in ('https', 'http') or not url.hostname or url.username or url.password or url.fragment:
        raise PriceWatchError('A public product URL is required.')
    price = value.get('unitPrice')
    if isinstance(price, bool) or not isinstance(price, (int, float)) or not math.isfinite(price) or not 0 < price <= 1e8:
        raise PriceWatchError('A known numeric USD unit price is required.')
    if value.get('currency', 'USD') != 'USD':
        raise PriceWatchError('Only USD price evidence is supported.')
    evidence = value.get('fieldEvidence')
    if not isinstance(evidence, dict):
        raise PriceWatchError('Source evidence is required.')
    cleaned = {}
    for key in ('unitPrice', 'exactSku', 'variant'):
        item = evidence.get(key)
        if not isinstance(item, dict) or item.get('url') != result['url'] or item.get('rawValue') != value.get(key):
            raise PriceWatchError('Exact product and price evidence must match the source.')
        stamp = _text(item.get('observedAt'), 64)
        try:
            parsed = datetime.fromisoformat(stamp.replace('Z', '+00:00'))
            if parsed.tzinfo is None:
                raise ValueError()
        except ValueError:
            raise PriceWatchError('Dated source evidence is required.') from None
        cleaned[key] = {'url': result['url'], 'rawValue': value[key], 'observedAt': stamp,
                        'method': _text(item.get('method'), 100), 'path': _text(item.get('path'), 200)}
    result.update(unitPrice=price, currency='USD', fieldEvidence=cleaned,
                  title=str(value.get('title') or result['exactSku'])[:500])
    return result


class PriceWatchStore:
    def __init__(self, path, checker=None, clock=time.time):
        self.path = Path(path)
        if checker is None:
            from .sourcing import enrich_product_url
            checker = enrich_product_url
        self.checker, self.clock = checker, clock
        self._lock = threading.RLock()
        self._run_lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = None
        self._state = {'watches': [], 'notifications': []}
        if self.path.exists():
            if self.path.stat().st_size > 8_000_000:
                raise PriceWatchError('Watch storage exceeds its limit.')
            try:
                state = json.loads(self.path.read_text())
                if not isinstance(state, dict) or not all(isinstance(state.get(k), list) and len(state[k]) <= 2000 for k in self._state):
                    raise ValueError()
                for watch in state['watches']:
                    _text(watch['owner'], 200)
                    _text(watch['id'], 100)
                    watch['product'] = _product(watch['product'])
                    if watch['consent'] is not True or watch['status'] not in ('active', 'error', 'cancelled'):
                        raise ValueError()
                    for key in ('createdAt', 'nextCheckAt', 'intervalSeconds'):
                        if isinstance(watch[key], bool) or not isinstance(watch[key], (float, int)) or not math.isfinite(watch[key]):
                            raise ValueError()
                    if not 60 <= watch['intervalSeconds'] <= 604800:
                        raise ValueError()
                for note in state['notifications']:
                    _text(note['owner'], 200)
                    _text(note['id'], 100)
                self._state = state
            except (ValueError, KeyError, TypeError):
                raise PriceWatchError('Watch storage is invalid; monitoring was not started.') from None

    def _save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, name = tempfile.mkstemp(prefix='.watch-', dir=self.path.parent)
        try:
            with os.fdopen(fd, 'w') as stream:
                json.dump(self._state, stream, allow_nan=False)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(name, self.path)
        finally:
            if os.path.exists(name):
                os.unlink(name)

    def start(self):
        with self._lock:
            if self._thread and self._thread.is_alive():
                return
            self._stop.clear()
            self._thread = threading.Thread(target=self._loop, daemon=True, name='homely-price-watch')
            self._thread.start()

    def stop(self):
        self._stop.set()
        thread = self._thread
        if thread:
            thread.join(timeout=1)

    def _loop(self):
        while not self._stop.wait(1):
            try:
                self.run_due()
            except Exception:
                # Do not log source pages, owner identifiers or private records.
                self._stop.set()

    def _public(self, record):
        result = copy.deepcopy(record)
        result.pop('owner', None)
        result['delivery'] = 'in_app'
        if result.get('status') in ('active', 'error') and not self.running:
            result['status'] = 'paused'
        return result

    @property
    def running(self):
        return bool(self._thread and self._thread.is_alive() and not self._stop.is_set())

    def _fresh(self, product):
        now = self.clock()
        for evidence in product['fieldEvidence'].values():
            observed = datetime.fromisoformat(evidence['observedAt'].replace('Z', '+00:00')).timestamp()
            if not 0 <= now - observed <= 86400:
                raise PriceWatchError('Product evidence must be from the last 24 hours and not future dated.')

    def subscribe(self, owner, product, consent=False, interval_seconds=3600):
        owner = _text(owner, 200)
        if consent is not True:
            raise PriceWatchError('Explicit consent is required to monitor this product.')
        product = _product(product)
        self._fresh(product)
        if isinstance(interval_seconds, bool) or not isinstance(interval_seconds, int) or not 60 <= interval_seconds <= 604800:
            raise PriceWatchError('Choose an interval between one minute and seven days.')
        with self._lock:
            owned = [w for w in self._state['watches'] if w['owner'] == owner]
            for watch in owned:
                if watch['status'] != 'cancelled' and all(watch['product'][k] == product[k] for k in ('url', 'exactSku', 'variant')):
                    return self._public(watch)
            if len(owned) >= 100 or len(self._state['watches']) >= 1000:
                raise PriceWatchError('The watch capacity has been reached.')
            now = self.clock()
            watch = dict(id=uuid.uuid4().hex, owner=owner, product=product, consent=True,
                         intervalSeconds=interval_seconds, createdAt=now, nextCheckAt=now + interval_seconds,
                         lastCheckedAt=None, status='active', error=None)
            self._state['watches'].append(watch)
            self._save()
            return self._public(watch)

    def list(self, owner):
        owner = _text(owner, 200)
        with self._lock:
            return [self._public(w) for w in self._state['watches'] if w['owner'] == owner]

    def cancel(self, owner, id):
        owner = _text(owner, 200)
        with self._lock:
            for watch in self._state['watches']:
                if watch['owner'] == owner and watch['id'] == id:
                    watch.update(status='cancelled', error=None)
                    self._save()
                    return self._public(watch)
        raise PriceWatchError('Watch not found.')

    def notifications(self, owner):
        owner = _text(owner, 200)
        with self._lock:
            return [self._public(n) for n in self._state['notifications'] if n['owner'] == owner]

    def mark_read(self, owner, id):
        owner = _text(owner, 200)
        with self._lock:
            for note in self._state['notifications']:
                if note['owner'] == owner and note['id'] == id:
                    note['read'] = True
                    self._save()
                    return self._public(note)
        raise PriceWatchError('Notification not found.')

    def run_due(self):
        """Explicit test/maintenance invocation also works without the daemon."""
        with self._run_lock:
            with self._lock:
                due = [copy.deepcopy(w) for w in self._state['watches']
                       if w['consent'] is True and w['status'] != 'cancelled' and w['nextCheckAt'] <= self.clock()][:20]
            for old in due:
                result, error = None, None
                try:
                    result = _product(self.checker(old['product']['url'], {}))
                    self._fresh(result)
                    if any(result[k] != old['product'][k] for k in ('url', 'exactSku', 'variant')):
                        raise PriceWatchError('Product identity changed.')
                except Exception:
                    result = None
                    error = 'Price could not be verified for this exact product. No price alert was generated.'
                with self._lock:
                    watch = next((w for w in self._state['watches'] if w['id'] == old['id']), None)
                    if watch is None or watch['status'] == 'cancelled':
                        continue
                    now = self.clock()
                    watch.update(lastCheckedAt=now, nextCheckAt=now + watch['intervalSeconds'],
                                 status='error' if error else 'active', error=error)
                    if result:
                        before, after = watch['product']['unitPrice'], result['unitPrice']
                        if before != after:
                            self._state['notifications'].append(dict(id=uuid.uuid4().hex, owner=watch['owner'],
                                watchId=watch['id'], title=result['title'], url=result['url'],
                                previousPrice=before, currentPrice=after, currency='USD', createdAt=now, read=False,
                                message='Observed public-page price changed; stock and delivered total remain unverified.'))
                            self._state['notifications'] = self._state['notifications'][-2000:]
                        watch['product'] = result
                    self._save()
