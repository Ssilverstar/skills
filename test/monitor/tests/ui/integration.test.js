// 통합 회귀(Claude 소유): 프로브 실라벨의 접미사('한도') 번역
const test = require('node:test');
const assert = require('node:assert');
const { formatLimitLabel, formatSkillCounts, formatGpuProcesses, calculateSkillBreakdown, formatMcpStatus, calculateMcpSummary, I18N } = require('../../app/static/app.js');

test('probe label "10080분 한도" maps to weekly in both languages', () => {
  assert.strictEqual(formatLimitLabel('10080분 한도', 'ko'), '주간(7일)');
  assert.strictEqual(formatLimitLabel('10080분 한도', 'en'), 'Weekly (7d)');
  assert.strictEqual(formatLimitLabel('세션 (과거 관측)', 'ko'), '세션 (과거 관측)', 'unknown labels stay as-is');
});

test('skill counts keep registered/enabled separate from common selected/installed', () => {
  const sa = { installed_count: 344, enabled_count: 39, common_selected_count: 36, common_installed_count: 35 };
  assert.deepStrictEqual(formatSkillCounts(sa, 'ko'),
    { registered: '등록 전체: 344', enabled: '활성: 39', common: '공통 선택 36 · 설치 35' });
  assert.strictEqual(formatSkillCounts({}, 'en').common, 'Common: selected Unknown · installed Unknown');
});

test('sort button title is localized', () => {
  assert.strictEqual(I18N.en.sortTitle.replace('{label}', 'Name'), 'Sort by Name');
  assert.ok(!/정렬/.test(I18N.en.sortTitle));
});

test('GPU process memory is shown as bytes with names, never as a VRAM ratio', () => {
  const gpu = { memory_used_bytes: null, process_memory_used_bytes: 72213 * 1024 ** 2,
    compute_processes: [{ name: 'llama-server', memory_used_bytes: 72213 * 1024 ** 2 }] };
  assert.deepStrictEqual(formatGpuProcesses(gpu, 'ko'), { total: '70.52 GiB', list: 'llama-server 70.52 GiB' });
  assert.deepStrictEqual(formatGpuProcesses({ compute_processes: [] }, 'en'), { total: 'Unknown', list: 'None' });
  assert.deepStrictEqual(formatGpuProcesses({}, 'ko'), { total: '미확인', list: '미확인' });
});

test('skill breakdown prefers probe common_enabled/platform_extra counts (also in compacted snapshots)', () => {
  const skills = [{ common_id: 'a', enabled: true }, { name: 'x', enabled: true }, { name: 'y', enabled: true }];
  const full = calculateSkillBreakdown({ agent: 'claude', common_enabled_count: 36, platform_extra_count: 3, skills }, 'ko');
  assert.strictEqual(full.commonActive, 36);
  assert.strictEqual(full.platformAdded, 3);
  const listOnly = calculateSkillBreakdown({ agent: 'claude', skills }, 'ko');
  assert.strictEqual(listOnly.commonActive, 1);
  assert.strictEqual(listOnly.platformAdded, 2);
  const compacted = calculateSkillBreakdown({ agent: 'codex', compacted: true, common_enabled_count: 36, platform_extra_count: 0 }, 'en');
  assert.strictEqual(compacted.commonActive, 36);
  assert.strictEqual(compacted.platformAdded, 0, '0 from probe is a real value, not unknown');
  assert.strictEqual(calculateSkillBreakdown({ agent: 'antigravity', compacted: true }, 'en').commonActive, null);
});

test('MCP connected is labelled as discovery, never as usable', () => {
  assert.strictEqual(formatMcpStatus('connected', 'en').label, 'Connected (discovery)');
  assert.strictEqual(formatMcpStatus('connected', 'ko').label, '연결 확인(디스커버리)');
  assert.strictEqual(I18N.en.btnLangToggle, 'Korean');
});

test('MCP summary has exactly the four real host ids (no phantom gemini card)', () => {
  const server = { name: 'git', scope: 'common', configured: true, enabled: true, status: 'connected', tool_count: 12 };
  const ids = ['codex', 'claude', 'opencode', 'antigravity'];
  const full = { common_servers: ['git', 'github', 'chrome-devtools'],
    agents: ids.map(agent => ({ agent, common_configured_count: 3, servers: [server] })) };
  const got = calculateMcpSummary(full, 'en').agents.map(a => a.agent).sort();
  assert.deepStrictEqual(got, [...ids].sort());
  const partial = calculateMcpSummary({ common_servers: ['git'], agents: [{ agent: 'codex', servers: [server] }] }, 'en');
  assert.strictEqual(partial.agents.length, 4, 'missing hosts still get an unknown tile, nothing extra');
  assert.ok(!partial.agents.some(a => a.agent === 'gemini'));
  assert.strictEqual(partial.agents.find(a => a.agent === 'antigravity').isMissing, true);
});

test('explicit null probe count stays unknown; only a missing field falls back to the list', () => {
  const skills = [{ common_id: 'a', enabled: null }, { common_id: 'b', enabled: null }];
  const agy = calculateSkillBreakdown({ agent: 'antigravity', common_enabled_count: null, platform_extra_count: 0, skills }, 'en');
  assert.strictEqual(agy.commonActive, null, 'Antigravity active state is unverified, not 0');
  assert.strictEqual(agy.platformAdded, 0);
  const absent = calculateSkillBreakdown({ agent: 'antigravity', skills }, 'en');
  assert.strictEqual(absent.commonActive, 0, 'field absent -> computed from list');
});
