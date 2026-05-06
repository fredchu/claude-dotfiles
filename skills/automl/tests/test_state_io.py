import json
import pytest
from state_io import (
    init_state, read_state, write_state, atomic_update, StateIOError
)


@pytest.fixture
def tmp_run_dir(tmp_path):
    run_dir = tmp_path / "20260506-143022-test"
    run_dir.mkdir()
    return run_dir


def test_init_state_creates_valid_state_json(tmp_run_dir):
    init_state(tmp_run_dir, run_id="20260506-143022-test", session_id="sess-1", pid=1234)
    state_path = tmp_run_dir / "state.json"
    assert state_path.exists()
    data = json.loads(state_path.read_text())
    assert data["lifecycle_state"] == "aligning"
    assert data["run_id"] == "20260506-143022-test"
    assert data["active_session"]["pid"] == 1234


def test_read_state_returns_parsed_dict(tmp_run_dir):
    init_state(tmp_run_dir, run_id="20260506-143022-test", session_id="sess-1", pid=1234)
    data = read_state(tmp_run_dir)
    assert data["run_id"] == "20260506-143022-test"


def test_write_state_persists_changes(tmp_run_dir):
    init_state(tmp_run_dir, run_id="20260506-143022-test", session_id="sess-1", pid=1234)
    data = read_state(tmp_run_dir)
    data["iterations"] = 5
    write_state(tmp_run_dir, data)
    reloaded = read_state(tmp_run_dir)
    assert reloaded["iterations"] == 5


def test_atomic_update_applies_callback(tmp_run_dir):
    init_state(tmp_run_dir, run_id="20260506-143022-test", session_id="sess-1", pid=1234)

    def increment(state):
        state["iterations"] += 1
        return state

    atomic_update(tmp_run_dir, increment)
    data = read_state(tmp_run_dir)
    assert data["iterations"] == 1


def test_atomic_update_creates_backup(tmp_run_dir):
    init_state(tmp_run_dir, run_id="20260506-143022-test", session_id="sess-1", pid=1234)
    atomic_update(tmp_run_dir, lambda s: s)
    backup = tmp_run_dir / "state.json.bak"
    assert backup.exists()


def test_write_state_rejects_invalid_data(tmp_run_dir):
    invalid = {"schema_version": "v6.0"}
    with pytest.raises(StateIOError):
        write_state(tmp_run_dir, invalid)
