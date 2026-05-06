from gates.context_gate import check_context_usage, classify_context_alert


def test_under_60_percent_no_alert():
    result = check_context_usage(used_pct=0.5)
    assert result.tripped is False
    assert result.alert_bucket is None


def test_at_60_percent_advisory_hint():
    result = check_context_usage(used_pct=0.60)
    assert result.tripped is False
    assert result.alert_bucket == 60


def test_at_75_percent_advisory_hint():
    result = check_context_usage(used_pct=0.75)
    assert result.tripped is False
    assert result.alert_bucket == 75


def test_at_80_percent_hard_transition():
    result = check_context_usage(used_pct=0.80)
    assert result.tripped is True
    assert result.target_state == "paused"
    assert result.pause_reason == "context_critical"


def test_classify_returns_correct_bucket():
    assert classify_context_alert(0.55) is None
    assert classify_context_alert(0.60) == 60
    assert classify_context_alert(0.65) == 65
    assert classify_context_alert(0.70) == 70
    assert classify_context_alert(0.75) == 75
    assert classify_context_alert(0.80) == 80
