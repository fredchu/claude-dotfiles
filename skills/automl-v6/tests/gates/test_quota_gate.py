import json
import pytest
from gates.quota_gate import check_quota, QuotaRegistry


@pytest.fixture
def tmp_registry(tmp_path):
    registry_dir = tmp_path / "quota_registry"
    registry_dir.mkdir()
    claude_max = registry_dir / "claude_max.json"
    claude_max.write_text(json.dumps({
        "quota_window": "2026-05-06T14:00 → 19:00",
        "total_used_pct": 0,
        "by_run": [],
        "last_updated": "2026-05-06T14:00:00+08:00",
    }))
    return registry_dir


def test_under_threshold_returns_pass(tmp_registry):
    result = check_quota(
        registry_dir=tmp_registry, cli="claude_max", run_id="r1", own_used_pct=30
    )
    assert result.tripped is False


def test_at_threshold_returns_trip(tmp_registry):
    result = check_quota(
        registry_dir=tmp_registry, cli="claude_max", run_id="r1", own_used_pct=75
    )
    assert result.tripped is True
    assert result.target_state == "paused"
    assert result.pause_reason == "quota_wait"


def test_unknown_cli_returns_pass(tmp_registry):
    """If we don't track this CLI, no gate."""
    result = check_quota(
        registry_dir=tmp_registry, cli="unknown_cli", run_id="r1", own_used_pct=99
    )
    assert result.tripped is False


def test_registry_update_writes_own_usage(tmp_registry):
    registry = QuotaRegistry(registry_dir=tmp_registry, cli="claude_max")
    registry.update_own_usage(run_id="r1", session_id="sess-1", used_pct=42)
    data = json.loads((tmp_registry / "claude_max.json").read_text())
    assert any(r["run_id"] == "r1" and r["used_pct"] == 42 for r in data["by_run"])
