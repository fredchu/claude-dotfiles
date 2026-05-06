# Changelog

## v6.0.0-alpha.3 — 2026-05-06 (Phase 3 dev complete)

Phase 3 multi-session safety landed. Heartbeat-driven active_session lock,
cross-session quota coordination, worktree advisory with same-cwd refusal,
and orphan recovery scan are now wired through orchestrator startup.

### Added
- `scripts/session_lock.py` — `update_heartbeat`, `is_session_alive`,
  `can_takeover`. Two thresholds: `HEARTBEAT_STALE_RESUME` (10 min) for
  resume conflicts, `HEARTBEAT_STALE_ORPHAN` (1 hour) for orphan recovery.
- `scripts/quota_coordinator.py` — `aggregate_other_sessions_used_pct` +
  `effective_threshold`. Quota gate now consults peers and throttles to
  `75% - others_usage` so concurrent sessions don't all run hot at the cap.
- `scripts/worktree_advisory.py` — `is_inside_worktree`,
  `find_active_runs_in_cwd`, `check_cwd_conflict`, `refuse_message`.
  Detects same-cwd concurrent runs via `git rev-parse --git-dir` vs
  `--git-common-dir`; orphans (paused + heartbeat > 1h) are excluded so
  they don't block legitimate takeover.
- `scripts/orphan_recovery.py` — `scan_for_orphans`, `classify_takeover_action`.
  Autonomous mode silently reclaims; interactive mode surfaces orphans for
  the user.
- `scripts/orchestrator.py::start_or_resume_run` — startup gate sequence
  (worktree advisory → orphan scan → classify → silent takeover for
  autonomous). `takeover_orphan` rewrites `active_session` and moves
  `paused → pursuing`. `heartbeat_state_path` lets the main session stamp
  heartbeat outside the round boundary.
- `scripts/round_dispatch.py::record_round_boundary` — wraps
  `update_heartbeat`; called from `apply_round_output_to_state` so each
  round persists fresh liveness.
- `scripts/cli_parser.py` — `--allow-cwd-conflict` and `--autonomous`
  flags surface on `ParsedCommand`.

### Modified
- `gates/quota_gate.py::QuotaRegistry.update_own_usage` now wraps the
  read-modify-write in an exclusive fcntl lock (sidecar `.lock` file) so
  concurrent updaters can't clobber each other.
- `gates/quota_gate.py::check_quota` consults
  `quota_coordinator.aggregate_other_sessions_used_pct` for the effective
  threshold; explicit `threshold=` kwarg still bypasses for legacy paths.

### Test coverage
- 149 tests passing total (Phase 1: 60 + Phase 2: 48 + Phase 3: 41)
- 7 session_lock + 6 quota_coordinator + 8 worktree_advisory + 6 orphan_recovery + 5 cli_parser additions + 2 round_dispatch boundary + 7 e2e (cross-session takeover, concurrent cwd refused, orphan autonomous takeover)

### Phase 3 deferred to later phases
- Concrete `pause` / `resume` / `clear` / `history` UX commands — Phase 5
- `/automl-legacy` parallel migration — Phase 5
- Calibrator self-improvement telemetry — Phase 4
- ScheduleWakeup tier 2 launchd workaround — v6.x external opt-in (§9.7)
- RED_TEAM 2-cycle main-session repair loop — Phase 2 follow-up if needed

### Plan deviations from `2026-05-06-automl-v6-phase3-multisession.md`
- Boundary heartbeat lives in `apply_round_output_to_state` (orchestrator),
  not in a new `round_dispatch` callback — matches existing round mutation
  surface; `record_round_boundary` is the helper.
- `find_active_runs_in_cwd` filters out orphan runs (paused + heartbeat
  > 1h) so the cwd advisory doesn't block the orphan-recovery startup
  path. Plan didn't anticipate this interaction.

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
