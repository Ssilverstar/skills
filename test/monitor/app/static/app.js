/**
 * Agent Observatory Front-End Application
 * Pure Vanilla JavaScript implementation adhering to strict CSP (no inline styles or scripts).
 * Supports Language (ko/en), Theme (dark/light), Sortable Tables, Telemetry Badges, and History Resolution.
 */

// ==========================================
// 1. Pure Functions & i18n (Unit-Testable, No DOM)
// ==========================================

const I18N = {
  ko: {
    // Brand & Navigation
    brandTitle: 'Agent Observatory',
    navAgents: '에이전트 사용량',
    navHardware: '하드웨어·추론',
    navSkills: '스킬 현황',
    titleAgents: '에이전트 사용량',
    titleHardware: '하드웨어·추론',
    titleSkills: '스킬 현황',

    // Status & Header Controls
    navMenuAria: '주 메뉴',
    btnLangAria: '언어 전환',
    btnThemeAria: '테마 전환',
    statusChecking: '수집 확인 중',
    statusHealthy: '수집 정상',
    statusStale: '수집 지연',
    statusWaiting: '수집 대기',
    statusRestored: 'DB 복원본',
    statusError: '수집 오류',
    sidebarChecking: '상태 확인 중...',
    sidebarHealthy: '모니터링 정상',
    sidebarStale: '수집 지연 경고',
    sidebarWaiting: '스냅샷 수집 대기',
    snapshotTime: '스냅샷 시각:',
    btnRefresh: '새로고침',
    btnRefreshTitle: '스냅샷 즉시 새로고침',
    btnLangToggle: 'English',
    btnThemeDark: '🌙 야간',
    btnThemeLight: '☀️ 주간',

    // Banners & Empty States
    staleMsgDefault: '수집 지연: 스냅샷이 최신 상태가 아닙니다.',
    errorMsgDefault: '수집 오류가 발생했습니다.',
    staleBannerPrefix: '수집 지연: 마지막 정상 수집 이후',
    staleBannerSuffix: '가 경과했습니다.',
    staleBannerThreshold: '임계:',
    errorBannerPrefix: '수집 경고:',
    compactedBanner: '목록 로딩 중(이력 복원본) - 다음 수집 주기에 전체 스킬 목록이 복원됩니다.',
    emptyTitle: '스냅샷 수집 대기 중',
    emptyDesc: '호스트 프로브로부터 첫 번째 모니터링 스냅샷을 수집하고 있습니다. 잠시만 기다려 주세요.',
    emptyInterval: '수집 주기: 15초',

    // Agents View
    titleAgentKpi: '에이전트 KPI 요약',
    kpiPrimaryModel: '대표 모델:',
    kpiTotalTokens: '세션 누적 토큰:',
    kpiMaxLimit: '최대 구독 한도:',
    kpiNoLimit: '한도 정보 없음',
    sectionAgentProfiles: '에이전트 프로필 및 구독 한도',
    sectionAgentTokens: '에이전트별 토큰 사용량',
    descAgentTokens: '세션 누적(브리지) 데이터입니다. 입력 토큰은 캐시 읽기/쓰기를 포함하며, 추론 토큰은 출력 토큰의 일부입니다. (중복 합산 금지)',
    sectionModelUsage: '모델별 세부 사용량',
    descModelUsage: '에이전트 내 모델별 세션 누적(브리지) 토큰 현황입니다. 모델 행을 더한 합계 행은 제공하지 않습니다.',

    // Agent Card Details
    detailsSummary: '세부 정보',
    nativeUsageTitle: '네이티브 OTel 최근 24시간 수신',
    nativeLastReceived: '마지막 수신:',
    nativeUsageLimit: 'Prometheus increase() 추정값(외삽)입니다. 처음 받은 값이나 5분 넘게 쉰 뒤 첫 값은 빠질 수 있어 실제보다 적게 보일 수 있습니다.',
    modelPrefix: '모델:',
    planPrefix: '플랜:',
    planHistoricalBadge: '과거 관측(이력)',
    sourcePrefix: '출처:',
    observedPrefix: '관측:',
    lastObservedPrefix: '최종 관측:',
    collectorSourcePrefix: '수집원:',
    noLimitInfo: '한도 정보 없음',
    usedPercentUnknown: '사용률 미확인',
    resetPrefix: '초기화:',
    notesTitle: '참고 사항:',
    telemetryUsagePrefix: '사용량:',
    telemetryQuotaPrefix: '한도:',
    telemetryNative: '네이티브 OTel',
    telemetryBridge: '브리지',
    telemetryUnsupported: '미지원',
    agentObserved: '관측됨',
    agentPartial: '부분 관측',
    agentUnavailable: '미지원/미확인',
    agentUnknown: '미확인',

    // Table Column Headers
    thAgent: '에이전트',
    thModel: '모델',
    thInputTokens: '입력 (캐시 포함)',
    thCachedInput: '캐시 읽기',
    thCacheWrite: '캐시 쓰기',
    thOutputTokens: '출력',
    thReasoningTokens: '추론 (출력 포함)',
    thTotalTokens: '합계',
    thSessions: '세션',
    thShare: '에이전트 내 비중',

    // Hardware View
    cardHost: '호스트 머신',
    cardGpu: 'NVIDIA GPU',
    cardInference: '추론 서버 (Inference)',
    hostHostname: '호스트 이름',
    hostOsArch: '운영체제 / 아키텍처',
    hostKernel: '커널 버전',
    hostCpuCores: 'CPU 코어 수',
    hostCpuUsage: 'CPU 사용률',
    hostMemoryUsage: '메모리 사용량',
    gpuModel: 'GPU 모델',
    gpuDriver: '드라이버 버전',
    gpuUsage: 'GPU 사용률',
    gpuTemp: '온도',
    gpuPower: '전력 사용 / 한도',
    gpuVram: 'GPU 전용 VRAM',
    gpuVramNa: 'N/A (통합 메모리)',
    gpuProcMem: '프로세스 GPU 메모리 합계',
    gpuProcs: 'GPU 사용 프로세스',
    gpuProcsNone: '없음',
    infEndpoint: '엔드포인트',
    infModels: '제공 모델',
    infEngine: '실행 런타임',
    infVersion: '런타임 버전',
    infExecutable: '실행 파일',
    infContainerImage: '컨테이너 이미지',
    infVllmVersion: '이미지 내 vLLM 패키지(미실행)',
    infReachableGood: '도달 가능',
    infReachableCritical: '응답 없음',
    infReachableUnknown: '상태 확인 중',

    // History & Charts
    sectionHistoryCharts: '시계열 추이 (Small Multiples)',
    descHistoryCharts: '호스트 및 GPU 주요 성능 지표의 과거 추이입니다. 데이터 미수집 구간은 선이 연결되지 않습니다.',
    sectionCharts: '시계열 추이 (Small Multiples)',
    descCharts: '호스트 및 GPU 주요 성능 지표의 과거 추이입니다. 데이터 미수집 구간은 선이 연결되지 않습니다.',
    rangeSelectorAria: '조회 시간 범위',
    range1h: '1시간',
    range6h: '6시간',
    range24h: '24시간',
    range7d: '7일',
    range30d: '30일',
    chartGpuUtil: 'GPU 사용률',
    chartGpuTemp: 'GPU 온도',
    chartGpuPower: 'GPU 전력',
    chartHostMem: '호스트 메모리 사용률',
    resRaw: '원본 스냅샷(약 15초)',
    res5m: '5분 집계 · 평균(최소~최대)',
    sectionHistoryTable: '스냅샷 수집 이력 (최근 50건)',
    thCollectedAt: '수집 시각',
    thCpuPercent: 'CPU 사용률',
    thMemPercent: '호스트 메모리',
    thGpuUtil: 'GPU 사용률',
    thGpuTemp: 'GPU 온도',
    thGpuPower: 'GPU 전력',
    thInference: '추론 서버',
    thErrors: '오류 수',
    thSamples: '샘플 수',
    retentionPrefix: '보존 설정:',
    retentionDaysSuffix: '일 보존',
    retentionMaxSuffix: '행',
    retentionMatchedPrefix: '조회:',
    retentionTotalPrefix: '전체 DB:',

    // Skills View
    sectionSkillsSummary: '에이전트별 스킬 개요',
    sectionSkillsList: '설치된 스킬 목록',
    descSkillsList: '호출 수는 요청 증거이며 성공 여부가 아닙니다. 미계측은 미사용과 구분됩니다.',
    filterAgentLabel: '에이전트:',
    filterAgentAll: '전체 에이전트',
    filterAgentRepo: '저장소 원본',
    filterSearchLabel: '검색:',
    filterSearchPlaceholder: '이름, 설명, 경로 검색...',
    skillInstalledPrefix: '등록 전체:',
    skillCommonCounts: '공통 선택 {selected} · 설치 {installed}',
    sortTitle: '{label} 정렬',
    skillEnabledPrefix: '활성:',
    thSkillName: '스킬 이름',
    thSkillAgent: '에이전트',
    thSkillStatus: '활성 상태',
    thSkillInvocations: '호출 요청 증거',
    thSkillLastUsed: '마지막 사용',
    thSkillPath: '스킬 경로',
    thSkillOrigin: '출처',
    skillActive: '활성',
    skillInactive: '비활성',
    skillUnmeasured: '미계측',
    skillInvocationsSuffix: '회 요청',
    skillsEmptyRepo: '저장소 원본 스킬 없음 및 등록된 스킬이 없습니다.',
    skillsEmptySearch: '검색 조건과 일치하는 스킬이 없습니다.',
    skillsNotesTitle: '스킬 참고 사항',
    titleSkillsCategoryTable: '에이전트별 스킬 분류 현황',
    thCommonSelected: '공통 선택',
    thCommonDiscovered: '공통 발견',
    thCommonActive: '공통 활성',
    thPlatformAdded: '플랫폼 추가',
    thInactive: '비활성',
    thUnconfirmed: '미확인',
    thRegisteredTotal: '등록 전체',
    thEnabledTotal: '활성',
    titleMcpSection: 'MCP 서버 현황',
    titleMcpSummary: '에이전트별 MCP 요약',
    titleMcpStatusTable: 'MCP 서버 상세 현황',
    mcpEmptyDesc: 'MCP 미확인',
    notComparableTooltip: '비교 대상 아님',
    labelCommonSelected: '공통 선택',
    labelCommonDiscovered: '공통 발견',
    labelCommonActive: '공통 활성',
    labelPlatformAdded: '플랫폼 추가',
    labelInactive: '비활성',
    labelUnconfirmed: '미확인',
    thMcpServer: '서버 이름',
    thMcpScope: '범위',
    thMcpConfigured: '설정',
    thMcpEnabled: '활성',
    thMcpStatus: '상태',
    thMcpTools: '도구 수',
    thMcpCheckedAt: '확인 시각',
    thMcpNote: '비고',
    mcpScopeCommon: '공통',
    mcpScopePlatform: '플랫폼',
    mcpConfiguredYes: '설정됨',
    mcpConfiguredNo: '미설정',
    mcpStatusConnected: '연결 확인(디스커버리)',
    mcpStatusConfigured: '설정만 확인',
    mcpStatusError: '오류',
    mcpStatusUnverified: '미확인',
    mcpCommonConfigured: '공통 설정',
    mcpCommonConnected: '공통 연결',
    mcpPlatformAdded: '플랫폼 추가',
    mcpErrorsCount: '{n}건 오류',

    // Relative Time & Generic
    timeJustNow: '방금 전',
    timeSecAgo: '{n}초 전',
    timeMinAgo: '{n}분 전',
    timeHourAgo: '{n}시간 전',
    timeDayAgo: '{n}일 전',
    timeSoon: '곧',
    timeSecFuture: '{n}초 후',
    timeMinFuture: '{n}분 후',
    timeHourFuture: '{n}시간 후',
    timeDayFuture: '{n}일 후',
    unknown: '미확인',
    coresSuffix: '코어'
  },
  en: {
    // Brand & Navigation
    brandTitle: 'Agent Observatory',
    navAgents: 'Agent Usage',
    navHardware: 'Hardware & Inference',
    navSkills: 'Skills Status',
    titleAgents: 'Agent Usage',
    titleHardware: 'Hardware & Inference',
    titleSkills: 'Skills Status',

    // Status & Header Controls
    navMenuAria: 'Main Menu',
    btnLangAria: 'Switch language',
    btnThemeAria: 'Toggle theme',
    statusChecking: 'Checking',
    statusHealthy: 'Healthy',
    statusStale: 'Stale',
    statusWaiting: 'Waiting',
    statusRestored: 'Restored',
    statusError: 'Collection error',
    sidebarChecking: 'Checking status...',
    sidebarHealthy: 'Monitoring Healthy',
    sidebarStale: 'Collection Stale Warning',
    sidebarWaiting: 'Awaiting Snapshot',
    snapshotTime: 'Snapshot Time:',
    btnRefresh: 'Refresh',
    btnRefreshTitle: 'Refresh snapshot now',
    btnLangToggle: 'Korean',
    btnThemeDark: '🌙 Dark',
    btnThemeLight: '☀️ Light',

    // Banners & Empty States
    staleMsgDefault: 'Collection stale: snapshot is not up to date.',
    errorMsgDefault: 'Collection error occurred.',
    staleBannerPrefix: 'Collection stale: ',
    staleBannerSuffix: ' have passed since last regular collection.',
    staleBannerThreshold: 'Threshold:',
    errorBannerPrefix: 'Collection warning:',
    compactedBanner: 'Loading list (from restored history) - complete skill list will be restored in next cycle.',
    emptyTitle: 'Awaiting Snapshot Collection',
    emptyDesc: 'Collecting the first monitoring snapshot from the host probe. Please wait a moment.',
    emptyInterval: 'Polling Interval: 15s',

    // Agents View
    titleAgentKpi: 'Agent KPI Summary',
    kpiPrimaryModel: 'Primary Model:',
    kpiTotalTokens: 'Session Tokens:',
    kpiMaxLimit: 'Max Limit:',
    kpiNoLimit: 'No limit info',
    sectionAgentProfiles: 'Agent Profiles & Subscription Limits',
    sectionAgentTokens: 'Token Usage by Agent',
    descAgentTokens: 'Session accumulated (bridge) data. Input tokens include cache reads/writes. Reasoning tokens are a subset of output tokens. (No duplicate sum)',
    sectionModelUsage: 'Detailed Usage by Model',
    descModelUsage: 'Session accumulated (bridge) token breakdown by model. No summed total row is provided.',

    // Agent Card Details
    detailsSummary: 'Details',
    nativeUsageTitle: 'Native OTel · last 24h',
    nativeLastReceived: 'Last received:',
    nativeUsageLimit: 'Estimated by Prometheus increase() (extrapolated). The first value received, or the first after a 5+ minute gap, can be missed, so totals may read low.',
    modelPrefix: 'Model:',
    planPrefix: 'Plan:',
    planHistoricalBadge: 'Historical Obs',
    sourcePrefix: 'Source:',
    observedPrefix: 'Observed:',
    lastObservedPrefix: 'Last Obs:',
    collectorSourcePrefix: 'Origin:',
    noLimitInfo: 'No limit info',
    usedPercentUnknown: 'Usage unknown',
    resetPrefix: 'Reset:',
    notesTitle: 'Notes:',
    telemetryUsagePrefix: 'Usage:',
    telemetryQuotaPrefix: 'Quota:',
    telemetryNative: 'Native OTel',
    telemetryBridge: 'Bridge',
    telemetryUnsupported: 'Unsupported',
    agentObserved: 'Observed',
    agentPartial: 'Partial',
    agentUnavailable: 'Unavailable',
    agentUnknown: 'Unknown',

    // Table Column Headers
    thAgent: 'Agent',
    thModel: 'Model',
    thInputTokens: 'Input (incl. Cache)',
    thCachedInput: 'Cache Read',
    thCacheWrite: 'Cache Write',
    thOutputTokens: 'Output',
    thReasoningTokens: 'Reasoning (in Output)',
    thTotalTokens: 'Total',
    thSessions: 'Sessions',
    thShare: 'Agent Share',

    // Hardware View
    cardHost: 'Host Machine',
    cardGpu: 'NVIDIA GPU',
    cardInference: 'Inference Server',
    hostHostname: 'Hostname',
    hostOsArch: 'OS / Architecture',
    hostKernel: 'Kernel Version',
    hostCpuCores: 'CPU Cores',
    hostCpuUsage: 'CPU Usage',
    hostMemoryUsage: 'Memory Usage',
    gpuModel: 'GPU Model',
    gpuDriver: 'Driver Version',
    gpuUsage: 'GPU Usage',
    gpuTemp: 'Temperature',
    gpuPower: 'Power Draw / Limit',
    gpuVram: 'Dedicated VRAM',
    gpuVramNa: 'N/A (unified memory)',
    gpuProcMem: 'Process GPU memory (sum)',
    gpuProcs: 'GPU processes',
    gpuProcsNone: 'None',
    infEndpoint: 'Endpoint',
    infModels: 'Served Models',
    infEngine: 'Runtime Engine',
    infVersion: 'Runtime Version',
    infExecutable: 'Executable',
    infContainerImage: 'Container Image',
    infVllmVersion: 'Container vLLM (Unused)',
    infReachableGood: 'Reachable',
    infReachableCritical: 'Unreachable',
    infReachableUnknown: 'Checking',

    // History & Charts
    sectionCharts: 'Metrics History (Small Multiples)',
    descCharts: 'Historical metrics for host and GPU. Gaps indicate uncollected periods.',
    rangeSelectorAria: 'Time range selection',
    sectionHistoryCharts: 'Metrics History (Small Multiples)',
    descHistoryCharts: 'Historical trend of host and GPU performance metrics. Uncollected periods have broken lines.',
    range1h: '1h',
    range6h: '6h',
    range24h: '24h',
    range7d: '7d',
    range30d: '30d',
    chartGpuUtil: 'GPU Util',
    chartGpuTemp: 'GPU Temp',
    chartGpuPower: 'GPU Power',
    chartHostMem: 'Host Memory Usage',
    resRaw: 'Raw snapshot (~15s)',
    res5m: '5m aggregation · Average (Min–Max)',
    sectionHistoryTable: 'Snapshot History (Recent 50)',
    thCollectedAt: 'Collected At',
    thCpuPercent: 'CPU %',
    thMemPercent: 'Host Memory %',
    thGpuUtil: 'GPU Util %',
    thGpuTemp: 'GPU Temp',
    thGpuPower: 'GPU Power',
    thInference: 'Inference',
    thErrors: 'Errors',
    thSamples: 'Samples',
    retentionPrefix: 'Retention:',
    retentionDaysSuffix: 'd retention',
    retentionMaxSuffix: 'rows',
    retentionMatchedPrefix: 'Matched:',
    retentionTotalPrefix: 'DB Total:',

    // Skills View
    sectionSkillsSummary: 'Skills Overview by Agent',
    sectionSkillsList: 'Installed Skills List',
    descSkillsList: 'Invocations represent request evidence, not successes. Unmeasured is distinct from unused.',
    filterAgentLabel: 'Agent:',
    filterAgentAll: 'All Agents',
    filterAgentRepo: 'Repository Origin',
    filterSearchLabel: 'Search:',
    filterSearchPlaceholder: 'Search name, description, path...',
    skillInstalledPrefix: 'Registered (all):',
    skillCommonCounts: 'Common: selected {selected} · installed {installed}',
    sortTitle: 'Sort by {label}',
    skillEnabledPrefix: 'Active:',
    thSkillName: 'Skill Name',
    thSkillAgent: 'Agent',
    thSkillStatus: 'Status',
    thSkillInvocations: 'Request Evidence',
    thSkillLastUsed: 'Last Used',
    thSkillPath: 'Skill Path',
    thSkillOrigin: 'Origin',
    skillActive: 'Active',
    skillInactive: 'Inactive',
    skillUnmeasured: 'Unmeasured',
    skillInvocationsSuffix: 'requests',
    skillsEmptyRepo: 'No repository origin skills and no registered skills.',
    skillsEmptySearch: 'No skills match the search criteria.',
    skillsNotesTitle: 'Skills Notes',
    titleSkillsCategoryTable: 'Skills Breakdown by Agent',
    thCommonSelected: 'Common Selected',
    thCommonDiscovered: 'Common Discovered',
    thCommonActive: 'Common Active',
    thPlatformAdded: 'Platform Added',
    thInactive: 'Inactive',
    thUnconfirmed: 'Unconfirmed',
    thRegisteredTotal: 'Registered Total',
    thEnabledTotal: 'Enabled',
    titleMcpSection: 'MCP Server Status',
    titleMcpSummary: 'MCP Overview by Agent',
    titleMcpStatusTable: 'MCP Server Details',
    mcpEmptyDesc: 'MCP unknown',
    notComparableTooltip: 'Not directly comparable',
    labelCommonSelected: 'Common Selected',
    labelCommonDiscovered: 'Common Discovered',
    labelCommonActive: 'Common Active',
    labelPlatformAdded: 'Platform Added',
    labelInactive: 'Inactive',
    labelUnconfirmed: 'Unconfirmed',
    thMcpServer: 'Server Name',
    thMcpScope: 'Scope',
    thMcpConfigured: 'Configured',
    thMcpEnabled: 'Enabled',
    thMcpStatus: 'Status',
    thMcpTools: 'Tools',
    thMcpCheckedAt: 'Checked At',
    thMcpNote: 'Note',
    mcpScopeCommon: 'Common',
    mcpScopePlatform: 'Platform',
    mcpConfiguredYes: 'Configured',
    mcpConfiguredNo: 'Not configured',
    mcpStatusConnected: 'Connected (discovery)',
    mcpStatusConfigured: 'Configured only',
    mcpStatusError: 'Error',
    mcpStatusUnverified: 'Unverified',
    mcpCommonConfigured: 'Common Configured',
    mcpCommonConnected: 'Common Connected',
    mcpPlatformAdded: 'Platform Added',
    mcpErrorsCount: '{n} error(s)',

    // Relative Time & Generic
    timeJustNow: 'just now',
    timeSecAgo: '{n}s ago',
    timeMinAgo: '{n}m ago',
    timeHourAgo: '{n}h ago',
    timeDayAgo: '{n}d ago',
    timeSoon: 'soon',
    timeSecFuture: 'in {n}s',
    timeMinFuture: 'in {n}m',
    timeHourFuture: 'in {n}h',
    timeDayFuture: 'in {n}d',
    unknown: 'Unknown',
    coresSuffix: 'Cores'
  }
};

