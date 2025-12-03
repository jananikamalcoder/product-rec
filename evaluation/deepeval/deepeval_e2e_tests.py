"""
DeepEval End-to-End Test Cases for 3-Agent System

LLM-as-judge evaluation for complete workflows:
1. New user styling journey
2. Returning user search flow
3. Feedback loop
4. Comparison workflow
5. Session override behavior
6. Multi-turn conversation
7. Budget constraint handling
8. Cross-agent data flow

Uses GitHub Models (gpt-4o-mini) as the LLM judge.
"""

import sys
from typing import List, Dict, Any
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Conditional import - deepeval only needed when running evals
try:
    from deepeval.test_case import LLMTestCase
except ImportError:
    LLMTestCase = None  # Will be available when deepeval is installed


def create_e2e_test_cases() -> List[Dict[str, Any]]:
    """
    Create DeepEval test cases for end-to-end workflow evaluation.

    Returns:
        List of test case dictionaries with:
        - name: Test case identifier
        - input: User query/scenario description
        - workflow: Description of the expected workflow
        - metrics: Which DeepEval metrics to apply
        - threshold: Expected score threshold
        - description: What this test validates
        - steps: Sequence of expected steps
    """

    test_cases = []

    # ========================================================================
    # E2E WORKFLOW TESTS
    # ========================================================================

    test_cases.append({
        "name": "E2E1_new_user_styling",
        "input": "I'm looking for an outfit for hiking in cold weather",
        "user_id": "e2e_new_user_1",
        "workflow": "new_user_styling",
        "steps": [
            "1. Orchestrator classifies intent as STYLING",
            "2. PersonalizationAgent identifies user as NEW",
            "3. PersonalizationAgent extracts context (activity=hiking, weather=cold)",
            "4. ProductSearch finds relevant products",
            "5. VisualAgent formats results appropriately"
        ],
        "expected_outputs": {
            "intent": "STYLING",
            "is_new_user": True,
            "context_extracted": ["hiking", "cold"],
            "products_returned": True,
            "visualization_format": "comparison_table or product_list"
        },
        "metrics": ["answer_relevancy", "faithfulness", "contextual_relevancy"],
        "threshold": 0.75,
        "description": "Complete new user styling workflow from query to visualization"
    })

    test_cases.append({
        "name": "E2E2_returning_user_search",
        "input": "Show me some jackets",
        "user_id": "e2e_returning_user_2",
        "setup": {
            "existing_preferences": {
                "sizing": {"fit": "relaxed"},
                "general": {"budget_max": 300},
                "preferences": {"outerwear": {"colors": ["blue", "black"]}}
            }
        },
        "workflow": "returning_user_search",
        "steps": [
            "1. Orchestrator classifies intent as PRODUCT_SEARCH",
            "2. PersonalizationAgent identifies user as RETURNING",
            "3. Stored preferences loaded (fit=relaxed, budget=300)",
            "4. Preferences applied as filters/context",
            "5. ProductSearch returns filtered results",
            "6. VisualAgent formats results"
        ],
        "expected_outputs": {
            "intent": "PRODUCT_SEARCH",
            "is_new_user": False,
            "preferences_applied": True,
            "products_match_preferences": True
        },
        "metrics": ["answer_relevancy", "faithfulness", "contextual_relevancy"],
        "threshold": 0.75,
        "description": "Returning user flow with preference application"
    })

    test_cases.append({
        "name": "E2E3_feedback_loop",
        "input": "These are too tight, I prefer looser fitting jackets",
        "user_id": "e2e_feedback_user_3",
        "previous_context": {
            "last_query": "Show me hiking jackets",
            "last_results": ["Jacket A", "Jacket B"]
        },
        "workflow": "feedback_loop",
        "steps": [
            "1. PersonalizationAgent processes feedback",
            "2. Extract signal: fit_issue = too_tight",
            "3. Update user preferences (fit preference → looser)",
            "4. Re-run search with updated preferences",
            "5. Return products matching new preference"
        ],
        "expected_outputs": {
            "feedback_processed": True,
            "signal_extracted": "fit_issue",
            "preferences_updated": True,
            "new_results_match_feedback": True
        },
        "metrics": ["faithfulness", "contextual_relevancy"],
        "threshold": 0.8,
        "description": "Feedback triggers preference update and improved results"
    })

    test_cases.append({
        "name": "E2E4_comparison_workflow",
        "input": "Compare NorthPeak and AlpineCo parkas",
        "user_id": "e2e_comparison_user_4",
        "workflow": "comparison",
        "steps": [
            "1. Orchestrator classifies intent as COMPARISON",
            "2. ProductSearch finds NorthPeak parkas",
            "3. ProductSearch finds AlpineCo parkas",
            "4. VisualAgent creates comparison table",
            "5. Highlight best price and best rating"
        ],
        "expected_outputs": {
            "intent": "COMPARISON",
            "brands_found": ["NorthPeak", "AlpineCo"],
            "visualization_format": "comparison_table",
            "highlights_present": True
        },
        "metrics": ["answer_relevancy", "faithfulness"],
        "threshold": 0.8,
        "description": "Brand comparison with appropriate visualization"
    })

    test_cases.append({
        "name": "E2E5_session_override",
        "input": "For today, show me oversized fits only",
        "user_id": "e2e_session_user_5",
        "setup": {
            "permanent_preferences": {"sizing": {"fit": "slim"}}
        },
        "workflow": "session_override",
        "steps": [
            "1. User has permanent preference: fit=slim",
            "2. User requests session override: fit=oversized",
            "3. Session override saved (permanent=False)",
            "4. Current query uses oversized fit",
            "5. After session clear, reverts to slim"
        ],
        "expected_outputs": {
            "permanent_fit": "slim",
            "session_override_fit": "oversized",
            "current_effective_fit": "oversized",
            "override_not_persisted": True
        },
        "metrics": ["faithfulness", "contextual_relevancy"],
        "threshold": 0.85,
        "description": "Session override takes priority but doesn't persist"
    })

    test_cases.append({
        "name": "E2E6_multi_turn_conversation",
        "input": "Make it under $200",
        "user_id": "e2e_multiturn_user_6",
        "conversation_history": [
            {"role": "user", "content": "Show me hiking jackets"},
            {"role": "assistant", "content": "Here are some hiking jackets..."},
            {"role": "user", "content": "Make it under $200"}
        ],
        "workflow": "multi_turn",
        "steps": [
            "1. Parse refinement query",
            "2. Extract price constraint: $200",
            "3. Apply to previous search context (hiking jackets)",
            "4. Return filtered results"
        ],
        "expected_outputs": {
            "context_maintained": True,
            "refinement_applied": True,
            "all_results_under_200": True
        },
        "metrics": ["answer_relevancy", "contextual_relevancy"],
        "threshold": 0.75,
        "description": "Refinement query uses previous context"
    })

    test_cases.append({
        "name": "E2E7_budget_constraint",
        "input": "I need a winter jacket under $300",
        "user_id": "e2e_budget_user_7",
        "workflow": "budget_constraint",
        "steps": [
            "1. Extract budget constraint: max_price=300",
            "2. Extract season: winter",
            "3. Apply both filters to search",
            "4. Return only products <= $300 for winter"
        ],
        "expected_outputs": {
            "budget_extracted": 300,
            "season_extracted": "Winter",
            "all_results_under_budget": True,
            "all_results_winter": True
        },
        "metrics": ["faithfulness", "contextual_relevancy"],
        "threshold": 0.9,
        "description": "Budget constraint strictly applied to results"
    })

    test_cases.append({
        "name": "E2E8_cross_agent_data_flow",
        "input": "Help me pick an outfit for camping",
        "user_id": "e2e_crossagent_user_8",
        "workflow": "cross_agent",
        "steps": [
            "1. Orchestrator receives query, classifies as STYLING",
            "2. Orchestrator calls PersonalizationAgent.extract_context()",
            "3. Context: {activity: camping} flows to ProductSearch",
            "4. ProductSearch returns camping-appropriate products",
            "5. Products flow to VisualAgent.auto_visualize()",
            "6. Visualization returned to user"
        ],
        "data_flow_checkpoints": [
            "orchestrator_input → personalization_context",
            "personalization_context → search_query",
            "search_results → visual_input",
            "visual_output → final_response"
        ],
        "expected_outputs": {
            "all_agents_called": True,
            "data_flow_complete": True,
            "context_preserved": True
        },
        "metrics": ["answer_relevancy", "faithfulness", "contextual_relevancy"],
        "threshold": 0.75,
        "description": "Data flows correctly through all 3 agents"
    })

    return test_cases


