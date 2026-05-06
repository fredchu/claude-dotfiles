import pytest
from lifecycle_fsm import (
    transition, is_terminal, IllegalTransitionError, VALID_TRANSITIONS
)


def test_valid_transition_aligning_to_pursuing():
    assert transition("aligning", "pursuing", reason="goal.md finalized") is True


def test_valid_transition_pursuing_to_paused():
    assert transition("pursuing", "paused", reason="quota gate") is True


def test_valid_transition_pursuing_to_achieved():
    assert transition("pursuing", "achieved", reason="all criteria met") is True


def test_invalid_transition_aligning_to_achieved_fails():
    with pytest.raises(IllegalTransitionError):
        transition("aligning", "achieved", reason="skipped pursuing")


def test_invalid_transition_achieved_to_pursuing_fails():
    with pytest.raises(IllegalTransitionError):
        transition("achieved", "pursuing", reason="retry")


def test_terminal_states():
    assert is_terminal("achieved") is True
    assert is_terminal("unmet") is True
    assert is_terminal("budget-limited") is True
    assert is_terminal("aborted") is True
    assert is_terminal("pursuing") is False
    assert is_terminal("paused") is False
    assert is_terminal("aligning") is False


def test_pause_resume_loop_allowed():
    assert transition("pursuing", "paused", reason="user pause") is True
    assert transition("paused", "pursuing", reason="user resume") is True


def test_all_states_have_defined_transitions():
    all_states = {"aligning", "pursuing", "paused", "achieved", "unmet", "budget-limited", "aborted"}
    keys = set(VALID_TRANSITIONS.keys())
    targets = set()
    for tos in VALID_TRANSITIONS.values():
        targets.update(tos)
    assert all_states <= (keys | targets)
