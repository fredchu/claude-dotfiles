from gates.budget_gate import check_budget_cap


def test_under_threshold_returns_pass():
    state = {"tokens": {"estimated": 100000, "actual": 30000}}
    result = check_budget_cap(state)
    assert result.tripped is False
    assert result.injection_required is False


def test_at_80_percent_returns_inject_budget_limit():
    state = {"tokens": {"estimated": 100000, "actual": 80000}}
    result = check_budget_cap(state)
    assert result.tripped is True
    assert result.injection_required is True
    assert result.target_state == "budget-limited"


def test_no_budget_strategy_skips_check():
    """If budget_strategy is 'none' (e.g. --no-budget), gate does nothing."""
    state = {
        "tokens": {"estimated": 100000, "actual": 200000},
        "budget_strategy": "none",
    }
    result = check_budget_cap(state)
    assert result.tripped is False


def test_zero_estimate_skips_check():
    """If estimated is 0 (uninitialized), don't divide by zero."""
    state = {"tokens": {"estimated": 0, "actual": 1000}}
    result = check_budget_cap(state)
    assert result.tripped is False


def test_threshold_configurable():
    state = {"tokens": {"estimated": 100000, "actual": 50000}}
    result = check_budget_cap(state, threshold=0.4)
    assert result.tripped is True
