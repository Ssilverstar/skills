const { test, describe } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const helpers = require('../../app/static/app.js');

describe('FE-008 Feature Unit Tests', () => {

  test('FE-008 AC2: calculateSkillBreakdown 순수 함수 검증', () => {
    // 1. 일반 케이스: 중복 common_id, platform 추가, 비활성, 미확인
    const agentSkills = {
      common_selected_count: 36,
      common_installed_count: 10,
      installed_count: 25,
      enabled_count: 15,
      skills: [
        { name: 's1', common_id: 'c1', enabled: true },
        { name: 's2', common_id: 'c1', enabled: true }, // 중복 common_id: 활성은 1개로 집계
        { name: 's3', common_id: 'c2', enabled: true },
        { name: 's4', common_id: 'c3', enabled: false }, // inactive
        { name: 's5', common_id: null, enabled: true }, // platform_added
        { name: 's6', common_id: undefined, enabled: true }, // platform_added
        { name: 's7', common_id: '', enabled: false }, // inactive
        { name: 's8', common_id: null, enabled: null }, // unconfirmed
        { name: 's9', common_id: 'c4', enabled: undefined }, // unconfirmed
      ]
    };

    const res = helpers.calculateSkillBreakdown(agentSkills);
    assert.equal(res.compacted, false);
    assert.equal(res.common_selected, 36);
    assert.equal(res.common_discovered, 10);
    assert.equal(res.common_active, 2); // c1, c2
    assert.equal(res.platform_added, 2); // s5, s6
    assert.equal(res.inactive, 2); // s4, s7
    assert.equal(res.unconfirmed, 2); // s8, s9
    assert.equal(res.installed_total, 25);
    assert.equal(res.enabled_total, 15);

    // 2. 압축본(compacted) 케이스: skills 배열 부재 또는 compacted: true
    const compactedSkills1 = {
      compacted: true,
      common_selected_count: 36,
      common_installed_count: 10,
      skills: []
    };
    const resCompact1 = helpers.calculateSkillBreakdown(compactedSkills1);
    assert.equal(resCompact1.compacted, true);
    assert.equal(resCompact1.common_selected, 36);
    assert.equal(resCompact1.common_discovered, 10);
    assert.equal(resCompact1.common_active, null);
    assert.equal(resCompact1.platform_added, null);
    assert.equal(resCompact1.inactive, null);
    assert.equal(resCompact1.unconfirmed, null);

    const compactedSkills2 = {
      installed_count: 10
    };
    const resCompact2 = helpers.calculateSkillBreakdown(compactedSkills2);
    assert.equal(resCompact2.compacted, true);
    assert.equal(resCompact2.common_active, null);

    // 3. null / undefined 입력 안전성
    const resNull = helpers.calculateSkillBreakdown(null);
    assert.equal(resNull.compacted, true);
    assert.equal(resNull.common_active, null);
  });

  test('FE-008 AC1: selectPrimaryModel 및 selectMaxLimit 순수 함수 검증', () => {
    // 1. selectPrimaryModel: models 중 usage 토큰 최다 모델 선택
    const models = [
      { model: 'claude-3-5-haiku', usage: { total_tokens: 5000 } },
      { model: 'claude-3-7-sonnet', usage: { total_tokens: 150000 } },
      { model: 'claude-3-opus', usage: { total_tokens: 12000 } }
    ];
    assert.equal(helpers.selectPrimaryModel(models), 'claude-3-7-sonnet');

    // total_tokens가 없는 경우 input_tokens + output_tokens 합산
    const modelsWithoutTotal = [
      { model: 'm1', usage: { input_tokens: 100, output_tokens: 200 } },
      { model: 'm2', usage: { input_tokens: 500, output_tokens: 500 } }
    ];
    assert.equal(helpers.selectPrimaryModel(modelsWithoutTotal), 'm2');

    // 빈 모델 목록 또는 null
    assert.equal(helpers.selectPrimaryModel([]), null);
    assert.equal(helpers.selectPrimaryModel(null), null);

    // 2. selectMaxLimit: used_percent 최댓값 한도 선택
    const limits = [
      { label: '5-hour limit', used_percent: 15, reset_at: '2026-10-31T18:00:00Z' },
      { label: 'Weekly limit', used_percent: 85.5, reset_at: '2026-11-05T00:00:00Z' },
      { label: 'Daily limit', used_percent: 40, reset_at: '2026-11-01T00:00:00Z' }
    ];
    const maxLim = helpers.selectMaxLimit(limits);
    assert.ok(maxLim);
    assert.equal(maxLim.label, 'Weekly limit');
    assert.equal(maxLim.used_percent, 85.5);
    assert.equal(maxLim.reset_at, '2026-11-05T00:00:00Z');

    // used_percent가 null인 경우
    const nullLimits = [
      { label: 'Unchecked', used_percent: null }
    ];
    const maxNullLim = helpers.selectMaxLimit(nullLimits);
    assert.equal(maxNullLim.label, 'Unchecked');
    assert.equal(maxNullLim.used_percent, null);

    // 빈 배열 / null
    assert.equal(helpers.selectMaxLimit([]), null);
    assert.equal(helpers.selectMaxLimit(null), null);

    // 3. calculateAgentKpi 종합 검증
    const agent = {
      id: 'claude',
      name: 'Claude Code',
      status: 'active',
      observed_at: '2026-10-31T12:00:00Z',
      models: models,
      usage: { total_tokens: 167000 },
      plan: {
        limits: limits,
        source: 'historical'
      }
    };
    const telemetry = {
      claude: {
        usage: 'native',
        quota: 'bridge'
      }
    };
    const kpi = helpers.calculateAgentKpi(agent, telemetry, new Date('2026-10-31T12:05:00Z'), 'en');
    assert.equal(kpi.rawStatus, 'active');
    assert.equal(kpi.primaryModel, 'claude-3-7-sonnet');
    assert.equal(kpi.totalTokens.text, '167K');
    assert.equal(kpi.maxLimit.label, 'Weekly (7d)');
    assert.equal(kpi.maxLimit.usedPercentNum, 85.5);
    assert.equal(kpi.maxLimit.isHistorical, true);
    assert.equal(kpi.usageTelemetryMode, 'Native OTel');
    assert.equal(kpi.quotaTelemetryMode, 'Bridge');
  });

  test('FE-008 AC4: translateProbeText 순수 함수 검증', () => {
    // 1. 한국어 모드('ko')에서는 원문 그대로 반환
    assert.equal(helpers.translateProbeText('호스트 OS', 'ko'), '호스트 OS');
    assert.equal(helpers.translateProbeText('임의의 한국어 프로브 텍스트', 'ko'), '임의의 한국어 프로브 텍스트');

    // 2. 영어 모드('en') - 알려진 프로브 번역어
    assert.equal(helpers.translateProbeText('호스트 OS', 'en'), 'Host OS');
    assert.equal(helpers.translateProbeText('5시간', 'en'), '5h');
    assert.equal(helpers.translateProbeText('10080분 한도', 'en'), 'Weekly limit');
    assert.equal(helpers.translateProbeText('부분 관측', 'en'), 'Partially Observed');
    assert.equal(helpers.translateProbeText('정상', 'en'), 'Healthy');

    // 3. 영어 모드('en') - 미지의 한글 문자열 -> 대체 문구로 치환
    const unknownKorean = '알 수 없는 새로운 프로브 출력 내용입니다.';
    const translatedUnknown = helpers.translateProbeText(unknownKorean, 'en');
    assert.equal(translatedUnknown, 'Korean-only probe text (not translated)');
    assert.ok(!/[가-힣]/.test(translatedUnknown), '치환 문구에 한글이 없어야 함');

    // 4. 영어 모드('en') - 영어 문자열은 그대로 통과
    assert.equal(helpers.translateProbeText('claude-3-7-sonnet', 'en'), 'claude-3-7-sonnet');
    assert.equal(helpers.translateProbeText('Already English probe', 'en'), 'Already English probe');

    // 5. 빈 값 / null / undefined 안전성
    assert.equal(helpers.translateProbeText('', 'en'), '');
    assert.equal(helpers.translateProbeText(null, 'en'), null);
    assert.equal(helpers.translateProbeText(undefined, 'en'), undefined);
  });

  test('FE-008 AC4/AC5: snapshot.json 실데이터 기준 en 모드 렌더링 시 한글 0건 검증', () => {
    const snapshotPath = path.resolve(__dirname, '../../../.local/monitor/snapshot.json');
    if (!fs.existsSync(snapshotPath)) {
      // 실데이터 파일이 없으면 테스트 통과
      return;
    }

    const raw = fs.readFileSync(snapshotPath, 'utf8');
    const snapshot = JSON.parse(raw);
    const hangulRegex = /[가-힣]/;

    // 1. agents 배열의 모든 프로브 필드를 translateProbeText(..., 'en') 통과 시 한글 0건 검증
    if (Array.isArray(snapshot.agents)) {
      snapshot.agents.forEach(agent => {
        // 이름, 상태 라벨
        const statusLabel = helpers.formatAgentStatus(agent.status, 'en');
        assert.ok(!hangulRegex.test(statusLabel), `Agent status contains Hangul in en: ${statusLabel}`);

        // notes
        if (Array.isArray(agent.notes)) {
          agent.notes.forEach(note => {
            const translatedNote = helpers.translateProbeText(String(note), 'en');
            assert.ok(!hangulRegex.test(translatedNote), `Agent note contains Hangul in en: ${translatedNote}`);
          });
        }

        // plan name, limits
        if (agent.plan) {
          if (agent.plan.name) {
            const planName = helpers.translateProbeText(agent.plan.name, 'en');
            assert.ok(!hangulRegex.test(planName), `Plan name contains Hangul in en: ${planName}`);
          }
          if (Array.isArray(agent.plan.limits)) {
            agent.plan.limits.forEach(limit => {
              const limLabel = helpers.formatLimitLabel(limit.label, 'en');
              assert.ok(!hangulRegex.test(limLabel), `Limit label contains Hangul in en: ${limLabel}`);
            });
          }
        }

        // models
        if (Array.isArray(agent.models)) {
          agent.models.forEach(m => {
            const modelName = helpers.translateProbeText(m.model, 'en');
            assert.ok(!hangulRegex.test(modelName), `Model name contains Hangul in en: ${modelName}`);
          });
        }

        // KPI 계산
        const kpi = helpers.calculateAgentKpi(agent, snapshot.telemetry, new Date(), 'en');
        if (kpi.maxLimit && kpi.maxLimit.label) {
          assert.ok(!hangulRegex.test(kpi.maxLimit.label), `KPI maxLimit label contains Hangul in en: ${kpi.maxLimit.label}`);
        }
      });
    }

    // 2. skills 데이터 검증
    if (snapshot.skills) {
      if (Array.isArray(snapshot.skills.notes)) {
        snapshot.skills.notes.forEach(note => {
          const transNote = helpers.translateProbeText(String(note), 'en');
          assert.ok(!hangulRegex.test(transNote), `Skill note contains Hangul in en: ${transNote}`);
        });
      }

      if (Array.isArray(snapshot.skills.agents)) {
        snapshot.skills.agents.forEach(ag => {
          if (Array.isArray(ag.skills)) {
            ag.skills.forEach(sk => {
              if (sk.description) {
                const transDesc = helpers.translateProbeText(sk.description, 'en');
                assert.ok(!hangulRegex.test(transDesc), `Skill desc contains Hangul in en: ${transDesc}`);
              }
              if (sk.origin) {
                const transOrigin = helpers.translateProbeText(sk.origin, 'en');
                assert.ok(!hangulRegex.test(transOrigin), `Skill origin contains Hangul in en: ${transOrigin}`);
              }
            });
          }
        });
      }
    }

    // 3. hardware & inference
    if (snapshot.hardware && Array.isArray(snapshot.hardware.inference_server)) {
      snapshot.hardware.inference_server.forEach(item => {
        Object.keys(item).forEach(key => {
          const keyLabel = helpers.formatInferenceKey(key, 'en');
          assert.ok(!hangulRegex.test(keyLabel), `Inference key contains Hangul in en: ${keyLabel}`);
          const valText = helpers.translateProbeText(String(item[key]), 'en');
          assert.ok(!hangulRegex.test(valText), `Inference val contains Hangul in en: ${valText}`);
        });
      });
    }
  });

  test('FE-008 AC4: I18N 사전 ko/en 키 집합 일치성 검사', () => {
    const koKeys = Object.keys(helpers.I18N.ko).sort();
    const enKeys = Object.keys(helpers.I18N.en).sort();
    assert.deepEqual(koKeys, enKeys, 'ko와 en 사전은 동일한 키 집합을 가져야 합니다.');

    // 영어 사전 값에 한글이 없는지 검사
    const hangulRegex = /[가-힣]/;
    enKeys.forEach(k => {
      if (k === 'btnLangToggle') return;
      assert.ok(!hangulRegex.test(helpers.I18N.en[k]), `I18N.en.${k} contains Hangul: ${helpers.I18N.en[k]}`);
    });
  });

});
