const { test, describe } = require('node:test');
const assert = require('node:assert/strict');
const helpers = require('../../app/static/app.js');

describe('FE-006 Feature Unit Tests', () => {

  test('FE-006 AC2: 한도 라벨 번역 매핑 (formatLimitLabel)', () => {
    // 1. 주간(7일) / Weekly (7d)
    const weeklyInputs = ['10080분', '10080 min', '10080m', 'weekly', 'seven_day', '7d'];
    weeklyInputs.forEach(input => {
      assert.equal(helpers.formatLimitLabel(input, 'ko'), '주간(7일)', `${input} ko 번역 실패`);
      assert.equal(helpers.formatLimitLabel(input, 'en'), 'Weekly (7d)', `${input} en 번역 실패`);
    });

    // 2. 5시간 / 5-hour
    const fiveHourInputs = ['five_hour', '5h', '300분', '300 min'];
    fiveHourInputs.forEach(input => {
      assert.equal(helpers.formatLimitLabel(input, 'ko'), '5시간', `${input} ko 번역 실패`);
      assert.equal(helpers.formatLimitLabel(input, 'en'), '5-hour', `${input} en 번역 실패`);
    });

    // 3. Antigravity 복합 버킷명 접두어 보존
    assert.equal(helpers.formatLimitLabel('Gemini Models · weekly', 'ko'), 'Gemini Models · 주간(7일)');
    assert.equal(helpers.formatLimitLabel('Gemini Models · weekly', 'en'), 'Gemini Models · Weekly (7d)');
    assert.equal(helpers.formatLimitLabel('Claude 3.7 Sonnet - five_hour', 'ko'), 'Claude 3.7 Sonnet - 5시간');
    assert.equal(helpers.formatLimitLabel('Claude 3.7 Sonnet - five_hour', 'en'), 'Claude 3.7 Sonnet - 5-hour');

    // 4. 알 수 없는/기타 라벨은 원문 유지
    assert.equal(helpers.formatLimitLabel('daily_quota', 'ko'), 'daily_quota');
    assert.equal(helpers.formatLimitLabel('custom_limit', 'en'), 'custom_limit');

    // 5. 빈 값 및 null 안전성
    assert.equal(helpers.formatLimitLabel(null, 'ko'), '');
    assert.equal(helpers.formatLimitLabel(undefined, 'ko'), '');
    assert.equal(helpers.formatLimitLabel('', 'ko'), '');
  });

  test('FE-006 AC3: 추론 서버 키 라벨 매핑 (formatInferenceKey)', () => {
    // 1. observed_at -> 관측 시각 / Observed at
    assert.equal(helpers.formatInferenceKey('observed_at', 'ko'), '관측 시각');
    assert.equal(helpers.formatInferenceKey('observed_at', 'en'), 'Observed at');

    // 2. 알려진 고정 키 사전 라벨
    assert.equal(helpers.formatInferenceKey('container_image', 'ko'), '컨테이너 이미지');
    assert.equal(helpers.formatInferenceKey('container_image', 'en'), 'Container Image');
    assert.equal(helpers.formatInferenceKey('runtime_executable', 'ko'), '실행 파일');
    assert.equal(helpers.formatInferenceKey('runtime_executable', 'en'), 'Executable');
    assert.equal(helpers.formatInferenceKey('installed_vllm_version', 'ko'), '이미지 내 vLLM 패키지(미실행)');
    assert.equal(helpers.formatInferenceKey('installed_vllm_version', 'en'), 'Container vLLM (Unused)');
    assert.equal(helpers.formatInferenceKey('engine', 'ko'), '실행 런타임');
    assert.equal(helpers.formatInferenceKey('engine', 'en'), 'Runtime Engine');
    assert.equal(helpers.formatInferenceKey('version', 'ko'), '런타임 버전');
    assert.equal(helpers.formatInferenceKey('version', 'en'), 'Runtime Version');

    // 3. 모르는 키는 원문 반환
    assert.equal(helpers.formatInferenceKey('custom_extra_key', 'ko'), 'custom_extra_key');
    assert.equal(helpers.formatInferenceKey('gpu_vram_overhead', 'en'), 'gpu_vram_overhead');
    assert.equal(helpers.formatInferenceKey(null, 'ko'), '');
  });

  test('FE-006 AC5: 차트 축 눈금 계산 (calculateChartAxes: 정상, 빈 배열, 1점, 전부 null)', () => {
    // 1. 정상 데이터셋 (6시간 범위, 0~100%)
    const now = Date.now();
    const points6h = [
      { collected_at: new Date(now - 6 * 3600 * 1000).toISOString() },
      { collected_at: new Date(now - 3 * 3600 * 1000).toISOString() },
      { collected_at: new Date(now).toISOString() }
    ];
    const values6h = [20, 55, 80];

    const res6h = helpers.calculateChartAxes(points6h, values6h, 0, 100, '%', 'ko');
    assert.equal(res6h.yTicks.min, 0);
    assert.equal(res6h.yTicks.max, 100);
    assert.equal(res6h.yTicks.minLabel, '0%');
    assert.equal(res6h.yTicks.maxLabel, '100%');
    assert.equal(res6h.timeTicks.length, 3, '최소 3개 시간 눈금(시작, 중간, 끝) 생성');
    // 24시간 이내이므로 HH:mm 포맷 (콜론 1개 포함)
    assert.match(res6h.timeTicks[0].label, /^\d{2}:\d{2}$/);
    assert.match(res6h.timeTicks[2].label, /^\d{2}:\d{2}$/);

    // 2. 장기 데이터셋 (>24시간, 7일)
    const points7d = [
      { collected_at: new Date(now - 7 * 24 * 3600 * 1000).toISOString() },
      { collected_at: new Date(now - 3.5 * 24 * 3600 * 1000).toISOString() },
      { collected_at: new Date(now).toISOString() }
    ];
    const res7d = helpers.calculateChartAxes(points7d, [30, 40, 50], null, null, '°C', 'ko');
    assert.equal(res7d.timeTicks.length, 3);
    // 24시간 초과이므로 MM-DD HH:mm 포맷
    assert.match(res7d.timeTicks[0].label, /^\d{2}-\d{2}\s\d{2}:\d{2}$/);

    // 3. 빈 배열 케이스
    const resEmpty = helpers.calculateChartAxes([], [], null, null, 'W', 'ko');
    assert.ok(resEmpty.yTicks);
    assert.ok(Array.isArray(resEmpty.timeTicks));
    assert.equal(resEmpty.timeTicks.length, 0);
    assert.equal(typeof resEmpty.yTicks.min, 'number');
    assert.equal(typeof resEmpty.yTicks.max, 'number');

    // 4. 단일 점 (1점) 케이스
    const points1 = [{ collected_at: new Date(now).toISOString() }];
    const values1 = [45];
    const res1 = helpers.calculateChartAxes(points1, values1, null, null, '°C', 'ko');
    assert.ok(res1.yTicks);
    assert.equal(res1.timeTicks.length, 1);
    assert.equal(res1.yTicks.unit, '°C');
    assert.ok(res1.yTicks.max >= 45);

    // 5. 전부 null 케이스
    const pointsNull = [
      { collected_at: new Date(now - 3600 * 1000).toISOString() },
      { collected_at: new Date(now).toISOString() }
    ];
    const valuesNull = [null, null];
    const resNull = helpers.calculateChartAxes(pointsNull, valuesNull, 0, 100, '%', 'ko');
    assert.equal(resNull.yTicks.min, 0);
    assert.equal(resNull.yTicks.max, 100);
    assert.equal(resNull.yTicks.minLabel, '0%');
    assert.equal(resNull.yTicks.maxLabel, '100%');
    assert.equal(resNull.timeTicks.length, 3);
  });

  test('FE-006 AC4: 상태 문구 양 언어 정의 확인', () => {
    const ko = helpers.I18N.ko;
    const en = helpers.I18N.en;

    // 수집 대기 / Waiting
    assert.ok(ko.statusWaiting && en.statusWaiting);
    // 정상 / Healthy
    assert.ok(ko.statusHealthy && en.statusHealthy);
    // 지연(stale) / Stale
    assert.ok(ko.statusStale && en.statusStale);
    // 오류 / Error
    assert.ok(ko.statusError && en.statusError);
    // 미확인 / Unknown
    assert.ok(ko.unknown && en.unknown);
    // 미계측 / Unmeasured
    assert.ok(ko.skillUnmeasured && en.skillUnmeasured);
    // 미지원 / Unsupported
    assert.ok(ko.telemetryUnsupported && en.telemetryUnsupported);
    // 부분 관측 / Partial
    assert.ok(ko.agentPartial && en.agentPartial);
    // 과거 관측 / Historical
    assert.ok(ko.planHistoricalBadge && en.planHistoricalBadge);
  });
});
