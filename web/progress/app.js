(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  let lastSuccess = null;
  let lastData = null;
  let busy = false;
  let expanded = new Set();
  const REFRESH_MS = 10000;
  const STALE_MS = 30000;
  const el = (tag, cls, text) => { const node = document.createElement(tag); if (cls) node.className = cls; if (text !== undefined) node.textContent = String(text); return node; };
  const percent = score => typeof score?.percent === 'number' && Number.isFinite(score.percent) && score.percent >= 0 && score.percent <= 100 ? score.percent : null;
  const formatPercent = score => percent(score) === null ? '—' : `${Math.round(percent(score) * 10) / 10}%`;
  const scoreText = score => typeof score?.earned === 'number' && typeof score?.total === 'number' ? `${score.earned} / ${score.total} points earned` : 'Checklist score unavailable';
  const strings = values => (Array.isArray(values) ? values : values ? [values] : []).map(v => typeof v === 'string' ? v : JSON.stringify(v));
  const readable = value => typeof value === 'string' ? value : value == null ? '' : JSON.stringify(value);

  function overall(kind, score) {
    $(`${kind}-percent`).textContent = formatPercent(score);
    $(`${kind}-score`).textContent = scoreText(score);
    $(`${kind}-bar`).style.width = `${percent(score) ?? 0}%`;
  }
  function mini(kind, score) {
    const node = el('div', `mini ${kind}-mini`);
    node.append(el('div', 'mini-label', kind === 'poc' ? 'POC / beta' : 'Production'), el('div', 'mini-value', formatPercent(score)));
    const meter = el('div', 'mini-meter'); const fill = el('span'); fill.style.width = `${percent(score) ?? 0}%`; meter.append(fill); node.append(meter);
    return node;
  }
  function criteria(title, score) {
    const group = el('section', 'criteria-group'); group.append(el('h3', null, `${title} · ${scoreText(score)}`));
    const list = el('ul', 'criteria-list');
    if (!Array.isArray(score?.criteria) || !score.criteria.length) list.append(el('li', 'criterion-evidence', 'No checklist criteria recorded yet.'));
    for (const row of score?.criteria || []) {
      const met = row.met === true;
      const item = el('li', `criterion${met ? ' met' : ''}`);
      const mark = el('span', 'criterion-mark', met ? '✓' : ''); mark.setAttribute('aria-label', met ? 'Complete' : 'Not complete');
      const text = el('div'); text.append(el('div', 'criterion-title', row.label || 'Unnamed criterion'));
      text.append(el('p', 'criterion-evidence', strings(row.evidence).join(' · ') || (met ? 'No evidence detail recorded.' : 'Evidence still needed.')));
      item.append(mark, text, el('span', 'criterion-weight', `${readable(row.weight) || '—'} pts`)); list.append(item);
    }
    group.append(list); return group;
  }
  function component(row, index) {
    const id = String(row.id ?? index); const node = el('details', 'component'); node.dataset.id = id; node.open = expanded.has(id);
    const summary = el('summary'); const title = el('div', 'component-title');
    title.append(el('div', 'component-name', row.name || 'Unnamed component'), el('div', 'owner', `Owner · ${readable(row.owner) || 'Unassigned'}`));
    const blockers = strings(row.blockers);
    if (blockers.length) title.append(el('span', 'blocker-badge', `${blockers.length} ${blockers.length === 1 ? 'blocker' : 'blockers'}`));
    summary.append(title, el('div', 'task', readable(row.currentTask) || 'No current task recorded.'), mini('poc', row.poc), mini('production', row.production)); node.append(summary);
    const body = el('div', 'component-body');
    if (blockers.length) { const panel = el('div', 'blockers'); panel.append(el('strong', null, 'Needs attention')); blockers.forEach(value => panel.append(el('p', null, value))); body.append(panel); }
    const columns = el('div', 'criteria-columns'); columns.append(criteria('POC / beta', row.poc), criteria('Production', row.production)); body.append(columns); node.append(body);
    node.addEventListener('toggle', () => { if (!node.isConnected) return; node.open ? expanded.add(id) : expanded.delete(id); updateExpandLabel(); });
    return node;
  }
  function updateExpandLabel() {
    const nodes = [...document.querySelectorAll('.component')];
    $('expand-all').textContent = nodes.length && nodes.every(node => node.open) ? 'Collapse all evidence' : 'Expand all evidence';
  }
  function journal(id, values, empty) {
    const list = $(id); list.replaceChildren(); const rows = strings(values);
    (rows.length ? rows : [empty]).forEach(value => list.append(el('li', null, value)));
  }
  function render(data) {
    overall('poc', data.poc); overall('production', data.production);
    const rows = Array.isArray(data.components) ? data.components : [];
    expanded = new Set([...document.querySelectorAll('.component[open]')].map(node => node.dataset.id));
    $('components').replaceChildren(...(rows.length ? rows.map(component) : [el('div', 'empty-state', 'No components have been added to the build checklist yet.')]));
    $('component-count').textContent = `${rows.length} ${rows.length === 1 ? 'component' : 'components'}`;
    $('expand-all').disabled = !rows.length; updateExpandLabel();
    journal('open-actions', data.openActions, 'No open actions recorded.');
    journal('decisions', data.recentDecisions, 'No decisions recorded yet.');
    journal('evidence', data.evidence, 'No verification evidence recorded yet.');
  }
  function freshness() {
    const age = lastSuccess ? Date.now() - lastSuccess : Infinity;
    const stale = age > STALE_MS;
    const sourceDate = lastData?.updatedAt ? new Date(lastData.updatedAt) : null;
    const sourceValid = sourceDate && Number.isFinite(sourceDate.getTime());
    const sourceText = sourceValid ? sourceDate.toLocaleString(undefined, { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' }) : 'not recorded';
    $('updated-at').textContent = lastSuccess ? `Checklist updated ${sourceText}. Last checked ${new Date(lastSuccess).toLocaleTimeString(undefined, { hour: 'numeric', minute: '2-digit', second: '2-digit' })}.` : 'Waiting for the first successful update';
    if (lastSuccess && stale) { $('connection').className = 'live-status stale'; $('connection-label').textContent = 'Updates delayed · showing saved snapshot'; }
  }
  async function refresh() {
    if (busy) return;
    busy = true; $('refresh').disabled = true;
    const controller = new AbortController(); const timeout = setTimeout(() => controller.abort(), 8000);
    try {
      const response = await fetch('/api/progress', { cache: 'no-store', signal: controller.signal });
      if (!response.ok) throw new Error('unavailable');
      const data = await response.json();
      if (!data || typeof data !== 'object' || !Array.isArray(data.components) || !data.poc || !data.production) throw new Error('invalid');
      // Only a canonical-record change replaces DOM: expanded evidence and focus
      // remain stable while someone is reading through a checklist.
      if (JSON.stringify(data) !== JSON.stringify(lastData)) render(data);
      lastData = data; lastSuccess = Date.now();
      $('connection').className = 'live-status live'; $('connection-label').textContent = 'Connected to build records';
      $('fetch-error').hidden = true;
    } catch (_) {
      $('connection').className = 'live-status error'; $('connection-label').textContent = lastData ? 'Update unavailable · previous data retained' : 'Build records unavailable';
      $('fetch-error').textContent = lastData ? 'The latest update could not be fetched. These are the last received checklist values, not current confirmation. We will keep checking automatically.' : 'The progress service is not responding yet. No completion percentages are assumed. This page will retry automatically.';
      $('fetch-error').hidden = false;
      if (!lastData) { $('components').replaceChildren(el('div', 'empty-state', 'Waiting for the progress service. Your build records will appear here once connected.')); $('component-count').textContent = 'Awaiting checklist'; }
    } finally { clearTimeout(timeout); busy = false; $('refresh').disabled = false; freshness(); }
  }
  $('refresh').addEventListener('click', refresh);
  $('expand-all').addEventListener('click', () => { const nodes = [...document.querySelectorAll('.component')]; const open = !nodes.every(node => node.open); nodes.forEach(node => { node.open = open; }); updateExpandLabel(); });
  document.addEventListener('visibilitychange', () => { if (!document.hidden) refresh(); });
  refresh(); setInterval(() => { freshness(); if (!document.hidden) refresh(); }, REFRESH_MS);
})();
