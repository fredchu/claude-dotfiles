from gates.repeat_loop_gate import check_repeat_loop


def test_no_failures_returns_pass():
    result = check_repeat_loop(state={"audit_failure_log": []})
    assert result.tripped is False


def test_two_same_hash_returns_pass():
    """Threshold is 3 — 2 same is not enough."""
    failures = [
        {"criterion_id": "c1", "reason": "missing evidence"},
        {"criterion_id": "c1", "reason": "missing evidence"},
    ]
    result = check_repeat_loop(state={"audit_failure_log": failures})
    assert result.tripped is False


def test_three_same_hash_returns_trip():
    failures = [
        {"criterion_id": "c1", "reason": "missing evidence"},
        {"criterion_id": "c1", "reason": "missing evidence"},
        {"criterion_id": "c1", "reason": "missing evidence"},
    ]
    result = check_repeat_loop(state={"audit_failure_log": failures})
    assert result.tripped is True
    assert result.target_state == "aborted"


def test_three_different_hashes_returns_pass():
    failures = [
        {"criterion_id": "c1", "reason": "reason A"},
        {"criterion_id": "c1", "reason": "reason B"},
        {"criterion_id": "c1", "reason": "reason C"},
    ]
    result = check_repeat_loop(state={"audit_failure_log": failures})
    assert result.tripped is False


def test_only_last_three_considered():
    """Older entries don't count — only most recent 3."""
    failures = [
        {"criterion_id": "c1", "reason": "old"},
        {"criterion_id": "c1", "reason": "old"},
        {"criterion_id": "c1", "reason": "old"},
        {"criterion_id": "c1", "reason": "new"},
    ]
    result = check_repeat_loop(state={"audit_failure_log": failures})
    assert result.tripped is False
