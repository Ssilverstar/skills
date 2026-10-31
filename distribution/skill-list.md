# 합의된 스킬 사용 목록

원본: [codex-general-sw.json](profiles/codex-general-sw.json). 이 문서는 `python3 distribution/render_skill_list.py`로 생성합니다. 직접 편집하지 않습니다.

2026-10-31 · Codex + Opus 5.5 high 합의. [공통 기준·에이전트별 예외](skill-policy.md)를 함께 적용합니다.

Codex 프로필 검토 목록 395개(로컬·앱 항목 포함): 활성 36개, 비활성 359개. 개수는 목표가 아니라 이 환경의 결과입니다.

전체 기본 선택 36개는 네 에이전트 공통입니다. Claude ECC 전체 노출 예외는 폐기했습니다. 플랫폼 내장·앱 동기화 항목은 별도이며 실제 도구 전제조건을 충족해야 실행할 수 있습니다.

## 공통 목록과 실제 이름

원본: [common-general-sw.json](profiles/common-general-sw.json). Claude의 ECC 13개는 `ecc-common` 로컬 플러그인으로 배포하며 원본 훅·보조 파일을 보존합니다.

| 공통 ID | Claude | OpenCode / Antigravity | 실행 전제 |
| --- | --- | --- | --- |
| `archify` | `archify` | `archify` | Consult SKILL.md and verify current tools |
| `docx` | `anthropic-skills:docx` | `docx` | Consult SKILL.md and verify current tools |
| `ecc:accessibility` | `ecc-common:accessibility` | `accessibility` | Consult SKILL.md and verify current tools |
| `ecc:api-design` | `ecc-common:api-design` | `api-design` | Consult SKILL.md and verify current tools |
| `ecc:architecture-decision-records` | `ecc-common:architecture-decision-records` | `architecture-decision-records` | Consult SKILL.md and verify current tools |
| `ecc:browser-qa` | `ecc-common:browser-qa` | `browser-qa` | Available browser automation; local Playwright Chromium is available |
| `ecc:codebase-onboarding` | `ecc-common:codebase-onboarding` | `codebase-onboarding` | Consult SKILL.md and verify current tools |
| `ecc:coding-standards` | `ecc-common:coding-standards` | `coding-standards` | Consult SKILL.md and verify current tools |
| `ecc:database-migrations` | `ecc-common:database-migrations` | `database-migrations` | Consult SKILL.md and verify current tools |
| `ecc:deployment-patterns` | `ecc-common:deployment-patterns` | `deployment-patterns` | Consult SKILL.md and verify current tools |
| `ecc:docker-patterns` | `ecc-common:docker-patterns` | `docker-patterns` | Consult SKILL.md and verify current tools |
| `ecc:error-handling` | `ecc-common:error-handling` | `error-handling` | Consult SKILL.md and verify current tools |
| `ecc:git-workflow` | `ecc-common:git-workflow` | `git-workflow` | Consult SKILL.md and verify current tools |
| `ecc:github-ops` | `ecc-common:github-ops` | `github-ops` | Consult SKILL.md and verify current tools |
| `ecc:security-review` | `ecc-common:security-review` | `security-review` | Consult SKILL.md and verify current tools |
| `graft` | `graft` | `graft` | Existing repository graft/ index; no init without request |
| `herdr` | `herdr` | `herdr` | HERDR_ENV=1 |
| `herdr-orchestrate` | `herdr-orchestrate` | `herdr-orchestrate` | HERDR_ENV=1, explicit orchestration request |
| `humanize-korean` | `humanize-korean:humanize-korean` | `humanize-korean` | Consult SKILL.md and verify current tools |
| `imagegen` | `imagegen` | `imagegen` | Native image generation tool; paid API fallback only on explicit request |
| `openai-docs` | `openai-docs` | `openai-docs` | Consult SKILL.md and verify current tools |
| `pdf` | `anthropic-skills:pdf` | `pdf` | Consult SKILL.md and verify current tools |
| `ponytail:ponytail` | `ponytail:ponytail` | `ponytail` | Consult SKILL.md and verify current tools |
| `ponytail:ponytail-audit` | `ponytail:ponytail-audit` | `ponytail-audit` | Consult SKILL.md and verify current tools |
| `ponytail:ponytail-debt` | `ponytail:ponytail-debt` | `ponytail-debt` | Consult SKILL.md and verify current tools |
| `ponytail:ponytail-gain` | `ponytail:ponytail-gain` | `ponytail-gain` | Consult SKILL.md and verify current tools |
| `ponytail:ponytail-help` | `ponytail:ponytail-help` | `ponytail-help` | Consult SKILL.md and verify current tools |
| `ponytail:ponytail-review` | `ponytail:ponytail-review` | `ponytail-review` | Consult SKILL.md and verify current tools |
| `prefer-gh-for-github` | `prefer-gh-for-github:prefer-gh-for-github` | `prefer-gh-for-github` | Consult SKILL.md and verify current tools |
| `review-agent` | `review-agent` | `review-agent` | Consult SKILL.md and verify current tools |
| `skill-creator` | `skill-creator:skill-creator` | `skill-creator` | Consult SKILL.md and verify current tools |
| `skill-installer` | `skill-installer` | `skill-installer` | Always pass --dest for the current agent; never default to another agent home |
| `superpowers:systematic-debugging` | `systematic-debugging` | `systematic-debugging` | Consult SKILL.md and verify current tools |
| `superpowers:test-driven-development` | `test-driven-development` | `test-driven-development` | Consult SKILL.md and verify current tools |
| `superpowers:verification-before-completion` | `verification-before-completion` | `verification-before-completion` | Consult SKILL.md and verify current tools |
| `visualize:visualize` | `visualize` | `visualize` | Codex inline visualization surface; other agents use a standalone HTML artifact only when requested |

