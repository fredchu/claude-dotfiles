"""Render the multi-section status text per spec §8.3.

Pure function: caller reads state.json + calibrator.json + env.json, then
passes dicts in. No I/O here so the renderer is straightforward to test.
"""
from datetime import datetime, timezone


def _format_tokens(actual: int, estimated: int) -> str:
    pct = round(actual / estimated * 100) if estimated else 0
    return f"{actual} / {estimated} ({pct}%)"


def _format_should_red_team(should: bool) -> str:
    return "yes" if should else "no"


def _last_activity(state: dict) -> str:
    """Return human-readable 'Xm ago' from the most recent heartbeat or transition."""
    active = state.get("active_session")
    if active and active.get("last_heartbeat"):
        try:
            ts = datetime.fromisoformat(active["last_heartbeat"])
        except ValueError:
            return "unknown"
    elif state.get("lifecycle_transitions"):
        try:
            ts = datetime.fromisoformat(state["lifecycle_transitions"][-1]["ts"])
        except ValueError:
            return "unknown"
    else:
        return "unknown"
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    delta = datetime.now(timezone.utc) - ts.astimezone(timezone.utc)
    minutes = int(delta.total_seconds() // 60)
    if minutes < 1:
        return "just now"
    if minutes < 60:
        return f"{minutes}m ago"
    return f"{minutes // 60}h ago"


CRITERION_GLYPH = {
    "achieved": "[✓]",
    "pursuing": "[⏳]",
    "pending": "[⏸]",
    "blocked": "[!]",
    "needs_user_clarification": "[?]",
}


def render_status(
    state: dict,
    calibrator: dict,
    goal_summary: str,
    env: dict,
    quota: dict,
    context_used_pct: int,
) -> str:
    lines: list[str] = []

    # 1. Header
    lifecycle = state.get("lifecycle_state", "?")
    iterations = state.get("iterations", 0)
    lines.append(f"Run: {state.get('run_id', '?')}")
    lines.append(f"State: {lifecycle} (round {iterations})")
    lines.append(f"Goal: {goal_summary}")
    lines.append("")

    # 2. Tokens / wall / CLI
    tokens = state.get("tokens", {})
    actual = tokens.get("actual", 0)
    estimated = tokens.get("estimated", 0)
    lines.append(f"Tokens: {_format_tokens(actual, estimated)}")
    cli_label = env.get("cli", "claude-code")
    lines.append(f"CLI:    {cli_label}")
    lines.append("")

    # 3. Criteria progress
    lines.append("Criteria progress:")
    for cid, prog in state.get("criteria_progress", {}).items():
        status = prog.get("status", "unknown")
        glyph = CRITERION_GLYPH.get(status, "[?]")
        lines.append(f"  {glyph} {cid}  {status}")
    lines.append("")

    # 4. Calibration
    alignment = calibrator.get("alignment", {})
    budget = calibrator.get("budget", {})
    verification = calibrator.get("verification", {})
    similar = calibrator.get("similar_lessons", [])
    confidence = calibrator.get("calibrator_confidence", "?")
    lines.append("Calibration:")
    lines.append(
        f"  depth: {alignment.get('dialogue_depth', '?')}"
        f"       budget: {budget.get('strategy', '?')}"
        f"     should_red_team: {_format_should_red_team(verification.get('should_red_team', False))}"
    )
    if isinstance(confidence, float):
        conf_str = f"{confidence:.2f}"
    else:
        conf_str = str(confidence)
    lines.append(f"  confidence: {conf_str}    similar_lessons: {len(similar)} found")
    lines.append("")

    # 5. Quota / Context
    lines.append(f"Quota: claude_max {quota.get('claude_max', 0)}%, codex {quota.get('codex', 0)}% (5h windows)")
    lines.append(f"Context: {context_used_pct}% used")
    lines.append("")

    # 6. Degraded mode banner
    missing = env.get("missing_soft_deps") or []
    if missing:
        lines.append(f"⚠ Degraded mode: missing [{', '.join(missing)}]")
        lines.append("  Alignment using built-in mini-* discipline")
        lines.append("")

    # 7. Last activity
    lines.append(f"Last activity: {_last_activity(state)}")

    return "\n".join(lines) + "\n"
