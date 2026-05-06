import json
from audit_gatekeeper import audit_round_output
from conftest import FIXTURES_DIR


def test_audit_passes_for_valid_achieved_with_all_3_evidence_types():
    fixture = json.loads(
        (FIXTURES_DIR / "sample_round_outputs/valid_achieved.json").read_text()
    )
    result = audit_round_output(fixture)
    assert result.all_pass is True
    assert result.audit_failures == []


def test_audit_fails_when_achieved_missing_file_change_evidence():
    fixture = json.loads(
        (FIXTURES_DIR / "sample_round_outputs/invalid_no_evidence.json").read_text()
    )
    result = audit_round_output(fixture)
    assert result.all_pass is False
    assert len(result.audit_failures) == 1
    assert result.audit_failures[0].criterion_id == "c1"
    assert "file_change" in result.audit_failures[0].reason
    assert "audit_check" in result.audit_failures[0].reason


def test_audit_passes_for_pursuing_status_no_evidence_required():
    fixture = json.loads(
        (FIXTURES_DIR / "sample_round_outputs/valid_pursuing.json").read_text()
    )
    result = audit_round_output(fixture)
    assert result.all_pass is True


def test_audit_fails_when_audit_check_satisfied_false_but_status_achieved():
    output = {
        "round_id": 1,
        "tokens_used_this_round": 100,
        "criteria_progress_update": {
            "c1": {
                "status": "achieved",
                "evidence": [
                    {"type": "file_change", "path": "x.py:1", "summary": "edit"},
                    {"type": "command_output", "command": "pytest", "verbatim_excerpt": "FAILED"},
                    {"type": "audit_check", "criterion_verbatim": "...", "satisfied": False, "rationale": "test failed"},
                ],
            }
        },
        "blockers": [],
        "main_session_action_request": None,
    }
    result = audit_round_output(output)
    assert result.all_pass is False
    assert "audit_check.satisfied is false" in result.audit_failures[0].reason


def test_audit_failures_list_each_failed_criterion():
    output = {
        "round_id": 1,
        "tokens_used_this_round": 100,
        "criteria_progress_update": {
            "c1": {
                "status": "achieved",
                "evidence": [{"type": "command_output", "command": "x", "verbatim_excerpt": "y"}],
            },
            "c2": {
                "status": "achieved",
                "evidence": [],
            },
        },
        "blockers": [],
        "main_session_action_request": None,
    }
    result = audit_round_output(output)
    assert result.all_pass is False
    assert len(result.audit_failures) == 2
    failure_ids = {f.criterion_id for f in result.audit_failures}
    assert failure_ids == {"c1", "c2"}
