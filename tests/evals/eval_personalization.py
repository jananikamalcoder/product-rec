"""
DeepEval evaluations for PersonalizationAgent.

Tests LLM behavior:
- Returns JSON data, not conversational questions
- Accepts partial preferences without demanding all fields
- Extracts feedback signals correctly
"""

import pytest
import json
from deepeval import assert_test
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase, LLMTestCaseParams


@pytest.mark.eval
@pytest.mark.asyncio
async def test_eval_identify_returns_json(personalization_agent):
    """Eval: PersonalizationAgent returns JSON, not questions."""
    thread = personalization_agent.get_new_thread()
    result = await personalization_agent.run("identify user EvalTestUser", thread=thread)

    test_case = LLMTestCase(
        input="identify user EvalTestUser",
        actual_output=result.text
    )

    metric = GEval(
        name="JSON Only Response",
        criteria="""The response must be structured data output (JSON or JSON-like).
        It should NOT contain:
        - Questions asking the user about their preferences
        - Numbered lists of preference questions (1. What fit do you prefer? 2. What's your size?)
        - Markdown bullet points asking for information
        - Conversational text asking for sizing, budget, colors, brands, etc.
        It SHOULD contain:
        - A JSON object or structured data
        - Fields like action, is_new, user_id, or similar data fields
        - Short, data-focused output""",
        evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT],
        threshold=0.7
    )

    assert_test(test_case, [metric])


@pytest.mark.eval
@pytest.mark.asyncio
async def test_eval_no_questionnaire(personalization_agent):
    """Eval: Agent should not generate preference questionnaires."""
    thread = personalization_agent.get_new_thread()
    result = await personalization_agent.run("identify user NewPersonForEval", thread=thread)

    test_case = LLMTestCase(
        input="identify user NewPersonForEval",
        actual_output=result.text
    )

    metric = GEval(
        name="No Questionnaire",
        criteria="""The response should NOT be a questionnaire or interview.
        REJECT responses that:
        - Ask about fit preference (slim, classic, relaxed, oversized)
        - Ask about shirt/pants/shoe sizes
        - Ask about budget
        - Ask about color preferences
        - Ask about brand preferences
        - Contain multiple numbered questions
        - Say things like "Let's start with a few questions" or "Let me gather your preferences"
        ACCEPT responses that:
        - Return data about the user (new/returning status)
        - Are brief and factual
        - Don't require user input to continue""",
        evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT],
        threshold=0.7
    )

    assert_test(test_case, [metric])


@pytest.mark.eval
@pytest.mark.asyncio
async def test_eval_save_partial_prefs(personalization_agent):
    """Eval: Agent accepts partial preferences without demanding more."""
    thread = personalization_agent.get_new_thread()
    result = await personalization_agent.run(
        "save preferences for PartialUser: fit=relaxed",
        thread=thread
    )

    test_case = LLMTestCase(
        input="save preferences for PartialUser: fit=relaxed",
        actual_output=result.text
    )

    metric = GEval(
        name="Accepts Partial Preferences",
        criteria="""The response should accept the partial preference data provided.
        REJECT responses that:
        - Ask for additional information (size, budget, colors, brands)
        - Say they need more information before saving
        - Generate a list of questions for missing fields
        - Require the user to provide all preference fields
        ACCEPT responses that:
        - Confirm the preference was saved
        - Return success confirmation
        - Work with the data provided without demanding more""",
        evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT],
        threshold=0.7
    )

    assert_test(test_case, [metric])


@pytest.mark.eval
@pytest.mark.asyncio
async def test_eval_feedback_extraction(personalization_agent):
    """Eval: Agent extracts signals from feedback text."""
    thread = personalization_agent.get_new_thread()
    result = await personalization_agent.run(
        "record feedback for FeedbackUser: too flashy and expensive",
        thread=thread
    )

    test_case = LLMTestCase(
        input="record feedback for FeedbackUser: too flashy and expensive",
        actual_output=result.text
    )

    metric = GEval(
        name="Extracts Feedback Signals",
        criteria="""The response should indicate that feedback signals were extracted.
        ACCEPT responses that:
        - Return extracted signals (avoid_style, budget, etc.)
        - Acknowledge the feedback was recorded
        - Show what was understood from the feedback
        - Return structured data about the feedback
        REJECT responses that:
        - Ask clarifying questions about the feedback
        - Don't acknowledge the feedback at all
        - Return generic "feedback noted" without signal extraction""",
        evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT],
        threshold=0.6
    )

    assert_test(test_case, [metric])


@pytest.mark.eval
@pytest.mark.asyncio
async def test_eval_json_structure(personalization_agent):
    """Eval: Response has valid JSON-like structure."""
    thread = personalization_agent.get_new_thread()
    result = await personalization_agent.run("get preferences for TestStructureUser", thread=thread)

    test_case = LLMTestCase(
        input="get preferences for TestStructureUser",
        actual_output=result.text
    )

    metric = GEval(
        name="Valid JSON Structure",
        criteria="""The response should have a valid JSON structure or be parseable data.
        ACCEPT responses that:
        - Are valid JSON (starts with { and ends with })
        - Contain key-value pairs
        - Are structured data output
        - Could be parsed by a JSON parser
        REJECT responses that:
        - Are conversational text
        - Are markdown formatted prose
        - Are questions or prompts for the user""",
        evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT],
        threshold=0.6
    )

    assert_test(test_case, [metric])
