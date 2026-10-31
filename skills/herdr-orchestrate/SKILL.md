---
name: herdr-orchestrate
description: "Coordinate an explicitly requested Herdr multi-agent workflow: preserve the chosen orchestrator, assign bounded tasks, verify results, and record integration evidence. Use when the user asks to orchestrate agents or improve Herdr workflows, not for ordinary standalone coding."
---

# Herdr orchestration

Use the installed Herdr skill or `herdr --skill` for command semantics. Verify
`HERDR_ENV=1`, then discover the current layout and live identities. This skill
adds workflow decisions; it does not replace the installed CLI's documentation.

## Establish who controls whom

Read the user's role assignment before assigning work. A controller that prepares
panels is not automatically the implementation orchestrator. If Claude is named
as the orchestrator, Claude issues worker prompts, handles their contracts and
integrates results. Codex may implement its explicitly owned slice or perform
independent review; it should not quietly become the workers' second manager.

Interpret `Codex | Claude | Agents` as three columns when requested. Multiple
workers occupy vertical splits in the right column. Preserve caller focus and
cwd. Use returned pane IDs, never predicted IDs. Confirm model identity in each
worker UI; an agent name alone does not prove the model or authentication.

For the tested three-column construction and recovery details, read
[the layout reference](references/layout.md). Adapt to the requested layout and
available width rather than imposing this layout on every task.

When changing session settings, verify that the running session picked them up.
Antigravity `/statusline` is a toggle: inspect its output and the actual sample
before sending it again; a second invocation can turn collection off.

## Delegate work that can be checked

Before editing, inspect existing instructions and the files necessary for the
task. Read only the relevant sections of long guides. A local write hook may
require callers, existing equivalents, data schema and the literal user request
before creating a file: provide those facts before the write, preserve the hook,
and inspect whether any partial edit happened after a denied call.

Use [the contract reference](references/contracts.md) when assigning implementation
or verification. Give each worker a small, explicit file set, inputs, acceptance
criteria, test commands and a concise result format. Keep shared APIs under one
owner. Capture existing file state when ownership changes. Avoid assigning the
same file to two writers; use isolated worktrees if the agreed workflow calls for
them, or explicitly record disjoint file ownership in a shared workspace.

Set a task-specific first-artifact checkpoint (for example, ten minutes for a
small test file). If it passes without an artifact, inspect the blocker and narrow
or reassign the task; this is a checkpoint, not an automatic termination timer.

The orchestrator should dispatch independent work promptly and reserve its own
effort for contracts, integration and difficult failures. Worker count is not a
success metric. Respect the user's selected models and local substitutions; do
not assume a home Antigravity deployment is approved for a corporate environment.

## Observe actual progress

Use agent controls for recognized agents and raw pane controls only for intended
shell work. Check status, then read `visible` when onboarding, working or blocked;
read `recent-unwrapped` for completed results. Prefer settled-state waits to
repeated large transcript reads. A successful prompt submission is not proof of
execution. After timeout or a stalled prompt, inspect before resubmitting.

Herdr can report Antigravity `idle` while a file permission dialog is visible.
After a wait returns, verify the actual response or dialog. Do not equate `idle`,
`done`, exit code 0, or an outer JSON `SUCCESS` with passing the task. A headless
response can be empty and contain `denied_actions` despite success status.

If a watcher is used, emit only changed approval/result events and distinguish a
new request from a duplicate notification. Read the full command before approving
a truncated multi-command prompt. Repeated test approval can dominate orchestration
time: prepare supported, task-scoped permissions up front where appropriate, or
batch the already-authorized checks, without switching to unrestricted mode.
Keep reading an approval and sending its response in separate tool calls. If the
full command cannot be inspected, cancel that request and have the worker use a
short command or an inspectable script in its owned path. A contract's allowed
commands list describes scope; it does not grant permissions by itself.
An agent can finish a turn while a background watcher or worker is still active;
keep the overall task open until the requested artifacts and checks are complete.

Only answer permissions already within the user's authorized task. Use the
narrowest applicable choice, such as a single requested file, and preserve
unrelated consent choices. Explain any remaining approval with the actual source.
Do not disable hooks or use blanket permission bypasses to make a check pass.

When a model reaches its usage limit, record the blocked task and its checkpoint.
Do not leave automatic quota retries or watchers unaccounted for at closure. Resume
through the named orchestrator when the limit clears; changing to another paid
provider is not an implicit fallback.

## Integrate and finish

The orchestrator checks actual artifacts and test output, not only the worker's
summary. Keep failed tests and blockers visible. After two unsuccessful repairs
of the same issue, change owner, narrow the contract or explicitly report the
blocker rather than running the same loop indefinitely.

Batch review feedback into one worker request when practical. After the worker
finishes, an integrator may take ownership of a remaining small fix, record that
transfer, and rerun the affected checks. Avoid another multi-minute delegation
round for a few lines when the contract permits direct integration.

Mark unexecuted checks `not_run` with a null exit code. For UI acceptance inspect
real screenshots or browser checks. Inspect stderr as well as exit status: a
Python destructor ResourceWarning can be printed despite exit code zero. Check
that a test runner reports the intended assertions, not merely loaded file counts.
Check end-to-end capability separately from discovery: an MCP tools list can pass
while its browser fails to launch. UI translation checks must cover rendered fixed
text, dynamic data, expanded details, dropdown options and accessibility attributes,
not just the translation dictionary. Inspect actual card counts and table cell
values as well as interactions; a sortable table can still render empty identity
columns. Preserve unknown values instead of silently turning them into zero.
Compare common skill IDs across loaders, keeping aliases,
platform-only extras and missing tool prerequisites explicit.

Before declaring completion, independently verify critical behavior, file scope,
the requested model and final layout. Close only the panels the user authorized
closing. Do not close ongoing worker jobs based on status alone. Never stop the
Herdr server to tidy a task's panels.

Use a final completion barrier for **every assigned task**, including evidence-only
workers. Match the latest prompt/task ID with its final RESULT and artifact mtime;
an older RESULT or a newly created file is not proof that the current turn ended.
Read each worker's actual visible UI after the result: check for active thinking,
tool execution, queued prompts and approval dialogs. Check the orchestrator's
background monitors and uncollected child tasks too. Recheck status and artifacts
after integration; if they change, repeat the affected verification.

Record a closure manifest with observation time, task ID, pane/model, final result,
artifact path/hash, inspected UI state, test exit/stderr, and remaining jobs. Never
report all workers finished while any assigned task is unresolved. A worker CLI
can remain open at its input prompt after finishing; report **task completed,
process retained** separately from **process exited**. If the user's live screen
disagrees with a prior observation, inspect it again and record the discrepancy
without claiming a past state that was not captured.

Record task/model roles, ownership changes, verified commands and exit codes,
remaining limitations, and deployment state in the user's chosen experiment
directory. Save sanitized results, not raw transcripts or account identities.
For architectural comparisons, distinguish measured runs from unexecuted
alternatives. Report coordination time and human corrections alongside tokens;
local token totals, estimated API cost and subscription budget consumption are
different quantities. Do not infer savings without a comparable baseline.
