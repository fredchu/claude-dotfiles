import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from orphan_recovery import classify_takeover_action, scan_for_orphans


def _hb_minus(hours: float) -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=hours)).astimezone().isoformat(timespec="seconds")


def _write(automl: Path, run_id: str, lifecycle: str, hb_hours_ago: float):
    d = automl / run_id
    d.mkdir(parents=True, exist_ok=True)
    (d / "state.json").write_text(json.dumps({
        "lifecycle_state": lifecycle,
        "active_session": {
            "session_id": "s",
            "pid": 1,
            "started_at": _hb_minus(hb_hours_ago + 1),
            "last_heartbeat": _hb_minus(hb_hours_ago),
        },
    }))


def test_scan_finds_paused_with_stale_heartbeat(tmp_path):
    automl = tmp_path / ".automl"
    automl.mkdir()
    _write(automl, "fresh-paused", "paused", hb_hours_ago=0.5)     # < 1h, not orphan
    _write(automl, "stale-paused", "paused", hb_hours_ago=2)       # > 1h, orphan
    _write(automl, "stale-pursuing", "pursuing", hb_hours_ago=3)   # not paused, not orphan
    orphans = scan_for_orphans(automl_dir=automl)
    assert {o["run_id"] for o in orphans} == {"stale-paused"}


def test_scan_empty_when_no_runs(tmp_path):
    automl = tmp_path / ".automl"
    automl.mkdir()
    assert scan_for_orphans(automl_dir=automl) == []


def test_scan_returns_empty_when_dir_missing(tmp_path):
    """No .automl/ -> empty (no exception)."""
    assert scan_for_orphans(automl_dir=tmp_path / ".automl") == []


def test_classify_autonomous_silent_takeover():
    decision = classify_takeover_action(mode="autonomous", orphans=[{"run_id": "r1"}])
    assert decision.silent is True
    assert decision.prompt_user is False


def test_classify_interactive_prompts_user():
    decision = classify_takeover_action(mode="interactive", orphans=[{"run_id": "r1"}])
    assert decision.silent is False
    assert decision.prompt_user is True


def test_classify_no_orphans_no_action():
    decision = classify_takeover_action(mode="autonomous", orphans=[])
    assert decision.silent is False
    assert decision.prompt_user is False
