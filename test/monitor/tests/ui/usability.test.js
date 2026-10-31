'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const app = require('../../app/static/app.js');

const ROOT = path.resolve(__dirname, '../..');
const HTML_PATH = path.join(ROOT, 'app/static/index.html');
const CSS_PATH = path.join(ROOT, 'app/static/style.css');
const SNAPSHOT_PATH = path.join(ROOT, 'data/snapshot.json');

test('UX-001 B: isLimitExpired, selectMaxLimit, and calculateAgentKpi handle expired limits', () => {
  const now = new Date('2026-04-20T20:00:00Z');

  // 1. One expired (95%), one active (42%) -> selects active 42%
  const mixedLimits = [
    { label: '5h rolling window', used_percent: 95.0, reset_at: '2026-04-20T18:00:00Z' },
    { label: '7d rolling window', used_percent: 42.5, reset_at: '2026-04-21T18:00:00Z' }
  ];
  assert.equal(app.isLimitExpired(mixedLimits[0], now), true);
  assert.equal(app.isLimitExpired(mixedLimits[1], now), false);

  const selectedMixed = app.selectMaxLimit(mixedLimits, 'ko', now);
  assert.ok(selectedMixed, 'Expected active limit to be selected');
  assert.equal(selectedMixed.used_percent, 42.5);

  const kpiMixed = app.calculateAgentKpi(
    {
      id: 'codex',
      name: 'Codex',
      status: 'authenticated',
      observed_at: '2026-04-20T19:55:00Z',
      plan: { name: 'Plus', limits: mixedLimits }
    },
    null,
    now,
    'ko'
  );
  assert.ok(kpiMixed.limitInfo, 'Expected limitInfo for active limit');
  assert.equal(kpiMixed.limitInfo.usedPercent, '42.5%');
  assert.equal(kpiMixed.allLimitsExpired, false);

  // 2. All limits expired -> selectMaxLimit returns null, KPI sets allLimitsExpired & limitStatusText
  const allExpired = [
    { label: '5h rolling window', used_percent: 88.0, reset_at: '2026-04-20T15:00:00Z' },
    { label: '7d rolling window', used_percent: 73.0, reset_at: '2026-04-20T19:59:59Z' }
  ];
  assert.equal(app.selectMaxLimit(allExpired, 'ko', now), null);

  const kpiExpiredKo = app.calculateAgentKpi(
    {
      id: 'claude',
      name: 'Claude Code',
      status: 'authenticated',
      observed_at: '2026-04-20T14:00:00Z',
      plan: { name: 'Max', limits: allExpired }
    },
    null,
    now,
    'ko'
  );
  assert.equal(kpiExpiredKo.limitInfo, null);
  assert.equal(kpiExpiredKo.allLimitsExpired, true);
  assert.equal(kpiExpiredKo.limitStatusText, '갱신 대기');

  const kpiExpiredEn = app.calculateAgentKpi(
    {
      id: 'claude',
      name: 'Claude Code',
      status: 'authenticated',
      observed_at: '2026-04-20T14:00:00Z',
      plan: { name: 'Max', limits: allExpired }
    },
    null,
    now,
    'en'
  );
  assert.equal(kpiExpiredEn.limitInfo, null);
  assert.equal(kpiExpiredEn.allLimitsExpired, true);
  assert.equal(kpiExpiredEn.limitStatusText, 'Awaiting update');

  // 3. Missing or invalid reset_at -> treated as active/current limit
  const noResetLimits = [
    { label: '5h rolling window', used_percent: 61.2 },
    { label: '7d rolling window', used_percent: 55.0, reset_at: 'invalid-date' }
  ];
  assert.equal(app.isLimitExpired(noResetLimits[0], now), false);
  assert.equal(app.isLimitExpired(noResetLimits[1], now), false);
  const selectedNoReset = app.selectMaxLimit(noResetLimits, 'ko', now);
  assert.ok(selectedNoReset);
  assert.equal(selectedNoReset.used_percent, 61.2);
});

