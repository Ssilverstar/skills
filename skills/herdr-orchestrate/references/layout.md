# Tested layout and lifecycle observations

Verified with Herdr 0.9.5 on 2026-10-31, Linux ARM64. Discover command groups again
when the installed version differs. Run `herdr pane` and `herdr agent` for current
syntax; these help invocations may exit 2 without indicating a runtime failure.

## Three columns with a worker group

1. Inspect `herdr pane list --workspace <workspace>` and
   `herdr pane layout --pane <caller>`.
2. From a single caller pane, split right using `--ratio 0.34`, explicit cwd and
   `--no-focus`. In this version the ratio is the original/left share.
3. Split the returned right pane right using `--ratio 0.5`. The first returned
   pane is the middle orchestrator, the next is the worker column.
4. Split the worker pane down with `--ratio 0.5` when a second worker is actually
   requested or useful. Use the returned ID for that worker.
5. Rename panels to show role and model. Verify rectangles: caller left,
   orchestrator middle, workers share the right x-coordinate.

Example command form (substitute discovered IDs; angle brackets are placeholders):

```bash
herdr pane split --pane <caller> --direction right --ratio 0.34 --cwd <repo> --no-focus
herdr agent start <unique-name> --kind claude --pane <middle> -- --model claude-opus-5-5 --effort high
herdr agent start <worker-name> --kind agy --pane <worker> -- --model gemini-3.8-flash-medium --mode accept-edits
herdr agent start <qa-name> --kind opencode --pane <qa-worker>
```

These models were observed locally; they are not universal defaults. `accept-edits`
is appropriate for an authorized file implementation task. Use `plan` for a
read-only task. OpenCode's default model must be verified after startup.

## Recovery details

- A previous agent process can leave a pane unavailable to `agent start`; inspect
  its foreground process and UI rather than repeatedly trying to start another.
- `agent start` requires an available shell. A shell-looking viewport alone does
  not guarantee that the previous foreground process exited.
- Agent names may change or disappear when a process is replaced. Re-discover
  live identity before resuming. Pane IDs are not reused after closure.
- A model picker or permissions screen is not a prompt. Inspect it before sending
  text; route dialogs through `agent send-keys` with inspected choices.
- `herdr agent prompt` to a working Claude queues a message. If a change of scope
  requires stopping overlapping edits immediately, interrupt that task, inspect
  partial artifacts and then deliver the ownership change once.
- For user-requested cleanup, close explicit task panes, then verify both the pane
  list and split layout. Focus and width should return to the retained caller.
