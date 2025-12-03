"""
DeepEval Test Cases for Orchestrator

LLM-as-judge evaluation for:
1. Intent Classification - Does classify_intent() correctly identify query type?
2. Query Routing - Does process_query() route to correct handler?
3. Filter Application - Does _apply_filters() correctly filter products?

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


def create_orchestrator_test_cases() -> List[Dict[str, Any]]:
    """
    Create DeepEval test cases for Orchestrator evaluation.

    Returns:
        List of test case dictionaries with:
        - name: Test case identifier
        - input: User query
        - expected_intent: Expected QueryIntent
        - metrics: Which DeepEval metrics to apply
        - threshold: Expected score threshold
        - description: What this test validates
        - test_type: Type of test (intent_classification, query_routing, filter_application)
    """

    test_cases = []

    # ========================================================================
    # INTENT CLASSIFICATION TESTS (Answer Relevancy)
    # Measures: Does classify_intent() correctly identify query type?
    # ========================================================================

    test_cases.append({
        "name": "OE1_intent_styling_outfit",
        "input": "I need an outfit for hiking this weekend",
        "expected_intent": "STYLING",
        "keywords_detected": ["outfit"],
        "metrics": ["answer_relevancy"],
        "threshold": 0.85,
        "description": "Classify outfit request as STYLING intent",
        "test_type": "intent_classification"
    })

    test_cases.append({
        "name": "OE2_intent_search_product",
        "input": "Show me waterproof jackets under $300",
        "expected_intent": "PRODUCT_SEARCH",
        "keywords_detected": ["show me", "jackets"],
        "metrics": ["answer_relevancy"],
        "threshold": 0.85,
        "description": "Classify product request as PRODUCT_SEARCH intent",
        "test_type": "intent_classification"
    })

    test_cases.append({
        "name": "OE3_intent_comparison",
        "input": "Compare NorthPeak vs AlpineCo parkas",
        "expected_intent": "COMPARISON",
        "keywords_detected": ["compare", "vs"],
        "metrics": ["answer_relevancy"],
        "threshold": 0.9,
        "description": "Classify comparison request as COMPARISON intent",
        "test_type": "intent_classification"
    })

    test_cases.append({
        "name": "OE4_intent_info",
        "input": "What brands do you carry?",
        "expected_intent": "INFO",
        "keywords_detected": ["brands"],
        "metrics": ["answer_relevancy"],
        "threshold": 0.85,
        "description": "Classify catalog question as INFO intent",
        "test_type": "intent_classification"
    })

    test_cases.append({
        "name": "OE5_intent_styling_dress",
        "input": "Help me dress for a ski trip next month",
        "expected_intent": "STYLING",
        "keywords_detected": ["dress", "help me"],
        "metrics": ["answer_relevancy"],
        "threshold": 0.85,
        "description": "Classify dressing help as STYLING intent",
        "test_type": "intent_classification"
    })

    test_cases.append({
        "name": "OE6_intent_comparison_better",
        "input": "Which jacket is better for rain - shell or parka?",
        "expected_intent": "COMPARISON",
        "keywords_detected": ["better"],
        "metrics": ["answer_relevancy"],
        "threshold": 0.85,
        "description": "Classify 'better' question as COMPARISON intent",
        "test_type": "intent_classification"
    })

    # ========================================================================
    # QUERY ROUTING TESTS (Faithfulness)
    # Measures: Does process_query() route to correct handler?
    # ========================================================================

    test_cases.append({
        "name": "OE7_routing_styling",
        "input": "I need an outfit for camping",
        "expected_handler": "_handle_styling_query",
        "expected_flow": "PersonalizationAgent -> extract_context -> ProductSearch",
        "metrics": ["faithfulness"],
        "threshold": 0.85,
        "description": "Styling query routes through PersonalizationAgent",
        "test_type": "query_routing"
    })

    test_cases.append({
        "name": "OE8_routing_search",
        "input": "Find me insulated parkas",
        "expected_handler": "_handle_search_query",
        "expected_flow": "Direct ProductSearch -> results",
        "metrics": ["faithfulness"],
        "threshold": 0.85,
        "description": "Search query routes directly to ProductSearch",
        "test_type": "query_routing"
    })

    test_cases.append({
        "name": "OE9_routing_comparison",
        "input": "Compare the Summit Pro and Alpine Explorer",
        "expected_handler": "_handle_comparison_query",
        "expected_flow": "ProductSearch -> comparison formatting",
        "metrics": ["faithfulness"],
        "threshold": 0.85,
        "description": "Comparison query includes comparison formatting",
        "test_type": "query_routing"
    })

    test_cases.append({
        "name": "OE10_routing_info",
        "input": "Show me your catalog statistics",
        "expected_handler": "_handle_info_query",
        "expected_flow": "Catalog info tools",
        "metrics": ["faithfulness"],
        "threshold": 0.85,
        "description": "Info query routes to catalog tools",
        "test_type": "query_routing"
    })

    # ========================================================================
    # FILTER APPLICATION TESTS (Contextual Relevancy)
    # Measures: Does _apply_filters() correctly filter products?
    # ========================================================================

    test_cases.append({
        "name": "OE11_filter_gender_price",
        "input": "Women's jackets under $300",
        "filters": {
            "gender": "Women",
            "max_price": 300
        },
        "expected_behavior": "All results are Women's gender AND price <= $300",
        "metrics": ["contextual_relevancy"],
        "threshold": 0.95,
        "description": "Gender and price filters applied correctly",
        "test_type": "filter_application"
    })

    test_cases.append({
        "name": "OE12_filter_brand_season",
        "input": "NorthPeak winter parkas",
        "filters": {
            "brands": ["NorthPeak"],
            "season": ["Winter"]
        },
        "expected_behavior": "All results are NorthPeak brand AND Winter season",
        "metrics": ["contextual_relevancy"],
        "threshold": 0.95,
        "description": "Brand and season filters applied correctly",
        "test_type": "filter_application"
    })

    return test_cases


def get_intent_classification_context(
    query: str,
    classified_intent: str,
    rule_based: bool = True
) -> List[str]:
    """
    Create retrieval context for intent classification tests.

    Args:
        query: Original user query
        classified_intent: Intent returned by classifier
        rule_based: Whether rule-based or LLM classification was used

    Returns:
        List of context strings describing the classification
    """
    context_items = []

    context_items.append(f"Query: {query}")
    context_items.append(f"Classified intent: {classified_intent}")
    context_items.append(f"Classification method: {'Rule-based' if rule_based else 'LLM-based'}")

    # Add keyword analysis
    query_lower = query.lower()
    styling_kw = ["outfit", "wear", "dress", "style", "look", "help me dress"]
    comparison_kw = ["compare", "versus", "vs", "better", "difference"]
    info_kw = ["brands", "categories", "statistics", "catalog"]

    detected = []
    for kw in styling_kw:
        if kw in query_lower:
            detected.append(f"STYLING: '{kw}'")
    for kw in comparison_kw:
        if kw in query_lower:
            detected.append(f"COMPARISON: '{kw}'")
    for kw in info_kw:
        if kw in query_lower:
            detected.append(f"INFO: '{kw}'")

    if detected:
        context_items.append(f"Keywords detected: {', '.join(detected)}")
    else:
        context_items.append("No specific keywords - defaulted to PRODUCT_SEARCH")

    return context_items


def get_query_routing_context(
    query: str,
    intent: str,
    handler_called: str,
    result_summary: Dict
) -> List[str]:
    """
    Create retrieval context for query routing tests.

    Args:
        query: Original user query
        intent: Classified intent
        handler_called: Which handler method was invoked
        result_summary: Summary of the result

    Returns:
        List of context strings describing the routing
    """
    context_items = []

    context_items.append(f"Query: {query}")
    context_items.append(f"Intent: {intent}")
    context_items.append(f"Handler: {handler_called}")

    if result_summary:
        context_items.append("Result summary:")
        for key, value in result_summary.items():
            context_items.append(f"  - {key}: {value}")

    return context_items


def get_filter_application_context(
    filters: Dict,
    products_before: int,
    products_after: int,
    sample_results: List[Dict]
) -> List[str]:
    """
    Create retrieval context for filter application tests.

    Args:
        filters: Applied filters
        products_before: Count before filtering
        products_after: Count after filtering
        sample_results: Sample of filtered products

    Returns:
        List of context strings describing the filtering
    """
    context_items = []

    context_items.append(f"Filters applied: {filters}")
    context_items.append(f"Products before: {products_before}")
    context_items.append(f"Products after: {products_after}")
    context_items.append(f"Filter efficiency: {100 * (1 - products_after/max(products_before, 1)):.1f}% removed")

    if sample_results:
        context_items.append("Sample results:")
        for p in sample_results[:3]:
            context_items.append(
                f"  - {p.get('product_name', 'Unknown')}: "
                f"${p.get('price_usd', 0)}, "
                f"{p.get('gender', 'Unisex')}, "
                f"{p.get('brand', 'Unknown')}"
            )

    return context_items


# Test the test case generator
if __name__ == "__main__":
    print("=" * 70)
    print("DeepEval Test Cases for Orchestrator")
    print("=" * 70)

    test_cases = create_orchestrator_test_cases()

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
    print(f"Total: {len(test_cases)} Orchestrator test cases ready")
    print("=" * 70)