test('UX-001 A: resolveConnectionStatus handles disconnect, snapshot retention, and recovery', () => {
  const now = new Date('2026-04-20T20:10:00Z');
  const snapshotState = {
    status: 'ok',
    age_seconds: 12,
    snapshot: { collected_at: '2026-04-20T20:05:00Z', agents: [{ id: 'codex' }] }
  };

  // Disconnected state with existing snapshot
  const disconnectedKo = app.resolveConnectionStatus(
    snapshotState,
    {
      disconnected: true,
      lastSuccessAt: '2026-04-20T20:05:00Z',
      errorMessage: 'HTTP 503',
      justRecovered: false
    },
    now,
    'ko'
  );
  assert.equal(disconnectedKo.badgeText, '연결 끊김');
  assert.equal(disconnectedKo.badgeClass, 'badge-critical');
  assert.equal(disconnectedKo.retainData, true);
  assert.equal(disconnectedKo.showErrorBanner, true);
  assert.ok(disconnectedKo.errorBannerText.includes('마지막 성공:'), 'Should include last success label');
  assert.ok(disconnectedKo.errorBannerText.includes('5분 전'), 'Should include relative elapsed time');

  const disconnectedEn = app.resolveConnectionStatus(
    snapshotState,
    {
      disconnected: true,
      lastSuccessAt: '2026-04-20T20:05:00Z',
      errorMessage: 'HTTP 503',
      justRecovered: false
    },
    now,
    'en'
  );
  assert.equal(disconnectedEn.badgeText, 'Disconnected');
  assert.equal(disconnectedEn.retainData, true);
  assert.ok(disconnectedEn.errorBannerText.includes('Last success:'));
  assert.ok(disconnectedEn.errorBannerText.includes('5m ago'));

  // Recovery state after reconnect
  const recoveredKo = app.resolveConnectionStatus(
    snapshotState,
    {
      disconnected: false,
      lastSuccessAt: '2026-04-20T20:10:00Z',
      errorMessage: '',
      justRecovered: true
    },
    now,
    'ko'
  );
  assert.equal(recoveredKo.badgeText, '수집 정상');
  assert.equal(recoveredKo.badgeClass, 'badge-good');
  assert.equal(recoveredKo.showErrorBanner, false);
  assert.equal(recoveredKo.recoveryText, '연결 복구됨');

  const recoveredEn = app.resolveConnectionStatus(
    snapshotState,
    {
      disconnected: false,
      lastSuccessAt: '2026-04-20T20:10:00Z',
      errorMessage: '',
      justRecovered: true
    },
    now,
    'en'
  );
  assert.equal(recoveredEn.badgeText, 'Healthy');
  assert.equal(recoveredEn.showErrorBanner, false);
  assert.equal(recoveredEn.recoveryText, 'Connection restored');
});

test('UX-001 D: buildChartAriaSummary generates accessible summary and empty-data fallback', () => {
  const koSummary = app.buildChartAriaSummary('GPU 사용률', '최근 24시간', [12, null, 45.5, 30], '%', 'ko');
  assert.ok(koSummary.includes('GPU 사용률'));
  assert.ok(koSummary.includes('최근 24시간'));
  assert.ok(koSummary.includes('최근 30%'));
  assert.ok(koSummary.includes('최소 12%'));
  assert.ok(koSummary.includes('최대 45.5%'));

  const enSummary = app.buildChartAriaSummary('GPU Utilization', 'Last 24h', [12, null, 45.5, 30], '%', 'en');
  assert.ok(enSummary.includes('GPU Utilization'));
  assert.ok(enSummary.includes('Last 24h'));
  assert.ok(enSummary.includes('latest 30%'));
  assert.ok(enSummary.includes('min 12%'));
  assert.ok(enSummary.includes('max 45.5%'));

  const koEmpty = app.buildChartAriaSummary('GPU 온도', '최근 1시간', [null, undefined], '°C', 'ko');
  assert.ok(koEmpty.includes('GPU 온도'));
  assert.ok(koEmpty.includes('데이터 없음'));

  const enEmpty = app.buildChartAriaSummary('GPU Temperature', 'Last 1h', [], '°C', 'en');
  assert.ok(enEmpty.includes('GPU Temperature'));
  assert.ok(enEmpty.includes('No data'));
});