const KNOWN_PROBE_TRANSLATIONS = {
  // Plan names
  '로컬 추론': 'Local Inference',
  'Claude Pro': 'Claude Pro',
  'Google AI Pro': 'Google AI Pro',
  'prolite': 'prolite',

  // Usage windows
  '보존된 로컬 이력 전체 · 계정 청구량 아님': 'Complete preserved local history · not account billing',
  '상태줄로 관측된 세션 누적 · 과거 미관측 세션 제외': 'Session accumulated via statusline · excludes past unobserved sessions',

  // Model names
  '세션 누적 · 모델별 분해 미지원': 'Session accumulated · model breakdown unsupported',

  // Limits
  '10080분 한도': 'Weekly (7d)',
  '세션 (과거 관측)': 'Session (Historical Obs)',

  // GPU Memory Notes
  'GB10 공유 메모리: 전용 VRAM 카운터 미지원': 'GB10 shared memory: Dedicated VRAM counter unsupported',

  // Agent Notes
  '캐시 읽기는 입력 토큰에 포함. 추론은 출력에 포함. 중복 합산하지 않음.': 'Cache reads included in input. Reasoning included in output. No duplicate summing.',
  '메시지 ID로 스트리밍 중복 제거. 입력은 일반 입력+캐시 읽기+캐시 쓰기.': 'Streaming deduplication by message ID. Input = prompt + cache read + cache write.',
  '구독 한도는 네이티브 상태줄의 마지막 관측값. 활동이 없으면 갱신되지 않으므로 관측 시각 확인.': 'Subscription quota reflects latest statusline observation. Check observation time if inactive.',
  '로컬 이력은 공급자가 바뀐 과거 모델도 포함할 수 있음.': 'Local history may include previous models across provider changes.',
  '토큰 비용과 GPU 전력 비용은 별도.': 'Token cost and GPU power cost are tracked separately.',
  '네이티브 상태줄이 관측한 세션 누적 입력/출력을 사용. 과거 미관측 세션은 포함되지 않음.': 'Uses session accumulated input/output from native statusline. Excludes past unobserved sessions.',
  '모델별 이력 분해·누적 캐시 토큰은 미지원. 현재 선택 모델과 세션 전체 토큰을 구분.': 'Model breakdown and cumulative cache tokens unsupported. Distinguishes active model from total session.',
  '표시 모델은 로컬 설정값이며 사용량 측정 모델을 추정한 값이 아닙니다.': 'Displayed model is local config, not an inference-measured estimate.',

  // Skills Notes & Usage evidence
  '저장소 원본과 외부 스킬 등록부는 별개입니다. 외부 등록 목록: skills/README.md': 'Repository source and external registry are distinct. External list: skills/README.md',
  '등록 목록과 build 에이전트의 최종 허용 목록은 다릅니다. 명시 규칙 외 활성 여부는 미확인입니다.': 'Registry list differs from build agent allowlist. Non-explicit active state is unverified.',
  '파일 존재·활성 설정·호출 요청은 다른 증거입니다. 미계측은 미사용이 아닙니다.': 'File existence, active config, and invocation requests are distinct evidence. Unmeasured is not unused.',
  '로컬 로그의 호출 요청 · 성공/완주 여부 별도': 'Invocation requests from local logs · success/completion tracked separately',
  '호출 집계 미계측': 'Invocation count unmeasured',

  // Probe strings & Status
  '호스트 OS': 'Host OS',
  '5시간': '5h',
  '10080분 한도': 'Weekly limit',
  '부분 관측': 'Partially Observed',
  '정상': 'Healthy',

  // Tooltip
  '비교 대상 아님': 'Not directly comparable'
};

function translateProbeText(text, lang = 'ko') {
  if (lang !== 'en') return text;
  if (text === null || text === undefined) return text;
  if (typeof text !== 'string') return text;
  if (!/[가-힣]/.test(text)) return text;
  const trimmed = text.trim();
  if (KNOWN_PROBE_TRANSLATIONS[trimmed]) {
    return KNOWN_PROBE_TRANSLATIONS[trimmed];
  }
  if (KNOWN_PROBE_TRANSLATIONS[text]) {
    return KNOWN_PROBE_TRANSLATIONS[text];
  }
  return 'Korean-only probe text (not translated)';
}

function selectPrimaryModel(input, lang = 'ko') {
  if (!input) return null;
  const models = Array.isArray(input) ? input : (Array.isArray(input.models) ? input.models : []);
  let maxModel = null;
  let maxTokens = -1;
  for (const m of models) {
    if (!m) continue;
    let tok = typeof m.total_tokens === 'number' ? m.total_tokens : null;
    if (tok === null && m.usage && typeof m.usage.total_tokens === 'number') {
      tok = m.usage.total_tokens;
    }
    if (tok === null && typeof m.input_tokens === 'number' && typeof m.output_tokens === 'number') {
      tok = m.input_tokens + m.output_tokens;
    }
    if (tok === null && m.usage && typeof m.usage.input_tokens === 'number' && typeof m.usage.output_tokens === 'number') {
      tok = m.usage.input_tokens + m.usage.output_tokens;
    }
    if (tok !== null && tok > maxTokens && tok > 0) {
      maxTokens = tok;
      maxModel = m.model;
    }
  }
  if (maxModel) return maxModel;
  if (!Array.isArray(input) && input.model) return input.model;
  return null;
}

function selectMaxLimit(input, lang = 'ko') {
  if (!input) return null;
  const limits = Array.isArray(input) ? input : (Array.isArray(input.limits) ? input.limits : []);
  if (limits.length === 0) return null;
  let maxLim = null;
  let maxPct = -Infinity;
  for (const lim of limits) {
    if (!lim) continue;
    const pct = typeof lim.used_percent === 'number' ? lim.used_percent : (lim.used_percent !== null && !isNaN(parseFloat(lim.used_percent)) ? parseFloat(lim.used_percent) : -Infinity);
    if (pct > maxPct) {
      maxPct = pct;
      maxLim = lim;
    }
  }
  if (!maxLim || maxPct === -Infinity) return limits[0];
  return maxLim;
}

function calculateAgentKpi(agent, telemetry = {}, now = new Date(), lang = 'ko') {
  const dict = I18N[lang] || I18N.ko;
  if (!agent || typeof agent !== 'object') return null;

  const status = formatAgentStatus(agent.status, lang);
  const observedAge = agent.observed_at ? formatRelativeTime(agent.observed_at, now, lang) : dict.unknown;
  const rawModel = selectPrimaryModel(agent, lang);
  const primaryModel = rawModel ? translateProbeText(rawModel, lang) : dict.unknown;

  const totalTokensNum = agent.usage && typeof agent.usage.total_tokens === 'number' ? agent.usage.total_tokens : null;
  const totalTokens = formatTokens(totalTokensNum, lang);

  const maxLim = selectMaxLimit(agent.plan, lang);
  let limitInfo = null;
  if (maxLim) {
    const rawLabel = maxLim.label || '';
    const label = formatLimitLabel(rawLabel, lang);
    const usedPercent = formatPercent(maxLim.used_percent, 1, lang);
    const resetAt = maxLim.reset_at ? formatRelativeTime(maxLim.reset_at, now, lang) : null;
    const isHistorical = isHistoricalPlan(agent.plan, now);
    limitInfo = {
      label,
      rawLabel: lang === 'en' ? translateProbeText(rawLabel, 'en') : rawLabel,
      usedPercent,
      usedPercentNum: maxLim.used_percent,
      resetAt,
      isHistorical
    };
  }

  const telem = (telemetry && telemetry[agent.id]) || {};
  const usageMode = telem.usage ? formatTelemetryMode(telem.usage, lang) : null;
  const quotaMode = telem.quota ? formatTelemetryMode(telem.quota, lang) : null;

  return {
    id: agent.id,
    name: agent.name || agent.id,
    status,
    rawStatus: agent.status,
    observedAge,
    primaryModel,
    totalTokens,
    limitInfo,
    maxLimit: limitInfo,
    telemetry: {
      usage: usageMode,
      quota: quotaMode
    },
    usageTelemetryMode: usageMode ? usageMode.text : null,
    quotaTelemetryMode: quotaMode ? quotaMode.text : null
  };
}

const REPO_FILTER_VALUE = '__repository__';

function calculateSkillBreakdown(agentSkills, lang = 'ko') {
  const dict = I18N[lang] || I18N.ko;
  const isObj = agentSkills && typeof agentSkills === 'object';
  const agentName = isObj && agentSkills.agent ? agentSkills.agent : dict.unknown;
  const commonSelected = isObj && typeof agentSkills.common_selected_count === 'number'
    ? agentSkills.common_selected_count : null;
  const commonDiscovered = isObj && typeof agentSkills.common_installed_count === 'number'
    ? agentSkills.common_installed_count : null;
  const registeredTotal = isObj && typeof agentSkills.installed_count === 'number'
    ? agentSkills.installed_count : null;
  const enabledTotal = isObj && typeof agentSkills.enabled_count === 'number'
    ? agentSkills.enabled_count : null;
  // 통합 수정(Claude, api.md v2.5): 프로브 계수가 있으면 우선(압축본에서도 유지), 없을 때만 목록 계산
  // 필드가 있으면(명시적 null=미확인 포함) 프로브 값을 그대로 쓰고, 필드가 없을 때만 목록으로 계산한다
  const hasProbeCommon = isObj && Object.prototype.hasOwnProperty.call(agentSkills, 'common_enabled_count');
  const hasProbeExtra = isObj && Object.prototype.hasOwnProperty.call(agentSkills, 'platform_extra_count');
  const probeCommonActive = hasProbeCommon && typeof agentSkills.common_enabled_count === 'number'
    ? agentSkills.common_enabled_count : null;
  const probePlatformExtra = hasProbeExtra && typeof agentSkills.platform_extra_count === 'number'
    ? agentSkills.platform_extra_count : null;

  const isCompacted = !isObj || agentSkills.compacted === true || !Array.isArray(agentSkills.skills);

  if (isCompacted) {
    return {
      agent: agentName,
      compacted: true,
      isCompacted: true,
      common_selected: commonSelected,
      commonSelected,
      common_discovered: commonDiscovered,
      commonDiscovered,
      common_active: probeCommonActive,
      commonActive: probeCommonActive,
      platform_added: probePlatformExtra,
      platformAdded: probePlatformExtra,
      inactive: null,
      unconfirmed: null,
      unknown: null,
      installed_total: registeredTotal,
      registered_total: registeredTotal,
      registeredTotal,
      enabled_total: enabledTotal,
      enabledTotal
    };
  }

  const skills = agentSkills.skills;
  const activeCommonIds = new Set();
  let platformAdded = 0;
  let inactive = 0;
  let unknown = 0;

  for (const s of skills) {
    if (!s || typeof s !== 'object') continue;
    const isCommon = Boolean(s.common_id);
    if (s.enabled === true) {
      if (isCommon) {
        activeCommonIds.add(s.common_id);
      } else {
        platformAdded++;
      }
    } else if (s.enabled === false) {
      inactive++;
    } else {
      unknown++;
    }
  }

  const commonActive = hasProbeCommon ? probeCommonActive : activeCommonIds.size;
  if (hasProbeExtra) platformAdded = probePlatformExtra;

  return {
    agent: agentName,
    compacted: false,
    isCompacted: false,
    common_selected: commonSelected,
    commonSelected,
    common_discovered: commonDiscovered,
    commonDiscovered,
    common_active: commonActive,
    commonActive,
    platform_added: platformAdded,
    platformAdded,
    inactive,
    unconfirmed: unknown,
    unknown,
    installed_total: registeredTotal,
    registered_total: registeredTotal,
    registeredTotal,
    enabled_total: enabledTotal,
    enabledTotal
  };
}

