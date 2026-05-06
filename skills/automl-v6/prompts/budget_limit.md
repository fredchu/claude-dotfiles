## BUDGET LIMIT REACHED — Graceful Wrap-Up

Your calibrated token budget for this run has been substantially consumed.
You are now in graceful wrap-up mode. The rules change:

### What you MUST do this round
1. **Do NOT start new substantive work.** No new features, no new fixes.
2. **Summarize useful progress** so far in `criteria_progress_update`.
3. **Identify remaining work** for each criterion still in `pursuing` status:
   - What concrete next step would have completed it?
   - Estimated additional tokens needed?
4. **Identify blockers** that prevented completion (in `blockers` field).
5. **Leave the user a clear next step** in `main_session_action_request`:
   - Suggest: `--no-budget` rerun, OR split goal, OR alternative approach.

### What you MUST NOT do
- Mark any criterion `achieved` unless evidence is already complete from prior rounds
- Speculate on completion ("would have worked if...")
- Continue editing files (this round is for reporting only)

### Output
Same `criteria_progress_update` JSON as normal rounds, but with focus on
documenting state for next user decision rather than advancing work.

This is a terminal round. After your output, lifecycle transitions to
`budget-limited` and the run completes (no more rounds).