test('UX-001 E: filterSkillsList deduplicates common scope with priority and filters status/search', () => {
  // Priority test: enabled: true -> enabled: null -> enabled: false
  const syntheticSkills = [
    // Claude duplicate common_id: one false, one true -> should keep true
    { name: 'ponytail-help (plugin)', common_id: 'ponytail-help', agentName: 'claude', enabled: false, isRepo: false, origin: 'plugin' },
    { name: 'ponytail-help', common_id: 'ponytail-help', agentName: 'claude', enabled: true, isRepo: false, origin: 'user' },
    // Antigravity duplicate common_id: one false, one null -> should keep null
    { name: 'archify-disabled', common_id: 'archify', agentName: 'antigravity', enabled: false, isRepo: false, origin: 'user' },
    { name: 'archify', common_id: 'archify', agentName: 'antigravity', enabled: null, isRepo: false, origin: 'user' },
    // Platform-only skill (common_id: null) -> excluded in common scope, included in all scope
    { name: 'claude-platform-only', common_id: null, agentName: 'claude', enabled: true, isRepo: false, origin: 'builtin' },
    // Repository skill -> preserved in both common and all scopes
    { name: 'ponytail-help', common_id: 'ponytail-help', agentName: '저장소 원본', enabled: null, isRepo: true, origin: 'repo' }
  ];

  const commonRes = app.filterSkillsList(syntheticSkills, {
    scope: 'common',
    agent: 'ALL',
    status: 'ALL',
    search: ''
  });
  // Should have: 1 repo + 1 claude (enabled: true) + 1 antigravity (enabled: null) = 3 shown out of 6 total
  assert.equal(commonRes.totalCount, 6);
  assert.equal(commonRes.shownCount, 3);

  const claudeCommon = commonRes.rows.find(r => r.agentName === 'claude' && r.common_id === 'ponytail-help');
  assert.ok(claudeCommon);
  assert.equal(claudeCommon.enabled, true);

  const agyCommon = commonRes.rows.find(r => r.agentName === 'antigravity' && r.common_id === 'archify');
  assert.ok(agyCommon);
  assert.equal(agyCommon.enabled, null);

  // All scope preserves all 6 rows
  const allRes = app.filterSkillsList(syntheticSkills, {
    scope: 'all',
    agent: 'ALL',
    status: 'ALL',
    search: ''
  });
  assert.equal(allRes.totalCount, 6);
  assert.equal(allRes.shownCount, 6);

  // Status filter: unknown (enabled === null)
  const unknownRes = app.filterSkillsList(syntheticSkills, {
    scope: 'common',
    agent: 'ALL',
    status: 'unknown',
    search: ''
  });
  assert.equal(unknownRes.totalCount, 6);
  assert.equal(unknownRes.shownCount, 2);
  assert.ok(unknownRes.rows.every(r => r.enabled === null));

  // Real snapshot verification if available
  if (fs.existsSync(SNAPSHOT_PATH)) {
    const snap = JSON.parse(fs.readFileSync(SNAPSHOT_PATH, 'utf8'));
    const skillsRoot = snap.skills || {};
    const repoSkills = Array.isArray(skillsRoot.repository) ? skillsRoot.repository : [];
    const skillAgents = Array.isArray(skillsRoot.agents) ? skillsRoot.agents : [];
    const flat = [];
    repoSkills.forEach(s => flat.push({ ...s, agentName: '저장소 원본', isRepo: true }));
    skillAgents.forEach(sa => {
      (sa.skills || []).forEach(s => flat.push({ ...s, agentName: sa.agent, isRepo: false }));
    });

    // Claude common scope -> 36 unique common skills
    const claudeFiltered = app.filterSkillsList(flat, {
      scope: 'common',
      agent: 'claude',
      status: 'ALL',
      search: ''
    });
    assert.equal(claudeFiltered.shownCount, 36);

    // Antigravity common scope -> 36 unique common skills with enabled: null preserved
    const agyFiltered = app.filterSkillsList(flat, {
      scope: 'common',
      agent: 'antigravity',
      status: 'ALL',
      search: ''
    });
    assert.equal(agyFiltered.shownCount, 36);
    assert.ok(agyFiltered.rows.every(r => r.enabled === null));

    // Search 'ponytail-help' with agent='ALL' -> >= 4 rows; with agent='opencode' -> 1 row
    const ponyAll = app.filterSkillsList(flat, {
      scope: 'common',
      agent: 'ALL',
      status: 'ALL',
      search: 'ponytail-help'
    });
    assert.ok(ponyAll.shownCount >= 4, `Expected >= 4 rows for ponytail-help, got ${ponyAll.shownCount}`);

    const ponyOpencode = app.filterSkillsList(flat, {
      scope: 'common',
      agent: 'opencode',
      status: 'ALL',
      search: 'ponytail-help'
    });
    assert.equal(ponyOpencode.shownCount, 1);
  }
});