function formatMcpStatus(status, lang = 'ko') {
  const dict = I18N[lang] || I18N.ko;
  const s = String(status || '').toLowerCase().trim();
  if (s === 'connected') {
    return { label: dict.mcpStatusConnected, className: 'badge-good', icon: '✓' };
  }
  if (s === 'configured') {
    return { label: dict.mcpStatusConfigured, className: 'badge-info', icon: '⚙️' };
  }
  if (s === 'error') {
    return { label: dict.mcpStatusError, className: 'badge-critical', icon: '⚠️' };
  }
  if (s === 'unverified') {
    return { label: dict.mcpStatusUnverified, className: 'badge-muted', icon: '?' };
  }
  if (!status) {
    return { label: dict.unknown, className: 'badge-muted', icon: '?' };
  }
  return { label: String(status), className: 'badge-muted', icon: '❓' };
}

function formatMcpScope(scope, lang = 'ko') {
  const dict = I18N[lang] || I18N.ko;
  if (scope === 'common') return dict.mcpScopeCommon;
  if (scope === 'platform') return dict.mcpScopePlatform;
  return scope || dict.unknown;
}

function calculateMcpSummary(mcpData, lang = 'ko') {
  const dict = I18N[lang] || I18N.ko;
  if (!mcpData || typeof mcpData !== 'object') {
    return null;
  }

  const commonServers = Array.isArray(mcpData.common_servers) ? mcpData.common_servers : [];
  const commonTotal = commonServers.length;
  const agentEntries = Array.isArray(mcpData.agents) ? mcpData.agents : [];

  // 통합 수정(Claude): 실제 호스트 id(api.md v2.4). 'gemini'는 존재하지 않는 id라 가짜 5번째 카드를 만들었다
  const defaultAgentIds = ['codex', 'claude', 'opencode', 'antigravity'];
  const agentMap = new Map();
  agentEntries.forEach(ae => {
    if (ae && ae.agent) {
      agentMap.set(ae.agent.toLowerCase(), ae);
    }
  });

  const allAgentIds = [...defaultAgentIds];
  agentEntries.forEach(ae => {
    if (ae && ae.agent && !allAgentIds.includes(ae.agent.toLowerCase())) {
      allAgentIds.push(ae.agent.toLowerCase());
    }
  });

  const agents = allAgentIds.map(agentId => {
    const entry = agentMap.get(agentId);
    if (!entry) {
      return {
        agent: agentId,
        isMissing: true,
        commonConfiguredText: dict.unknown,
        commonConnectedText: dict.unknown,
        platformAddedText: dict.unknown,
        commonConfigured: null,
        commonTotal,
        commonConnected: null,
        platformAdded: null,
        errorCount: null,
        servers: []
      };
    }

    const servers = Array.isArray(entry.servers) ? entry.servers : [];
    const commonConfigured = typeof entry.common_configured_count === 'number'
      ? entry.common_configured_count
      : null;

    let commonConnected = 0;
    let platformAdded = 0;
    let errorCount = 0;

    for (const s of servers) {
      if (!s || typeof s !== 'object') continue;
      const isPlatform = s.scope === 'platform';
      const isCommon = s.scope === 'common' || !isPlatform;

      if (isCommon && s.status === 'connected') {
        commonConnected++;
      }
      if (isPlatform) {
        platformAdded++;
      }
      if (s.status === 'error') {
        errorCount++;
      }
    }

    const commonConfiguredText = commonConfigured !== null && commonTotal > 0
      ? `${commonConfigured}/${commonTotal}`
      : (commonConfigured !== null ? String(commonConfigured) : dict.unknown);

    return {
      agent: entry.agent || agentId,
      isMissing: false,
      commonConfigured,
      commonTotal,
      commonConfiguredText,
      commonConnected,
      commonConnectedText: String(commonConnected),
      platformAdded,
      platformAddedText: String(platformAdded),
      errorCount,
      servers
    };
  });

  return {
    commonServers,
    commonTotal,
    observedAt: mcpData.observed_at || null,
    agents
  };
}

function formatValue(val, lang = 'ko') {
  const dict = I18N[lang] || I18N.ko;
  if (val === null || val === undefined) return dict.unknown;
  if (typeof val === 'number') {
    if (isNaN(val)) return dict.unknown;
    if (val === 0) return '0';
    return val.toLocaleString(lang === 'ko' ? 'ko-KR' : 'en-US');
  }
  return String(val);
}

function formatPercent(val, decimals = 1, lang = 'ko') {
  const dict = I18N[lang] || I18N.ko;
  if (val === null || val === undefined || isNaN(val)) return dict.unknown;
  if (val === 0) return '0%';
  return `${Number(val).toFixed(decimals)}%`;
}

function formatBytes(bytes, lang = 'ko') {
  const dict = I18N[lang] || I18N.ko;
  if (bytes === null || bytes === undefined || isNaN(bytes)) return dict.unknown;
  if (bytes === 0) return '0 B';
  const units = ['B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB'];
  let b = Math.abs(bytes);
  let i = 0;
  while (b >= 1024 && i < units.length - 1) {
    b /= 1024;
    i++;
  }
  const formatted = i === 0 ? b.toString() : b.toFixed(2);
  return `${bytes < 0 ? '-' : ''}${formatted} ${units[i]}`;
}

function formatTokens(tokens, lang = 'ko') {
  const dict = I18N[lang] || I18N.ko;
  if (tokens === null || tokens === undefined || isNaN(tokens)) {
    return { text: dict.unknown, full: dict.unknown };
  }
  if (tokens === 0) {
    return { text: '0', full: '0' };
  }
  const full = tokens.toLocaleString(lang === 'ko' ? 'ko-KR' : 'en-US');
  let text = full;
  const abs = Math.abs(tokens);

  if (lang === 'ko') {
    if (abs >= 100000000) {
      const val = (tokens / 100000000).toFixed(2);
      text = `${val.replace(/\.?0+$/, '')}억`;
    } else if (abs >= 10000) {
      const val = Math.round(tokens / 10000).toLocaleString('ko-KR');
      text = `${val}만`;
    }
  } else {
    // English K/M/B abbreviations
    if (abs >= 1000000000) {
      text = `${(tokens / 1000000000).toFixed(1).replace(/\.0$/, '')}B`;
    } else if (abs >= 1000000) {
      text = `${(tokens / 1000000).toFixed(1).replace(/\.0$/, '')}M`;
    } else if (abs >= 1000) {
      text = `${(tokens / 1000).toFixed(1).replace(/\.0$/, '')}K`;
    }
  }
  return { text, full };
}

function formatRelativeTime(dateStr, now = new Date(), lang = 'ko') {
  const dict = I18N[lang] || I18N.ko;
  if (!dateStr) return dict.unknown;
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return dict.unknown;
  const nowDate = (now instanceof Date) ? now : new Date(now);
  const diffSec = Math.floor((nowDate.getTime() - d.getTime()) / 1000);

  if (diffSec < 0) {
    // Future
    const futureSec = Math.abs(diffSec);
    if (futureSec < 10) return dict.timeSoon;
    if (futureSec < 60) return dict.timeSecFuture.replace('{n}', futureSec);
    const diffMin = Math.floor(futureSec / 60);
    if (diffMin < 60) return dict.timeMinFuture.replace('{n}', diffMin);
    const diffHour = Math.floor(diffMin / 60);
    if (diffHour < 24) return dict.timeHourFuture.replace('{n}', diffHour);
    const diffDays = Math.floor(diffHour / 24);
    return dict.timeDayFuture.replace('{n}', diffDays);
  }

  // Past
  if (diffSec < 10) return dict.timeJustNow;
  if (diffSec < 60) return dict.timeSecAgo.replace('{n}', diffSec);
  const diffMin = Math.floor(diffSec / 60);
  if (diffMin < 60) return dict.timeMinAgo.replace('{n}', diffMin);
  const diffHour = Math.floor(diffMin / 60);
  if (diffHour < 24) return dict.timeHourAgo.replace('{n}', diffHour);
  const diffDays = Math.floor(diffHour / 24);
  return dict.timeDayAgo.replace('{n}', diffDays);
}

function formatDateTime(dateStr, lang = 'ko') {
  const dict = I18N[lang] || I18N.ko;
  if (!dateStr) return dict.unknown;
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return dict.unknown;
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  const h = String(d.getHours()).padStart(2, '0');
  const min = String(d.getMinutes()).padStart(2, '0');
  const s = String(d.getSeconds()).padStart(2, '0');
  return `${y}-${m}-${day} ${h}:${min}:${s}`;
}

function isHistoricalPlan(plan, now = new Date()) {
  if (!plan) return false;
  const src = String(plan.source || '').toLowerCase();
  const st = String(plan.status || '').toLowerCase();
  if (src.includes('preflight') || src.includes('historical') || st.includes('historical')) {
    return true;
  }
  if (plan.observed_at) {
    const obs = new Date(plan.observed_at);
    if (!isNaN(obs.getTime())) {
      const nowDate = (now instanceof Date) ? now : new Date(now);
      const diffMs = nowDate.getTime() - obs.getTime();
      if (diffMs > 24 * 60 * 60 * 1000) {
        return true;
      }
    }
  }
  return false;
}

function formatAgentStatus(status, lang = 'ko') {
  const dict = I18N[lang] || I18N.ko;
  if (status === 'observed') {
    return { label: dict.agentObserved, className: 'badge-good' };
  }
  if (status === 'partial') {
    return { label: dict.agentPartial, className: 'badge-warning' };
  }
  if (status === 'unavailable') {
    return { label: dict.agentUnavailable, className: 'badge-warning' };
  }
  if (!status) {
    return { label: dict.agentUnknown, className: 'badge-warning' };
  }
  return { label: String(status), className: 'badge-warning' };
}

function formatTelemetryMode(mode, lang = 'ko') {
  const dict = I18N[lang] || I18N.ko;
  if (mode === 'native') return { text: dict.telemetryNative, class: 'badge-good' };
  if (mode === 'bridge') return { text: dict.telemetryBridge, class: 'badge-info' };
  return { text: dict.telemetryUnsupported, class: 'badge-muted' };
}

function formatResolutionLabel(resolution, lang = 'ko') {
  const dict = I18N[lang] || I18N.ko;
  return resolution === '5m' ? dict.res5m : dict.resRaw;
}

function formatLimitDuration(term, lang = 'ko') {
  if (!term || typeof term !== 'string') return term;
  // 통합 수정(Claude): 프로브 라벨 '10080분 한도'처럼 붙는 접미사를 떼고 판정
  const t = term.trim().toLowerCase().replace(/\s*(한도|limit|window)$/, '');
  // 주간(7일) / Weekly (7d)
  if (t === '10080분' || t === '10080 min' || t === '10080m' || t === '10080' ||
      t === 'weekly' || t === 'seven_day' || t === '7d' || t === '7 days' || t === '7day') {
    return lang === 'en' ? 'Weekly (7d)' : '주간(7일)';
  }
  // 5시간 / 5-hour
  if (t === 'five_hour' || t === '5h' || t === '5hr' || t === '5-hour' || t === '5 hours' || t === '5 hour' ||
      t === '300분' || t === '300 min' || t === '300m' || t === '300') {
    return lang === 'en' ? '5-hour' : '5시간';
  }
  return term;
}

function formatLimitLabel(rawLabel, lang = 'ko') {
  if (rawLabel === null || rawLabel === undefined) return '';
  const str = String(rawLabel).trim();
  if (!str) return '';

  const delimiters = [' · ', ' - ', ' : ', ': '];
  for (const delim of delimiters) {
    const idx = str.lastIndexOf(delim);
    if (idx !== -1) {
      const prefix = str.slice(0, idx);
      const suffix = str.slice(idx + delim.length);
      const translatedSuffix = formatLimitDuration(suffix, lang);
      if (translatedSuffix !== suffix) {
        return `${prefix}${delim}${translatedSuffix}`;
      }
    }
  }

  return formatLimitDuration(str, lang);
}

const INFERENCE_KEY_LABELS = {
  ko: {
    observed_at: '관측 시각',
    container_image: '컨테이너 이미지',
    runtime_executable: '실행 파일',
    installed_vllm_version: '이미지 내 vLLM 패키지(미실행)',
    engine: '실행 런타임',
    version: '런타임 버전',
    endpoint: '엔드포인트',
    models: '제공 모델',
    reachable: '도달 가능 여부',
    source: '출처',
    status: '상태'
  },
  en: {
    observed_at: 'Observed at',
    container_image: 'Container Image',
    runtime_executable: 'Executable',
    installed_vllm_version: 'Container vLLM (Unused)',
    engine: 'Runtime Engine',
    version: 'Runtime Version',
    endpoint: 'Endpoint',
    models: 'Served Models',
    reachable: 'Reachability',
    source: 'Source',
    status: 'Status'
  }
};

function formatInferenceKey(key, lang = 'ko') {
  if (key === null || key === undefined) return '';
  const dict = INFERENCE_KEY_LABELS[lang] || INFERENCE_KEY_LABELS.ko;
  return dict[key] || String(key);
}

const CLAUDE_NATIVE_TYPE_LABELS = {
  ko: {
    input: '입력',
    output: '출력',
    cacheRead: '캐시 읽기',
    cacheCreation: '캐시 쓰기'
  },
  en: {
    input: 'input',
    output: 'output',
    cacheRead: 'cacheRead',
    cacheCreation: 'cacheCreation'
  }
};

function formatNativeTokenType(typeKey, agentId = '', lang = 'ko') {
  if (!typeKey) return '';
  const isClaude = String(agentId || '').toLowerCase().includes('claude');
  if (isClaude) {
    const dict = CLAUDE_NATIVE_TYPE_LABELS[lang] || CLAUDE_NATIVE_TYPE_LABELS.ko;
    return dict[typeKey] || String(typeKey);
  }
  // Codex 및 기타: 공급자 원문 라벨 그대로 반환 (번역·합산 금지)
  return String(typeKey);
}

// GPU 프로세스 메모리: 합계와 '이름 크기' 목록. 누락=미확인, 빈 목록=없음.
function formatGpuProcesses(gpu, lang = 'ko') {
  const dict = I18N[lang] || I18N.ko;
  const g = gpu || {};
  const list = Array.isArray(g.compute_processes)
    ? (g.compute_processes.length
      ? g.compute_processes.map(p => `${(p && p.name) || dict.unknown} ${formatBytes(p && p.memory_used_bytes, lang)}`).join(', ')
      : dict.gpuProcsNone)
    : dict.unknown;
  return { total: formatBytes(g.process_memory_used_bytes, lang), list };
}

// 스킬 요약 숫자: 등록 전체 / 활성 / 공통 선택·설치. null·누락은 미확인.
function formatSkillCounts(sa, lang = 'ko') {
  const dict = I18N[lang] || I18N.ko;
  const n = v => (typeof v === 'number' && Number.isFinite(v) ? String(v) : dict.unknown);
  return {
    registered: `${dict.skillInstalledPrefix} ${n(sa && sa.installed_count)}`,
    enabled: `${dict.skillEnabledPrefix} ${n(sa && sa.enabled_count)}`,
    common: dict.skillCommonCounts
      .replace('{selected}', n(sa && sa.common_selected_count))
      .replace('{installed}', n(sa && sa.common_installed_count))
  };
}

function formatNativeUsage(nativeUsage, agentId = '', lang = 'ko') {
  if (!nativeUsage || typeof nativeUsage !== 'object') return null;
  const rawTokens = nativeUsage.tokens;
  if (!rawTokens || typeof rawTokens !== 'object') return null;

  const dict = I18N[lang] || I18N.ko;
  const modelItems = [];

  for (const [model, typesObj] of Object.entries(rawTokens)) {
    if (!typesObj || typeof typesObj !== 'object') continue;
    const items = [];
    for (const [typeKey, val] of Object.entries(typesObj)) {
      if (val === null || val === undefined || typeof val !== 'number' || isNaN(val) || val <= 0) {
        // 증가분 0인 시계열은 제외
        continue;
      }
      const label = formatNativeTokenType(typeKey, agentId, lang);
      const formatted = formatTokens(val, lang);
      items.push({
        rawType: typeKey,
        type: label,
        countText: formatted.text,
        countFull: formatted.full,
        value: val
      });
    }
    if (items.length > 0) {
      modelItems.push({
        model,
        items
      });
    }
  }

  if (modelItems.length === 0) return null;

  let lastReceived = null;
  if (nativeUsage.last_received_at) {
    const relTime = formatRelativeTime(nativeUsage.last_received_at, new Date(), lang);
    lastReceived = `${dict.nativeLastReceived} ${relTime}`;
  }

  return {
    title: dict.nativeUsageTitle,
    lastReceived,
    lastReceivedAt: nativeUsage.last_received_at || null,
    window: nativeUsage.window || '24h',
    limit: dict.nativeUsageLimit,
    models: modelItems
  };
}

