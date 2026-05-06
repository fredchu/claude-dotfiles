import json

from list_command import collect_runs, render_list


def _seed_run(automl: "Path", run_id: str, lifecycle: str, iterations: int = 3):
    d = automl / run_id
    d.mkdir(parents=True, exist_ok=True)
    (d / "state.json").write_text(json.dumps({
        "schema_version": "v6.0",
        "run_id": run_id,
        "lifecycle_state": lifecycle,
        "lifecycle_transitions": [],
        "active_session": None,
        "criteria_progress": {},
        "tokens": {"estimated": 50000, "actual": 12000, "by_round": []},
        "iterations": iterations,
        "expected_wake_at": None,
        "audit_failure_log": [],
    }))


def test_collect_runs_empty(tmp_path):
    automl = tmp_path / ".automl"
    automl.mkdir()
    assert collect_runs(automl_dir=automl) == []


def test_collect_runs_returns_lifecycle_summaries(tmp_path):
    automl = tmp_path / ".automl"
    automl.mkdir()
    _seed_run(automl, "20260506-100000-aaaa", "achieved", iterations=5)
    _seed_run(automl, "20260506-110000-bbbb", "pursuing", iterations=2)
    runs = collect_runs(automl_dir=automl)
    assert {r["run_id"] for r in runs} == {"20260506-100000-aaaa", "20260506-110000-bbbb"}
    achieved = next(r for r in runs if r["run_id"] == "20260506-100000-aaaa")
    assert achieved["lifecycle_state"] == "achieved"
    assert achieved["iterations"] == 5


def test_render_list_empty():
    out = render_list([])
    assert "no runs" in out.lower() or "0 runs" in out.lower()


def test_render_list_includes_each_run():
    rows = [
        {"run_id": "20260506-100000-aaaa", "lifecycle_state": "achieved", "iterations": 5, "actual_tokens": 12000},
        {"run_id": "20260506-110000-bbbb", "lifecycle_state": "pursuing", "iterations": 2, "actual_tokens": 4000},
    ]
    out = render_list(rows)
    assert "20260506-100000-aaaa" in out
    assert "20260506-110000-bbbb" in out
    assert "achieved" in out
    assert "pursuing" in out


def test_collect_runs_skips_non_dir_entries(tmp_path):
    """Stray files (e.g. .DS_Store) shouldn't crash."""
    automl = tmp_path / ".automl"
    automl.mkdir()
    (automl / ".DS_Store").write_text("noise")
    _seed_run(automl, "20260506-100000-aaaa", "achieved")
    runs = collect_runs(automl_dir=automl)
    assert len(runs) == 1
