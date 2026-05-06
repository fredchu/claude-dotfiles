from status_renderer import render_status


def _state_fixture():
    return {
        "schema_version": "v6.0",
        "run_id": "20260506-143022-a8f3",
        "lifecycle_state": "pursuing",
        "lifecycle_transitions": [
            {"from": None, "to": "aligning", "ts": "2026-05-06T14:30:22+08:00", "reason": "init"},
            {"from": "aligning", "to": "pursuing", "ts": "2026-05-06T14:33:00+08:00", "reason": "goal finalized"},
        ],
        "active_session": {"session_id": "s1", "pid": 100, "started_at": "2026-05-06T14:30:22+08:00", "last_heartbeat": "2026-05-06T14:48:00+08:00"},
        "criteria_progress": {
            "c1": {"status": "achieved", "evidence": [{"type": "audit_check", "criterion_verbatim": "Bug A reproduces in failing test, then passes", "satisfied": True, "rationale": "..."}]},
            "c2": {"status": "pursuing", "evidence": []},
            "c3": {"status": "pending", "evidence": []},
        },
        "tokens": {"estimated": 80000, "actual": 23400, "by_round": []},
        "iterations": 3,
        "expected_wake_at": None,
        "audit_failure_log": [],
    }


def _calibrator_fixture():
    return {
        "schema_version": "v6.0",
        "calibrator_confidence": 0.85,
        "task_classification": {"type": "bug_fix", "estimated_blast_radius": {"files": 3, "modules": 1, "touches_core_abstraction": False}, "uncertainty_signals": []},
        "alignment": {"dialogue_depth": "normal", "rationale": "..."},
        "budget": {"estimated_tokens": 80000, "strategy": "hard", "rationale": "..."},
        "verification": {"should_red_team": False, "red_team_rationale": "..."},
        "criteria_template": [],
        "similar_lessons": ["lessonA.md", "lessonB.md"],
    }


def test_status_includes_run_id_and_lifecycle_state():
    out = render_status(_state_fixture(), _calibrator_fixture(),
                        goal_summary="Improve auth module reliability — fix 3 known auth bugs",
                        env={"missing_soft_deps": []},
                        quota={"claude_max": 47, "codex": 12},
                        context_used_pct=32)
    assert "Run: 20260506-143022-a8f3" in out
    assert "pursuing" in out


def test_status_includes_goal_one_liner():
    out = render_status(_state_fixture(), _calibrator_fixture(),
                        goal_summary="Improve auth module reliability — fix 3 known auth bugs",
                        env={"missing_soft_deps": []},
                        quota={"claude_max": 47, "codex": 12},
                        context_used_pct=32)
    assert "Improve auth module reliability — fix 3 known auth bugs" in out


def test_status_includes_token_budget_with_percentage():
    out = render_status(_state_fixture(), _calibrator_fixture(),
                        goal_summary="x", env={"missing_soft_deps": []},
                        quota={"claude_max": 0, "codex": 0}, context_used_pct=0)
    assert "23400" in out or "23.4k" in out
    assert "80000" in out or "80k" in out
    assert "29%" in out  # 23400/80000 = 0.2925 -> 29%


def test_status_renders_all_three_criteria_statuses():
    out = render_status(_state_fixture(), _calibrator_fixture(),
                        goal_summary="x", env={"missing_soft_deps": []},
                        quota={"claude_max": 0, "codex": 0}, context_used_pct=0)
    assert "c1" in out
    assert "c2" in out
    assert "c3" in out
    # marker chars per spec §8.3 (✓ / ⏳ / ⏸ are example glyphs; renderer may use ASCII fallbacks)
    assert "achieved" in out
    assert "pursuing" in out
    assert "pending" in out


def test_status_calibration_section():
    out = render_status(_state_fixture(), _calibrator_fixture(),
                        goal_summary="x", env={"missing_soft_deps": []},
                        quota={"claude_max": 0, "codex": 0}, context_used_pct=0)
    assert "depth: normal" in out
    assert "budget: hard" in out  # spec says "hard cap" but the strategy string is "hard"
    assert "should_red_team: no" in out
    assert "confidence: 0.85" in out
    assert "similar_lessons: 2" in out


def test_status_quota_line():
    out = render_status(_state_fixture(), _calibrator_fixture(),
                        goal_summary="x", env={"missing_soft_deps": []},
                        quota={"claude_max": 47, "codex": 12}, context_used_pct=32)
    assert "claude_max 47%" in out
    assert "codex 12%" in out


def test_status_context_line():
    out = render_status(_state_fixture(), _calibrator_fixture(),
                        goal_summary="x", env={"missing_soft_deps": []},
                        quota={"claude_max": 0, "codex": 0}, context_used_pct=32)
    assert "Context: 32%" in out


def test_status_shows_degraded_when_missing_soft_deps():
    out = render_status(_state_fixture(), _calibrator_fixture(),
                        goal_summary="x", env={"missing_soft_deps": ["grill-me"]},
                        quota={"claude_max": 0, "codex": 0}, context_used_pct=0)
    assert "Degraded" in out
    assert "grill-me" in out


def test_status_no_degraded_section_when_all_deps_present():
    out = render_status(_state_fixture(), _calibrator_fixture(),
                        goal_summary="x", env={"missing_soft_deps": []},
                        quota={"claude_max": 0, "codex": 0}, context_used_pct=0)
    assert "Degraded" not in out


def test_status_last_activity_from_lifecycle_transitions():
    """Last activity timestamp should derive from the most recent transition or heartbeat."""
    out = render_status(_state_fixture(), _calibrator_fixture(),
                        goal_summary="x", env={"missing_soft_deps": []},
                        quota={"claude_max": 0, "codex": 0}, context_used_pct=0)
    assert "Last activity" in out
