"""Iteration cap gate — ultimate safety against pure logic loops."""
from dataclasses import dataclass

DEFAULT_MAX_ITER = 10000


@dataclass
class IterationGateResult:
    tripped: bool
    target_state: str | None = None
    reason: str = ""


def check_iteration_cap(state: dict, max_iter: int = DEFAULT_MAX_ITER) -> IterationGateResult:
    """Trip when state.iterations >= max_iter."""
    iterations = state.get("iterations", 0)
    if iterations >= max_iter:
        return IterationGateResult(
            tripped=True,
            target_state="aborted",
            reason=f"iteration cap reached: {iterations} >= {max_iter}",
        )
    return IterationGateResult(tripped=False)
