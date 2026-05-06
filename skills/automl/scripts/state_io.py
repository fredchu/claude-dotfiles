"""Read/write .automl/{run_id}/state.json with fcntl lock + atomic backup."""
import fcntl
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable
from schema_validators import validate_state_json, SchemaValidationError


class StateIOError(Exception):
    """Raised on state.json I/O or validation failure."""


def _state_path(run_dir: Path) -> Path:
    return run_dir / "state.json"


def _backup_path(run_dir: Path) -> Path:
    return run_dir / "state.json.bak"


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def init_state(run_dir: Path, run_id: str, session_id: str, pid: int) -> None:
    """Create initial state.json with lifecycle_state='aligning'."""
    now = _now_iso()
    state = {
        "schema_version": "v6.0",
        "run_id": run_id,
        "lifecycle_state": "aligning",
        "lifecycle_transitions": [
            {"from": None, "to": "aligning", "ts": now, "reason": "run started"}
        ],
        "active_session": {
            "session_id": session_id,
            "pid": pid,
            "started_at": now,
            "last_heartbeat": now,
        },
        "criteria_progress": {},
        "tokens": {"estimated": 0, "actual": 0, "by_round": []},
        "iterations": 0,
        "expected_wake_at": None,
        "audit_failure_log": [],
        "red_team_invocations": [],
    }
    write_state(run_dir, state)


def read_state(run_dir: Path) -> dict:
    """Read state.json with shared file lock."""
    path = _state_path(run_dir)
    if not path.exists():
        raise StateIOError(f"state.json not found at {path}")
    with open(path, "r") as f:
        fcntl.flock(f, fcntl.LOCK_SH)
        try:
            return json.load(f)
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


def write_state(run_dir: Path, state: dict) -> None:
    """Write state.json with exclusive lock + schema validation."""
    try:
        validate_state_json(state)
    except SchemaValidationError as e:
        raise StateIOError(str(e))

    path = _state_path(run_dir)
    tmp_path = path.with_suffix(".json.tmp")
    with open(tmp_path, "w") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            json.dump(state, f, indent=2, ensure_ascii=False)
            f.flush()
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)
    tmp_path.rename(path)


def atomic_update(run_dir: Path, mutator: Callable[[dict], dict]) -> dict:
    """Atomically read → mutate → backup → write state.

    Args:
        run_dir: directory containing state.json
        mutator: callable taking current state dict, returning new state dict

    Returns:
        the new state dict
    """
    path = _state_path(run_dir)
    backup = _backup_path(run_dir)

    with open(path, "r+") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            current = json.load(f)
            shutil.copy(path, backup)
            new_state = mutator(current)
            validate_state_json(new_state)
            f.seek(0)
            f.truncate()
            json.dump(new_state, f, indent=2, ensure_ascii=False)
            f.flush()
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)
    return new_state
