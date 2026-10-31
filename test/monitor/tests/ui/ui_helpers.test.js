const { test, describe } = require('node:test');
const assert = require('node:assert/strict');
const helpers = require('../../app/static/app.js');

describe('FE-001 UI Helper Unit Tests', () => {

  test('TC-M1: 순수함수 모듈 노출 확인', () => {
    assert.equal(typeof helpers.formatValue, 'function');
    assert.equal(typeof helpers.formatPercent, 'function');
    assert.equal(typeof helpers.formatBytes, 'function');
    assert.equal(typeof helpers.formatTokens, 'function');
    assert.equal(typeof helpers.formatRelativeTime, 'function');
    assert.equal(typeof helpers.formatDateTime, 'function');
    assert.equal(typeof helpers.isHistoricalPlan, 'function');
    assert.equal(typeof helpers.calculateSvgPath, 'function');
    assert.equal(typeof helpers.formatAgentStatus, 'function');
  });

  test('TC-M2: null→"미확인"과 0→"0" 구분 검증', () => {
    // formatValue
    assert.equal(helpers.formatValue(null), '미확인');
    assert.equal(helpers.formatValue(undefined), '미확인');
    assert.equal(helpers.formatValue(NaN), '미확인');
    assert.equal(helpers.formatValue(0), '0');
    assert.equal(helpers.formatValue(42), '42');
    assert.equal(helpers.formatValue(1234567), '1,234,567');

    // formatTokens
    const nullTokens = helpers.formatTokens(null);
    assert.equal(nullTokens.text, '미확인');
    assert.equal(nullTokens.full, '미확인');

    const undefTokens = helpers.formatTokens(undefined);
    assert.equal(undefTokens.text, '미확인');
    assert.equal(undefTokens.full, '미확인');

    const zeroTokens = helpers.formatTokens(0);
    assert.equal(zeroTokens.text, '0');
    assert.equal(zeroTokens.full, '0');
  });

  test('TC-M3: 바이트 포맷 검증 (formatBytes, IEC 1024 단위: B, KiB, MiB, GiB, TiB, PiB)', () => {
    assert.equal(helpers.formatBytes(null), '미확인');
    assert.equal(helpers.formatBytes(undefined), '미확인');
    assert.equal(helpers.formatBytes(0), '0 B');
    assert.equal(helpers.formatBytes(1024), '1.00 KiB');
    assert.equal(helpers.formatBytes(1048576), '1.00 MiB');
    assert.equal(helpers.formatBytes(1073741824), '1.00 GiB');

    // 호스트 메모리 실제 값 (약 128GB -> 119.63 GiB)
    const hostMem = helpers.formatBytes(128452161536);
    assert.equal(hostMem, '119.63 GiB');
  });

  test('TC-M4: 퍼센트 포맷 검증 (formatPercent)', () => {
    assert.equal(helpers.formatPercent(null), '미확인');
    assert.equal(helpers.formatPercent(undefined), '미확인');
    assert.equal(helpers.formatPercent(0), '0%');
    assert.equal(helpers.formatPercent(73.36), '73.4%');
    assert.equal(helpers.formatPercent(73.36, 2), '73.36%');
    assert.equal(helpers.formatPercent(100), '100.0%');
  });

  test('TC-M5: 큰 토큰 축약 및 한국어 ko-KR 구분 (formatTokens)', () => {
    // 1만 단위 축약 ('4,321만')
    const t4321 = helpers.formatTokens(43210000);
    assert.equal(t4321.text, '4,321만');
    assert.equal(t4321.full, '43,210,000');

    // 44,386,461 -> 4,439만
    const tCodex = helpers.formatTokens(44386461);
    assert.equal(tCodex.text, '4,439만');
    assert.equal(tCodex.full, '44,386,461');

    // 1억 단위 축약 (212,182,534 -> 2.12억)
    const tClaude = helpers.formatTokens(212182534);
    assert.equal(tClaude.text, '2.12억');
    assert.equal(tClaude.full, '212,182,534');

    // 1만 미만은 천 단위 콤마
    const tSmall = helpers.formatTokens(4268);
    assert.equal(tSmall.text, '4,268');
    assert.equal(tSmall.full, '4,268');
  });

  test('TC-M6: 이력 플랜 판정 검증 (isHistoricalPlan: preflight, historical, >24h)', () => {
    const fixedNow = new Date('2026-10-31T12:00:00Z');

    // 1. source 에 preflight 포함
    const planPreflight = {
      name: 'Claude Pro',
      source: 'preflight /usage UI observation',
      observed_at: '2026-10-31T11:00:00Z'
    };
    assert.equal(helpers.isHistoricalPlan(planPreflight, fixedNow), true);

    // 2. source 에 historical 포함
    const planHist = {
      name: 'Plan X',
      source: 'historical account DB',
      observed_at: '2026-10-31T11:00:00Z'
    };
    assert.equal(helpers.isHistoricalPlan(planHist, fixedNow), true);

    // 3. observed_at이 24시간 초과
    const planOld = {
      name: 'Plan Old',
      source: 'live api',
      observed_at: '2026-10-29T10:00:00Z' // 약 50시간 전
    };
    assert.equal(helpers.isHistoricalPlan(planOld, fixedNow), true);

    // 4. 정상 실시간 플랜 (최근 관측, preflight/historical 없음)
    const planLive = {
      name: 'prolite',
      source: 'Codex account API',
      observed_at: '2026-10-31T11:30:00Z' // 30분 전
    };
    assert.equal(helpers.isHistoricalPlan(planLive, fixedNow), false);

    // 5. plan이 없는 경우
    assert.equal(helpers.isHistoricalPlan(null, fixedNow), false);
  });

  test('TC-M7: null 구간에서 선이 끊기는 SVG 경로 검증 (calculateSvgPath)', () => {
    // [10, 20, null, 30, 40] -> 2개 별개의 M 세그먼트로 분리되어야 함
    const values = [10, 20, null, 30, 40];
    const result = helpers.calculateSvgPath(values, 200, 100, 10);

    assert.ok(result.d, 'SVG path 문자열이 생성되어야 함');

    // 'M ' 명령어가 2회 등장해야 함 (null에서 선이 끊김)
    const mMatches = result.d.match(/M\s/g);
    assert.equal(mMatches ? mMatches.length : 0, 2, 'null로 인해 2개의 M 세그먼트가 생성되어야 함');

    // 0으로 연결되는 L 명령어가 없어야 함
    assert.equal(result.points[2].value, null);
    assert.equal(result.points[2].y, null);

    // 모두 null인 경우
    const allNull = helpers.calculateSvgPath([null, null, null], 200, 100, 10);
    assert.equal(allNull.d, '');
    assert.equal(allNull.points.length, 0);

    // 연속된 숫자만 있는 경우 M은 1개
    const continuous = helpers.calculateSvgPath([10, 20, 30], 200, 100, 10);
    const continuousM = continuous.d.match(/M\s/g);
    assert.equal(continuousM ? continuousM.length : 0, 1);
  });

  test('TC-M8: 상대 시간 포맷 검증 (formatRelativeTime)', () => {
    const now = new Date('2026-10-31T12:00:00Z');

    assert.equal(helpers.formatRelativeTime(null, now), '미확인');
    assert.equal(helpers.formatRelativeTime('invalid-date', now), '미확인');

    // 5초 전
    const sec5 = new Date('2026-10-31T11:59:55Z').toISOString();
    assert.equal(helpers.formatRelativeTime(sec5, now), '방금 전');

    // 30초 전
    const sec30 = new Date('2026-10-31T11:59:30Z').toISOString();
    assert.equal(helpers.formatRelativeTime(sec30, now), '30초 전');

    // 15분 전
    const min15 = new Date('2026-10-31T11:45:00Z').toISOString();
    assert.equal(helpers.formatRelativeTime(min15, now), '15분 전');

    // 3시간 전
    const hr3 = new Date('2026-10-31T09:00:00Z').toISOString();
    assert.equal(helpers.formatRelativeTime(hr3, now), '3시간 전');

    // 2일 전
    const day2 = new Date('2026-10-29T12:00:00Z').toISOString();
    assert.equal(helpers.formatRelativeTime(day2, now), '2일 전');

    // 미래 시각 케이스 (reset_at)
    const futureSec30 = new Date('2026-10-31T12:00:30Z').toISOString();
    assert.equal(helpers.formatRelativeTime(futureSec30, now), '30초 후');

    const futureMin15 = new Date('2026-10-31T12:15:00Z').toISOString();
    assert.equal(helpers.formatRelativeTime(futureMin15, now), '15분 후');

    const futureHr3 = new Date('2026-10-31T15:00:00Z').toISOString();
    assert.equal(helpers.formatRelativeTime(futureHr3, now), '3시간 후');

    const futureDay2 = new Date('2026-11-02T12:00:00Z').toISOString();
    assert.equal(helpers.formatRelativeTime(futureDay2, now), '2일 후');

    const futureDay7 = new Date('2026-11-07T00:29:39Z').toISOString();
    assert.equal(helpers.formatRelativeTime(futureDay7, now), '6일 후');
  });

  test('TC-M9: 시각 포맷 검증 (formatDateTime)', () => {
    assert.equal(helpers.formatDateTime(null), '미확인');
    assert.equal(helpers.formatDateTime('invalid'), '미확인');

    const dt = helpers.formatDateTime('2026-10-31T03:23:38Z');
    // 브라우저 로컬 시간 형식 (YYYY-MM-DD HH:mm:ss)
    assert.match(dt, /^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/);
  });

  test('TC-M10: 에이전트 상태 라벨 매핑 검증 (formatAgentStatus: partial = "부분 관측")', () => {
    assert.deepEqual(helpers.formatAgentStatus('observed'), { label: '관측됨', className: 'badge-good' });
    assert.deepEqual(helpers.formatAgentStatus('partial'), { label: '부분 관측', className: 'badge-warning' });
    assert.deepEqual(helpers.formatAgentStatus('unavailable'), { label: '미지원/미확인', className: 'badge-warning' });
    assert.deepEqual(helpers.formatAgentStatus(null), { label: '미확인', className: 'badge-warning' });
    assert.deepEqual(helpers.formatAgentStatus('unknown_status'), { label: 'unknown_status', className: 'badge-warning' });
  });

});
