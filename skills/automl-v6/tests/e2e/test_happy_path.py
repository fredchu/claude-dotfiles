"""E2E happy path: invoke → calibrate → align (mock approve) → 2 rounds → achieved."""
import pytest
from state_io import init_state, read_state, atomic_update
from orchestrator import apply_round_output_to_state, decide_next_action
from audit_gatekeeper import audit_round_output
from lifecycle_fsm import transition


@pytest.fixture
def run_dir(tmp_path):
    return tmp_path / "20260506-143022-test"


def test_happy_path_calibrate_align_two_rounds_achieved(
    run_dir, mock_calibrator_response, mock_round_responses
):
    # Phase A: init state.json (lifecycle = aligning)
    run_dir.mkdir()
    init_state(run_dir, run_id="20260506-143022-test", session_id="sess-1", pid=1234)

    state = read_state(run_dir)
    assert state["lifecycle_state"] == "aligning"

    # Phase B: post-alignment (mock approval) — set up criteria from calibrator
    def setup_criteria(s):
        for c in mock_calibrator_response["criteria_template"]:
            s["criteria_progress"][c["id"]] = {"status": "pending", "evidence": []}
        s["tokens"]["estimated"] = mock_calibrator_response["budget"]["estimated_tokens"]
        transition("aligning", "pursuing", reason="goal.md finalized (mock)")
        s["lifecycle_state"] = "pursuing"
        s["lifecycle_transitions"].append({
            "from": "aligning", "to": "pursuing",
            "ts": "2026-05-06T14:31:00+08:00",
            "reason": "goal.md finalized (mock)",
        })
        return s

    atomic_update(run_dir, setup_criteria)
    state = read_state(run_dir)
    assert state["lifecycle_state"] == "pursuing"
    assert "c1" in state["criteria_progress"]
    assert state["criteria_progress"]["c1"]["status"] == "pending"

    # Phase C: Round 1 — pursuing, no progress yet
    round1_output = mock_round_responses[0]
    audit1 = audit_round_output(round1_output)
    assert audit1.all_pass is True

    state = atomic_update(run_dir, lambda s: apply_round_output_to_state(
        s, round1_output,
        audit_failures=[(f.criterion_id, f.reason) for f in audit1.audit_failures],
    ))
    assert state["criteria_progress"]["c1"]["status"] == "pursuing"
    assert state["iterations"] == 1
    assert state["tokens"]["actual"] == 5200

    decision1 = decide_next_action(state, audit_pass=audit1.all_pass, blockers=[])
    assert decision1.action == "next_round"

    # Phase D: Round 2 — achieved with full evidence
    round2_output = mock_round_responses[1]
    audit2 = audit_round_output(round2_output)
    assert audit2.all_pass is True

    state = atomic_update(run_dir, lambda s: apply_round_output_to_state(
        s, round2_output,
        audit_failures=[(f.criterion_id, f.reason) for f in audit2.audit_failures],
    ))
    assert state["criteria_progress"]["c1"]["status"] == "achieved"
    assert state["iterations"] == 2

    decision2 = decide_next_action(state, audit_pass=audit2.all_pass, blockers=[])
    assert decision2.action == "transition"
    assert decision2.target_state == "achieved"

    # Phase E: Apply terminal transition
    transition(state["lifecycle_state"], decision2.target_state, reason=decision2.reason)

    def apply_terminal(s):
        s["lifecycle_state"] = decision2.target_state
        s["lifecycle_transitions"].append({
            "from": "pursuing", "to": decision2.target_state,
            "ts": "2026-05-06T14:45:00+08:00",
            "reason": decision2.reason,
        })
        return s

    final_state = atomic_update(run_dir, apply_terminal)
    assert final_state["lifecycle_state"] == "achieved"
