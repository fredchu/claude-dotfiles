"""Calibrated budget cap gate — injects budget_limit prompt at 80% by default."""
from dataclasses import dataclass

DEFAULT_THRESHOLD = 0.80


@dataclass
class BudgetGateResult:
    tripped: bool
    target_state: str | None = None
    reason: str = ""
    injection_required: bool = False


def check_budget_cap(state: dict, threshold: float = DEFAULT_THRESHOLD) -> BudgetGateResult:
    """Trip when actual / estimated >= threshold AND budget_strategy != 'none'."""
    if state.get("budget_strategy") == "none":
        return BudgetGateResult(tripped=False)

    tokens = state.get("tokens", {})
    estimated = tokens.get("estimated", 0)
    actual = tokens.get("actual", 0)

    if estimated <= 0:
        return BudgetGateResult(tripped=False)

    ratio = actual / estimated
    if ratio >= threshold:
        return BudgetGateResult(
            tripped=True,
            target_state="budget-limited",
            reason=f"budget threshold reached: {actual}/{estimated} = {ratio:.0%} >= {threshold:.0%}",
            injection_required=True,
        )
    return BudgetGateResult(tripped=False)
