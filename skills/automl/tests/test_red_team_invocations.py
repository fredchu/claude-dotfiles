import pytest

from red_team_dispatch import record_red_team_invocation


def test_record_appends_entry():
    state = {}
    record_red_team_invocation(state, round_id=2, verdict="approved", rationale="ok")
    assert len(state["red_team_invocations"]) == 1
    entry = state["red_team_invocations"][0]
    assert entry["round_id"] == 2
    assert entry["verdict"] == "approved"
    assert entry["rationale"] == "ok"
    assert "ts" in entry


def test_record_appends_to_existing_list():
    state = {"red_team_invocations": [{"round_id": 1, "ts": "2026-01-01T00:00:00+08:00", "verdict": "blocked"}]}
    record_red_team_invocation(state, round_id=2, verdict="approved")
    assert len(state["red_team_invocations"]) == 2


def test_record_rejects_invalid_verdict():
    state = {}
    with pytest.raises(ValueError):
        record_red_team_invocation(state, round_id=1, verdict="maybe")
