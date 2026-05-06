from alignment_dialogue import (
    select_dialogue_strategy, build_initial_goal_draft
)


def test_select_strategy_full_uses_external_skill():
    env = {"skills_available": {"superpowers:brainstorming": True, "grill-me": True}}
    strategy = select_dialogue_strategy(env, dialogue_depth="normal")
    assert strategy.uses_external_brainstorming is True
    assert strategy.uses_external_grillme is True
    assert strategy.fallback_references == []


def test_select_strategy_degraded_uses_mini_references():
    env = {"skills_available": {"superpowers:brainstorming": False, "grill-me": False}}
    strategy = select_dialogue_strategy(env, dialogue_depth="normal")
    assert strategy.uses_external_brainstorming is False
    assert strategy.uses_external_grillme is False
    assert "mini-brainstorm.md" in strategy.fallback_references
    assert "mini-grill.md" in strategy.fallback_references


def test_select_strategy_partial_mixes_external_and_mini():
    env = {"skills_available": {"superpowers:brainstorming": True, "grill-me": False}}
    strategy = select_dialogue_strategy(env, dialogue_depth="deep")
    assert strategy.uses_external_brainstorming is True
    assert strategy.uses_external_grillme is False
    assert "mini-grill.md" in strategy.fallback_references


def test_build_initial_goal_draft_from_calibrator_template():
    calibrator_output = {
        "criteria_template": [
            {"id": "c1", "desc_draft": "Bug A fixed", "verification_draft": "pytest x", "needs_user_confirmation": False},
            {"id": "c2", "desc_draft": "Test added", "verification_draft": "pytest y", "needs_user_confirmation": True},
        ],
        "task_classification": {"type": "bug_fix"},
        "alignment": {"dialogue_depth": "shallow"},
        "budget": {"estimated_tokens": 40000, "strategy": "hard"},
        "calibrator_confidence": 0.85,
        "verification": {"should_red_team": False},
    }
    draft = build_initial_goal_draft(
        calibrator_output, run_id="20260506-143022-test", user_input="Fix auth bugs"
    )
    assert draft["frontmatter"]["run_id"] == "20260506-143022-test"
    assert draft["frontmatter"]["calibrator"]["dialogue_depth"] == "shallow"
    assert len(draft["frontmatter"]["acceptance_criteria"]) == 2
    assert draft["frontmatter"]["acceptance_criteria"][0]["desc"] == "Bug A fixed"
    assert "Fix auth bugs" in draft["body"]
    assert "c2" in draft["needs_user_confirmation_ids"]


def test_record_alignment_completion_sets_metadata():
    from alignment_dialogue import record_alignment_completion
    state = {"alignment_metadata": None}
    record_alignment_completion(state, questions_asked=3, depth="normal")
    assert state["alignment_metadata"] == {"questions_asked": 3, "depth": "normal"}


def test_record_alignment_completion_overwrites_existing():
    from alignment_dialogue import record_alignment_completion
    state = {"alignment_metadata": {"questions_asked": 1, "depth": "shallow"}}
    record_alignment_completion(state, questions_asked=5, depth="deep")
    assert state["alignment_metadata"] == {"questions_asked": 5, "depth": "deep"}
