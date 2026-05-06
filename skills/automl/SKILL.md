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

## Migration from v5.10

`/automl-legacy` runs frozen v5.10 during the 4-6 week migration window. Removed flags: `--cap` (calibrator handles), `--max-ticks` (renamed `--max-iter`). `--goal` replaced by `--no-budget` for clearer semantics.

## Adapter status

- v6.0: claude-code (this skill)
- v6.1: Codex `/goal` adapter (≥4 weeks after v6.0 stable)
- v6.2: Gemini adapter (≥8 weeks after v6.0)
