"""
DeepEval Test Cases for PersonalizationAgent

LLM-as-judge evaluation for:
1. Context Extraction Quality - Does extract_context() correctly parse user intent?
2. Feedback Signal Extraction - Does process_feedback() correctly identify signals?
3. User Memory Consistency - Does memory system maintain correct state?

Uses GitHub Models (gpt-4o-mini) as the LLM judge.
"""

import sys
import os
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


def create_personalization_test_cases() -> List[Dict[str, Any]]:
    """
    Create DeepEval test cases for PersonalizationAgent evaluation.

    Returns:
        List of test case dictionaries with:
        - name: Test case identifier
        - input: User query or feedback
        - expected_output: Expected extraction result
        - metrics: Which DeepEval metrics to apply
        - threshold: Expected score threshold
        - description: What this test validates
        - test_type: Type of test (context_extraction, feedback_signal, memory)
    """

    test_cases = []

    # ========================================================================
    # CONTEXT EXTRACTION QUALITY TESTS (Answer Relevancy)
    # Measures: Does extract_context() correctly parse user intent?
    # ========================================================================

    test_cases.append({
        "name": "PE1_context_extraction_hiking_cold",
        "input": "hiking jacket for cold weather",
        "expected_context": {
            "activity": "hiking",
            "weather": "cold"
        },
        "metrics": ["answer_relevancy"],
        "threshold": 0.8,
        "description": "Extract activity and weather from simple query",
        "test_type": "context_extraction"
    })

    test_cases.append({
        "name": "PE2_context_multi_attribute",
        "input": "women's blue ski outfit under $500",
        "expected_context": {
            "gender": "Women",
            "colors": ["blue"],
            "activity": "skiing",
            "budget_max": 500
        },
        "metrics": ["answer_relevancy"],
        "threshold": 0.8,
        "description": "Extract multiple attributes including gender, color, activity, budget",
        "test_type": "context_extraction"
    })

    test_cases.append({
        "name": "PE3_context_fit_style",
        "input": "relaxed fit casual jacket for everyday wear",
        "expected_context": {
            "fit_preference": "relaxed",
            "style_preference": "casual"
        },
        "metrics": ["answer_relevancy"],
        "threshold": 0.75,
        "description": "Extract fit and style preferences",
        "test_type": "context_extraction"
    })

    test_cases.append({
        "name": "PE4_context_brand_feature",
        "input": "NorthPeak waterproof parka for mountaineering",
        "expected_context": {
            "brands": ["NorthPeak"],
            "features": ["waterproof"],
            "activity": "mountaineering"
        },
        "metrics": ["answer_relevancy"],
        "threshold": 0.8,
        "description": "Extract brand name and specific features",
        "test_type": "context_extraction"
    })

    test_cases.append({
        "name": "PE5_context_summer_travel",
        "input": "lightweight summer travel jacket that packs small",
        "expected_context": {
            "weather": "warm",
            "activity": "travel",
            "features": ["lightweight", "packable"]
        },
        "metrics": ["answer_relevancy"],
        "threshold": 0.75,
        "description": "Extract season/weather and travel-specific needs",
        "test_type": "context_extraction"
    })

    # ========================================================================
    # FEEDBACK SIGNAL EXTRACTION TESTS (Faithfulness)
    # Measures: Does process_feedback() correctly identify preference signals?
    # ========================================================================

    test_cases.append({
        "name": "PE6_feedback_fit_tight",
        "input": "This jacket is too tight, I prefer a looser fit",
        "expected_signals": [
            {"type": "fit_issue", "value": "too_tight"}
        ],
        "metrics": ["faithfulness"],
        "threshold": 0.85,
        "description": "Detect fit issue signal from negative feedback",
        "test_type": "feedback_signal"
    })

    test_cases.append({
        "name": "PE7_feedback_style_flashy",
        "input": "Too flashy and bright, I want something more subtle",
        "expected_signals": [
            {"type": "avoid_style", "value": "bright_colors"}
        ],
        "metrics": ["faithfulness"],
        "threshold": 0.85,
        "description": "Detect style preference signal from feedback",
        "test_type": "feedback_signal"
    })

    test_cases.append({
        "name": "PE8_feedback_price",
        "input": "This is way too expensive for what it offers",
        "expected_signals": [
            {"type": "price_issue", "value": "too_expensive"}
        ],
        "metrics": ["faithfulness"],
        "threshold": 0.85,
        "description": "Detect price concern signal",
        "test_type": "feedback_signal"
    })

    test_cases.append({
        "name": "PE9_feedback_positive",
        "input": "Perfect fit and I love the blue color!",
        "expected_signals": [
            {"type": "positive", "attribute": "fit"},
            {"type": "positive", "attribute": "color"}
        ],
        "metrics": ["faithfulness"],
        "threshold": 0.8,
        "description": "Detect positive feedback signals",
        "test_type": "feedback_signal"
    })

    test_cases.append({
        "name": "PE10_feedback_warmth",
        "input": "Not warm enough for real winter weather",
        "expected_signals": [
            {"type": "warmth_issue", "value": "insufficient"}
        ],
        "metrics": ["faithfulness"],
        "threshold": 0.85,
        "description": "Detect warmth/insulation concern",
        "test_type": "feedback_signal"
    })

    # ========================================================================
    # USER MEMORY CONSISTENCY TESTS (Contextual Relevancy)
    # Measures: Does memory system maintain correct user state?
    # ========================================================================

    test_cases.append({
        "name": "PE11_memory_save_retrieve",
        "input": "Save preferences then retrieve them",
        "test_scenario": {
            "action": "save_and_retrieve",
            "user_id": "test_user_pe11",
            "save_data": {
                "sizing": {"fit": "relaxed", "shirt": "M"},
                "general": {"budget_max": 300}
            }
        },
        "expected_behavior": "Retrieved preferences match saved values exactly",
        "metrics": ["contextual_relevancy"],
        "threshold": 0.9,
        "description": "Verify save/retrieve roundtrip maintains data integrity",
        "test_type": "memory_consistency"
    })

    test_cases.append({
        "name": "PE12_memory_session_override",
        "input": "Session override takes priority over permanent",
        "test_scenario": {
            "action": "session_override",
            "user_id": "test_user_pe12",
            "permanent_data": {"sizing": {"fit": "relaxed"}},
            "session_data": {"sizing": {"fit": "oversized"}}
        },
        "expected_behavior": "Session override value (oversized) returned, not permanent (relaxed)",
        "metrics": ["contextual_relevancy"],
        "threshold": 0.9,
        "description": "Verify session overrides take priority",
        "test_type": "memory_consistency"
    })

    test_cases.append({
        "name": "PE13_memory_user_isolation",
        "input": "User A cannot see User B data",
        "test_scenario": {
            "action": "user_isolation",
            "user_a": "test_user_pe13_a",
            "user_b": "test_user_pe13_b",
            "user_a_data": {"sizing": {"fit": "slim"}},
            "user_b_data": {"sizing": {"fit": "oversized"}}
        },
        "expected_behavior": "Each user's data is isolated - User A sees slim, User B sees oversized",
        "metrics": ["contextual_relevancy"],
        "threshold": 0.95,
        "description": "Verify user data isolation",
        "test_type": "memory_consistency"
    })

    test_cases.append({
        "name": "PE14_memory_returning_user",
        "input": "Identify returning user correctly",
        "test_scenario": {
            "action": "returning_user",
            "user_id": "test_user_pe14",
            "existing_data": {"sizing": {"fit": "classic"}}
        },
        "expected_behavior": "User identified as returning (is_new=False) with existing preferences",
        "metrics": ["contextual_relevancy"],
        "threshold": 0.9,
        "description": "Verify returning user identification",
        "test_type": "memory_consistency"
    })

    test_cases.append({
        "name": "PE15_memory_new_user",
        "input": "New user gets default structure",
        "test_scenario": {
            "action": "new_user",
            "user_id": "test_user_pe15_new"
        },
        "expected_behavior": "User identified as new (is_new=True) with default empty preferences",
        "metrics": ["contextual_relevancy"],
        "threshold": 0.9,
        "description": "Verify new user flow creates proper defaults",
        "test_type": "memory_consistency"
    })

    return test_cases


