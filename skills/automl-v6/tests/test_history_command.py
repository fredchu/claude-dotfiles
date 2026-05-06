from datetime import datetime, timedelta, timezone

import yaml

from history_command import collect_history, render_history


def _hb_minus_days(d: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=d)).astimezone().isoformat(timespec="seconds")


def _seed_run_summary(automl, run_id, diff_pct, days_ago=1, lifecycle="achieved"):
    d = automl / run_id
    d.mkdir(parents=True, exist_ok=True)
    fm = {
        "schema_version": "v6.0",
        "run_id": run_id,
        "lifecycle_state": lifecycle,
        "iterations": 3,
        "terminal_ts": _hb_minus_days(days_ago),
        "calibrator_telemetry": {
            "estimated_tokens": 80000,
            "actual_tokens": 23400,
            "diff_pct": diff_pct,
            "estimated_dialogue_depth": "normal",
            "actual_dialogue_depth": "normal",
            "actual_questions_asked": 3,
            "estimated_should_red_team": False,
            "red_team_skipped": True,
            "red_team_was_needed_in_hindsight": None,
        },
    }
    md = "---\n" + yaml.safe_dump(fm, sort_keys=False) + "---\n\n# body\n"
    (d / "run_summary.md").write_text(md)


def test_collect_history_empty(tmp_path):
    automl = tmp_path / ".automl"
    automl.mkdir()
    assert collect_history(automl_dir=automl) == []


def test_collect_history_returns_per_run_telemetry(tmp_path):
    automl = tmp_path / ".automl"
    automl.mkdir()
    _seed_run_summary(automl, "r1", diff_pct=-50, days_ago=2)
    _seed_run_summary(automl, "r2", diff_pct=15, days_ago=1)
    rows = collect_history(automl_dir=automl)
    assert len(rows) == 2
    assert {r["run_id"] for r in rows} == {"r1", "r2"}
    by_id = {r["run_id"]: r for r in rows}
    assert by_id["r1"]["diff_pct"] == -50
    assert by_id["r2"]["diff_pct"] == 15


def test_render_history_includes_per_run():
    rows = [
        {"run_id": "r1", "lifecycle_state": "achieved", "iterations": 4, "estimated_tokens": 80000, "actual_tokens": 23400, "diff_pct": -71, "terminal_ts": "2026-05-06T20:00:00+08:00"},
        {"run_id": "r2", "lifecycle_state": "achieved", "iterations": 3, "estimated_tokens": 50000, "actual_tokens": 30000, "diff_pct": -40, "terminal_ts": "2026-05-06T21:00:00+08:00"},
    ]
    out = render_history(rows)
    assert "r1" in out and "r2" in out
    assert "-71" in out and "-40" in out


def test_render_history_empty():
    out = render_history([])
    assert "no runs" in out.lower() or "0 runs" in out.lower()
