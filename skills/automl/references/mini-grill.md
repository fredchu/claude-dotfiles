# Mini-Grill — Built-in Decision-Tree Discipline

This is /automl's built-in decision-tree interview discipline, used when the
external `grill-me` skill is not installed. Apply during alignment phase
when calibrator dialogue_depth is `deep` or when user signals high uncertainty.

## Core rules

1. **Start from the root decision.** What's the most fundamental choice that
   shapes everything downstream? Ask that first.

2. **Each answer reveals new branches.** When user's answer surfaces a
   sub-decision you hadn't anticipated, expand the tree — ask the new
   sub-question before moving to your next planned question.

3. **Force a stance.** Don't accept "whatever you think" or "I'm not sure" —
   give the user options + your recommendation, force them to confirm or
   redirect.

4. **Don't skip on high confidence.** Even if you're 90% sure of the answer,
   ask once and confirm. The 10% chance of being wrong is worth one question.

5. **Every leaf must be visited.** Don't leave a branch half-explored to move
   to a sibling. Finish the current decision tree path before pivoting.

6. **User says "go deeper" → expand.** If user wants more rigor on a specific
   branch, ask follow-up questions on that branch before moving on.

## Termination

- All planned root branches asked + answered + confirmed
- No new sub-branches were revealed in the most recent 2 questions
- User says "OK that's enough, go" or "GO" or "B" (approval signal)

When terminated, transition to writing goal.md (per mini-brainstorm step 4).
