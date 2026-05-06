"""Alignment dialogue strategy selection + initial goal.md draft from calibrator output.

The actual back-and-forth dialogue runs in main session conversation, applying
either external brainstorming/grill-me skills or built-in mini-* references.
"""
from dataclasses import dataclass, field


@dataclass
class DialogueStrategy:
    uses_external_brainstorming: bool
    uses_external_grillme: bool
    fallback_references: list[str] = field(default_factory=list)


def select_dialogue_strategy(env: dict, dialogue_depth: str) -> DialogueStrategy:
    """Choose which alignment skill / fallback references to use."""
    skills = env.get("skills_available", {})
    has_brainstorming = skills.get("superpowers:brainstorming", False)
    has_grillme = skills.get("grill-me", False)

    fallbacks = []
    if not has_brainstorming:
        fallbacks.append("mini-brainstorm.md")
    if not has_grillme:
        fallbacks.append("mini-grill.md")

    return DialogueStrategy(
        uses_external_brainstorming=has_brainstorming,
        uses_external_grillme=has_grillme,
        fallback_references=fallbacks,
    )


def build_initial_goal_draft(
    calibrator_output: dict,
    run_id: str,
    user_input: str,
) -> dict:
    """Build initial goal.md frontmatter + body draft from calibrator output.

    Returns:
        {
          "frontmatter": <goal.md frontmatter dict>,
          "body": <markdown body str>,
          "needs_user_confirmation_ids": <list of criterion ids needing confirm>
        }
    """
    criteria = []
    needs_confirm = []
    for c in calibrator_output["criteria_template"]:
        criteria.append({
            "id": c["id"],
            "desc": c["desc_draft"],
            "verification": c["verification_draft"],
        })
        if c.get("needs_user_confirmation", False):
            needs_confirm.append(c["id"])

    frontmatter = {
        "run_id": run_id,
        "schema_version": "v6.0",
        "calibrator": {
            "dialogue_depth": calibrator_output["alignment"]["dialogue_depth"],
            "budget_estimate": calibrator_output["budget"]["estimated_tokens"],
            "budget_strategy": calibrator_output["budget"]["strategy"],
            "confidence": calibrator_output["calibrator_confidence"],
            "similar_lessons": calibrator_output.get("similar_lessons", []),
        },
        "acceptance_criteria": criteria,
    }

    criteria_lines = "\n".join(f"{i+1}. {c['desc']}" for i, c in enumerate(criteria))
    verification_lines = "\n".join(f"- {c['verification']}" for c in criteria)
    body = f"""# Goal: {user_input}

## Outcome
<to be filled by alignment dialogue>

## Scope
<to be filled by alignment dialogue>

## Acceptance Criteria
{criteria_lines}

## Verification
{verification_lines}

## Stop Rules
<to be filled by alignment dialogue>
"""

    return {
        "frontmatter": frontmatter,
        "body": body,
        "needs_user_confirmation_ids": needs_confirm,
    }
