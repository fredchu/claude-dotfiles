import json
import os
import subprocess
from datetime import datetime, timedelta, timezone

from worktree_advisory import (
    check_cwd_conflict,
    find_active_runs_in_cwd,
    is_inside_worktree,
    refuse_message,
)


def _fresh_hb() -> str:
    """Heartbeat well within HEARTBEAT_STALE_ORPHAN -- counts as alive."""
    return (datetime.now(timezone.utc) - timedelta(minutes=2)).astimezone().isoformat(timespec="seconds")


def _git_env():
    """Sandboxed git env so test commits don't pick up user identity / hooks."""
    env = os.environ.copy()
    env.update({
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@t",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@t",
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_CONFIG_SYSTEM": "/dev/null",
    })
    return env


def test_is_inside_worktree_main_repo(tmp_path):
    """A fresh git repo's main checkout is NOT a worktree."""
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True, env=_git_env())
    assert is_inside_worktree(tmp_path) is False


def test_is_inside_worktree_added(tmp_path):
    """git worktree add creates an isolated checkout."""
    env = _git_env()
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=tmp_path, check=True, env=env)
    subprocess.run(
        ["git", "commit", "--allow-empty", "-m", "init", "-q"],
        cwd=tmp_path, check=True, env=env,
    )
    wt = tmp_path / "wt"
    subprocess.run(
        ["git", "worktree", "add", "-q", str(wt)],
        cwd=tmp_path, check=True, env=env,
    )
    assert is_inside_worktree(wt) is True


def test_is_inside_worktree_non_git_returns_false(tmp_path):
    """Outside any git repo -> False (no exception)."""
    assert is_inside_worktree(tmp_path) is False


def _write_run(automl_dir, run_id, lifecycle, hb_iso=None, goal_summary=""):
    rd = automl_dir / run_id
    rd.mkdir(parents=True, exist_ok=True)
    hb = hb_iso or _fresh_hb()
    (rd / "state.json").write_text(json.dumps({
        "lifecycle_state": lifecycle,
        "active_session": {
            "session_id": "s", "pid": 1,
            "started_at": hb, "last_heartbeat": hb,
        },
        "goal_summary": goal_summary,
    }))


def test_find_active_runs_skips_terminal(tmp_path):
    automl = tmp_path / ".automl"
    automl.mkdir()
    _write_run(automl, "r1", "achieved")
    _write_run(automl, "r2", "pursuing")
    actives = find_active_runs_in_cwd(automl_dir=automl)
    assert len(actives) == 1
    assert actives[0]["run_id"] == "r2"


def test_check_cwd_conflict_no_actives(tmp_path):
    automl = tmp_path / ".automl"
    automl.mkdir()
    decision = check_cwd_conflict(cwd=tmp_path, automl_dir=automl, allow_override=False)
    assert decision.refuse is False


def test_check_cwd_conflict_active_refuses(tmp_path):
    automl = tmp_path / ".automl"
    automl.mkdir()
    _write_run(automl, "r-active", "pursuing")
    decision = check_cwd_conflict(cwd=tmp_path, automl_dir=automl, allow_override=False)
    assert decision.refuse is True
    assert "r-active" in decision.message


def test_check_cwd_conflict_override_proceeds(tmp_path):
    automl = tmp_path / ".automl"
    automl.mkdir()
    _write_run(automl, "r-active", "pursuing")
    decision = check_cwd_conflict(cwd=tmp_path, automl_dir=automl, allow_override=True)
    assert decision.refuse is False
    assert decision.warning is True


def test_refuse_message_contains_run_id_and_command():
    msg = refuse_message(
        active_runs=[{"run_id": "20260506-143022-a8f3", "goal_summary": "Improve auth"}],
    )
    assert "20260506-143022-a8f3" in msg
    assert "git worktree add" in msg
    assert "--allow-cwd-conflict" in msg
