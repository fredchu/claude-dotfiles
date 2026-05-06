# Changelog

## v6.0.0-alpha.2 — 2026-05-06 (Phase 2 dev complete)

Phase 2 always-on gates + RED_TEAM opt-in landed. FIXED ORDER tick gate orchestrator integrates 6 standalone gates plus RED_TEAM dispatch hook.

### Added
- `prompts/budget_limit.md` — graceful wrap-up prompt for budget-limited terminal round
- `prompts/red_team.md` — RED_TEAM evaluator-gaming subagent prompt
- `schemas/red_team_output.schema.json` — RED_TEAM JSON output contract
- `scripts/gates/` package — 6 standalone gate modules:
  - `iteration_gate.py` — cap at 10000 iterations
  - `wall_time_gate.py` — cap at 72h wall-time
  - `repeat_loop_gate.py` — abort on 3 identical audit failures
  - `budget_gate.py` — calibrated 80% threshold + injection signal (skipped when `budget_strategy=="none"`)
  - `context_gate.py` — 60/65/70/75% advisory + 80% hard transition to paused
  - `quota_gate.py` — per-CLI registry (single-session for Phase 2)
- `scripts/tick_gate.py` — FIXED ORDER orchestrator (paused → terminal → quota → context → budget → repeat → iter → wall → next_round)
- `scripts/red_team_dispatch.py` — opt-in trigger detector + prompt builder + output parser
- `scripts/orchestrator.py::decide_with_gates` — wraps tick_gate over Phase 1 `decide_next_action`
- `scripts/schema_validators.py::validate_red_team_output`

### Test coverage
- 108 tests passing total (Phase 1: 60 + Phase 2: 48)
- 6 gate unit tests + 7 tick_gate orchestration + 7 red_team + 5 E2E + 2 orchestrator integration

### Phase 2 deferred to later phases
- Multi-session quota coordination (`~/.automl/quota_registry/` shared lock) — Phase 3
- Active session lock + heartbeat — Phase 3
- ScheduleWakeup integration when quota gate trips — Phase 5
- RED_TEAM 2-cycle main-session repair loop — Phase 2 follow-up if needed
- Calibrator self-improvement telemetry — Phase 4

## v6.0.0-alpha.1 — 2026-05-06 (Phase 1 dev complete)

Phase 1 MVP foundation complete. End-to-end happy path verified via mocked subagents.

### Added
- Schema definitions: state.json, env.json, goal.md frontmatter, calibrator output, round output
- File I/O with fcntl lock + atomic writes + .bak backup (state_io.py, goal_io.py)
- Lifecycle FSM with 7 states + transition validation
- Environment probe (skill/tool detection + calibration_quality classification)
- Calibrator subagent: prompt template + output parser + validator
- Round subagent: prompt template + continuation.md audit directive + output parser
- Audit gatekeeper: validates `achieved` claims have all 3 evidence types
- Alignment dialogue: strategy selection (external skill vs mini-* fallback) + initial goal draft
- Mini references: mini-brainstorm.md, mini-grill.md (alignment fallbacks)
- Orchestrator: round decision logic + state mutation per round
- CLI parser: invoke / status / list commands + --no-budget / --spec flags

### Test coverage
- 12 test files (10 unit/integration + 1 E2E + conftest)
- 60 tests, all passing in 0.14s
- E2E happy path: calibrate → align → 2 rounds → achieved (mocked subagents)

### Known limitations (deferred to later phases)
- No always-on gates (quota / context / wall / iteration / repeat-loop) — Phase 2
- No RED_TEAM integration — Phase 2
- No multi-session lock / quota_registry / worktree advisory / orphan recovery — Phase 3
- No telemetry / calibrator self-improvement — Phase 4
- No pause/resume/clear/history commands — Phase 5
- No migration to /automl-legacy — Phase 5
- Skill name still `automl-v6` (renamed to `automl` only at v6.0 ship)
