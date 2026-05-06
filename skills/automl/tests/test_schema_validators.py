import pytest
from schema_validators import validate_state_json, SchemaValidationError


def test_valid_state_json_passes():
    valid = {
        "schema_version": "v6.0",
        "run_id": "20260506-143022-a8f3",
        "lifecycle_state": "aligning",
        "lifecycle_transitions": [
            {"from": None, "to": "aligning", "ts": "2026-05-06T14:30:22+08:00", "reason": "run started"}
        ],
        "active_session": {
            "session_id": "abc-123",
            "pid": 84521,
            "started_at": "2026-05-06T14:30:22+08:00",
            "last_heartbeat": "2026-05-06T14:30:22+08:00"
        },
        "criteria_progress": {},
        "tokens": {"estimated": 0, "actual": 0, "by_round": []},
        "iterations": 0,
        "expected_wake_at": None,
        "audit_failure_log": []
    }
    assert validate_state_json(valid) is True


def test_missing_required_field_fails():
    invalid = {"schema_version": "v6.0"}
    with pytest.raises(SchemaValidationError):
        validate_state_json(invalid)


def test_invalid_lifecycle_state_fails():
    invalid = {
        "schema_version": "v6.0",
        "run_id": "20260506-143022-a8f3",
        "lifecycle_state": "invented_state",
        "lifecycle_transitions": [],
        "active_session": None,
        "criteria_progress": {},
        "tokens": {"estimated": 0, "actual": 0, "by_round": []},
        "iterations": 0,
        "expected_wake_at": None,
        "audit_failure_log": []
    }
    with pytest.raises(SchemaValidationError):
        validate_state_json(invalid)


def test_state_with_alignment_metadata_validates():
    """Phase 4: alignment_metadata is optional, accepts {questions_asked, depth}."""
    state = {
        "schema_version": "v6.0",
        "run_id": "20260506-200000-test",
        "lifecycle_state": "achieved",
        "lifecycle_transitions": [],
        "active_session": None,
        "criteria_progress": {},
        "tokens": {"estimated": 1000, "actual": 800, "by_round": []},
        "iterations": 0,
        "expected_wake_at": None,
        "audit_failure_log": [],
        "alignment_metadata": {"questions_asked": 3, "depth": "normal"},
    }
    assert validate_state_json(state) is True


def test_state_alignment_metadata_null_validates():
    """alignment_metadata may be null when alignment hasn't completed."""
    state = {
        "schema_version": "v6.0",
        "run_id": "20260506-200000-test",
        "lifecycle_state": "aligning",
        "lifecycle_transitions": [],
        "active_session": None,
        "criteria_progress": {},
        "tokens": {"estimated": 0, "actual": 0, "by_round": []},
        "iterations": 0,
        "expected_wake_at": None,
        "audit_failure_log": [],
        "alignment_metadata": None,
    }
    assert validate_state_json(state) is True


def test_state_alignment_metadata_invalid_object_fails():
    """Malformed alignment_metadata (missing required key) is rejected."""
    state = {
        "schema_version": "v6.0",
        "run_id": "20260506-200000-bad1",
        "lifecycle_state": "aligning",
        "lifecycle_transitions": [],
        "active_session": None,
        "criteria_progress": {},
        "tokens": {"estimated": 0, "actual": 0, "by_round": []},
        "iterations": 0,
        "expected_wake_at": None,
        "audit_failure_log": [],
        "alignment_metadata": {"questions_asked": 3},  # missing 'depth'
    }
    with pytest.raises(SchemaValidationError):
        validate_state_json(state)