function formatChartTime(dateStr, isLongRange = false) {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return '';
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  const h = String(d.getHours()).padStart(2, '0');
  const min = String(d.getMinutes()).padStart(2, '0');
  return isLongRange ? `${m}-${day} ${h}:${min}` : `${h}:${min}`;
}

function calculateChartAxes(points = [], values = [], forcedMin = null, forcedMax = null, unit = '', lang = 'ko') {
  const validNums = (Array.isArray(values) ? values : []).filter(
    v => v !== null && v !== undefined && typeof v === 'number' && !isNaN(v)
  );

  let yMin = (forcedMin !== null && forcedMin !== undefined) ? forcedMin : 0;
  let yMax = (forcedMax !== null && forcedMax !== undefined) ? forcedMax : 100;

  if (forcedMin === null || forcedMax === null) {
    if (validNums.length === 0) {
      yMin = forcedMin !== null ? forcedMin : 0;
      yMax = forcedMax !== null ? forcedMax : (unit === '%' ? 100 : 10);
    } else if (validNums.length === 1) {
      const val = validNums[0];
      if (forcedMin !== null) {
        yMin = forcedMin;
        yMax = forcedMax !== null ? forcedMax : Math.max(val + 1, val * 1.2);
      } else if (forcedMax !== null) {
        yMax = forcedMax;
        yMin = Math.min(val - 1, 0);
      } else {
        yMin = val > 0 ? 0 : val - 5;
        yMax = val > 0 ? Math.ceil(val * 1.2) : 10;
        if (yMin === yMax) yMax = yMin + 1;
      }
    } else {
      const computedMin = Math.min(...validNums);
      const computedMax = Math.max(...validNums);
      yMin = forcedMin !== null ? forcedMin : computedMin;
      yMax = forcedMax !== null ? forcedMax : computedMax;
      if (yMin === yMax) {
        yMax = yMin + (unit === '%' ? 10 : 1);
      }
    }
  }

  const yTicks = {
    min: yMin,
    max: yMax,
    minLabel: `${yMin}${unit}`,
    maxLabel: `${yMax}${unit}`,
    unit
  };

  const validPoints = (Array.isArray(points) ? points : []).map((pt, idx) => ({
    pt,
    idx,
    time: pt && pt.collected_at ? new Date(pt.collected_at).getTime() : NaN
  })).filter(x => !isNaN(x.time));

  let timeTicks = [];
  if (validPoints.length === 0) {
    timeTicks = [];
  } else if (validPoints.length === 1) {
    const single = validPoints[0];
    timeTicks = [{
      index: single.idx,
      xRatio: 0.5,
      label: formatChartTime(single.pt.collected_at, false)
    }];
  } else {
    const first = validPoints[0];
    const last = validPoints[validPoints.length - 1];
    const spanMs = Math.abs(last.time - first.time);
    const isLongRange = spanMs > 24 * 60 * 60 * 1000;

    const midIdx = Math.floor((validPoints.length - 1) / 2);
    const mid = validPoints[midIdx];
    const totalSpan = points.length > 1 ? (points.length - 1) : 1;

    timeTicks = [
      {
        index: first.idx,
        xRatio: first.idx / totalSpan,
        label: formatChartTime(first.pt.collected_at, isLongRange)
      },
      {
        index: mid.idx,
        xRatio: mid.idx / totalSpan,
        label: formatChartTime(mid.pt.collected_at, isLongRange)
      },
      {
        index: last.idx,
        xRatio: last.idx / totalSpan,
        label: formatChartTime(last.pt.collected_at, isLongRange)
      }
    ];
  }

  return { yTicks, timeTicks };
}

function calculateSvgPath(values, width = 300, height = 100, padding = 10, yMin = null, yMax = null) {
  if (!Array.isArray(values) || values.length === 0) {
    return { d: '', points: [], min: 0, max: 0 };
  }
  const nums = values.filter(v => v !== null && v !== undefined && typeof v === 'number' && !isNaN(v));
  if (nums.length === 0) {
    return { d: '', points: [], min: 0, max: 0 };
  }
  const min = (yMin !== null) ? yMin : Math.min(...nums);
  const max = (yMax !== null) ? yMax : Math.max(...nums);
  const range = (max - min) === 0 ? 1 : (max - min);

  const padLeft = typeof padding === 'object' && padding !== null ? (padding.left !== undefined ? padding.left : 10) : padding;
  const padRight = typeof padding === 'object' && padding !== null ? (padding.right !== undefined ? padding.right : 10) : padding;
  const padTop = typeof padding === 'object' && padding !== null ? (padding.top !== undefined ? padding.top : 10) : padding;
  const padBottom = typeof padding === 'object' && padding !== null ? (padding.bottom !== undefined ? padding.bottom : 10) : padding;

  const innerW = width - padLeft - padRight;
  const innerH = height - padTop - padBottom;
  const stepX = values.length > 1 ? innerW / (values.length - 1) : 0;

  let d = '';
  let inSegment = false;
  const pointCoords = [];

  for (let i = 0; i < values.length; i++) {
    const v = values[i];
    const x = padLeft + i * stepX;
    if (v === null || v === undefined || typeof v !== 'number' || isNaN(v)) {
      inSegment = false;
      pointCoords.push({ x, y: null, value: null, index: i });
    } else {
      const normalized = (v - min) / range;
      const y = height - padBottom - (normalized * innerH);
      pointCoords.push({ x, y, value: v, index: i });
      if (!inSegment) {
        d += (d ? ' ' : '') + `M ${x.toFixed(1)} ${y.toFixed(1)}`;
        inSegment = true;
      } else {
        d += ` L ${x.toFixed(1)} ${y.toFixed(1)}`;
      }
    }
  }
  return { d, points: pointCoords, min, max };
}

// Table Sorting Logic (Stable sort, null always at bottom)
function compareValues(a, b, type, direction, lang = 'ko') {
  const isNilA = a === null || a === undefined || a === '미확인' || a === '미계측' || a === 'Unknown' || a === 'Unmeasured';
  const isNilB = b === null || b === undefined || b === '미확인' || b === '미계측' || b === 'Unknown' || b === 'Unmeasured';

  if (isNilA && isNilB) return 0;
  if (isNilA) return 1; // A to bottom
  if (isNilB) return -1; // B to bottom

  let cmp = 0;
  if (type === 'number') {
    const numA = typeof a === 'number' ? a : parseFloat(a);
    const numB = typeof b === 'number' ? b : parseFloat(b);
    if (isNaN(numA) && isNaN(numB)) cmp = 0;
    else if (isNaN(numA)) return 1;
    else if (isNaN(numB)) return -1;
    else cmp = numA - numB;
  } else if (type === 'date') {
    const dateA = a ? new Date(a).getTime() : NaN;
    const dateB = b ? new Date(b).getTime() : NaN;
    if (isNaN(dateA) && isNaN(dateB)) cmp = 0;
    else if (isNaN(dateA)) return 1;
    else if (isNaN(dateB)) return -1;
    else cmp = dateA - dateB;
  } else {
    // string
    const collator = new Intl.Collator(lang === 'en' ? 'en-US' : 'ko-KR', { numeric: true, sensitivity: 'base' });
    cmp = collator.compare(String(a), String(b));
  }

  return direction === 'desc' ? -cmp : cmp;
}

function sortTableData(items, keyExtractor, type, direction, lang = 'ko') {
  if (!Array.isArray(items)) return [];
  const indexed = items.map((item, idx) => ({ item, idx, val: keyExtractor(item) }));
  indexed.sort((x, y) => {
    const diff = compareValues(x.val, y.val, type, direction, lang);
    return diff !== 0 ? diff : x.idx - y.idx;
  });
  return indexed.map(x => x.item);
}


// ==========================================
// 2. Browser DOM & Application Logic
// ==========================================

