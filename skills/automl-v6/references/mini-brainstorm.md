# Mini-Brainstorm — Built-in Alignment Dialogue Discipline

This is /automl's built-in alignment dialogue discipline, used when the external
`superpowers:brainstorming` skill is not installed. Apply these rules during
the alignment phase (lifecycle: aligning).

## Core rules

1. **One question at a time.** Multiple-choice format preferred when possible.

2. **Lead with your recommendation.** Never ask blank questions like "what do
   you think?". Always: "Option A: X. Option B: Y. I recommend B because Z.
   Which?".

3. **After user answers, restate your understanding.** "So you want X. Is that
   right?" — give them a chance to correct.

4. **All questions answered → write goal.md → user reviews → user approves.**

5. **HARD GATE**: do not write any code, do not dispatch round subagent,
   until user has approved the written goal.md.

## Question budget by depth (calibrator-determined)

- `shallow`: 1-2 confirmation questions only ("here's my understanding, OK?")
- `normal`: 3-5 questions covering scope / criteria / verification
- `deep`: 6+ questions, applying mini-grill discipline (see mini-grill.md)

## When to escalate to user

- User answer reveals contradiction with previous answer → flag it, ask
  for clarification
- Answer reveals new sub-decision not in original scope → ask: "Should this
  be in this run, or a separate /automl invocation?"
- Calibrator marked criterion as `needs_user_confirmation: true` → must ask
  user before adding to goal.md
