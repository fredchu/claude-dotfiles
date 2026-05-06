"""E2E: pursuing -> pause -> resume cycle preserves criteria_progress and lifecycle history."""
from datetime import datetime, timezone

from lifecycle_commands import pause, resume
from state_io import init_state, read_state, atomic_update


def test_pause_resume_round_trip(tmp_path):
    run_dir = tmp_path / "20260506-200000-pare"
    run_dir.mkdir()
    init_state(run_dir, run_id="20260506-200000-pare", session_id="sess-1", pid=1)

    # Mature the run a bit: aligning -> pursuing
    def into_pursuing(s):
        s["lifecycle_state"] = "pursuing"
        s["lifecycle_transitions"].append({
            "from": "aligning", "to": "pursuing",
            "ts": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
            "reason": "goal finalized",
        })
        s["criteria_progress"]["c1"] = {"status": "pursuing", "evidence": []}
        return s

    state = atomic_update(run_dir, into_pursuing)
    assert state["lifecycle_state"] == "pursuing"

    # Pause: apply pause() to state then persist with atomic_update
    def apply_pause(s):
        updated, _ = pause(s)
        return updated

    state = atomic_update(run_dir, apply_pause)
    assert state["lifecycle_state"] == "paused"
    assert state["active_session"] is None

    # Resume: apply resume() to state then persist with atomic_update
    def apply_resume(s):
        updated, _ = resume(s, session_id="sess-2", pid=2)
        return updated

    state = atomic_update(run_dir, apply_resume)
    assert state["lifecycle_state"] == "pursuing"
    assert state["active_session"]["session_id"] == "sess-2"

    # Lifecycle history retained: aligning -> pursuing -> paused -> pursuing
    transitions = [t["to"] for t in state["lifecycle_transitions"]]
    assert transitions == ["aligning", "pursuing", "paused", "pursuing"]

    # criteria_progress preserved
    assert state["criteria_progress"]["c1"]["status"] == "pursuing"