(function initBrowserApp() {
  if (typeof window === 'undefined') return;

  function safeStorageGet(key, fallback) {
    try {
      return localStorage.getItem(key) || fallback;
    } catch (_) {
      return fallback;
    }
  }

  function safeStorageSet(key, value) {
    try {
      localStorage.setItem(key, value);
    } catch (_) {}
  }

  // Application State
  const state = {
    lang: safeStorageGet('agent_obs_lang', 'ko'),
    theme: safeStorageGet('agent_obs_theme', 'dark'),
    currentRoute: 'agents',
    snapshotState: null,
    historyData: null,
    historyHours: 24,
    skillsFilterAgent: 'ALL',
    skillsSearchQuery: '',
    pollTimer: null,
    sortState: {
      tokens: { col: 'name', dir: 'asc' },
      models: { col: 'agent', dir: 'asc' },
      history: { col: 'collected_at', dir: 'desc' },
      skills: { col: 'name', dir: 'asc' },
      skillsCategory: { col: 'agent', dir: 'asc' },
      mcp: { col: 'agent', dir: 'asc' }
    }
  };

  function t(key, params) {
    const dict = I18N[state.lang] || I18N.ko;
    let str = dict[key] !== undefined ? dict[key] : key;
    if (params) {
      for (const [k, v] of Object.entries(params)) {
        str = str.replace(new RegExp(`\\{${k}\\}`, 'g'), v);
      }
    }
    return str;
  }

  // DOM creation helper (Strict XSS prevention)
  function el(tag, attrs = {}, children = []) {
    const elem = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) {
      if (k === 'class' || k === 'className') {
        elem.className = v;
      } else if (k === 'textContent') {
        elem.textContent = v;
      } else if (k.startsWith('data-') || k.startsWith('aria-') || k === 'id' || k === 'href' || k === 'title' || k === 'role' || k === 'type' || k === 'for' || k === 'value' || k === 'placeholder') {
        elem.setAttribute(k, v);
      }
    }
    if (attrs.textContent !== undefined) {
      return elem;
    }
    // 통합 수정(Claude): attrs.children도 받는다(MCP 표 Agent 열·모델 점유율 라벨이 비어 보이던 원인)
    const kids = Array.isArray(attrs.children) ? attrs.children.concat(children) : children;
    for (const child of kids) {
      if (child === null || child === undefined) continue;
      if (typeof child === 'string' || typeof child === 'number') {
        elem.appendChild(document.createTextNode(String(child)));
      } else if (child instanceof Node) {
        elem.appendChild(child);
      }
    }
    return elem;
  }

  function createProgressBar(percent, statusClass = '') {
    if (percent === null || percent === undefined || isNaN(percent)) {
      return el('span', { class: 'text-muted', textContent: t('unknown') });
    }
    const p = Math.min(100, Math.max(0, Number(percent)));
    const track = el('div', { class: 'progress-track' });
    const fill = el('div', { class: `progress-fill ${statusClass}`.trim() });
    fill.style.width = `${p.toFixed(1)}%`;
    track.appendChild(fill);
    return track;
  }

  // Theme & Language Setters
  function applyTheme(theme) {
    state.theme = theme === 'light' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', state.theme);
    safeStorageSet('agent_obs_theme', state.theme);
    const btn = document.getElementById('btn-toggle-theme');
    if (btn) {
      btn.textContent = state.theme === 'dark' ? t('btnThemeLight') : t('btnThemeDark');
    }
  }

  function applyLang(lang) {
    state.lang = lang === 'en' ? 'en' : 'ko';
    document.documentElement.setAttribute('lang', state.lang);
    safeStorageSet('agent_obs_lang', state.lang);

    const btnLang = document.getElementById('btn-toggle-lang');
    if (btnLang) {
      btnLang.textContent = state.lang === 'ko' ? 'English' : 'Korean';
      btnLang.setAttribute('aria-label', t('btnLangAria'));
    }
    const btnTheme = document.getElementById('btn-toggle-theme');
    if (btnTheme) {
      btnTheme.textContent = state.theme === 'dark' ? t('btnThemeLight') : t('btnThemeDark');
      btnTheme.setAttribute('aria-label', t('btnThemeAria'));
    }

    updateStaticI18n();
    renderRoute();
    if (state.snapshotState) {
      renderSnapshot();
    }
  }

  function updateStaticI18n() {
    // 1. Text content via data-i18n
    document.querySelectorAll('[data-i18n]').forEach(node => {
      const key = node.getAttribute('data-i18n');
      if (key) {
        node.textContent = t(key);
      }
    });

    // 2. Aria-labels via data-i18n-aria
    document.querySelectorAll('[data-i18n-aria]').forEach(node => {
      const key = node.getAttribute('data-i18n-aria');
      if (key) {
        node.setAttribute('aria-label', t(key));
      }
    });

    // 3. Titles via data-i18n-title
    document.querySelectorAll('[data-i18n-title]').forEach(node => {
      const key = node.getAttribute('data-i18n-title');
      if (key) {
        node.setAttribute('title', t(key));
      }
    });

    // 4. Placeholders via data-i18n-placeholder
    document.querySelectorAll('[data-i18n-placeholder]').forEach(node => {
      const key = node.getAttribute('data-i18n-placeholder');
      if (key) {
        node.setAttribute('placeholder', t(key));
      }
    });

    // Range buttons
    const rangeBtns = document.querySelectorAll('.btn-range');
    rangeBtns.forEach(rb => {
      const hrs = rb.getAttribute('data-hours');
      if (hrs === '1') rb.textContent = t('range1h');
      else if (hrs === '6') rb.textContent = t('range6h');
      else if (hrs === '24') rb.textContent = t('range24h');
      else if (hrs === '168') rb.textContent = t('range7d');
      else if (hrs === '720') rb.textContent = t('range30d');
    });

    const btnRef = document.getElementById('btn-manual-refresh');
    if (btnRef) {
      btnRef.textContent = t('btnRefresh');
      btnRef.setAttribute('title', t('btnRefreshTitle'));
    }

    const btnLang = document.getElementById('btn-toggle-lang');
    if (btnLang) {
      btnLang.textContent = state.lang === 'ko' ? 'English' : 'Korean';
      btnLang.setAttribute('aria-label', t('btnLangAria'));
    }

    const btnTheme = document.getElementById('btn-toggle-theme');
    if (btnTheme) {
      btnTheme.textContent = state.theme === 'dark' ? t('btnThemeLight') : t('btnThemeDark');
      btnTheme.setAttribute('aria-label', t('btnThemeAria'));
    }
  }

  // Routing
  function renderRoute() {
    const rawHash = window.location.hash.replace(/^#/, '');
    const validRoutes = ['agents', 'hardware', 'skills'];
    const targetRoute = validRoutes.includes(rawHash) ? rawHash : 'agents';
    state.currentRoute = targetRoute;

    validRoutes.forEach(r => {
      const link = document.getElementById(`nav-${r}`);
      if (link) {
        if (r === targetRoute) {
          link.classList.add('active');
          link.setAttribute('aria-current', 'page');
        } else {
          link.classList.remove('active');
          link.removeAttribute('aria-current');
        }
      }
    });

    const titleElem = document.getElementById('current-view-title');
    if (titleElem) {
      if (targetRoute === 'agents') titleElem.textContent = t('titleAgents');
      else if (targetRoute === 'hardware') titleElem.textContent = t('titleHardware');
      else if (targetRoute === 'skills') titleElem.textContent = t('titleSkills');
    }

    const isWaiting = state.snapshotState && state.snapshotState.status === 'waiting';
    const viewWaiting = document.getElementById('view-waiting');
    const viewAgents = document.getElementById('view-agents');
    const viewHardware = document.getElementById('view-hardware');
    const viewSkills = document.getElementById('view-skills');

    if (isWaiting) {
      if (viewWaiting) viewWaiting.classList.remove('hidden');
      if (viewAgents) viewAgents.classList.add('hidden');
      if (viewHardware) viewHardware.classList.add('hidden');
      if (viewSkills) viewSkills.classList.add('hidden');
      return;
    }

    if (viewWaiting) viewWaiting.classList.add('hidden');
    if (viewAgents) viewAgents.classList.toggle('hidden', targetRoute !== 'agents');
    if (viewHardware) viewHardware.classList.toggle('hidden', targetRoute !== 'hardware');
    if (viewSkills) viewSkills.classList.toggle('hidden', targetRoute !== 'skills');

    if (targetRoute === 'hardware' && !state.historyData) {
      fetchHistory(state.historyHours);
    }
  }

  // API Fetching
  async function fetchSnapshot() {
    try {
      const resp = await fetch('/api/snapshot');
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();
      state.snapshotState = data;
      renderSnapshot();
      if (state.currentRoute === 'hardware') {
        fetchHistory(state.historyHours);
      }
    } catch (err) {
      renderErrorState(err.message);
    }
  }

  async function fetchHistory(hours = 24) {
    try {
      state.historyHours = hours;
      const resp = await fetch(`/api/history?hours=${encodeURIComponent(hours)}&limit=500`);
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();
      state.historyData = data;
      renderHistory();
    } catch (err) {
      console.error('Failed to fetch history:', err);
    }
  }

  function renderErrorState(msg) {
    const errorBanner = document.getElementById('error-banner');
    const errorMsg = document.getElementById('error-msg');
    if (errorBanner && errorMsg) {
      errorMsg.textContent = `${t('errorBannerPrefix')} ${msg}`;
      errorBanner.classList.remove('hidden');
    }
  }

  // Render Top Status & Snapshot
  function renderSnapshot() {
    const data = state.snapshotState;
    if (!data) return;

    const snap = data.snapshot;
    const status = data.status; // 'waiting' | 'ok' | 'stale'
    const source = data.source; // 'file' | 'history' | null
    const ageSec = data.age_seconds;
    const err = data.error;

    const statusBadge = document.getElementById('status-badge');
    const sourceBadge = document.getElementById('source-badge');
    const sidebarDot = document.getElementById('sidebar-status-dot');
    const sidebarText = document.getElementById('sidebar-status-text');

    if (statusBadge) {
      statusBadge.className = 'badge';
      if (status === 'ok') {
        statusBadge.classList.add('badge-good');
        statusBadge.textContent = t('statusHealthy');
      } else if (status === 'stale') {
        statusBadge.classList.add('badge-warning');
        statusBadge.textContent = t('statusStale');
      } else {
        statusBadge.textContent = t('statusWaiting');
      }
    }

    if (sourceBadge) {
      if (source === 'history') {
        sourceBadge.classList.remove('hidden');
        sourceBadge.textContent = t('statusRestored');
      } else {
        sourceBadge.classList.add('hidden');
      }
    }

    if (sidebarDot && sidebarText) {
      sidebarDot.className = 'status-dot';
      if (status === 'ok') {
        sidebarDot.classList.add('good');
        sidebarText.textContent = t('sidebarHealthy');
      } else if (status === 'stale') {
        sidebarDot.classList.add('warning');
        sidebarText.textContent = t('sidebarStale');
      } else {
        sidebarDot.classList.add('serious');
        sidebarText.textContent = t('sidebarWaiting');
      }
    }

    const collectedAtVal = document.getElementById('collected-at-val');
    const collectedAgeVal = document.getElementById('collected-age-val');
    if (snap && snap.collected_at) {
      if (collectedAtVal) collectedAtVal.textContent = formatDateTime(snap.collected_at, state.lang);
      if (collectedAgeVal) collectedAgeVal.textContent = `(${formatRelativeTime(snap.collected_at, new Date(), state.lang)})`;
    } else {
      if (collectedAtVal) collectedAtVal.textContent = '-';
      if (collectedAgeVal) collectedAgeVal.textContent = '';
    }

    const staleBanner = document.getElementById('stale-banner');
    const staleMsg = document.getElementById('stale-msg');
    if (staleBanner && staleMsg) {
      if (status === 'stale') {
        staleBanner.classList.remove('hidden');
        const secText = (ageSec !== null && ageSec !== undefined) ? `${Math.round(ageSec)}s` : '';
        staleMsg.textContent = `${t('staleBannerPrefix')} ${secText}${t('staleBannerSuffix')} (${t('staleBannerThreshold')} ${data.stale_after_seconds}s)`;
      } else {
        staleBanner.classList.add('hidden');
      }
    }

    const errorBanner = document.getElementById('error-banner');
    const errorMsg = document.getElementById('error-msg');
    if (errorBanner && errorMsg) {
      if (err) {
        errorBanner.classList.remove('hidden');
        errorMsg.textContent = `${t('errorBannerPrefix')} ${err}`;
      } else {
        errorBanner.classList.add('hidden');
      }
    }

    const compactedBanner = document.getElementById('compacted-banner');
    if (compactedBanner) {
      const isCompacted = snap && snap.skills && snap.skills.compacted === true;
      compactedBanner.classList.toggle('hidden', !isCompacted);
      if (isCompacted) {
        const msg = compactedBanner.querySelector('.alert-msg');
        if (msg) msg.textContent = t('compactedBanner');
      }
    }

    renderRoute();
    if (snap) {
      renderAgentsView(snap);
      renderHardwareView(snap);
      renderSkillsView(snap);
    }
  }

  // ==========================================
  // Sortable Table Header Builder
  // ==========================================
  function setupSortableHeader(tableKey, tableElem, columns, onSortChange) {
    let thead = tableElem.querySelector('thead');
    if (!thead) {
      thead = el('thead');
      tableElem.appendChild(thead);
    }
    thead.textContent = '';
    const tr = el('tr');

    const curSort = state.sortState[tableKey];

    columns.forEach(col => {
      const th = el('th', { scope: 'col' });
      const isSorted = curSort && curSort.col === col.id;
      const dir = isSorted ? curSort.dir : 'none';
      th.setAttribute('aria-sort', dir === 'asc' ? 'ascending' : (dir === 'desc' ? 'descending' : 'none'));

      const btn = el('button', {
        type: 'button',
        class: 'th-sort-btn',
        title: t('sortTitle', { label: t(col.labelKey) })
      });

      btn.appendChild(el('span', { textContent: t(col.labelKey) }));

      let arrow = '↕';
      if (isSorted) {
        arrow = curSort.dir === 'asc' ? '▲' : '▼';
      }
      btn.appendChild(el('span', { class: 'sort-indicator', textContent: arrow }));

      const handleSort = () => {
        if (curSort.col === col.id) {
          curSort.dir = curSort.dir === 'asc' ? 'desc' : 'asc';
        } else {
          curSort.col = col.id;
          curSort.dir = (col.type === 'number' || col.type === 'date') ? 'desc' : 'asc';
        }
        setupSortableHeader(tableKey, tableElem, columns, onSortChange);
        onSortChange();
      };

      btn.addEventListener('click', handleSort);
      btn.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          handleSort();
        }
      });

      th.appendChild(btn);
      tr.appendChild(th);
    });

    thead.appendChild(tr);
  }

  // ==========================================
  // AC3 & AC4 & AC6: Agents & Models View
  // ==========================================
  function renderAgentsView(snap) {
    const agents = Array.isArray(snap.agents) ? snap.agents : [];

    // 0. KPI Dashboard (AC1)
    const kpiContainer = document.getElementById('agent-kpi-container');
    if (kpiContainer) {
      kpiContainer.textContent = '';
      agents.forEach(agent => {
        const kpi = calculateAgentKpi(agent, snap.telemetry, new Date(), state.lang);
        if (!kpi) return;

        const tile = el('div', { class: 'kpi-tile' });

        // Header: Name & Status Badge
        const hdr = el('div', { class: 'kpi-tile-header' });
        hdr.appendChild(el('div', { class: 'kpi-agent-name', textContent: kpi.name }));
        hdr.appendChild(el('span', { class: `badge ${kpi.status.className}`, textContent: kpi.status.label }));
        tile.appendChild(hdr);

        // Meta: Observation Age
        const meta = el('div', { class: 'kpi-meta-row' });
        meta.appendChild(el('span', { textContent: `${t('observedPrefix')} ${kpi.observedAge}` }));
        tile.appendChild(meta);

        // Metrics Body
        const body = el('div', { class: 'kpi-metrics-body' });

        // Primary Model
        const mRow = el('div', { class: 'kpi-metric-item' });
        mRow.appendChild(el('span', { class: 'kpi-metric-label', textContent: t('kpiPrimaryModel') }));
        mRow.appendChild(el('span', { class: 'kpi-metric-val', textContent: kpi.primaryModel }));
        body.appendChild(mRow);

        // Session Total Tokens
        const tRow = el('div', { class: 'kpi-metric-item' });
        tRow.appendChild(el('span', { class: 'kpi-metric-label', textContent: t('kpiTotalTokens') }));
        tRow.appendChild(el('span', {
          class: 'kpi-metric-val',
          textContent: kpi.totalTokens.text,
          title: kpi.totalTokens.full
        }));
        body.appendChild(tRow);

        // Subscription Quota / Max Limit
        const lRow = el('div', { class: 'kpi-metric-item' });
        lRow.appendChild(el('span', { class: 'kpi-metric-label', textContent: t('kpiMaxLimit') }));
        const lBox = el('div', { class: 'kpi-limit-box' });
        if (kpi.limitInfo) {
          const lTxt = el('span', {
            class: 'kpi-metric-val',
            textContent: `${kpi.limitInfo.label} (${kpi.limitInfo.usedPercent})`,
            title: kpi.limitInfo.rawLabel
          });
          lBox.appendChild(lTxt);
          if (kpi.limitInfo.resetAt) {
            lBox.appendChild(el('span', {
              class: 'kpi-meta-row',
              textContent: `${t('resetPrefix')} ${kpi.limitInfo.resetAt}`
            }));
          }
          if (kpi.limitInfo.isHistorical) {
            lBox.appendChild(el('span', {
              class: 'badge badge-history',
              textContent: t('planHistoricalBadge')
            }));
          }
        } else {
          lBox.appendChild(el('span', { class: 'kpi-metric-val', textContent: t('kpiNoLimit') }));
        }
        lRow.appendChild(lBox);
        body.appendChild(lRow);

        tile.appendChild(body);

        // Telemetry Badges Row
        if (kpi.telemetry.usage || kpi.telemetry.quota) {
          const telemRow = el('div', { class: 'kpi-telemetry-row' });
          if (kpi.telemetry.usage) {
            telemRow.appendChild(el('span', {
              class: `badge ${kpi.telemetry.usage.class}`,
              textContent: `${t('telemetryUsagePrefix')} ${kpi.telemetry.usage.text}`
            }));
          }
          if (kpi.telemetry.quota) {
            telemRow.appendChild(el('span', {
              class: `badge ${kpi.telemetry.quota.class}`,
              textContent: `${t('telemetryQuotaPrefix')} ${kpi.telemetry.quota.text}`
            }));
          }
          tile.appendChild(telemRow);
        }

        kpiContainer.appendChild(tile);
      });
    }

    // 1. Agent Cards
    const cardsContainer = document.getElementById('agent-cards-container');
    if (cardsContainer) {
      cardsContainer.textContent = '';

      agents.forEach(agent => {
        const card = el('div', { class: 'agent-card' });

        // Header: Agent Name, Model Tag, Status Badge
        const header = el('div', { class: 'agent-card-header' });
        const nameBox = el('div');
        nameBox.appendChild(el('div', { class: 'agent-name', textContent: agent.name || agent.id }));

        const modelStr = translateProbeText(agent.model ? String(agent.model) : t('unknown'), state.lang);
        nameBox.appendChild(el('span', { class: 'agent-model-tag', textContent: `${t('modelPrefix')} ${modelStr}` }));

        // Status badge
        const st = formatAgentStatus(agent.status, state.lang);
        const statusBadge = el('span', { class: `badge ${st.className}`, textContent: st.label });
        header.appendChild(nameBox);
        header.appendChild(statusBadge);
        card.appendChild(header);

        // Top Priority: Observation Age
        const plan = agent.plan || {};
        const obsTime = agent.observed_at || plan.observed_at;
        const obsRel = obsTime ? formatRelativeTime(obsTime, new Date(), state.lang) : t('unknown');
        const obsAgeRow = el('div', { class: 'plan-source-meta' });
        obsAgeRow.appendChild(el('span', { textContent: `${t('observedPrefix')} ${obsRel}` }));
        card.appendChild(obsAgeRow);

        // Top Priority: Plan & Limits
        const planBox = el('div', { class: 'agent-plan-box' });

        const isHist = isHistoricalPlan(plan);
        const planTitleRow = el('div', { class: 'plan-title-row' });
        planTitleRow.appendChild(el('span', { textContent: `${t('planPrefix')} ${translateProbeText(plan.name, state.lang) || t('unknown')}` }));
        if (isHist) {
          planTitleRow.appendChild(el('span', { class: 'badge badge-history', textContent: t('planHistoricalBadge') }));
        }
        planBox.appendChild(planTitleRow);

        // Limits bars (AC2: formatLimitLabel, raw in title tooltip)
        const limits = Array.isArray(plan.limits) ? plan.limits : [];
        if (limits.length === 0) {
          planBox.appendChild(el('div', { class: 'limit-reset', textContent: t('noLimitInfo') }));
        } else {
          limits.forEach(lim => {
            const limItem = el('div', { class: 'limit-item' });
            const labelRow = el('div', { class: 'limit-labels' });
            const friendlyLabel = formatLimitLabel(lim.label, state.lang);
            const rawLabel = state.lang === 'en' ? translateProbeText(lim.label, 'en') : (lim.label || t('unknown'));
            labelRow.appendChild(el('span', { textContent: friendlyLabel, title: rawLabel }));
            labelRow.appendChild(el('span', { textContent: formatPercent(lim.used_percent, 1, state.lang) }));
            limItem.appendChild(labelRow);

            if (lim.used_percent === null || lim.used_percent === undefined) {
              limItem.appendChild(el('div', { class: 'limit-reset', textContent: t('usedPercentUnknown') }));
            } else {
              let barStatus = 'status-good';
              if (lim.used_percent >= 90) barStatus = 'status-critical';
              else if (lim.used_percent >= 70) barStatus = 'status-warning';

              limItem.appendChild(createProgressBar(lim.used_percent, barStatus));
            }

            if (lim.reset_at) {
              limItem.appendChild(el('div', {
                class: 'limit-reset',
                textContent: `${t('resetPrefix')} ${formatDateTime(lim.reset_at, state.lang)} (${formatRelativeTime(lim.reset_at, new Date(), state.lang)})`
              }));
            }
            planBox.appendChild(limItem);
          });
        }
        card.appendChild(planBox);

        // Secondary Info folded in <details> (AC1: source/notes/수집원)
        const detailsEl = el('details', { class: 'agent-details-toggle' });
        const summaryEl = el('summary', { class: 'details-summary', textContent: t('detailsSummary') });
        detailsEl.appendChild(summaryEl);

        const detailsContent = el('div', { class: 'details-content' });

        // Telemetry Badges & Native Usage Sub-block
        if (snap.telemetry && snap.telemetry[agent.id]) {
          const telem = snap.telemetry[agent.id];
          const telemBox = el('div', { class: 'agent-telemetry-box' });

          const badgesRow = el('div', { class: 'telemetry-badges-row' });
          if (telem.usage) {
            const u = formatTelemetryMode(telem.usage, state.lang);
            badgesRow.appendChild(el('span', {
              class: `badge ${u.class}`,
              textContent: `${t('telemetryUsagePrefix')} ${u.text}`,
              title: telem.usage_source ? `${t('sourcePrefix')} ${translateProbeText(telem.usage_source, state.lang)}` : ''
            }));
          }

          if (telem.quota) {
            const q = formatTelemetryMode(telem.quota, state.lang);
            badgesRow.appendChild(el('span', {
              class: `badge ${q.class}`,
              textContent: `${t('telemetryQuotaPrefix')} ${q.text}`,
              title: telem.quota_source ? `${t('sourcePrefix')} ${translateProbeText(telem.quota_source, state.lang)}` : ''
            }));
          }
          telemBox.appendChild(badgesRow);

          // AC1: native_usage sub-block (next to the badge)
          const nativeData = formatNativeUsage(telem.native_usage, agent.id, state.lang);
          if (nativeData) {
            const block = el('div', { class: 'native-usage-block' });
            const blockHdr = el('div', { class: 'native-usage-header' });
            blockHdr.appendChild(el('span', { class: 'native-usage-title', textContent: nativeData.title }));
            if (nativeData.lastReceived) {
              blockHdr.appendChild(el('span', { class: 'native-usage-rel', textContent: nativeData.lastReceived }));
            }
            block.appendChild(blockHdr);

            const listEl = el('div', { class: 'native-usage-list' });
            nativeData.models.forEach(m => {
              const row = el('div', { class: 'native-model-row' });
              row.appendChild(el('span', { class: 'native-model-name', textContent: translateProbeText(m.model, state.lang) }));
              const itemsBox = el('div', { class: 'native-model-items' });
              m.items.forEach(it => {
                const itemSpan = el('span', {
                  class: 'native-token-item',
                  textContent: `${it.type}: ${it.countText}`,
                  title: `${it.type}: ${it.countFull}`
                });
                itemsBox.appendChild(itemSpan);
              });
              row.appendChild(itemsBox);
              listEl.appendChild(row);
            });
            block.appendChild(listEl);
            block.appendChild(el('span', { class: 'native-usage-rel', textContent: nativeData.limit }));
            telemBox.appendChild(block);
          }

          detailsContent.appendChild(telemBox);
        }

        // Plan source & full datetime
        const planMeta = el('div', { class: 'plan-source-meta' });
        planMeta.appendChild(el('span', { textContent: `${t('sourcePrefix')} ${translateProbeText(plan.source, state.lang) || t('unknown')}` }));
        if (plan.observed_at) {
          planMeta.appendChild(el('span', {
            textContent: `${t('observedPrefix')} ${formatDateTime(plan.observed_at, state.lang)}`
          }));
        }
        detailsContent.appendChild(planMeta);

        // Agent source & observed_at
        const agentMeta = el('div', { class: 'plan-source-meta' });
        agentMeta.appendChild(el('span', { textContent: `${t('collectorSourcePrefix')} ${translateProbeText(agent.source, state.lang) || t('unknown')}` }));
        if (agent.observed_at) {
          agentMeta.appendChild(el('span', {
            textContent: `${t('lastObservedPrefix')} ${formatDateTime(agent.observed_at, state.lang)}`
          }));
        }
        detailsContent.appendChild(agentMeta);

        // Notes
        if (Array.isArray(agent.notes) && agent.notes.length > 0) {
          const notesBox = el('div', { class: 'agent-notes-box' });
          notesBox.appendChild(el('span', { textContent: t('notesTitle') }));
          const ul = el('ul', { class: 'agent-notes-list' });
          agent.notes.forEach(note => {
            ul.appendChild(el('li', { textContent: translateProbeText(String(note), state.lang) }));
          });
          notesBox.appendChild(ul);
          detailsContent.appendChild(notesBox);
        }

        detailsEl.appendChild(detailsContent);
        card.appendChild(detailsEl);

        cardsContainer.appendChild(card);
      });
    }

    // 2. Tokens Table with Sorting
    const tokenCols = [
      { id: 'name', labelKey: 'thAgent', type: 'string', get: a => a.name || a.id },
      { id: 'input', labelKey: 'thInputTokens', type: 'number', get: a => a.usage ? a.usage.input_tokens : null },
      { id: 'cached_read', labelKey: 'thCachedInput', type: 'number', get: a => a.usage ? a.usage.cached_input_tokens : null },
      { id: 'cached_write', labelKey: 'thCacheWrite', type: 'number', get: a => a.usage ? a.usage.cache_write_input_tokens : null },
      { id: 'output', labelKey: 'thOutputTokens', type: 'number', get: a => a.usage ? a.usage.output_tokens : null },
      { id: 'reasoning', labelKey: 'thReasoningTokens', type: 'number', get: a => a.usage ? a.usage.reasoning_tokens : null },
      { id: 'total', labelKey: 'thTotalTokens', type: 'number', get: a => a.usage ? a.usage.total_tokens : null },
      { id: 'sessions', labelKey: 'thSessions', type: 'number', get: a => a.usage ? a.usage.sessions : null }
    ];

    const tokenTable = document.getElementById('agent-tokens-table');
    const tokenTbody = document.getElementById('agent-tokens-tbody');

    function renderTokensRows() {
      if (!tokenTbody) return;
      tokenTbody.textContent = '';

      const sortCfg = state.sortState.tokens;
      const activeCol = tokenCols.find(c => c.id === sortCfg.col) || tokenCols[0];
      const sortedAgents = sortTableData(agents, activeCol.get, activeCol.type, sortCfg.dir, state.lang);

      sortedAgents.forEach(agent => {
        const tr = el('tr');
        const usage = agent.usage || {};

        const tdName = el('td');
        tdName.appendChild(el('strong', { textContent: agent.name || agent.id }));
        tr.appendChild(tdName);

        const inFmt = formatTokens(usage.input_tokens, state.lang);
        const crFmt = formatTokens(usage.cached_input_tokens, state.lang);
        const cwFmt = formatTokens(usage.cache_write_input_tokens, state.lang);
        const outFmt = formatTokens(usage.output_tokens, state.lang);
        const reaFmt = formatTokens(usage.reasoning_tokens, state.lang);
        const totFmt = formatTokens(usage.total_tokens, state.lang);

        tr.appendChild(el('td', { class: 'token-num', textContent: inFmt.text, title: inFmt.full }));
        tr.appendChild(el('td', { class: 'token-num', textContent: crFmt.text, title: crFmt.full }));
        tr.appendChild(el('td', { class: 'token-num', textContent: cwFmt.text, title: cwFmt.full }));
        tr.appendChild(el('td', { class: 'token-num', textContent: outFmt.text, title: outFmt.full }));
        tr.appendChild(el('td', { class: 'token-num', textContent: reaFmt.text, title: reaFmt.full }));
        tr.appendChild(el('td', { class: 'token-num', textContent: totFmt.text, title: totFmt.full }));
        tr.appendChild(el('td', { class: 'token-num', textContent: formatValue(usage.sessions, state.lang) }));

        tokenTbody.appendChild(tr);
      });
    }

    if (tokenTable) {
      setupSortableHeader('tokens', tokenTable, tokenCols, renderTokensRows);
      renderTokensRows();
    }

    // 3. Models Table with Sorting
    const flattenedModels = [];
    agents.forEach(agent => {
      const models = Array.isArray(agent.models) ? agent.models : [];
      const agentTotal = (agent.usage && typeof agent.usage.total_tokens === 'number') ? agent.usage.total_tokens : null;
      models.forEach(m => {
        const sharePct = (agentTotal && agentTotal > 0 && typeof m.total_tokens === 'number')
          ? (m.total_tokens / agentTotal) * 100 : null;
        flattenedModels.push({
          ...m,
          agentName: agent.name || agent.id,
          agentTotal,
          sharePct
        });
      });
    });

    const modelCols = [
      { id: 'agent', labelKey: 'thAgent', type: 'string', get: m => m.agentName },
      { id: 'model', labelKey: 'thModel', type: 'string', get: m => m.model },
      { id: 'input', labelKey: 'thInputTokens', type: 'number', get: m => m.input_tokens },
      { id: 'cached_read', labelKey: 'thCachedInput', type: 'number', get: m => m.cached_input_tokens },
      { id: 'cached_write', labelKey: 'thCacheWrite', type: 'number', get: m => m.cache_write_input_tokens },
      { id: 'output', labelKey: 'thOutputTokens', type: 'number', get: m => m.output_tokens },
      { id: 'total', labelKey: 'thTotalTokens', type: 'number', get: m => m.total_tokens },
      { id: 'sessions', labelKey: 'thSessions', type: 'number', get: m => m.sessions },
      { id: 'share', labelKey: 'thShare', type: 'number', get: m => m.sharePct }
    ];

    const modelTable = document.getElementById('model-usage-table');
    const modelTbody = document.getElementById('model-usage-tbody');

    function renderModelsRows() {
      if (!modelTbody) return;
      modelTbody.textContent = '';

      const sortCfg = state.sortState.models;
      const activeCol = modelCols.find(c => c.id === sortCfg.col) || modelCols[0];
      const sortedModels = sortTableData(flattenedModels, activeCol.get, activeCol.type, sortCfg.dir, state.lang);

      sortedModels.forEach(model => {
        const tr = el('tr');
        tr.appendChild(el('td', { textContent: model.agentName }));
        tr.appendChild(el('td', { textContent: translateProbeText(model.model || t('unknown'), state.lang) }));

        const inFmt = formatTokens(model.input_tokens, state.lang);
        const crFmt = formatTokens(model.cached_input_tokens, state.lang);
        const cwFmt = formatTokens(model.cache_write_input_tokens, state.lang);
        const outFmt = formatTokens(model.output_tokens, state.lang);
        const totFmt = formatTokens(model.total_tokens, state.lang);

        tr.appendChild(el('td', { class: 'token-num', textContent: inFmt.text, title: inFmt.full }));
        tr.appendChild(el('td', { class: 'token-num', textContent: crFmt.text, title: crFmt.full }));
        tr.appendChild(el('td', { class: 'token-num', textContent: cwFmt.text, title: cwFmt.full }));
        tr.appendChild(el('td', { class: 'token-num', textContent: outFmt.text, title: outFmt.full }));
        tr.appendChild(el('td', { class: 'token-num', textContent: totFmt.text, title: totFmt.full }));
        tr.appendChild(el('td', { class: 'token-num', textContent: formatValue(model.sessions, state.lang) }));

        // Share Bar
        const tdShare = el('td', { class: 'col-share' });
        if (typeof model.sharePct === 'number') {
          const shareWrap = el('div');
          const pctLabel = el('div', {
            class: 'limit-labels',
            children: [
              el('span', { textContent: `${model.sharePct.toFixed(1)}%` }),
              el('span', { class: 'text-muted', textContent: `/${totFmt.text}` })
            ]
          });
          shareWrap.appendChild(pctLabel);
          shareWrap.appendChild(createProgressBar(model.sharePct));
          tdShare.appendChild(shareWrap);
        } else {
          tdShare.appendChild(el('span', { class: 'text-muted', textContent: t('unknown') }));
        }
        tr.appendChild(tdShare);

        modelTbody.appendChild(tr);
      });
    }

    if (modelTable) {
      setupSortableHeader('models', modelTable, modelCols, renderModelsRows);
      renderModelsRows();
    }
  }

  // ==========================================
  // AC5 & AC7: Hardware & History View
  // ==========================================
  function renderHardwareView(snap) {
    const hw = snap.hardware || {};
    const gpuList = Array.isArray(hw.gpu) ? hw.gpu : [];
    const gpu = gpuList[0] || {};
    const inf = hw.inference || {};

    // 1. Host machine
    const hostDetails = document.getElementById('host-details');
    if (hostDetails) {
      hostDetails.textContent = '';
      function addRow(label, value) {
        const row = el('div', { class: 'prop-row' });
        row.appendChild(el('span', { class: 'prop-key', textContent: label }));
        row.appendChild(el('span', { class: 'prop-val', textContent: value }));
        hostDetails.appendChild(row);
      }

      addRow(t('hostHostname'), hw.hostname || t('unknown'));
      addRow(t('hostOsArch'), `${hw.os || 'Linux'} / ${hw.architecture || t('unknown')}`);
      addRow(t('hostKernel'), hw.kernel || t('unknown'));
      addRow(t('hostCpuCores'), hw.cpu_count ? `${hw.cpu_count} ${t('coresSuffix')}` : t('unknown'));
      addRow(t('hostCpuUsage'), formatPercent(hw.cpu_percent, 1, state.lang));

      const memUsedStr = formatBytes(hw.memory_used_bytes, state.lang);
      const memTotStr = formatBytes(hw.memory_total_bytes, state.lang);
      const memPctStr = formatPercent(hw.memory_used_percent, 1, state.lang);
      addRow(t('hostMemoryUsage'), `${memUsedStr} / ${memTotStr} (${memPctStr})`);
    }

    // 2. GPU
    const gpuDetails = document.getElementById('gpu-details');
    if (gpuDetails) {
      gpuDetails.textContent = '';
      function addGpuRow(label, value) {
        const row = el('div', { class: 'prop-row' });
        row.appendChild(el('span', { class: 'prop-key', textContent: label }));
        row.appendChild(el('span', { class: 'prop-val', textContent: value }));
        gpuDetails.appendChild(row);
      }

      addGpuRow(t('gpuModel'), gpu.name || t('unknown'));
      addGpuRow(t('gpuDriver'), gpu.driver_version || t('unknown'));
      addGpuRow(t('gpuUsage'), formatPercent(gpu.utilization_percent, 1, state.lang));
      addGpuRow(t('gpuTemp'), (gpu.temperature_c !== null && gpu.temperature_c !== undefined) ? `${gpu.temperature_c} °C` : t('unknown'));

      const pwr = (gpu.power_watts !== null && gpu.power_watts !== undefined) ? `${gpu.power_watts} W` : t('unknown');
      const lim = (gpu.power_limit_watts !== null && gpu.power_limit_watts !== undefined) ? `${gpu.power_limit_watts} W` : 'N/A';
      addGpuRow(t('gpuPower'), `${pwr} / ${lim}`);

      let memDisplay = t('gpuVramNa');
      if (gpu.memory_used_bytes !== null && gpu.memory_used_bytes !== undefined) {
        memDisplay = formatBytes(gpu.memory_used_bytes, state.lang);
      }
      addGpuRow(t('gpuVram'), memDisplay);
      // 프로세스별 GPU 메모리(nvidia-smi compute-apps)는 전용 VRAM과 별개 지표. 비율로 환산하지 않는다.
      const procs = formatGpuProcesses(gpu, state.lang);
      addGpuRow(t('gpuProcMem'), procs.total);
      addGpuRow(t('gpuProcs'), procs.list);

      if (gpu.memory_note) {
        const noteBox = el('div', { class: 'memory-note-text', textContent: translateProbeText(gpu.memory_note, state.lang) });
        gpuDetails.appendChild(noteBox);
      }
    }

    // 3. Inference Server
    const infDetails = document.getElementById('inference-details');
    const infTag = document.getElementById('inference-status-tag');
    if (infTag) {
      infTag.className = 'card-tag';
      if (inf.reachable === true) {
        infTag.classList.add('badge-good');
        infTag.textContent = t('infReachableGood');
      } else if (inf.reachable === false) {
        infTag.classList.add('badge-critical');
        infTag.textContent = t('infReachableCritical');
      } else {
        infTag.textContent = t('infReachableUnknown');
      }
    }

    if (infDetails) {
      infDetails.textContent = '';
      function addInfRow(label, value) {
        const row = el('div', { class: 'prop-row' });
        row.appendChild(el('span', { class: 'prop-key', textContent: label }));
        row.appendChild(el('span', { class: 'prop-val', textContent: value }));
        infDetails.appendChild(row);
      }

      addInfRow(t('infEndpoint'), inf.endpoint || t('unknown'));
      const modelsStr = Array.isArray(inf.models) && inf.models.length > 0 ? inf.models.join(', ') : t('unknown');
      addInfRow(t('infModels'), modelsStr);
      addInfRow(t('infEngine'), (inf.engine !== null && inf.engine !== undefined && inf.engine !== '') ? String(inf.engine) : t('unknown'));
      addInfRow(t('infVersion'), (inf.version !== null && inf.version !== undefined && inf.version !== '') ? String(inf.version) : t('unknown'));
      addInfRow(t('infExecutable'), (inf.runtime_executable !== null && inf.runtime_executable !== undefined && inf.runtime_executable !== '') ? String(inf.runtime_executable) : t('unknown'));
      addInfRow(t('infContainerImage'), (inf.container_image !== null && inf.container_image !== undefined && inf.container_image !== '') ? String(inf.container_image) : t('unknown'));
      addInfRow(t('infVllmVersion'), (inf.installed_vllm_version !== null && inf.installed_vllm_version !== undefined && inf.installed_vllm_version !== '') ? String(inf.installed_vllm_version) : t('unknown'));

      const fixedKeys = new Set([
        'endpoint', 'reachable', 'models',
        'engine', 'version', 'runtime_executable', 'container_image', 'installed_vllm_version'
      ]);
      for (const [k, v] of Object.entries(inf)) {
        if (!fixedKeys.has(k) && typeof v !== 'object' && v !== null && v !== undefined) {
          const label = formatInferenceKey(k, state.lang);
          let valStr = String(v);
          if (k === 'observed_at') {
            valStr = formatDateTime(v, state.lang);
          }
          addInfRow(label, valStr);
        }
      }
    }
  }

  function renderHistory() {
    const hist = state.historyData;
    if (!hist) return;

    const points = Array.isArray(hist.points) ? hist.points : [];

    // AC7: History Resolution
    const res = hist.resolution === '5m' ? '5m' : 'raw';
    const resLabel = formatResolutionLabel(res, state.lang);

    const resBadge = document.getElementById('history-resolution-badge');
    if (resBadge) resBadge.textContent = resLabel;

    // Retention metadata
    const metaBox = document.getElementById('history-retention-meta');
    if (metaBox) {
      // 통합 수정(Claude): 보이는 해상도의 실제 보존 기간·상한을 표시(원본 24시간, 5분 집계 30일)
      const isAgg = hist.resolution === '5m';
      const keep = isAgg
        ? `${hist.agg_retention_days ?? hist.retention_days}${t('retentionDaysSuffix')}`
        : (state.lang === 'en' ? `${hist.raw_retention_hours ?? 24}h retention` : `${hist.raw_retention_hours ?? 24}시간 보존`);
      const cap = isAgg ? (hist.agg_max_rows ?? hist.max_rows) : (hist.raw_max_rows ?? hist.max_rows);
      metaBox.textContent = `${t('retentionPrefix')} ${keep} / ${state.lang === 'en' ? 'max' : '최대'} ${(cap || 0).toLocaleString(state.lang === 'ko' ? 'ko-KR' : 'en-US')}${t('retentionMaxSuffix')} (${t('retentionMatchedPrefix')} ${(hist.matched || points.length).toLocaleString(state.lang === 'ko' ? 'ko-KR' : 'en-US')} / ${t('retentionTotalPrefix')} ${(hist.stored_total || 0).toLocaleString(state.lang === 'ko' ? 'ko-KR' : 'en-US')})`;
    }

    // Chart series data
    const gpuUtils = points.map(p => p.gpu && p.gpu[0] ? p.gpu[0].utilization_percent : null);
    const gpuTemps = points.map(p => p.gpu && p.gpu[0] ? p.gpu[0].temperature_c : null);
    const gpuPowers = points.map(p => p.gpu && p.gpu[0] ? p.gpu[0].power_watts : null);
    const hostMems = points.map(p => p.memory_used_percent);

    const lastPoint = points.length > 0 ? points[points.length - 1] : null;
    const lastGpu = (lastPoint && lastPoint.gpu && lastPoint.gpu[0]) ? lastPoint.gpu[0] : null;

    const valGpuUtil = document.getElementById('chart-val-gpu-util');
    if (valGpuUtil) valGpuUtil.textContent = lastGpu ? formatPercent(lastGpu.utilization_percent, 1, state.lang) : '-';

    const valGpuTemp = document.getElementById('chart-val-gpu-temp');
    if (valGpuTemp) valGpuTemp.textContent = (lastGpu && lastGpu.temperature_c !== null) ? `${lastGpu.temperature_c} °C` : '-';

    const valGpuPower = document.getElementById('chart-val-gpu-power');
    if (valGpuPower) valGpuPower.textContent = (lastGpu && lastGpu.power_watts !== null) ? `${lastGpu.power_watts} W` : '-';

    const valHostMem = document.getElementById('chart-val-host-mem');
    if (valHostMem) valHostMem.textContent = lastPoint ? formatPercent(lastPoint.memory_used_percent, 1, state.lang) : '-';

    renderSvgChart('chart-svg-gpu-util', gpuUtils, points, '%', 0, 100);
    renderSvgChart('chart-svg-gpu-temp', gpuTemps, points, '°C');
    renderSvgChart('chart-svg-gpu-power', gpuPowers, points, 'W');
    renderSvgChart('chart-svg-host-mem', hostMems, points, '%', 0, 100);

    // 4. History Table with Sorting (Recent 50 snapshots)
    const recentPoints = points.slice(-50);
    const historyCols = [
      { id: 'collected_at', labelKey: 'thCollectedAt', type: 'date', get: p => p.collected_at },
      { id: 'cpu', labelKey: 'thCpuPercent', type: 'number', get: p => p.cpu_percent },
      { id: 'memory', labelKey: 'thMemPercent', type: 'number', get: p => p.memory_used_percent },
      { id: 'gpu_util', labelKey: 'thGpuUtil', type: 'number', get: p => p.gpu && p.gpu[0] ? p.gpu[0].utilization_percent : null },
      { id: 'gpu_temp', labelKey: 'thGpuTemp', type: 'number', get: p => p.gpu && p.gpu[0] ? p.gpu[0].temperature_c : null },
      { id: 'gpu_power', labelKey: 'thGpuPower', type: 'number', get: p => p.gpu && p.gpu[0] ? p.gpu[0].power_watts : null },
      { id: 'inference', labelKey: 'thInference', type: 'string', get: p => p.inference_reachable === true ? t('infReachableGood') : (p.inference_reachable === false ? t('infReachableCritical') : null) },
      { id: 'errors', labelKey: 'thErrors', type: 'number', get: p => p.errors },
      { id: 'samples', labelKey: 'thSamples', type: 'number', get: p => p.samples }
    ];

    const histTable = document.getElementById('snapshot-history-table');
    const histTbody = document.getElementById('snapshot-history-tbody');

    function renderHistoryRows() {
      if (!histTbody) return;
      histTbody.textContent = '';

      const sortCfg = state.sortState.history;
      const activeCol = historyCols.find(c => c.id === sortCfg.col) || historyCols[0];
      const sortedPoints = sortTableData(recentPoints, activeCol.get, activeCol.type, sortCfg.dir, state.lang);

      sortedPoints.forEach(p => {
        const tr = el('tr');
        const pGpu = p.gpu && p.gpu[0] ? p.gpu[0] : null;

        tr.appendChild(el('td', {
          textContent: `${formatDateTime(p.collected_at, state.lang)} (${formatRelativeTime(p.collected_at, new Date(), state.lang)})`
        }));
        tr.appendChild(el('td', { textContent: formatPercent(p.cpu_percent, 1, state.lang) }));
        tr.appendChild(el('td', { textContent: formatPercent(p.memory_used_percent, 1, state.lang) }));
        tr.appendChild(el('td', { textContent: pGpu ? formatPercent(pGpu.utilization_percent, 1, state.lang) : t('unknown') }));
        tr.appendChild(el('td', { textContent: (pGpu && pGpu.temperature_c !== null) ? `${pGpu.temperature_c} °C` : t('unknown') }));
        tr.appendChild(el('td', { textContent: (pGpu && pGpu.power_watts !== null) ? `${pGpu.power_watts} W` : t('unknown') }));

        let infText = t('unknown');
        if (p.inference_reachable === true) infText = t('infReachableGood');
        else if (p.inference_reachable === false) infText = t('infReachableCritical');
        tr.appendChild(el('td', { textContent: infText }));

        tr.appendChild(el('td', { textContent: formatValue(p.errors, state.lang) }));

        // Show samples column if 5m aggregation
        if (p.samples !== undefined && p.samples !== null) {
          tr.appendChild(el('td', { textContent: formatValue(p.samples, state.lang) }));
        }

        histTbody.appendChild(tr);
      });
    }

    if (histTable) {
      // If samples exist in data, include samples column in headers
      const hasSamples = points.some(p => p.samples !== undefined && p.samples !== null);
      const activeCols = hasSamples ? historyCols : historyCols.filter(c => c.id !== 'samples');
      setupSortableHeader('history', histTable, activeCols, renderHistoryRows);
      renderHistoryRows();
    }
  }

  function renderSvgChart(containerId, series, points, unit = '', forcedMin = null, forcedMax = null) {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.textContent = '';

    const width = 320;
    const height = 140;
    const padding = { left: 42, right: 12, top: 16, bottom: 26 };

    const axes = calculateChartAxes(points, series, forcedMin, forcedMax, unit, state.lang);
    const { d, points: coords } = calculateSvgPath(series, width, height, padding, axes.yTicks.min, axes.yTicks.max);

    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('viewBox', `0 0 ${width} ${height}`);

    const strokeGrid = state.theme === 'light' ? '#dcdbd6' : '#33322f';
    const textSubtle = state.theme === 'light' ? '#73726c' : '#8f8e86';

    const yTop = padding.top;
    const yBottom = height - padding.bottom;

    // Horizontal grid lines
    const gridBottom = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    gridBottom.setAttribute('x1', String(padding.left));
    gridBottom.setAttribute('y1', String(yBottom));
    gridBottom.setAttribute('x2', String(width - padding.right));
    gridBottom.setAttribute('y2', String(yBottom));
    gridBottom.setAttribute('stroke', strokeGrid);
    gridBottom.setAttribute('stroke-width', '1');
    svg.appendChild(gridBottom);

    const gridTop = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    gridTop.setAttribute('x1', String(padding.left));
    gridTop.setAttribute('y1', String(yTop));
    gridTop.setAttribute('x2', String(width - padding.right));
    gridTop.setAttribute('y2', String(yTop));
    gridTop.setAttribute('stroke', strokeGrid);
    gridTop.setAttribute('stroke-width', '1');
    gridTop.setAttribute('stroke-dasharray', '2,2');
    svg.appendChild(gridTop);

    // Y-axis labels
    const txtMax = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    txtMax.setAttribute('x', String(padding.left - 4));
    txtMax.setAttribute('y', String(yTop + 4));
    txtMax.setAttribute('text-anchor', 'end');
    txtMax.setAttribute('font-size', '10px');
    txtMax.setAttribute('font-family', 'var(--font-mono)');
    txtMax.setAttribute('fill', textSubtle);
    txtMax.textContent = axes.yTicks.maxLabel;
    svg.appendChild(txtMax);

    const txtMin = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    txtMin.setAttribute('x', String(padding.left - 4));
    txtMin.setAttribute('y', String(yBottom));
    txtMin.setAttribute('text-anchor', 'end');
    txtMin.setAttribute('font-size', '10px');
    txtMin.setAttribute('font-family', 'var(--font-mono)');
    txtMin.setAttribute('fill', textSubtle);
    txtMin.textContent = axes.yTicks.minLabel;
    svg.appendChild(txtMin);

    // X-axis time ticks
    axes.timeTicks.forEach(tick => {
      const tickX = padding.left + tick.xRatio * (width - padding.left - padding.right);
      const txtTime = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      txtTime.setAttribute('x', String(tickX));
      txtTime.setAttribute('y', String(height - 8));
      if (tick.xRatio <= 0.1) {
        txtTime.setAttribute('text-anchor', 'start');
      } else if (tick.xRatio >= 0.9) {
        txtTime.setAttribute('text-anchor', 'end');
      } else {
        txtTime.setAttribute('text-anchor', 'middle');
      }
      txtTime.setAttribute('font-size', '10px');
      txtTime.setAttribute('font-family', 'var(--font-mono)');
      txtTime.setAttribute('fill', textSubtle);
      txtTime.textContent = tick.label;
      svg.appendChild(txtTime);
    });

    if (d) {
      const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
      path.setAttribute('d', d);
      path.setAttribute('fill', 'none');
      path.setAttribute('stroke', state.theme === 'light' ? '#2a78d6' : '#3987e5');
      path.setAttribute('stroke-width', '2');
      svg.appendChild(path);
    }

    const crosshair = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    crosshair.setAttribute('stroke', textSubtle);
    crosshair.setAttribute('stroke-width', '1');
    crosshair.setAttribute('stroke-dasharray', '2,2');
    crosshair.setAttribute('y1', String(yTop));
    crosshair.setAttribute('y2', String(yBottom));
    crosshair.setAttribute('display', 'none');
    svg.appendChild(crosshair);

    const dot = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    dot.setAttribute('r', '3.5');
    dot.setAttribute('fill', state.theme === 'light' ? '#2a78d6' : '#3987e5');
    dot.setAttribute('stroke', state.theme === 'light' ? '#ffffff' : '#f0efec');
    dot.setAttribute('stroke-width', '1.5');
    dot.setAttribute('display', 'none');
    svg.appendChild(dot);

    svg.addEventListener('mousemove', (e) => {
      const rect = svg.getBoundingClientRect();
      const mouseX = e.clientX - rect.left;
      const svgX = (mouseX / rect.width) * width;

      let closest = null;
      let minDiff = Infinity;
      coords.forEach(cp => {
        const diff = Math.abs(cp.x - svgX);
        if (diff < minDiff) {
          minDiff = diff;
          closest = cp;
        }
      });

      if (closest) {
        crosshair.setAttribute('x1', String(closest.x));
        crosshair.setAttribute('x2', String(closest.x));
        crosshair.setAttribute('display', 'block');

        if (closest.y !== null) {
          dot.setAttribute('cx', String(closest.x));
          dot.setAttribute('cy', String(closest.y));
          dot.setAttribute('display', 'block');
        } else {
          dot.setAttribute('display', 'none');
        }

        const pt = points[closest.index];
        const timeStr = pt ? formatDateTime(pt.collected_at, state.lang) : '';
        const valStr = closest.value !== null ? `${closest.value}${unit}` : t('unknown');

        let tooltipStr = `${timeStr} | ${valStr}`;
        if (pt && pt.samples) {
          tooltipStr += ` (${t('thSamples')}: ${pt.samples})`;
        }
        svg.setAttribute('title', tooltipStr);
      }
    });

    svg.addEventListener('mouseleave', () => {
      crosshair.setAttribute('display', 'none');
      dot.setAttribute('display', 'none');
    });

    container.appendChild(svg);
  }

  // ==========================================
  // AC6: Skills View
  // ==========================================
  function renderSkillsView(snap) {
    const skillsRoot = snap.skills || {};
    const skillAgents = Array.isArray(skillsRoot.agents) ? skillsRoot.agents : [];
    const repoSkills = Array.isArray(skillsRoot.repository) ? skillsRoot.repository : [];

    const summaryContainer = document.getElementById('skills-summary-cards');
    const agentFilterSelect = document.getElementById('filter-skill-agent');

    if (summaryContainer) {
      summaryContainer.textContent = '';
      skillAgents.forEach(sa => {
        const b = calculateSkillBreakdown(sa, state.lang);
        const card = el('div', { class: 'skill-summary-card' });
        card.appendChild(el('div', { class: 'skill-card-agent-name', textContent: b.agent }));

        // Categories Grid (AC2)
        const catGrid = el('div', { class: 'skill-categories-grid' });

        const addCat = (label, val) => {
          const item = el('div', { class: 'skill-cat-item' });
          item.appendChild(el('span', { class: 'skill-cat-name', textContent: label }));
          item.appendChild(el('span', { class: 'skill-cat-count', textContent: formatValue(val, state.lang) }));
          catGrid.appendChild(item);
        };

        addCat(t('labelCommonSelected'), b.commonSelected);
        addCat(t('labelCommonDiscovered'), b.commonDiscovered);
        addCat(t('labelCommonActive'), b.commonActive);
        addCat(t('labelPlatformAdded'), b.platformAdded);
        addCat(t('labelInactive'), b.inactive);
        addCat(t('labelUnconfirmed'), b.unknown);

        card.appendChild(catGrid);

        // Auxiliary Counts Line (AC2)
        const counts = formatSkillCounts(sa, state.lang);
        const aux = el('div', {
          class: 'skill-aux-counts',
          textContent: `${counts.registered} · ${counts.enabled}`,
          title: t('notComparableTooltip')
        });
        card.appendChild(aux);

        card.appendChild(el('div', { class: 'plan-source-meta', textContent: `${t('sourcePrefix')} ${translateProbeText(sa.source, state.lang) || t('unknown')}` }));
        card.appendChild(el('div', {
          class: 'plan-source-meta',
          textContent: `${t('observedPrefix')} ${formatDateTime(sa.observed_at, state.lang)} (${formatRelativeTime(sa.observed_at, new Date(), state.lang)})`
        }));
        summaryContainer.appendChild(card);
      });
    }

    // AC3: Skills Category Table
    const catTable = document.getElementById('skills-category-table');
    const catTbody = document.getElementById('skills-category-tbody');
    const catRows = skillAgents.map(sa => calculateSkillBreakdown(sa, state.lang));

    const catCols = [
      { id: 'agent', labelKey: 'thSkillAgent', type: 'string', get: r => r.agent },
      { id: 'commonSelected', labelKey: 'thCommonSelected', type: 'number', get: r => r.commonSelected },
      { id: 'commonDiscovered', labelKey: 'thCommonDiscovered', type: 'number', get: r => r.commonDiscovered },
      { id: 'commonActive', labelKey: 'thCommonActive', type: 'number', get: r => r.commonActive },
      { id: 'platformAdded', labelKey: 'thPlatformAdded', type: 'number', get: r => r.platformAdded },
      { id: 'inactive', labelKey: 'thInactive', type: 'number', get: r => r.inactive },
      { id: 'unknown', labelKey: 'thUnconfirmed', type: 'number', get: r => r.unknown },
      { id: 'registeredTotal', labelKey: 'thRegisteredTotal', type: 'number', get: r => r.registeredTotal },
      { id: 'enabledTotal', labelKey: 'thEnabledTotal', type: 'number', get: r => r.enabledTotal }
    ];

    function renderCategoryRows() {
      if (!catTbody) return;
      catTbody.textContent = '';
      const sortCfg = state.sortState.skillsCategory || { col: 'agent', dir: 'asc' };
      const activeCol = catCols.find(c => c.id === sortCfg.col) || catCols[0];
      const sortedRows = sortTableData(catRows, activeCol.get, activeCol.type, sortCfg.dir, state.lang);

      sortedRows.forEach(r => {
        const tr = el('tr');
        tr.appendChild(el('td', { textContent: r.agent }));
        tr.appendChild(el('td', { textContent: formatValue(r.commonSelected, state.lang) }));
        tr.appendChild(el('td', { textContent: formatValue(r.commonDiscovered, state.lang) }));
        tr.appendChild(el('td', { textContent: formatValue(r.commonActive, state.lang) }));
        tr.appendChild(el('td', { textContent: formatValue(r.platformAdded, state.lang) }));
        tr.appendChild(el('td', { textContent: formatValue(r.inactive, state.lang) }));
        tr.appendChild(el('td', { textContent: formatValue(r.unknown, state.lang) }));
        tr.appendChild(el('td', { textContent: formatValue(r.registeredTotal, state.lang) }));
        tr.appendChild(el('td', { textContent: formatValue(r.enabledTotal, state.lang) }));
        catTbody.appendChild(tr);
      });
    }

    if (catTable) {
      setupSortableHeader('skillsCategory', catTable, catCols, renderCategoryRows);
      renderCategoryRows();
    }

    // AC1-AC3: MCP Section
    const mcpContainer = document.getElementById('mcp-container');
    if (mcpContainer) {
      mcpContainer.textContent = '';
      if (!snap.mcp || typeof snap.mcp !== 'object') {
        const mcpCard = el('div', { class: 'empty-state-card' });
        mcpCard.appendChild(el('p', { class: 'empty-desc', textContent: t('mcpEmptyDesc') }));
        mcpContainer.appendChild(mcpCard);
      } else {
        const summary = calculateMcpSummary(snap.mcp, state.lang);
        if (summary) {
          // 1. Summary Cards
          const summaryWrap = el('div', { class: 'mcp-summary-wrap' });
          summaryWrap.appendChild(el('h4', { class: 'block-sub-title', textContent: t('titleMcpSummary') }));
          const grid = el('div', { class: 'kpi-grid mcp-summary-grid' });

          summary.agents.forEach(ag => {
            const tile = el('div', { class: 'kpi-tile' });
            const header = el('div', { class: 'kpi-tile-header' });
            header.appendChild(el('span', { class: 'kpi-agent-name', textContent: ag.agent.toUpperCase() }));
            tile.appendChild(header);

            const body = el('div', { class: 'kpi-metrics-body' });

            // Common Configured
            const itemCfg = el('div', { class: 'kpi-metric-item' });
            itemCfg.appendChild(el('span', { class: 'kpi-metric-label', textContent: t('mcpCommonConfigured') }));
            itemCfg.appendChild(el('span', { class: 'kpi-metric-val', textContent: ag.commonConfiguredText }));
            body.appendChild(itemCfg);

            // Common Connected
            const itemConn = el('div', { class: 'kpi-metric-item' });
            itemConn.appendChild(el('span', { class: 'kpi-metric-label', textContent: t('mcpCommonConnected') }));
            itemConn.appendChild(el('span', { class: 'kpi-metric-val', textContent: ag.commonConnectedText }));
            body.appendChild(itemConn);

            // Platform Added
            const itemPlat = el('div', { class: 'kpi-metric-item' });
            itemPlat.appendChild(el('span', { class: 'kpi-metric-label', textContent: t('mcpPlatformAdded') }));
            itemPlat.appendChild(el('span', { class: 'kpi-metric-val', textContent: ag.platformAddedText }));
            body.appendChild(itemPlat);

            // Error count alert if > 0
            if (ag.errorCount && ag.errorCount > 0) {
              const errRow = el('div', { class: 'mcp-error-row' });
              errRow.appendChild(el('span', {
                class: 'badge badge-critical',
                textContent: `⚠️ ${t('mcpErrorsCount', { n: ag.errorCount })}`
              }));
              body.appendChild(errRow);
            }

            tile.appendChild(body);
            grid.appendChild(tile);
          });
          summaryWrap.appendChild(grid);
          mcpContainer.appendChild(summaryWrap);

          // 2. Status Table
          const tableWrap = el('div', { class: 'mcp-table-wrap' });
          tableWrap.appendChild(el('h4', { class: 'block-sub-title', textContent: t('titleMcpStatusTable') }));

          const scrollDiv = el('div', { class: 'table-scroll' });
          const table = el('table', { class: 'data-table', id: 'mcp-status-table' });
          const thead = el('thead');
          const theadTr = el('tr');
          thead.appendChild(theadTr);
          table.appendChild(thead);

          const tbody = el('tbody', { id: 'mcp-status-tbody' });
          table.appendChild(tbody);
          scrollDiv.appendChild(table);
          tableWrap.appendChild(scrollDiv);
          mcpContainer.appendChild(tableWrap);

          // Flatten servers for table
          const flatServers = [];
          summary.agents.forEach(ag => {
            const servers = Array.isArray(ag.servers) ? ag.servers : [];
            servers.forEach(s => {
              flatServers.push({
                ...s,
                agentName: ag.agent
              });
            });
          });

          const mcpCols = [
            { id: 'agent', labelKey: 'thSkillAgent', type: 'string', get: s => s.agentName },
            { id: 'name', labelKey: 'thMcpServer', type: 'string', get: s => s.name },
            { id: 'scope', labelKey: 'thMcpScope', type: 'string', get: s => formatMcpScope(s.scope, state.lang) },
            { id: 'configured', labelKey: 'thMcpConfigured', type: 'string', get: s => s.configured === true ? t('mcpConfiguredYes') : (s.configured === false ? t('mcpConfiguredNo') : t('unknown')) },
            { id: 'enabled', labelKey: 'thMcpEnabled', type: 'string', get: s => s.enabled === true ? t('skillActive') : (s.enabled === false ? t('skillInactive') : t('unknown')) },
            { id: 'status', labelKey: 'thMcpStatus', type: 'string', get: s => formatMcpStatus(s.status, state.lang).label },
            { id: 'tools', labelKey: 'thMcpTools', type: 'number', get: s => s.tool_count },
            { id: 'checked', labelKey: 'thMcpCheckedAt', type: 'date', get: s => s.checked_at },
            { id: 'note', labelKey: 'thMcpNote', type: 'string', get: s => s.note }
          ];

          function renderMcpRows() {
            tbody.textContent = '';
            const sortCfg = state.sortState.mcp || { col: 'agent', dir: 'asc' };
            const activeCol = mcpCols.find(c => c.id === sortCfg.col) || mcpCols[0];
            const sortedServers = sortTableData(flatServers, activeCol.get, activeCol.type, sortCfg.dir, state.lang);

            sortedServers.forEach(s => {
              const tr = el('tr');

              tr.appendChild(el('td', { children: [el('strong', { textContent: s.agentName })] }));
              tr.appendChild(el('td', { textContent: s.name || t('unknown') }));
              tr.appendChild(el('td', { textContent: formatMcpScope(s.scope, state.lang) }));

              const cfgText = s.configured === true ? t('mcpConfiguredYes') : (s.configured === false ? t('mcpConfiguredNo') : t('unknown'));
              tr.appendChild(el('td', { textContent: cfgText }));

              const tdEnabled = el('td');
              let enBadgeClass = 'badge';
              let enLabel = t('unknown');
              if (s.enabled === true) {
                enBadgeClass += ' badge-good';
                enLabel = t('skillActive');
              } else if (s.enabled === false) {
                enBadgeClass += ' text-muted';
                enLabel = t('skillInactive');
              }
              tdEnabled.appendChild(el('span', { class: enBadgeClass, textContent: enLabel }));
              tr.appendChild(tdEnabled);

              const tdStatus = el('td');
              const stObj = formatMcpStatus(s.status, state.lang);
              tdStatus.appendChild(el('span', { class: `badge ${stObj.className}`.trim(), textContent: `${stObj.icon} ${stObj.label}` }));
              tr.appendChild(tdStatus);

              const tdTools = el('td', { class: 'token-num' });
              tdTools.textContent = s.tool_count !== null && s.tool_count !== undefined ? String(s.tool_count) : t('unknown');
              tr.appendChild(tdTools);

              const tdChecked = el('td');
              if (s.checked_at) {
                tdChecked.textContent = formatRelativeTime(s.checked_at, new Date(), state.lang);
                tdChecked.setAttribute('title', formatDateTime(s.checked_at, state.lang));
              } else {
                tdChecked.textContent = t('unknown');
              }
              tr.appendChild(tdChecked);

              tr.appendChild(el('td', { class: 'text-muted', textContent: s.note || '' }));

              tbody.appendChild(tr);
            });
          }

          setupSortableHeader('mcp', table, mcpCols, renderMcpRows);
          renderMcpRows();
        }
      }
    }

    if (agentFilterSelect && agentFilterSelect.options.length <= 1) {
      const knownAgents = new Set();
      skillAgents.forEach(sa => knownAgents.add(sa.agent));
      knownAgents.forEach(ag => {
        const opt = el('option', { value: ag, textContent: ag });
        agentFilterSelect.appendChild(opt);
      });
      if (repoSkills.length > 0) {
        agentFilterSelect.appendChild(el('option', { value: REPO_FILTER_VALUE, textContent: t('filterAgentRepo') }));
      }
    }
    // 통합 수정(Claude): 옵션은 한 번만 만들어지므로 언어 전환 때 저장소 옵션 라벨을 다시 쓴다(값은 언어와 무관한 고정값)
    if (agentFilterSelect) {
      const repoOpt = agentFilterSelect.querySelector(`option[value="${REPO_FILTER_VALUE}"]`);
      if (repoOpt) repoOpt.textContent = t('filterAgentRepo');
    }

    const allSkills = [];
    repoSkills.forEach(s => {
      allSkills.push({ ...s, agentName: t('filterAgentRepo'), isRepo: true });
    });
    skillAgents.forEach(sa => {
      const sList = Array.isArray(sa.skills) ? sa.skills : [];
      sList.forEach(s => {
        allSkills.push({ ...s, agentName: sa.agent, isRepo: false });
      });
    });

    const filtered = allSkills.filter(s => {
      const filterKey = s.isRepo ? REPO_FILTER_VALUE : s.agentName;
      if (state.skillsFilterAgent !== 'ALL' && filterKey !== state.skillsFilterAgent) {
        return false;
      }
      if (state.skillsSearchQuery) {
        const q = state.skillsSearchQuery.toLowerCase();
        const matchName = String(s.name || '').toLowerCase().includes(q);
        const matchDesc = String(s.description || '').toLowerCase().includes(q);
        const matchPath = String(s.path || '').toLowerCase().includes(q);
        if (!matchName && !matchDesc && !matchPath) return false;
      }
      return true;
    });

    const skillCols = [
      { id: 'name', labelKey: 'thSkillName', type: 'string', get: s => s.name },
      { id: 'agent', labelKey: 'thSkillAgent', type: 'string', get: s => s.agentName },
      { id: 'enabled', labelKey: 'thSkillStatus', type: 'string', get: s => s.enabled === true ? t('skillActive') : (s.enabled === false ? t('skillInactive') : null) },
      { id: 'invocations', labelKey: 'thSkillInvocations', type: 'number', get: s => s.invocations },
      { id: 'last_used_at', labelKey: 'thSkillLastUsed', type: 'date', get: s => s.last_used_at },
      { id: 'path', labelKey: 'thSkillPath', type: 'string', get: s => s.path },
      { id: 'origin', labelKey: 'thSkillOrigin', type: 'string', get: s => s.origin }
    ];

    const skillsTable = document.getElementById('skills-table');
    const tbody = document.getElementById('skills-tbody');

    function renderSkillsRows() {
      if (!tbody) return;
      tbody.textContent = '';

      if (filtered.length === 0) {
        const emptyTr = el('tr');
        const emptyTd = el('td', { class: 'text-muted' });
        emptyTd.setAttribute('colspan', '7');
        if (repoSkills.length === 0 && allSkills.length === 0) {
          emptyTd.textContent = t('skillsEmptyRepo');
        } else {
          emptyTd.textContent = t('skillsEmptySearch');
        }
        emptyTr.appendChild(emptyTd);
        tbody.appendChild(emptyTr);
        return;
      }

      const sortCfg = state.sortState.skills;
      const activeCol = skillCols.find(c => c.id === sortCfg.col) || skillCols[0];
      const sortedSkills = sortTableData(filtered, activeCol.get, activeCol.type, sortCfg.dir, state.lang);

      sortedSkills.forEach(s => {
        const tr = el('tr');

        const tdName = el('td');
        tdName.appendChild(el('strong', { textContent: s.name || t('unknown') }));
        if (s.description) {
          const transDesc = translateProbeText(s.description, state.lang);
          tdName.appendChild(el('div', { class: 'skill-desc-cell text-muted', textContent: transDesc, title: transDesc }));
        }
        tr.appendChild(tdName);

        tr.appendChild(el('td', { textContent: s.agentName }));

        let enBadgeClass = 'badge';
        let enLabel = t('unknown');
        if (s.enabled === true) {
          enBadgeClass += ' badge-good';
          enLabel = t('skillActive');
        } else if (s.enabled === false) {
          enBadgeClass += ' text-muted';
          enLabel = t('skillInactive');
        }
        const tdEnabled = el('td');
        tdEnabled.appendChild(el('span', { class: enBadgeClass, textContent: enLabel }));
        tr.appendChild(tdEnabled);

        const tdInvocations = el('td');
        if (s.invocations === null || s.invocations === undefined) {
          const rawEv = s.usage_evidence || t('skillUnmeasured');
          const ev = translateProbeText(rawEv, state.lang);
          tdInvocations.appendChild(el('span', { class: 'text-muted', textContent: t('skillUnmeasured'), title: ev }));
        } else {
          const ev = s.usage_evidence ? ` (${translateProbeText(s.usage_evidence, state.lang)})` : '';
          tdInvocations.appendChild(el('span', {
            textContent: `${s.invocations.toLocaleString(state.lang === 'ko' ? 'ko-KR' : 'en-US')} ${t('skillInvocationsSuffix')}`,
            title: `${t('thSkillInvocations')}${ev}`
          }));
        }
        tr.appendChild(tdInvocations);

        tr.appendChild(el('td', {
          textContent: s.last_used_at ? `${formatDateTime(s.last_used_at, state.lang)} (${formatRelativeTime(s.last_used_at, new Date(), state.lang)})` : t('unknown')
        }));

        tr.appendChild(el('td', {
          class: 'skill-path-cell',
          textContent: s.path || t('unknown'),
          title: s.path || ''
        }));

        tr.appendChild(el('td', { textContent: translateProbeText(s.origin, state.lang) || t('unknown') }));

        tbody.appendChild(tr);
      });
    }

    if (skillsTable) {
      setupSortableHeader('skills', skillsTable, skillCols, renderSkillsRows);
      renderSkillsRows();
    }

    const notesContainer = document.getElementById('skills-notes-container');
    const notesList = document.getElementById('skills-notes-list');
    if (notesContainer && notesList) {
      const notes = Array.isArray(skillsRoot.notes) ? skillsRoot.notes : [];
      if (notes.length > 0) {
        notesContainer.classList.remove('hidden');
        notesList.textContent = '';
        notes.forEach(n => {
          notesList.appendChild(el('li', { textContent: translateProbeText(String(n), state.lang) }));
        });
      } else {
        notesContainer.classList.add('hidden');
      }
    }
  }

  // Setup Global Event Listeners
  window.addEventListener('hashchange', renderRoute);

  const btnRefresh = document.getElementById('btn-manual-refresh');
  if (btnRefresh) {
    btnRefresh.addEventListener('click', () => {
      fetchSnapshot();
    });
  }

  const btnLang = document.getElementById('btn-toggle-lang');
  if (btnLang) {
    btnLang.addEventListener('click', () => {
      applyLang(state.lang === 'ko' ? 'en' : 'ko');
    });
  }

  const btnTheme = document.getElementById('btn-toggle-theme');
  if (btnTheme) {
    btnTheme.addEventListener('click', () => {
      applyTheme(state.theme === 'dark' ? 'light' : 'dark');
      renderHistory(); // Re-render chart strokes
    });
  }

  const rangeButtons = document.querySelectorAll('.btn-range');
  rangeButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      rangeButtons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const hours = parseInt(btn.getAttribute('data-hours'), 10) || 24;
      fetchHistory(hours);
    });
  });

  const filterSelect = document.getElementById('filter-skill-agent');
  if (filterSelect) {
    filterSelect.addEventListener('change', (e) => {
      state.skillsFilterAgent = e.target.value;
      if (state.snapshotState && state.snapshotState.snapshot) {
        renderSkillsView(state.snapshotState.snapshot);
      }
    });
  }

  const searchInput = document.getElementById('input-skill-search');
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      state.skillsSearchQuery = e.target.value.trim();
      if (state.snapshotState && state.snapshotState.snapshot) {
        renderSkillsView(state.snapshotState.snapshot);
      }
    });
  }

  // Initial Theme & Language Setup
  applyTheme(state.theme);
  applyLang(state.lang);

  // Initial Load & 15s Polling (AC2)
  renderRoute();
  fetchSnapshot();
  state.pollTimer = setInterval(fetchSnapshot, 15000);
})();

// ==========================================
// 3. CommonJS Export for Testing
// ==========================================
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    I18N,
    compareValues,
    sortTableData,
    formatValue,
    formatPercent,
    formatBytes,
    formatTokens,
    formatRelativeTime,
    formatDateTime,
    formatResolutionLabel,
    formatTelemetryMode,
    formatAgentStatus,
    calculateSvgPath,
    isHistoricalPlan,
    formatLimitLabel,
    formatInferenceKey,
    calculateChartAxes,
    formatNativeTokenType,
    formatNativeUsage,
    formatSkillCounts,
    formatGpuProcesses,
    translateProbeText,
    KNOWN_PROBE_TRANSLATIONS,
    selectPrimaryModel,
    selectMaxLimit,
    calculateAgentKpi,
    calculateSkillBreakdown,
    calculateMcpSummary,
    formatMcpStatus,
    formatMcpScope
  };
}
