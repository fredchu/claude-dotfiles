## CONTINUATION DIRECTIVE — Audit Discipline

You CANNOT claim a criterion is "achieved" without ALL of:

1. **Restate** the criterion verbatim from goal.md
2. **List the deliverables** for this criterion (concrete files / outputs)
3. **Map each deliverable to evidence**:
   - `file_path:line_number` showing the change
   - `command + verbatim output snippet` showing verification
4. **Negate proxy signals**:
   - ❌ "tests pass" insufficient — must show WHICH test, WHICH command, output line "1 passed"
   - ❌ "code compiles" insufficient — necessary not sufficient
   - ❌ "function exists" insufficient — must show called from where, returns what
5. **Cross-check against acceptance language**:
   - What did the user write in goal.md for this criterion?
   - Did you LITERALLY satisfy that wording?
   - If ambiguous, mark `status: needs_user_clarification` not `achieved`

## Required evidence types per `achieved` claim

Each criterion claimed `achieved` MUST have evidence list containing all THREE types:

- `{"type": "file_change", "path": "...", "summary": "..."}`
- `{"type": "command_output", "command": "...", "verbatim_excerpt": "..."}`
- `{"type": "audit_check", "criterion_verbatim": "...", "satisfied": true, "rationale": "..."}`

## Status options when not achieved

- `pursuing`: actively working, not done yet
- `blocked`: declare what's blocking (in `blockers` field)
- `needs_user_clarification`: criterion ambiguous, need user input
- `pursuing-regressed`: was previously achieved, but new edits broke it

## Anti-game guardrails

NEVER mark `achieved` without evidence list passing audit.
Main session will validate your evidence list against this directive.
False `achieved` reports will be reverted to `pursuing` and treated as a bug — your next round will be told why.
