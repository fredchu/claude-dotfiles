import json
from pathlib import Path

import pytest
import yaml

from run_summary import (
    build_calibrator_telemetry,
    build_run_summary_md,
    write_run_summary,
)


@pytest.fixture
def calibrator_fixture():
    return {
        "schema_version": "v6.0",
        "calibrator_confidence": 0.85,
        "task_classification": {
            "type": "bug_fix",
            "estimated_blast_radius": {"files": 5, "modules": 1, "touches_core_abstraction": False},
            "uncertainty_signals": [],
        },
        "alignment": {"dialogue_depth": "normal", "rationale": "..."},
        "budget": {"estimated_tokens": 80000, "strategy": "soft", "rationale": "..."},
        "verification": {"should_red_team": False, "red_team_rationale": "..."},
        "criteria_template": [{"id": "c1", "desc_draft": "x", "verification_draft": "y", "needs_user_confirmation": False}],
    }


@pytest.fixture
def state_fixture():
    return {
        "schema_version": "v6.0",
        "run_id": "20260506-200000-test",
        "lifecycle_state": "achieved",
        "lifecycle_transitions": [
            {"from": None, "to": "aligning", "ts": "2026-05-06T20:00:00+08:00", "reason": "run started"},
            {"from": "aligning", "to": "pursuing", "ts": "2026-05-06T20:05:00+08:00", "reason": "goal finalized"},
            {"from": "pursuing", "to": "achieved", "ts": "2026-05-06T20:30:00+08:00", "reason": "criteria met"},
        ],
        "active_session": None,
        "criteria_progress": {"c1": {"status": "achieved", "evidence": []}},
        "tokens": {"estimated": 80000, "actual": 23400, "by_round": []},
        "iterations": 3,
        "expected_wake_at": None,
        "audit_failure_log": [],
        "alignment_metadata": {"questions_asked": 3, "depth": "normal"},
    }


def test_telemetry_diff_pct_when_overestimated(calibrator_fixture, state_fixture):
    t = build_calibrator_telemetry(calibrator_fixture, state_fixture)
    assert t["estimated_tokens"] == 80000
    assert t["actual_tokens"] == 23400
    assert t["diff_pct"] == -71  # round((23400-80000)/80000*100) = -71


def test_telemetry_diff_pct_zero_when_estimated_zero(calibrator_fixture, state_fixture):
    """Avoid div-by-zero: estimate=0 -> diff_pct=None."""
    calibrator_fixture["budget"]["estimated_tokens"] = 0
    t = build_calibrator_telemetry(calibrator_fixture, state_fixture)
    assert t["diff_pct"] is None


def test_telemetry_questions_asked_null_when_missing(calibrator_fixture, state_fixture):
    state_fixture["alignment_metadata"] = None
    t = build_calibrator_telemetry(calibrator_fixture, state_fixture)
    assert t["actual_questions_asked"] is None
    assert t["actual_dialogue_depth"] is None


def test_telemetry_red_team_skipped_when_no_failure_log_entry(calibrator_fixture, state_fixture):
    """No red_team_invoked entry in audit_failure_log -> red_team_skipped=True."""
    t = build_calibrator_telemetry(calibrator_fixture, state_fixture)
    assert t["red_team_skipped"] is True
    assert t["estimated_should_red_team"] is False


def test_telemetry_red_team_was_needed_optional(calibrator_fixture, state_fixture):
    """Hindsight field defaults to None; main session retrospective fills it."""
    t = build_calibrator_telemetry(calibrator_fixture, state_fixture)
    assert t["red_team_was_needed_in_hindsight"] is None


def test_build_run_summary_md_has_yaml_frontmatter(calibrator_fixture, state_fixture):
    md = build_run_summary_md(calibrator_fixture, state_fixture)
    assert md.startswith("---\n")
    parts = md.split("\n---\n", 1)
    assert len(parts) == 2
    fm = yaml.safe_load(parts[0].lstrip("-").lstrip("\n"))
    assert fm["run_id"] == "20260506-200000-test"
    assert fm["lifecycle_state"] == "achieved"
    assert fm["calibrator_telemetry"]["diff_pct"] == -71


def test_write_run_summary_creates_file(tmp_path, calibrator_fixture, state_fixture):
    run_dir = tmp_path / "20260506-200000-test"
    run_dir.mkdir()
    (run_dir / "calibrator.json").write_text(json.dumps(calibrator_fixture))
    write_run_summary(run_dir, state_fixture)
    out = run_dir / "run_summary.md"
    assert out.exists()
    assert "calibrator_telemetry" in out.read_text()


def test_telemetry_red_team_invoked_via_invocations_field(calibrator_fixture, state_fixture):
    """Phase 5: red_team_invocations entry sets red_team_skipped=False."""
    state_fixture["red_team_invocations"] = [{"round_id": 1, "ts": "2026-05-06T14:30:00+08:00", "verdict": "approved"}]
    t = build_calibrator_telemetry(calibrator_fixture, state_fixture)
    assert t["red_team_skipped"] is False


def test_write_run_summary_idempotent_overwrites(tmp_path, calibrator_fixture, state_fixture):
    """Re-writing replaces in place (single source of truth at terminal)."""
    run_dir = tmp_path / "20260506-200000-test"
    run_dir.mkdir()
    (run_dir / "calibrator.json").write_text(json.dumps(calibrator_fixture))
    write_run_summary(run_dir, state_fixture)
    state_fixture["tokens"]["actual"] = 25000
    write_run_summary(run_dir, state_fixture)
    md = (run_dir / "run_summary.md").read_text()
    assert "actual_tokens: 25000" in md
