"""Lifecycle state machine for /automl v6.

States: aligning, pursuing, paused, achieved, unmet, budget-limited, aborted.
"""
from enum import Enum


class LifecycleState(str, Enum):
    ALIGNING = "aligning"
    PURSUING = "pursuing"
    PAUSED = "paused"
    ACHIEVED = "achieved"
    UNMET = "unmet"
    BUDGET_LIMITED = "budget-limited"
    ABORTED = "aborted"


VALID_TRANSITIONS: dict[str, set[str]] = {
    "aligning": {"pursuing", "aborted"},
    "pursuing": {"paused", "achieved", "unmet", "budget-limited", "aborted"},
    "paused": {"pursuing", "aborted"},
    "achieved": set(),
    "unmet": set(),
    "budget-limited": set(),
    "aborted": set(),
}

TERMINAL_STATES = {"achieved", "unmet", "budget-limited", "aborted"}


class IllegalTransitionError(Exception):
    """Raised when a state transition is not allowed."""


def transition(from_state: str, to_state: str, reason: str) -> bool:
    """Validate a state transition. Returns True if valid, raises on invalid."""
    if from_state not in VALID_TRANSITIONS:
        raise IllegalTransitionError(f"Unknown from_state: {from_state}")
    if to_state not in VALID_TRANSITIONS[from_state]:
        raise IllegalTransitionError(
            f"Invalid transition {from_state} -> {to_state} (reason: {reason}). "
            f"Allowed from {from_state}: {VALID_TRANSITIONS[from_state]}"
        )
    return True


def is_terminal(state: str) -> bool:
    """True if state is terminal (no outgoing transitions)."""
    return state in TERMINAL_STATES
