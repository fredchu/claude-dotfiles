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

# /automl v6 (Phase 1 + 2 dev)

Phase 1 implements: calibrator subagent → alignment dialogue → round loop → audit → terminal lifecycle.
Phase 2 adds: 6 always-on gates (iteration / wall-time / repeat-loop / budget / context / quota) via FIXED ORDER tick_gate orchestrator + RED_TEAM opt-in dispatch.

Spec: `docs/superpowers/specs/2026-05-06-automl-v6-design.md`
Phase 1 plan: `docs/superpowers/plans/2026-05-06-automl-v6-phase1-foundation.md`
Phase 2 plan: `docs/superpowers/plans/2026-05-06-automl-v6-phase2-gates.md`
Algorithm: `ALGORITHM.md`

## Invocation

```
/automl-v6 <freeform goal description>
/automl-v6 status [run_id]
/automl-v6 list
```

(Other commands deferred to Phase 5.)

## Current limitations (after Phase 2)

- No multi-session quota coordination (Phase 3)
- No telemetry (Phase 4)
- No `pause` / `resume` / `clear` / `history` commands (Phase 5)
- Single CC adapter only (Codex/Gemini adapters in v6.1+)

Use v5.10 (`/automl`) for production work until v6.0 ship.
