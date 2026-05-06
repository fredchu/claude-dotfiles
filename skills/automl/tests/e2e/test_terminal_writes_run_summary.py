"""E2E: a full happy path through pursuing -> achieved produces run_summary.md
with correct telemetry derived from the calibrator output and final state."""
import json
from pathlib import Path

import yaml

from orchestrator import write_run_summary_if_terminal
from state_io import init_state, atomic_update


def test_happy_path_writes_run_summary_with_correct_telemetry(tmp_path):
    run_dir = tmp_path / "20260506-200000-e2e1"
    run_dir.mkdir()
    init_state(run_dir, run_id="20260506-200000-e2e1", session_id="sess-1", pid=1)

    (run_dir / "calibrator.json").write_text(json.dumps({
        "schema_version": "v6.0",
        "calibrator_confidence": 0.9,
        "task_classification": {
            "type": "bug_fix",
            "estimated_blast_radius": {"files": 2, "modules": 1, "touches_core_abstraction": False},
            "uncertainty_signals": [],
        },
        "alignment": {"dialogue_depth": "shallow", "rationale": "."},
        "budget": {"estimated_tokens": 40000, "strategy": "soft", "rationale": "."},
        "verification": {"should_red_team": False, "red_team_rationale": "."},
        "criteria_template": [{"id": "c1", "desc_draft": "x", "verification_draft": "y", "needs_user_confirmation": False}],
    }))

    def finalize(s):
        s["lifecycle_state"] = "achieved"
        s["lifecycle_transitions"].append({
            "from": "pursuing", "to": "achieved",
            "ts": "2026-05-06T20:30:00+08:00",
            "reason": "all criteria achieved",
        })
        s["tokens"]["actual"] = 12000
        s["iterations"] = 4
        s["alignment_metadata"] = {"questions_asked": 2, "depth": "shallow"}
        return s

    state = atomic_update(run_dir, finalize)

    out = write_run_summary_if_terminal(run_dir, state)
    assert out is not None and out.exists()

    content = out.read_text()
    fm = yaml.safe_load(content.split("---")[1])
    t = fm["calibrator_telemetry"]
    assert t["estimated_tokens"] == 40000
    assert t["actual_tokens"] == 12000
    assert t["diff_pct"] == -70  # (12000-40000)/40000 * 100 = -70
    assert t["estimated_dialogue_depth"] == "shallow"
    assert t["actual_questions_asked"] == 2
    assert t["red_team_skipped"] is True
