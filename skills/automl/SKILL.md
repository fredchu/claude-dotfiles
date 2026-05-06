---
name: automl
version: 6.0.0
description: |
  Autonomous Evaluation Loop — calibrated alignment + round loop + audit discipline + always-on gates + RED_TEAM opt-in + multi-session lock + cross-session quota coordination + worktree advisory + orphan recovery + calibrator self-improvement telemetry.
  Triggered: /automl, "let it run to completion", "let it run until done".
allowed-tools:
  - Agent
  - Read
  - Write
  - Edit
  - Bash
---

# /automl v6.0

Calibrator subagent → alignment dialogue → round loop → audit → terminal lifecycle, with 6 always-on gates (iteration / wall-time / repeat-loop / budget / context / quota) via FIXED ORDER `tick_gate` orchestrator + RED_TEAM opt-in dispatch + multi-session safety (active_session lock, cross-session quota coordination, worktree advisory, orphan recovery) + calibrator self-improvement telemetry (`run_summary.md` per terminal run, weekly aggregator alerts on Discord).

Spec: `docs/superpowers/specs/2026-05-06-automl-v6-design.md`
Algorithm: `ALGORITHM.md`
Changelog: `CHANGELOG.md`

## Commands

```
/automl <freeform goal description>     start a new run (calibrator + alignment + round loop)
/automl --spec <path/to/goal.md>        start from existing goal.md (skip alignment)
/automl pause [run_id]                  pause an active run (release session lock)
/automl resume [run_id]                 resume a paused run (claim session lock)
/automl status [run_id]                 multi-section run status (spec §8.3 format)
/automl clear <run_id>                  delete a terminal run's directory
/automl list                            scan cwd .automl/ + per-run summary
/automl history                         calibrator vs actual telemetry across runs
```

## Flags

```
--no-budget                  disable calibrated budget cap
--budget <int>               override calibrator's budget estimate
--depth shallow|normal|deep  override calibrator's dialogue depth
--red-team                   force RED_TEAM dispatch
--no-red-team                force skip RED_TEAM
--no-codex                   route Codex tasks to sonnet/opus fallback
--max-iter <int>             ultimate safety cap (default 10000)
--max-wall <hours>           ultimate safety cap (default 72)
--force-fallback <dep>       debug: force a soft dep to fallback path
--cli claude|codex|gemini    debug: force adapter (v6.0 only ships claude)
--allow-cwd-conflict         override worktree advisory for concurrent same-cwd
--autonomous                 silent orphan takeover, no interactive prompts
```

`--red-team` + `--no-red-team` are mutually exclusive.

## Invocation routing (main session — read this before dispatching)

Use `scripts/cli_parser.py::parse_args` to parse the user's `/automl ...` arguments into a `ParsedCommand`, then route as follows:

| ParsedCommand shape | Action |
|---|---|
| `command == "invoke"` AND `flags.get("spec")` is set | **Spec bypass path.** Call `scripts/spec_bypass.py::init_run_from_spec(spec_path, run_dir, session_id, pid)`. This reads + validates the existing `goal.md`, copies it into `run_dir/`, writes `state.json` with lifecycle directly at `pursuing` (transition history shows `aligning → pursuing` reason `"spec bypass"`), and seeds `criteria_progress` from the goal's `acceptance_criteria`. **Do NOT dispatch the calibrator subagent. Do NOT run the alignment dialogue.** Skip Phase 0 + Phase 1 entirely; jump straight to the Phase 2 round loop. |
| `command == "invoke"` AND no `spec` flag, freeform present | Default path: Phase 0 calibrator subagent (using `prompts/calibrator.md`) → Phase 1 alignment dialogue → write `goal.md` + init `state.json` → Phase 2 round loop. |
| `command == "pause"` | Call `scripts/lifecycle_commands.py::pause(state)`; write returned state. |
| `command == "resume"` | Call `scripts/lifecycle_commands.py::resume(state, session_id, pid)`; write returned state. |
| `command == "clear"` | Call `scripts/lifecycle_commands.py::clear(state)`; on success, `rm -rf` the run directory. |
| `command == "status"` | Read state.json + calibrator.json (best-effort) + env.json + quota → call `scripts/status_renderer.py::render_status(...)` → print. |
| `command == "list"` | Call `scripts/list_command.py::collect_runs(automl_dir)` then `render_list(rows)` → print. |
| `command == "history"` | Call `scripts/history_command.py::collect_history(automl_dir)` then `render_history(rows)` → print. |

For `--spec` bypass specifically: the run inherits its `run_id` from the goal.md frontmatter. `run_dir` is `cwd/.automl/{run_id}/`. Because no calibrator was dispatched, no `calibrator.json` is written; `run_summary.py::write_run_summary` is null-safe and will produce a slimmer telemetry block (estimated_tokens=0, diff_pct=null, etc.) at the terminal hook.

## Migration from v5.10

`/automl-legacy` runs frozen v5.10 during the 4-6 week migration window. Removed flags: `--cap` (calibrator handles), `--max-ticks` (renamed `--max-iter`). `--goal` replaced by `--no-budget` for clearer semantics.

## Adapter status

- v6.0: claude-code (this skill)
- v6.1: Codex `/goal` adapter (≥4 weeks after v6.0 stable)
- v6.2: Gemini adapter (≥8 weeks after v6.0)
