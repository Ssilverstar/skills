# Bounded task and result contracts

Keep the contract small enough to read before work. It can be inline or a local
file referenced by a prompt. The orchestrator owns changes to shared APIs.

```yaml
task: FE-001
orchestrator: claude
worker: gemini
model: observed-model-id
goal: Three navigation views backed by the agreed snapshot API
read: [contracts/api.md]
write: [app/static/index.html, app/static/style.css, app/static/app.js]
do_not_edit: [app/server.py, host_probe.py]
acceptance:
  - Missing values display as unknown, while numeric zero remains zero
  - All three routes render without console errors
  - Untrusted strings render as text
verification:
  - node --check app/static/app.js
allowed_commands: ["node --check app/static/app.js"] # scope only, not a permission grant
first_artifact_checkpoint: 10 minutes # adjust to task; inspect before reassigning
result: concise status, changed files, test commands and exits, blockers, risks
```

Give raw test evidence or a bounded local result file when a short terminal
summary cannot capture it. A file result is useful for formal experiments and
large reports; do not require duplicate reports for every one-line task.

Completion requires evidence for acceptance criteria. Record at least:

- status: passed / failed / blocked / partial / not_run
- actual agent and model, owned files and any ownership transfer
- actual test command, exit code, relevant result, and where evidence is stored
- blockers and untested behavior
- commit if one exists; never invent or create a commit just to fill this field

An unexecuted check has `status: not_run`, `exit_code: null`, and no invented
passing count. UI acceptance is finalized using the orchestrator's inspected
screenshots or real-browser evidence, not the worker's unchecked assertion.

For controlled comparisons also record observed start/end time, available usage
window, input/output/cache counters, retries and user interventions. Cache is
included in input for some agents and separate for others: normalize before
comparing. One session can use several models; sum tokens by model but deduplicate
sessions at agent level. Failed/denied attempts still consume time and tokens.

An orchestration trial with shared files and live human corrections is not an
isolated performance benchmark. Preserve this distinction when presenting results.
