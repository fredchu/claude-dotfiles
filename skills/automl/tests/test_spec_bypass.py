"""Tests for --spec bypass: init_run_from_spec skips alignment, lifecycle pursuing direct."""
import json
import yaml
from pathlib import Path

import pytest

from spec_bypass import init_run_from_spec, SpecBypassError


def _make_goal_md(path: Path, run_id: str = "20260506-200000-spec") -> None:
    """Helper: write a valid goal.md to path."""
    fm = {
        "run_id": run_id,
        "schema_version": "v6.0",
        "calibrator": {
            "dialogue_depth": "normal",
            "budget_estimate": 50000,
            "budget_strategy": "soft",
            "confidence": 0.8,
        },
        "acceptance_criteria": [
            {"id": "c1", "desc": "Bug A reproduces in failing test, then passes",
             "verification": "pytest tests/test_a.py shows red then green"},
            {"id": "c2", "desc": "Token refresh edge case has new test",
             "verification": "tests/test_token_refresh.py exists with the case"},
        ],
    }
    body = "# Goal\n\nFix two known auth bugs.\n"
    path.write_text("---\n" + yaml.safe_dump(fm, sort_keys=False) + "---\n\n" + body)


def test_init_state_skips_aligning(tmp_path):
    spec_path = tmp_path / "goal.md"
    _make_goal_md(spec_path)
    run_dir = tmp_path / "run"
    state = init_run_from_spec(spec_path=spec_path, run_dir=run_dir,
                               session_id="s1", pid=42)
    assert state["lifecycle_state"] == "pursuing"
    # transitions: aligning -> pursuing with "spec bypass" reason
    transitions = state["lifecycle_transitions"]
    assert transitions[0]["to"] == "aligning"
    assert transitions[-1]["from"] == "aligning"
    assert transitions[-1]["to"] == "pursuing"
    assert "spec bypass" in transitions[-1]["reason"].lower()


def test_seeds_criteria_from_goal_md(tmp_path):
    spec_path = tmp_path / "goal.md"
    _make_goal_md(spec_path)
    run_dir = tmp_path / "run"
    state = init_run_from_spec(spec_path=spec_path, run_dir=run_dir,
                               session_id="s1", pid=42)
    progress = state["criteria_progress"]
    assert set(progress.keys()) == {"c1", "c2"}
    assert progress["c1"]["status"] == "pending"
    assert progress["c1"]["evidence"] == []
    assert progress["c2"]["status"] == "pending"


def test_copies_goal_md_into_run_dir(tmp_path):
    spec_path = tmp_path / "goal.md"
    _make_goal_md(spec_path)
    run_dir = tmp_path / "run"
    init_run_from_spec(spec_path=spec_path, run_dir=run_dir,
                       session_id="s1", pid=42)
    assert (run_dir / "goal.md").exists()
    # And the run_dir's goal.md is parseable (still has frontmatter)
    text = (run_dir / "goal.md").read_text()
    assert text.startswith("---\n")


def test_missing_spec_raises(tmp_path):
    run_dir = tmp_path / "run"
    with pytest.raises(SpecBypassError, match="not found|does not exist"):
        init_run_from_spec(spec_path=tmp_path / "nope.md", run_dir=run_dir,
                           session_id="s1", pid=42)
