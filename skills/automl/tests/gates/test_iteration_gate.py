from gates.iteration_gate import check_iteration_cap


def test_under_cap_returns_pass():
    result = check_iteration_cap(state={"iterations": 50}, max_iter=10000)
    assert result.tripped is False


def test_at_cap_returns_trip():
    result = check_iteration_cap(state={"iterations": 10000}, max_iter=10000)
    assert result.tripped is True
    assert result.target_state == "aborted"
    assert "iteration cap" in result.reason.lower()


def test_over_cap_returns_trip():
    result = check_iteration_cap(state={"iterations": 10001}, max_iter=10000)
    assert result.tripped is True


def test_default_max_is_10000():
    result = check_iteration_cap(state={"iterations": 9999})
    assert result.tripped is False
    result = check_iteration_cap(state={"iterations": 10000})
    assert result.tripped is True