## 필수 — 네 에이전트 모두 보존/설치 (8개)

사용자가 지정한 8개. 강한 트리거도 사용자 필수 예외로 보존.

- `archify`
- `graft`
- `ponytail:ponytail`
- `ponytail:ponytail-audit`
- `ponytail:ponytail-debt`
- `ponytail:ponytail-gain`
- `ponytail:ponytail-help`
- `ponytail:ponytail-review`

## 기본 유지 — 공통 선택 목록 (28개)

도구 전제조건과 호스트별 별칭은 공통 프로필에 기록. 전체 워크플로 호환성 인증은 아님.

- `docx`
- `ecc:accessibility`
- `ecc:api-design`
- `ecc:architecture-decision-records`
- `ecc:browser-qa`
- `ecc:codebase-onboarding`
- `ecc:coding-standards`
- `ecc:database-migrations`
- `ecc:deployment-patterns`
- `ecc:docker-patterns`
- `ecc:error-handling`
- `ecc:git-workflow`
- `ecc:github-ops`
- `ecc:security-review`
- `herdr`
- `herdr-orchestrate`
- `humanize-korean`
- `imagegen`
- `openai-docs`
- `pdf`
- `prefer-gh-for-github`
- `review-agent`
- `skill-creator`
- `skill-installer`
- `superpowers:systematic-debugging`
- `superpowers:test-driven-development`
- `superpowers:verification-before-completion`
- `visualize:visualize`

## 프로젝트별 사용 (2개)

해당 스택 작업에서 선택. 현재 Codex 전역에서는 비활성.

- `ecc:python-patterns`
- `ecc:python-testing`

## Codex 호환성 제외 (41개)

Claude 전용 하네스/명령 또는 도구 전제. 다른 에이전트는 자체 호환성을 판단.

- `ecc:ck`
- `ecc:config-gc`
- `ecc:continuous-learning`
- `ecc:continuous-learning-v2`
- `ecc:security-scan`
- `ecc:skill-stocktake`
- `ecc:source-command-auto-update`
- `ecc:source-command-build-fix`
- `ecc:source-command-cpp-review`
- `ecc:source-command-ecc-guide`
- `ecc:source-command-epic-claim`
- `ecc:source-command-epic-decompose`
- `ecc:source-command-epic-publish`
- `ecc:source-command-epic-review`
- `ecc:source-command-epic-sync`
- `ecc:source-command-epic-unblock`
- `ecc:source-command-epic-validate`
- `ecc:source-command-fastapi-review`
- `ecc:source-command-feature-dev`
- `ecc:source-command-go-build`
- `ecc:source-command-go-review`
- `ecc:source-command-gradle-build`
- `ecc:source-command-hookify`
- `ecc:source-command-hookify-configure`
- `ecc:source-command-hookify-help`
- `ecc:source-command-hookify-list`
- `ecc:source-command-instinct-export`
- `ecc:source-command-instinct-import`
- `ecc:source-command-instinct-status`
- `ecc:source-command-jira`
- `ecc:source-command-learn`
- `ecc:source-command-plan-canvas`
- `ecc:source-command-projects`
- `ecc:source-command-promote`
- `ecc:source-command-prune`
- `ecc:source-command-refactor-clean`
- `ecc:source-command-review-pr`
- `ecc:source-command-setup-pm`
- `ecc:source-command-test-coverage`
- `ecc:source-command-update-codemaps`
- `ecc:source-command-update-docs`

