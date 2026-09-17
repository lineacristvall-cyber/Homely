// Run with the bundled Node runtime and NODE_PATH pointing at its node_modules.
const assert = require('node:assert/strict');
const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('playwright');

const score = (earned, total, percent) => ({ earned, total, percent, criteria: [
  { label: 'Measured source truth gate', weight: 4, met: true, evidence: 'Four negative stock fixtures passed.' },
  { label: 'Live provider evaluation', weight: 6, met: false, evidence: 'Requires an authorized product reference.' },
] });
let data = { updatedAt: new Date().toISOString(), poc: score(4, 10, 40), production: score(1, 10, 10),
  components: [{ id: 'visual', name: 'Actual-product visualization', owner: 'Visualization worker', currentTask: 'Inspect product identity against the source reference.',
    blockers: ['Need a permitted room and product photo.'], poc: score(4, 10, 40), production: score(1, 10, 10) },
    { id: 'source', name: 'Stock & source truth', owner: 'Integration supervisor', currentTask: 'Connect a verified inventory source.',
      blockers: [], poc: score(7, 10, 70), production: score(0, 10, 0) }],
  openActions: ['Test the core workflow on mobile.'], recentDecisions: ['Unknown stock remains a lead.'], evidence: ['18 visualization unit tests passed.'] };
let failing = false;
const server = http.createServer((req, res) => {
  if (req.url === '/api/progress') { res.writeHead(failing ? 503 : 200, { 'Content-Type': 'application/json' }); return res.end(JSON.stringify(data)); }
  const filename = req.url === '/progress' || req.url === '/progress/' ? 'index.html' : req.url.split('/').pop();
  if (!['index.html', 'styles.css', 'app.js'].includes(filename)) { res.writeHead(404); return res.end(); }
  res.setHeader('Content-Type', filename.endsWith('.css') ? 'text/css' : filename.endsWith('.js') ? 'text/javascript' : 'text/html');
  res.end(fs.readFileSync(path.join(__dirname, filename)));
});

(async () => {
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const browser = await chromium.launch({ headless: true, channel: 'chrome' });
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 1100 } });
    const errors = []; page.on('pageerror', error => errors.push(error.message));
    await page.goto(`http://127.0.0.1:${server.address().port}/progress`);
    await page.waitForFunction(() => document.querySelector('#poc-percent').textContent === '40%');
    assert.equal(await page.locator('#production-percent').textContent(), '10%');
    assert.equal(await page.locator('.component').count(), 2);
    await page.locator('.component summary').first().click();
    assert.equal(await page.locator('.component[open]').count(), 1);
    await page.locator('#refresh').click();
    await page.waitForFunction(() => !document.querySelector('#refresh').disabled);
    assert.equal(await page.locator('.component[open]').count(), 1, 'refresh retains expanded evidence');
    data = { ...data, poc: score(5, 10, 50), openActions: ['<img src=x onerror="window.injected=true">'] };
    await page.locator('#refresh').click();
    await page.waitForFunction(() => document.querySelector('#poc-percent').textContent === '50%');
    assert.equal(await page.locator('.component[open]').count(), 1, 'new record retains expanded evidence');
    assert.equal(await page.locator('#open-actions img').count(), 0, 'record text cannot inject HTML');
    await page.locator('#expand-all').click();
    assert.equal(await page.locator('.component[open]').count(), 2);
    failing = true;
    await page.locator('#refresh').click();
    await page.waitForFunction(() => !document.querySelector('#fetch-error').hidden);
    assert.equal(await page.locator('#poc-percent').textContent(), '50%', 'failure retains last confirmed score');
    assert.match(await page.locator('#fetch-error').textContent(), /last received/);
    failing = false;
    await page.locator('#refresh').click();
    await page.waitForFunction(() => document.querySelector('#fetch-error').hidden);
    await page.screenshot({ path: '/tmp/homely-progress-laptop.png', fullPage: true });
    await page.setViewportSize({ width: 390, height: 844 });
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true, 'mobile layout has no horizontal overflow');
    await page.screenshot({ path: '/tmp/homely-progress-mobile.png', fullPage: true });
    await page.setViewportSize({ width: 320, height: 700 });
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true, 'narrow mobile layout has no overflow');
    failing = true;
    await page.reload();
    await page.waitForFunction(() => !document.querySelector('#fetch-error').hidden);
    assert.equal(await page.locator('#poc-percent').textContent(), '—', 'initial offline state never invents progress');
    assert.deepEqual(errors, []);
    console.log('PASS: server scores, component evidence, refresh persistence, XSS handling, failure/recovery, offline initial state, laptop and 390px/320px layouts.');
    console.log('Screenshots: /tmp/homely-progress-laptop.png and /tmp/homely-progress-mobile.png');
  } finally { await browser.close(); server.close(); }
})().catch(error => { console.error(error); server.close(); process.exitCode = 1; });