test('UX-001 F & HTML/CSS invariants: KPI token note, range aria-pressed, jump bar, and minimum font size', () => {
  const now = new Date('2026-04-20T20:00:00Z');
  const kpiKo = app.calculateAgentKpi({ id: 'codex', name: 'Codex' }, null, now, 'ko');
  const kpiEn = app.calculateAgentKpi({ id: 'codex', name: 'Codex' }, null, now, 'en');
  assert.equal(kpiKo.totalTokensNote, '관측된 세션 누적 · 청구량 아님');
  assert.equal(kpiEn.totalTokensNote, 'Observed session total · not billing');

  const html = fs.readFileSync(HTML_PATH, 'utf8');
  assert.ok(html.includes('id="filter-skill-scope"'), 'index.html should contain #filter-skill-scope');
  assert.ok(html.includes('id="filter-skill-status"'), 'index.html should contain #filter-skill-status');
  assert.ok(html.includes('id="skills-row-count"'), 'index.html should contain #skills-row-count');
  assert.ok(html.includes('class="skills-jump-bar"'), 'index.html should contain .skills-jump-bar');
  assert.ok(html.includes('aria-pressed="true"'), 'index.html should include aria-pressed="true" on active range button');

  const css = fs.readFileSync(CSS_PATH, 'utf8');
  assert.ok(!/font-size:\s*1[01]px/.test(css), 'style.css should not use 10px or 11px font sizes');
});

// Integrator (Claude) addition after ownership transfer: live-region text excludes the ticking elapsed value; aria values rounded.
test('UX-001 integration: disconnect live text has no elapsed value; chart aria rounds to 1 decimal', () => {
  const now = new Date('2026-04-20T20:05:00Z');
  const s = app.resolveConnectionStatus(null, { isDisconnected: true, error: 'HTTP 502', lastSuccessAt: '2026-04-20T20:00:00Z' }, now, 'en');
  assert.ok(s.errorBannerText.includes('5m ago') || /5/.test(s.lastSuccessElapsed));
  assert.ok(s.errorBannerLive.includes('Last success:') && s.errorBannerLive.includes('HTTP 502'));
  assert.ok(!s.errorBannerLive.includes(s.lastSuccessElapsed), s.errorBannerLive);
  const aria = app.buildChartAriaSummary('GPU', '1h', [12.3456, 7.04], '%', 'en');
  assert.ok(aria.includes('latest 7%') && aria.includes('max 12.3%'), aria);
});