## 중복/강제 트리거 제외 (4개)

대표 기능과 중복하거나 작업 범위를 강제하는 흐름. 사용자 요청 시 재검토.

- `ecc:dmux-workflows`
- `ecc:tdd-workflow`
- `superpowers:brainstorming`
- `superpowers:using-superpowers`

## 검토 보류 — 현재 Codex 전역 비활성 (312개)

불필요 판정이 아님. 최초 일괄 제외 상태를 승계했으며 본문·사용 필요를 확인한 후 복구 가능.

- `ecc:agent-architecture-audit`
- `ecc:agent-eval`
- `ecc:agent-harness-construction`
- `ecc:agent-introspection-debugging`
- `ecc:agent-payment-x402`
- `ecc:agent-self-evaluation`
- `ecc:agent-sort`
- `ecc:agentic-engineering`
- `ecc:agentic-os`
- `ecc:ai-first-engineering`
- `ecc:ai-regression-testing`
- `ecc:android-clean-architecture`
- `ecc:angular-developer`
- `ecc:api-connector-builder`
- `ecc:article-writing`
- `ecc:automation-audit-ops`
- `ecc:autonomous-agent-harness`
- `ecc:autonomous-loops`
- `ecc:backend-patterns`
- `ecc:benchmark`
- `ecc:benchmark-methodology`
- `ecc:benchmark-optimization-loop`
- `ecc:blender-motion-state-inspection`
- `ecc:blueprint`
- `ecc:brand-discovery`
- `ecc:brand-voice`
- `ecc:bun-runtime`
- `ecc:canary-watch`
- `ecc:carrier-relationship-management`
- `ecc:cisco-ios-patterns`
- `ecc:claude-devfleet`
- `ecc:click-path-audit`
- `ecc:clickhouse-io`
- `ecc:code-tour`
- `ecc:codehealth-mcp`
- `ecc:competitive-platform-analysis`
- `ecc:competitive-report-structure`
- `ecc:compose-multiplatform-patterns`
- `ecc:configure-ecc`
- `ecc:connections-optimizer`
- `ecc:content-engine`
- `ecc:content-hash-cache-pattern`
- `ecc:context-budget`
- `ecc:continuous-agent-loop`
- `ecc:contract-first`
- `ecc:cost-aware-llm-pipeline`
- `ecc:cost-tracking`
- `ecc:council`
- `ecc:council-multi-model`
- `ecc:counterparty-channel-discipline`
- `ecc:cpp-coding-standards`
- `ecc:cpp-testing`
- `ecc:crosspost`
- `ecc:csharp-testing`
- `ecc:customer-billing-ops`
- `ecc:customs-trade-compliance`
- `ecc:dart-flutter-patterns`
- `ecc:dashboard-builder`
- `ecc:data-scraper-agent`
- `ecc:data-throughput-accelerator`
- `ecc:deep-research`
- `ecc:defi-amm-security`
- `ecc:delivery-gate`
- `ecc:design-system`
- `ecc:dev-team`
- `ecc:django-celery`
- `ecc:django-patterns`
- `ecc:django-security`
- `ecc:django-tdd`
- `ecc:django-verification`
- `ecc:documentation-lookup`
- `ecc:dotnet-patterns`
- `ecc:dynamic-workflow-mode`
- `ecc:e2e-testing`
- `ecc:ecc-guide`
- `ecc:ecc-recipes`
- `ecc:ecc-tools-cost-audit`
- `ecc:email-ops`
- `ecc:energy-procurement`
- `ecc:enterprise-agent-ops`
- `ecc:esign-field-placement`
- `ecc:eval-harness`
- `ecc:evm-token-decimals`
- `ecc:exa-search`
- `ecc:fal-ai-media`
- `ecc:fastapi-patterns`
- `ecc:finance-billing-ops`
- `ecc:flox-environments`
- `ecc:flutter-dart-code-review`
- `ecc:foundation-models-on-device`
- `ecc:frontend-a11y`
- `ecc:frontend-design-direction`
- `ecc:frontend-patterns`
- `ecc:frontend-slides`
- `ecc:fsharp-testing`
- `ecc:gan-style-harness`
- `ecc:gateguard`
- `ecc:generating-python-installer`
- `ecc:golang-patterns`
- `ecc:golang-testing`
- `ecc:google-workspace-ops`
- `ecc:growth-log`
- `ecc:healthcare-cdss-patterns`
- `ecc:healthcare-emr-patterns`
- `ecc:healthcare-eval-harness`
- `ecc:healthcare-phi-compliance`
- `ecc:hermes-imports`
- `ecc:hexagonal-architecture`
- `ecc:hipaa-compliance`
- `ecc:homelab-network-readiness`
- `ecc:homelab-network-setup`
- `ecc:homelab-pihole-dns`
- `ecc:homelab-vlan-segmentation`
- `ecc:homelab-wireguard-vpn`
- `ecc:hookify-rules`
- `ecc:i18n-sync`
- `ecc:inherit-legacy-style`
- `ecc:intent-driven-development`
- `ecc:inventory-demand-planning`
- `ecc:investor-materials`
- `ecc:investor-outreach`
- `ecc:ios-icon-gen`
- `ecc:iterative-retrieval`
- `ecc:ito-baskets`
- `ecc:ito-compute`
- `ecc:ito-inference`
- `ecc:ito-training`
- `ecc:java-coding-standards`
- `ecc:jira-integration`
- `ecc:jpa-patterns`
- `ecc:knowledge-ops`
- `ecc:kotlin-coroutines-flows`
- `ecc:kotlin-exposed-patterns`
- `ecc:kotlin-ktor-patterns`
- `ecc:kotlin-patterns`
- `ecc:kotlin-testing`
- `ecc:kubernetes-patterns`
- `ecc:laravel-patterns`
- `ecc:laravel-plugin-discovery`
- `ecc:laravel-security`
- `ecc:laravel-tdd`
- `ecc:laravel-verification`
- `ecc:latency-critical-systems`
- `ecc:lead-intelligence`
- `ecc:liquid-glass-design`
- `ecc:living-docs-governance`
- `ecc:llm-trading-agent-security`
- `ecc:logistics-exception-management`
- `ecc:loop-design-check`
- `ecc:mailtrap-email-integration`
- `ecc:make-interfaces-feel-better`
- `ecc:manim-video`
- `ecc:market-research`
- `ecc:marketing-campaign`
- `ecc:master-agreement-generator`
- `ecc:mcp-server-patterns`
- `ecc:messages-ops`
- `ecc:ml-adoption-playbook`
- `ecc:mle-workflow`
- `ecc:motion-advanced`
- `ecc:motion-foundations`
- `ecc:motion-patterns`
- `ecc:mysql-patterns`
- `ecc:nanoclaw-repl`
- `ecc:nasiko-control-plane`
- `ecc:nestjs-patterns`
- `ecc:netmiko-ssh-automation`
- `ecc:network-bgp-diagnostics`
- `ecc:network-config-validation`
- `ecc:network-interface-health`
- `ecc:nextjs-turbopack`
- `ecc:nodejs-keccak256`
- `ecc:nutrient-document-processing`
- `ecc:nuxt4-patterns`
- `ecc:openclaw-persona-forge`
- `ecc:opensource-pipeline`
- `ecc:operator-approval-loop`
- `ecc:orch-add-feature`
- `ecc:orch-build-mvp`
- `ecc:orch-change-feature`
- `ecc:orch-fix-defect`
- `ecc:orch-pipeline`
- `ecc:orch-refine-code`
- `ecc:parallel-execution-optimizer`
- `ecc:perl-patterns`
- `ecc:perl-security`
- `ecc:perl-testing`
- `ecc:plan-canvas`
- `ecc:plan-orchestrate`
- `ecc:plankton-code-quality`
- `ecc:postgres-patterns`
- `ecc:prediction-market-oracle-research`
- `ecc:prediction-market-risk-review`
- `ecc:prisma-patterns`
- `ecc:product-capability`
- `ecc:product-lens`
- `ecc:production-audit`
- `ecc:production-scheduling`
- `ecc:project-flow-ops`
- `ecc:prompt-optimizer`
- `ecc:pytorch-patterns`
- `ecc:quality-nonconformance`
- `ecc:quarkus-patterns`
- `ecc:quarkus-security`
- `ecc:quarkus-tdd`
- `ecc:quarkus-verification`
- `ecc:rails-patterns`
- `ecc:ralphinho-rfc-pipeline`
- `ecc:react-native-patterns`
- `ecc:react-patterns`
- `ecc:react-performance`
- `ecc:react-testing`
- `ecc:recsys-pipeline-architect`
- `ecc:recursive-decision-ledger`
- `ecc:redis-patterns`
- `ecc:regex-vs-llm-structured-text`
- `ecc:remotion-video-creation`
- `ecc:repo-scan`
- `ecc:research-ops`
- `ecc:returns-reverse-logistics`
- `ecc:rules-distill`
- `ecc:rust-patterns`
- `ecc:rust-testing`
- `ecc:safety-guard`
- `ecc:santa-method`
- `ecc:scientific-db-pubmed-database`
- `ecc:scientific-db-uspto-database`
- `ecc:scientific-pkg-gget`
- `ecc:scientific-thinking-literature-review`
- `ecc:scientific-thinking-scholar-evaluation`
- `ecc:search-first`
- `ecc:security-bounty-hunter`
- `ecc:seo`
- `ecc:skill-comply`
- `ecc:skill-scout`
- `ecc:social-graph-ranker`
- `ecc:social-publisher`
- `ecc:springboot-patterns`
- `ecc:springboot-security`
- `ecc:springboot-tdd`
- `ecc:springboot-verification`
- `ecc:strategic-compact`
- `ecc:swift-actor-persistence`
- `ecc:swift-concurrency-6-2`
- `ecc:swift-protocol-di-testing`
- `ecc:swiftui-patterns`
- `ecc:taste`
- `ecc:taste-application`
- `ecc:taste-distillation`
- `ecc:tasteforge-video`
- `ecc:team-agent-orchestration`
- `ecc:team-builder`
- `ecc:terminal-opener`
- `ecc:terminal-ops`
- `ecc:tinystruct-patterns`
- `ecc:token-budget-advisor`
- `ecc:ui-demo`
- `ecc:ui-to-vue`
- `ecc:uncloud`
- `ecc:unified-memory`
- `ecc:unified-notifications-ops`
- `ecc:verification-loop`
- `ecc:video-editing`
- `ecc:videodb`
- `ecc:visa-doc-translate`
- `ecc:vite-patterns`
- `ecc:vue-patterns`
- `ecc:windows-desktop-e2e`
- `ecc:workspace-surface-audit`
- `ecc:x-api`
- `openai-templates:artifact-template-analytics-dashboard`
- `openai-templates:artifact-template-business-review`
- `openai-templates:artifact-template-design-report`
- `openai-templates:artifact-template-experiment-analysis`
- `openai-templates:artifact-template-financial-budget`
- `openai-templates:artifact-template-investment-committee-memo`
- `openai-templates:artifact-template-legal-memorandum`
- `openai-templates:artifact-template-market-trends-report`
- `openai-templates:artifact-template-minimal-letterhead`
- `openai-templates:artifact-template-operating-calendar`
- `openai-templates:artifact-template-operating-review`
- `openai-templates:artifact-template-project-kickoff`
- `openai-templates:artifact-template-project-tracker`
- `openai-templates:artifact-template-sales-pipeline`
- `openai-templates:artifact-template-simple-dark-mode`
- `openai-templates:artifact-template-simple-light-mode`
- `openai-templates:artifact-template-strategy-memorandum`
- `openai-templates:artifact-template-system-design`
- `openai-templates:artifact-template-team-alignment`
- `openai-templates:artifact-template-three-statement-forecast`
- `pages:maintain-space`
- `pages:manage-schedules`
- `pages:organize-space`
- `pages:write-page`
- `plugin-management:plugin-management`
- `pptx`
- `sites:sites`
- `sites:sites-remix`
- `superpowers:dispatching-parallel-agents`
- `superpowers:executing-plans`
- `superpowers:finishing-a-development-branch`
- `superpowers:receiving-code-review`
- `superpowers:requesting-code-review`
- `superpowers:subagent-driven-development`
- `superpowers:using-git-worktrees`
- `superpowers:writing-plans`
- `superpowers:writing-skills`
- `web-slides`
- `work-pets:create-pet`
- `work-pets:pets`
- `work-pets:update-pet`
- `xlsx`