def get_e2e_workflow_context(
    workflow_name: str,
    steps_executed: List[str],
    checkpoints: Dict[str, Any],
    final_output: str
) -> List[str]:
    """
    Create retrieval context for E2E workflow tests.

    Args:
        workflow_name: Name of the workflow
        steps_executed: List of steps that were executed
        checkpoints: Data at various checkpoints
        final_output: Final output to user

    Returns:
        List of context strings describing the workflow execution
    """
    context_items = []

    context_items.append(f"Workflow: {workflow_name}")
    context_items.append(f"Steps executed: {len(steps_executed)}")

    for i, step in enumerate(steps_executed, 1):
        context_items.append(f"  Step {i}: {step}")

    if checkpoints:
        context_items.append("Checkpoints:")
        for checkpoint, value in checkpoints.items():
            context_items.append(f"  - {checkpoint}: {value}")

    if final_output:
        preview = final_output[:200] + "..." if len(final_output) > 200 else final_output
        context_items.append(f"Final output preview: {preview}")

    return context_items


def validate_e2e_result(
    test_case: Dict[str, Any],
    actual_result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Validate E2E test result against expected outputs.

    Args:
        test_case: Test case definition
        actual_result: Actual execution result

    Returns:
        Validation result with pass/fail for each expected output
    """
    expected = test_case.get("expected_outputs", {})
    validation = {"passed": True, "checks": []}

    for key, expected_value in expected.items():
        actual_value = actual_result.get(key)

        if isinstance(expected_value, bool):
            passed = actual_value == expected_value
        elif isinstance(expected_value, list):
            passed = all(v in actual_value for v in expected_value) if actual_value else False
        elif isinstance(expected_value, (int, float)):
            passed = actual_value == expected_value if actual_value else False
        else:
            passed = str(expected_value).lower() in str(actual_value).lower() if actual_value else False

        validation["checks"].append({
            "key": key,
            "expected": expected_value,
            "actual": actual_value,
            "passed": passed
        })

        if not passed:
            validation["passed"] = False

    return validation


# Test the test case generator
if __name__ == "__main__":
    print("=" * 70)
    print("DeepEval End-to-End Test Cases for 3-Agent System")
    print("=" * 70)

    test_cases = create_e2e_test_cases()

    print(f"\nGenerated {len(test_cases)} test cases:\n")

    for tc in test_cases:
        print(f"\n{tc['name']}:")
        print(f"  Input: {tc['input']}")
        print(f"  Workflow: {tc['workflow']}")
        print(f"  Description: {tc['description']}")
        print(f"  Steps: {len(tc['steps'])}")
        print(f"  Metrics: {tc['metrics']}")
        print(f"  Threshold: {tc['threshold']}")

    print("\n" + "=" * 70)
    print(f"Total: {len(test_cases)} E2E test cases ready")
    print("=" * 70)
