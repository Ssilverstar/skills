const { test, describe } = require('node:test');
const assert = require('node:assert/strict');
const helpers = require('../../app/static/app.js');

describe('FE-007 Feature Unit Tests', () => {

  test('FE-007 AC3: 라벨 매핑 (formatNativeTokenType: Claude 번역 vs Codex 원문 보존)', () => {
    // Claude: input/output/cacheRead/cacheCreation 매핑
    assert.equal(helpers.formatNativeTokenType('input', 'claude', 'ko'), '입력');
    assert.equal(helpers.formatNativeTokenType('input', 'claude', 'en'), 'input');
    assert.equal(helpers.formatNativeTokenType('output', 'claude', 'ko'), '출력');
    assert.equal(helpers.formatNativeTokenType('output', 'claude', 'en'), 'output');
    assert.equal(helpers.formatNativeTokenType('cacheRead', 'claude', 'ko'), '캐시 읽기');
    assert.equal(helpers.formatNativeTokenType('cacheRead', 'claude', 'en'), 'cacheRead');
    assert.equal(helpers.formatNativeTokenType('cacheCreation', 'claude', 'ko'), '캐시 쓰기');
    assert.equal(helpers.formatNativeTokenType('cacheCreation', 'claude', 'en'), 'cacheCreation');

    // Codex 및 기타: 원문 라벨 보존 (번역·합산 금지)
    const codexTypes = ['prompt_tokens', 'completion_tokens', 'cache_read_input_tokens', 'custom_token_type'];
    codexTypes.forEach(ct => {
      assert.equal(helpers.formatNativeTokenType(ct, 'codex', 'ko'), ct);
      assert.equal(helpers.formatNativeTokenType(ct, 'codex', 'en'), ct);
    });

    // 빈 값 안전성
    assert.equal(helpers.formatNativeTokenType('', 'claude', 'ko'), '');
    assert.equal(helpers.formatNativeTokenType(null, 'codex', 'ko'), '');
  });

  test('FE-007 AC1: native_usage 포맷 및 증가분 0 제외 검증 (formatNativeUsage)', () => {
    // 1. null / 빈 객체 -> null 반환 (블록 숨김)
    assert.equal(helpers.formatNativeUsage(null, 'claude', 'ko'), null);
    assert.equal(helpers.formatNativeUsage(undefined, 'claude', 'ko'), null);
    assert.equal(helpers.formatNativeUsage({}, 'claude', 'ko'), null);
    assert.equal(helpers.formatNativeUsage({ tokens: {} }, 'claude', 'ko'), null);

    // 2. 증가분 0 또는 음수만 있는 경우 -> null 반환 (블록 숨김)
    const allZero = {
      window: '24h',
      tokens: {
        'claude-3-7-sonnet': { input: 0, output: 0, cacheRead: 0, cacheCreation: 0 }
      },
      last_received_at: '2026-10-31T13:00:00Z'
    };
    assert.equal(helpers.formatNativeUsage(allZero, 'claude', 'ko'), null);

    // 3. 정상 데이터: 0은 제외되고 양수만 포맷팅
    const sampleData = {
      window: '24h',
      tokens: {
        'claude-3-7-sonnet': {
          input: 12500,
          output: 4500,
          cacheRead: 500000,
          cacheCreation: 0 // 제외되어야 함
        }
      },
      last_received_at: new Date(Date.now() - 5 * 60 * 1000).toISOString() // 5분 전
    };

    const resKo = helpers.formatNativeUsage(sampleData, 'claude', 'ko');
    assert.ok(resKo, '포맷된 데이터가 반환되어야 함');
    assert.equal(resKo.title, '네이티브 OTel 최근 24시간 수신');
    assert.match(resKo.limit, /increase\(\).*빠질 수/, '단발 counter 최초값 누락 한계 표시');
    assert.match(resKo.lastReceived, /마지막 수신:.*5분 전/);
    assert.equal(resKo.models.length, 1);
    assert.equal(resKo.models[0].model, 'claude-3-7-sonnet');

    // 0인 cacheCreation이 제외되어 items는 3개
    const items = resKo.models[0].items;
    assert.equal(items.length, 3);
    assert.deepEqual(items.map(i => i.rawType), ['input', 'output', 'cacheRead']);
    assert.deepEqual(items.map(i => i.type), ['입력', '출력', '캐시 읽기']);
    assert.equal(items[0].countText, '1만'); // 12500 -> Math.round(1.25) -> 1만 (ko)
    assert.equal(items[0].countFull, '12,500');

    // English 포맷 검증
    const resEn = helpers.formatNativeUsage(sampleData, 'claude', 'en');
    assert.equal(resEn.title, 'Native OTel · last 24h');
    assert.match(resEn.limit, /can be missed/);
    assert.match(resEn.lastReceived, /Last received:.*5m ago/);
    assert.deepEqual(resEn.models[0].items.map(i => i.type), ['input', 'output', 'cacheRead']);
    assert.equal(resEn.models[0].items[0].countText, '12.5K'); // 12500 -> 12.5K (en)
  });

  test('FE-007 AC2: 토큰 표·모델 표 상단 문구에 "세션 누적(브리지)" 명시 검증', () => {
    const ko = helpers.I18N.ko;
    const en = helpers.I18N.en;

    assert.ok(ko.descAgentTokens.includes('세션 누적(브리지)'), '한국어 토큰 표 설명에 "세션 누적(브리지)" 명시 필요');
    assert.ok(ko.descModelUsage.includes('세션 누적(브리지)'), '한국어 모델 표 설명에 "세션 누적(브리지)" 명시 필요');

    assert.ok(en.descAgentTokens.includes('Session accumulated (bridge)'), '영어 토큰 표 설명에 "Session accumulated (bridge)" 명시 필요');
    assert.ok(en.descModelUsage.includes('Session accumulated (bridge)'), '영어 모델 표 설명에 "Session accumulated (bridge)" 명시 필요');
  });

  test('FE-007 AC4: i18n 사전 키 일치성 검사', () => {
    const koKeys = Object.keys(helpers.I18N.ko).sort();
    const enKeys = Object.keys(helpers.I18N.en).sort();
    assert.deepEqual(koKeys, enKeys, 'ko와 en 사전은 동일한 키 집합을 가져야 합니다.');
  });
});