def get_context_extraction_context(query: str, extracted_context: Dict) -> List[str]:
    """
    Create retrieval context for context extraction tests.

    Args:
        query: Original user query
        extracted_context: Context extracted by PersonalizationAgent

    Returns:
        List of context strings describing the extraction
    """
    context_items = []

    context_items.append(f"Original query: {query}")

    if extracted_context:
        context_items.append("Extracted context fields:")
        for key, value in extracted_context.items():
            context_items.append(f"  - {key}: {value}")

    return context_items


def get_feedback_signal_context(feedback: str, signals: List[Dict]) -> List[str]:
    """
    Create retrieval context for feedback signal tests.

    Args:
        feedback: Original feedback text
        signals: Signals extracted by PersonalizationAgent

    Returns:
        List of context strings describing the signals
    """
    context_items = []

    context_items.append(f"Original feedback: {feedback}")

    if signals:
        context_items.append("Extracted signals:")
        for signal in signals:
            signal_str = ", ".join(f"{k}={v}" for k, v in signal.items())
            context_items.append(f"  - {signal_str}")
    else:
        context_items.append("No signals extracted")

    return context_items


def get_memory_test_context(scenario: Dict, result: Dict) -> List[str]:
    """
    Create retrieval context for memory consistency tests.

    Args:
        scenario: Test scenario configuration
        result: Actual result from memory operations

    Returns:
        List of context strings describing the memory state
    """
    context_items = []

    context_items.append(f"Test action: {scenario.get('action', 'unknown')}")
    context_items.append(f"User ID(s): {scenario.get('user_id', scenario.get('user_a', 'unknown'))}")

    if "save_data" in scenario:
        context_items.append(f"Saved data: {scenario['save_data']}")

    if "permanent_data" in scenario:
        context_items.append(f"Permanent data: {scenario['permanent_data']}")

    if "session_data" in scenario:
        context_items.append(f"Session data: {scenario['session_data']}")

    context_items.append(f"Result: {result}")

    return context_items


# Test the test case generator
if __name__ == "__main__":
    print("=" * 70)
    print("DeepEval Test Cases for PersonalizationAgent")
    print("=" * 70)

    test_cases = create_personalization_test_cases()

    print(f"\nGenerated {len(test_cases)} test cases:\n")

    # Group by test type
    by_type = {}
    for tc in test_cases:
        test_type = tc.get("test_type", "unknown")
        if test_type not in by_type:
            by_type[test_type] = []
        by_type[test_type].append(tc)

    for test_type, cases in by_type.items():
        print(f"\n{test_type.upper().replace('_', ' ')} ({len(cases)} cases):")
        for tc in cases:
            print(f"  - {tc['name']}: {tc['description']}")

    print("\n" + "=" * 70)
    print(f"Total: {len(test_cases)} PersonalizationAgent test cases ready")
    print("=" * 70)
