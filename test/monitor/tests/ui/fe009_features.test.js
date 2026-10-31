const { test, describe } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const helpers = require('../../app/static/app.js');

describe('FE-009 Feature Unit Tests', () => {

  test('FE-009 AC1/AC5: calculateMcpSummary 순수 함수 검증', () => {
    // 1. null / undefined / 빈 객체 -> null 반환 (미확인 빈 상태 신호)
    assert.equal(helpers.calculateMcpSummary(null), null);
    assert.equal(helpers.calculateMcpSummary(undefined), null);
    assert.equal(helpers.calculateMcpSummary('invalid'), null);

    // 2. 정상 MCP 데이터: 공통 서버 3개, 에이전트 2개 정의, 2개 누락
    const sampleMcp = {
      common_servers: ['git', 'github', 'chrome-devtools'],
      observed_at: '2026-10-31T12:00:00Z',
      agents: [
        {
          agent: 'claude',
          common_configured_count: 3,
          servers: [
            { name: 'git', scope: 'common', configured: true, enabled: true, status: 'connected', tool_count: 5 },
            { name: 'github', scope: 'common', configured: true, enabled: true, status: 'connected', tool_count: 10 },
            { name: 'chrome-devtools', scope: 'common', configured: true, enabled: false, status: 'configured', tool_count: null },
            { name: 'custom-platform-tool', scope: 'platform', configured: true, enabled: true, status: 'connected', tool_count: 2 },
            { name: 'broken-server', scope: 'platform', configured: false, enabled: false, status: 'error', tool_count: 0 }
          ]
        },
        {
          agent: 'codex',
          common_configured_count: 2,
          servers: [
            { name: 'git', scope: 'common', configured: true, enabled: true, status: 'connected', tool_count: 3 },
            { name: 'github', scope: 'common', configured: true, enabled: false, status: 'error', tool_count: null }
          ]
        }
      ]
    };

    const summaryKo = helpers.calculateMcpSummary(sampleMcp, 'ko');
    assert.ok(summaryKo, '요약 객체가 반환되어야 함');
    assert.equal(summaryKo.commonTotal, 3);
    assert.equal(summaryKo.agents.length, 4, '기본 4개 호스트(codex, claude, opencode, antigravity) 모두 타일 목록에 포함');

    // Claude 검증
    const claude = summaryKo.agents.find(a => a.agent === 'claude');
    assert.ok(claude);
    assert.equal(claude.isMissing, false);
    assert.equal(claude.commonConfigured, 3);
    assert.equal(claude.commonConfiguredText, '3/3');
    assert.equal(claude.commonConnected, 2); // git, github (connected & scope common)
    assert.equal(claude.platformAdded, 2); // custom-platform-tool, broken-server
    assert.equal(claude.errorCount, 1); // broken-server

    // Codex 검증
    const codex = summaryKo.agents.find(a => a.agent === 'codex');
    assert.ok(codex);
    assert.equal(codex.isMissing, false);
    assert.equal(codex.commonConfiguredText, '2/3');
    assert.equal(codex.commonConnected, 1); // git
    assert.equal(codex.platformAdded, 0);
    assert.equal(codex.errorCount, 1); // github (error)

    // Antigravity (누락 에이전트) 검증: 0이 아니라 미확인(null)이어야 함
    const antigravity = summaryKo.agents.find(a => a.agent === 'antigravity');
    assert.ok(antigravity);
    assert.equal(antigravity.isMissing, true);
    assert.equal(antigravity.commonConfigured, null);
    assert.equal(antigravity.commonConnected, null);
    assert.equal(antigravity.platformAdded, null);
    assert.equal(antigravity.commonConfiguredText, '미확인');
    assert.equal(antigravity.commonConnectedText, '미확인');
    assert.equal(antigravity.platformAddedText, '미확인');

    // English 모드 검증
    const summaryEn = helpers.calculateMcpSummary(sampleMcp, 'en');
    const antigravityEn = summaryEn.agents.find(a => a.agent === 'antigravity');
    assert.equal(antigravityEn.commonConfiguredText, 'Unknown');
  });

  test('FE-009 AC2/AC5: formatMcpStatus 및 formatMcpScope 순수 함수 검증', () => {
    // 1. formatMcpStatus 한국어 매핑
    assert.deepEqual(helpers.formatMcpStatus('connected', 'ko'), { label: '연결 확인(디스커버리)', className: 'badge-good', icon: '✓' });
    assert.deepEqual(helpers.formatMcpStatus('configured', 'ko'), { label: '설정만 확인', className: 'badge-info', icon: '⚙️' });
    assert.deepEqual(helpers.formatMcpStatus('error', 'ko'), { label: '오류', className: 'badge-critical', icon: '⚠️' });
    assert.deepEqual(helpers.formatMcpStatus('unverified', 'ko'), { label: '미확인', className: 'badge-muted', icon: '?' });

    // 2. formatMcpStatus 영어 매핑
    assert.deepEqual(helpers.formatMcpStatus('connected', 'en'), { label: 'Connected (discovery)', className: 'badge-good', icon: '✓' });
    assert.deepEqual(helpers.formatMcpStatus('configured', 'en'), { label: 'Configured only', className: 'badge-info', icon: '⚙️' });
    assert.deepEqual(helpers.formatMcpStatus('error', 'en'), { label: 'Error', className: 'badge-critical', icon: '⚠️' });
    assert.deepEqual(helpers.formatMcpStatus('unverified', 'en'), { label: 'Unverified', className: 'badge-muted', icon: '?' });

    // 3. 미지의 상태 문자열은 원문 라벨 유지 (textContent 사용)
    const unknownSt = helpers.formatMcpStatus('custom_testing_state', 'ko');
    assert.equal(unknownSt.label, 'custom_testing_state');
    assert.equal(unknownSt.className, 'badge-muted');

    // 4. null / undefined 처리
    assert.equal(helpers.formatMcpStatus(null, 'ko').label, '미확인');
    assert.equal(helpers.formatMcpStatus(null, 'en').label, 'Unknown');

    // 5. formatMcpScope 매핑
    assert.equal(helpers.formatMcpScope('common', 'ko'), '공통');
    assert.equal(helpers.formatMcpScope('common', 'en'), 'Common');
    assert.equal(helpers.formatMcpScope('platform', 'ko'), '플랫폼');
    assert.equal(helpers.formatMcpScope('platform', 'en'), 'Platform');
  });

  test('FE-009 AC6: index.html 내 모든 한글 노출 요소의 data-i18n 속성 및 I18N 사전 대응 검증', () => {
    const htmlPath = path.resolve(__dirname, '../../app/static/index.html');
    const html = fs.readFileSync(htmlPath, 'utf8');

    // 1. 텍스트 노드에 한글이 포함된 모든 HTML 태그가 data-i18n 속성을 가져야 함
    const tagMatches = [...html.matchAll(/<([a-zA-Z0-9]+)([^>]*)>([^<]*[가-힣][^<]*)<\/\1>/g)];
    const missingI18nTags = tagMatches.filter(m => !m[2].includes('data-i18n'));
    assert.deepEqual(missingI18nTags, [], 'index.html 내 모든 한글 텍스트 태그는 data-i18n 속성을 보유해야 합니다');

    // 2. aria-label, title, placeholder 속성에 한글이 포함된 경우 대응하는 data-i18n-* 속성을 가져야 함
    const attrMatches = [...html.matchAll(/<([a-zA-Z0-9]+)([^>]*\b(aria-label|title|placeholder)=\"[^\"]*[가-힣][^\"]*\"[^>]*)>/g)];
    const missingI18nAttrs = attrMatches.filter(m => !m[2].includes('data-i18n-'));
    assert.deepEqual(missingI18nAttrs, [], 'index.html 내 모든 한글 속성은 data-i18n-* 속성을 보유해야 합니다');

    // 3. index.html에 정의된 모든 data-i18n 키가 I18N.ko 및 I18N.en 사전에 존재해야 함
    const allKeys = [...html.matchAll(/data-i18n(?:-aria|-title|-placeholder)?=\"([^\"]+)\"/g)].map(m => m[1]);
    allKeys.forEach(key => {
      assert.ok(helpers.I18N.ko[key] !== undefined, `I18N.ko에 키 누락: ${key}`);
      assert.ok(helpers.I18N.en[key] !== undefined, `I18N.en에 키 누락: ${key}`);
    });

    // 4. I18N.en 사전에는 단 한 글자의 한글도 없어야 함 (btnLangToggle 포함)
    const hangulRegex = /[가-힣]/;
    Object.keys(helpers.I18N.en).forEach(k => {
      assert.ok(!hangulRegex.test(helpers.I18N.en[k]), `I18N.en.${k}에 한글 포함됨: ${helpers.I18N.en[k]}`);
    });
    assert.equal(helpers.I18N.en.btnLangToggle, 'Korean');

    // 5. 프로브 번역어 중 모델 표의 '세션 누적 · 모델별 분해 미지원' 변환 확인
    const modelTransEn = helpers.translateProbeText('세션 누적 · 모델별 분해 미지원', 'en');
    assert.ok(!hangulRegex.test(modelTransEn), `모델명 번역에 한글이 남아있음: ${modelTransEn}`);
    assert.equal(modelTransEn, 'Session accumulated · model breakdown unsupported');
  });

});
