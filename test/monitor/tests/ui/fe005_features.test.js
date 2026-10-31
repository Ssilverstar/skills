const { test, describe } = require('node:test');
const assert = require('node:assert/strict');
const helpers = require('../../app/static/app.js');

describe('FE-005 Feature Unit Tests', () => {

  test('FE-005 AC1: i18n 사전 키 누락 검사 (ko와 en의 키 집합이 완전히 동일해야 함)', () => {
    assert.ok(helpers.I18N, 'I18N 객체가 존재해야 함');
    assert.ok(helpers.I18N.ko, 'I18N.ko 객체가 존재해야 함');
    assert.ok(helpers.I18N.en, 'I18N.en 객체가 존재해야 함');

    const koKeys = Object.keys(helpers.I18N.ko).sort();
    const enKeys = Object.keys(helpers.I18N.en).sort();

    // 두 언어의 키 수가 일치하고 누락된 키가 없어야 함
    assert.deepEqual(koKeys, enKeys, 'ko와 en 사전은 동일한 키 집합을 가져야 합니다.');
    assert.ok(koKeys.length > 50, '충분한 수의 UI 번역 키가 정의되어야 함');
  });

  test('FE-005 AC1: 단위 축약 en/ko 검증 (formatTokens)', () => {
    // 한국어: 만/억
    const koSmall = helpers.formatTokens(4268, 'ko');
    assert.equal(koSmall.text, '4,268');

    const koMan = helpers.formatTokens(43210000, 'ko');
    assert.equal(koMan.text, '4,321만');

    const koEok = helpers.formatTokens(212182534, 'ko');
    assert.equal(koEok.text, '2.12억');

    // 영어: K/M/B
    const enSmall = helpers.formatTokens(4268, 'en');
    assert.equal(enSmall.text, '4.3K');

    const enMil = helpers.formatTokens(43210000, 'en');
    assert.equal(enMil.text, '43.2M');

    const en212M = helpers.formatTokens(212182534, 'en');
    assert.equal(en212M.text, '212.2M');

    const enBil = helpers.formatTokens(1500000000, 'en');
    assert.equal(enBil.text, '1.5B');

    // 0 및 null 처리
    const zeroKo = helpers.formatTokens(0, 'ko');
    assert.equal(zeroKo.text, '0');
    assert.equal(zeroKo.full, '0');

    const zeroEn = helpers.formatTokens(0, 'en');
    assert.equal(zeroEn.text, '0');
    assert.equal(zeroEn.full, '0');

    const nullKo = helpers.formatTokens(null, 'ko');
    assert.equal(nullKo.text, '미확인');

    const nullEn = helpers.formatTokens(null, 'en');
    assert.equal(nullEn.text, 'Unknown');
  });

  test('FE-005 AC4: 정렬 비교기 - 타입별 정렬 검증 (string, number, date)', () => {
    // 1. 숫자 정렬
    const numAsc = helpers.compareValues(5, 20, 'number', 'asc');
    assert.ok(numAsc < 0, '5가 20보다 앞에 와야 함');

    const numDesc = helpers.compareValues(5, 20, 'number', 'desc');
    assert.ok(numDesc > 0, '20이 5보다 앞에 와야 함');

    // 2. 문자열 정렬 (Intl.Collator numeric: true)
    const strAsc = helpers.compareValues('item2', 'item10', 'string', 'asc', 'ko');
    assert.ok(strAsc < 0, 'item2가 item10보다 앞에 와야 함 (numeric: true)');

    // 3. 날짜 정렬
    const d1 = '2026-10-31T01:00:00Z';
    const d2 = '2026-10-31T05:00:00Z';
    const dateAsc = helpers.compareValues(d1, d2, 'date', 'asc');
    assert.ok(dateAsc < 0, '이른 날짜가 앞에 와야 함');

    const dateDesc = helpers.compareValues(d1, d2, 'date', 'desc');
    assert.ok(dateDesc > 0, '늦은 날짜가 앞에 와야 함');
  });

  test('FE-005 AC4: 정렬 비교기 - null/미확인/미계측은 asc/desc 모두 항상 맨 아래 위치', () => {
    const list = [
      { id: 1, val: 50 },
      { id: 2, val: null },
      { id: 3, val: 10 },
      { id: 4, val: '미확인' },
      { id: 5, val: 100 },
      { id: 6, val: undefined },
      { id: 7, val: '미계측' }
    ];

    // 오름차순 (asc)
    const sortedAsc = helpers.sortTableData(list, x => x.val, 'number', 'asc', 'ko');
    const idsAsc = sortedAsc.map(x => x.id);
    // 유효한 숫자 10, 50, 100이 먼저 오고, null/미확인/undefined/미계측은 뒤에 와야 함
    assert.deepEqual(idsAsc.slice(0, 3), [3, 1, 5], '오름차순에서 유효한 숫자가 먼저 정렬되어야 함');
    assert.ok(idsAsc.slice(3).every(id => [2, 4, 6, 7].includes(id)), 'null 관련 값은 뒤에 위치해야 함');

    // 내림차순 (desc)
    const sortedDesc = helpers.sortTableData(list, x => x.val, 'number', 'desc', 'ko');
    const idsDesc = sortedDesc.map(x => x.id);
    // 유효한 숫자 100, 50, 10이 먼저 오고, null 관련 값은 여전히 맨 뒤에 와야 함!
    assert.deepEqual(idsDesc.slice(0, 3), [5, 1, 3], '내림차순에서 유효한 숫자가 큰 순서대로 와야 함');
    assert.ok(idsDesc.slice(3).every(id => [2, 4, 6, 7].includes(id)), '내림차순에서도 null 관련 값은 맨 뒤에 위치해야 함');
  });

  test('FE-005 AC4: 정렬 비교기 - 안정 정렬 (Stable sort) 검증', () => {
    const list = [
      { id: 'a', score: 10 },
      { id: 'b', score: 20 },
      { id: 'c', score: 10 },
      { id: 'd', score: 20 },
      { id: 'e', score: 10 }
    ];

    const sorted = helpers.sortTableData(list, x => x.score, 'number', 'asc');
    const ids = sorted.map(x => x.id);
    // 점수 10인 항목들 ('a', 'c', 'e')의 원래 상대적 순서가 보존되어야 함
    assert.deepEqual(ids, ['a', 'c', 'e', 'b', 'd']);
  });

  test('FE-005 AC6: 수집 방식 (Telemetry) 배지 라벨 매핑 검증 (formatTelemetryMode)', () => {
    // 한국어
    const tKoNative = helpers.formatTelemetryMode('native', 'ko');
    assert.equal(tKoNative.text, '네이티브 OTel');
    assert.equal(tKoNative.class, 'badge-good');

    const tKoBridge = helpers.formatTelemetryMode('bridge', 'ko');
    assert.equal(tKoBridge.text, '브리지');
    assert.equal(tKoBridge.class, 'badge-info');

    const tKoUnsup = helpers.formatTelemetryMode('unsupported', 'ko');
    assert.equal(tKoUnsup.text, '미지원');
    assert.equal(tKoUnsup.class, 'badge-muted');

    // 영어
    const tEnNative = helpers.formatTelemetryMode('native', 'en');
    assert.equal(tEnNative.text, 'Native OTel');

    const tEnBridge = helpers.formatTelemetryMode('bridge', 'en');
    assert.equal(tEnBridge.text, 'Bridge');

    const tEnUnsup = helpers.formatTelemetryMode('unsupported', 'en');
    assert.equal(tEnUnsup.text, 'Unsupported');
  });

  test('FE-005 AC7: 해상도 라벨 검증 (formatResolutionLabel)', () => {
    // 5m 집계
    assert.equal(helpers.formatResolutionLabel('5m', 'ko'), '5분 집계 · 평균(최소~최대)');
    assert.equal(helpers.formatResolutionLabel('5m', 'en'), '5m aggregation · Average (Min–Max)');

    // raw 원본
    assert.equal(helpers.formatResolutionLabel('raw', 'ko'), '원본 스냅샷(약 15초)');
    assert.equal(helpers.formatResolutionLabel('raw', 'en'), 'Raw snapshot (~15s)');

    // 미지정/기본값 -> raw 취급
    assert.equal(helpers.formatResolutionLabel(null, 'ko'), '원본 스냅샷(약 15초)');
    assert.equal(helpers.formatResolutionLabel(undefined, 'en'), 'Raw snapshot (~15s)');
  });

});
