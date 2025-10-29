"""
DeepEval Test Cases for Product Search Agent

LLM-as-judge test cases to evaluate:
1. Answer Relevancy - Does the response match user intent?
2. Faithfulness - Does the agent hallucinate product features?
3. Contextual Relevancy - Are retrieved products semantically appropriate?

These complement the existing IR metrics (Precision, Recall, NDCG, MRR, Hit Rate)
with semantic quality assessment using GitHub Models as the LLM judge.
"""

from typing import List, Dict, Any
from deepeval.test_case import LLMTestCase
import agent_tools


def create_deepeval_test_cases() -> List[Dict[str, Any]]:
    """
    Create DeepEval test cases for LLM-as-judge evaluation.

    Returns:
        List of test case dictionaries with:
        - name: Test case name
        - input: User query
        - actual_output: Agent's response (to be filled by runner)
        - retrieval_context: Retrieved product descriptions
        - expected_output: Expected response (optional)
        - metrics: Which DeepEval metrics to apply
        - threshold: Expected score threshold
    """

    test_cases = []

    # ========================================================================
    # ANSWER RELEVANCY TESTS
    # Measures: Does the agent's response semantically match user intent?
    # ========================================================================

    # Test 1: Skiing jacket - semantic understanding
    test_cases.append({
        "name": "AR1_skiing_jacket_semantic",
        "input": "I need a warm jacket for skiing in extreme cold",
        "query": "warm jacket for skiing",
        "expected_attributes": {
            "season": "Winter",
            "primary_purpose": "Skiing",
            "insulation": "Insulated"
        },
        "metrics": ["answer_relevancy"],
        "threshold": 0.8,
        "description": "Agent should recommend insulated winter jackets suitable for skiing"
    })

    # Test 2: Waterproof hiking gear
    test_cases.append({
        "name": "AR2_waterproof_hiking",
        "input": "Show me waterproof jackets for hiking in the rain",
        "query": "waterproof jacket for hiking",
        "expected_attributes": {
            "waterproofing": "Waterproof",
            "primary_purpose": ["Trail Hiking", "Backpacking"]
        },
        "metrics": ["answer_relevancy"],
        "threshold": 0.8,
        "description": "Agent should focus on waterproof jackets for outdoor activities"
    })

    # Test 3: Travel jacket - lightweight requirement
    test_cases.append({
        "name": "AR3_travel_lightweight",
        "input": "I'm looking for a lightweight jacket for travel that packs small",
        "query": "lightweight jacket for travel",
        "expected_attributes": {
            "primary_purpose": "Travel",
            "subcategory": ["Lightweight Jackets", "Bombers/Softshell"]
        },
        "metrics": ["answer_relevancy"],
        "threshold": 0.75,
        "description": "Agent should prioritize packable, travel-friendly jackets"
    })

    # Test 4: Women's winter jacket with price constraint
    test_cases.append({
        "name": "AR4_womens_budget",
        "input": "Show me women's winter jackets under $300",
        "query": "women's winter jacket",
        "filter_params": {
            "gender": "Women",
            "max_price": 300,
            "category": "Outerwear"
        },
        "expected_attributes": {
            "gender": "Women",
            "price_range": "under $300"
        },
        "metrics": ["answer_relevancy"],
        "threshold": 0.85,
        "description": "Agent should filter by gender and price correctly"
    })

    # Test 5: Brand-specific query
    test_cases.append({
        "name": "AR5_brand_specific",
        "input": "What NorthPeak parkas do you have?",
        "query": "parka",
        "filter_params": {
            "brand": "NorthPeak",
            "category": "Outerwear"
        },
        "expected_attributes": {
            "brand": "NorthPeak",
            "subcategory": "Parkas"
        },
        "metrics": ["answer_relevancy"],
        "threshold": 0.9,
        "description": "Agent should only show NorthPeak parkas"
    })

    # ========================================================================
    # FAITHFULNESS TESTS
    # Measures: Does the agent hallucinate product features?
    # ========================================================================

    # Test 6: Price accuracy
    test_cases.append({
        "name": "F1_price_accuracy",
        "input": "Tell me about the prices of NorthPeak jackets",
        "query": "jacket",
        "filter_params": {"brand": "NorthPeak", "category": "Outerwear"},
        "metrics": ["faithfulness"],
        "threshold": 0.9,
        "description": "Agent must report accurate prices from product data",
        "check_attributes": ["price_usd"]
    })

    # Test 7: Feature accuracy - waterproofing
    test_cases.append({
        "name": "F2_waterproof_accuracy",
        "input": "Which jackets are fully waterproof?",
        "query": "waterproof jacket",
        "expected_attributes": {
            "waterproofing": "Waterproof"  # Must not confuse with "Weather Resistant"
        },
        "metrics": ["faithfulness"],
        "threshold": 0.9,
        "description": "Agent must distinguish waterproof from water-resistant",
        "check_attributes": ["waterproofing"]
    })

    # Test 8: Insulation type accuracy
    test_cases.append({
        "name": "F3_insulation_accuracy",
        "input": "Show me down-insulated parkas",
        "query": "down parka",
        "expected_attributes": {
            "material": "Down",
            "subcategory": "Parkas"
        },
        "metrics": ["faithfulness"],
        "threshold": 0.9,
        "description": "Agent must accurately report insulation type (down vs synthetic)",
        "check_attributes": ["material", "insulation"]
    })

    # Test 9: Product availability
    test_cases.append({
        "name": "F4_availability",
        "input": "How many jackets do you have in total?",
        "query": "jacket",
        "filter_params": {"category": "Outerwear"},
        "metrics": ["faithfulness"],
        "threshold": 0.95,
        "description": "Agent must report actual count from database",
        "check_attributes": ["count"]
    })

    # Test 10: Brand accuracy
    test_cases.append({
        "name": "F5_brand_accuracy",
        "input": "What brands carry winter parkas?",
        "query": "parka",
        "filter_params": {"subcategory": "Parkas"},
        "metrics": ["faithfulness"],
        "threshold": 0.95,
        "description": "Agent must only mention brands that actually exist in catalog",
        "check_attributes": ["brand"]
    })

    # ========================================================================
    # CONTEXTUAL RELEVANCY TESTS
    # Measures: Are retrieved products semantically appropriate?
    # ========================================================================

    # Test 11: Skiing gear - context match
    test_cases.append({
        "name": "CR1_skiing_context",
        "input": "warm jacket for skiing",
        "query": "warm jacket for skiing",
        "expected_context_themes": ["skiing", "winter", "insulated", "cold weather"],
        "metrics": ["contextual_relevancy"],
        "threshold": 0.75,
        "description": "Retrieved products should be contextually relevant to skiing"
    })

    # Test 12: Summer hiking - negative test
    test_cases.append({
        "name": "CR2_summer_hiking",
        "input": "lightweight jacket for summer hiking",
        "query": "lightweight jacket summer",
        "expected_context_themes": ["lightweight", "summer", "breathable", "hiking"],
        "unexpected_context": ["down", "insulated", "winter", "parka"],
        "metrics": ["contextual_relevancy"],
        "threshold": 0.7,
        "description": "Should NOT retrieve heavy winter gear for summer query"
    })

    # Test 13: Waterproof context
    test_cases.append({
        "name": "CR3_waterproof_context",
        "input": "waterproof shell jacket for rain",
        "query": "waterproof shell jacket",
        "expected_context_themes": ["waterproof", "rain", "shell", "weather protection"],
        "metrics": ["contextual_relevancy"],
        "threshold": 0.75,
        "description": "Retrieved products should focus on rain/waterproof features"
    })

    # Test 14: Travel/urban context
    test_cases.append({
        "name": "CR4_travel_urban",
        "input": "stylish jacket for city travel",
        "query": "jacket travel urban",
        "expected_context_themes": ["travel", "urban", "versatile", "casual"],
        "unexpected_context": ["alpine", "mountaineering", "extreme", "technical"],
        "metrics": ["contextual_relevancy"],
        "threshold": 0.65,
        "description": "Should retrieve casual/urban jackets, not technical climbing gear"
    })

    # Test 15: Multi-attribute context
    test_cases.append({
        "name": "CR5_multi_attribute",
        "input": "women's waterproof jacket for trail hiking under $250",
        "query": "waterproof jacket hiking",
        "filter_params": {
            "gender": "Women",
            "max_price": 250
        },
        "expected_context_themes": ["women", "waterproof", "hiking", "trail", "affordable"],
        "metrics": ["contextual_relevancy"],
        "threshold": 0.75,
        "description": "Retrieved products should match multiple contextual requirements"
    })

    return test_cases


def get_product_context(product_data: Dict[str, Any]) -> str:
    """
    Convert product data into context string for DeepEval.

    Args:
        product_data: Product dictionary from agent_tools

    Returns:
        Formatted context string with key product attributes
    """
    return (
        f"{product_data['product_name']} by {product_data['brand']} - "
        f"${product_data['price_usd']} - "
        f"{product_data['category']} > {product_data['subcategory']} - "
        f"{product_data.get('material', 'N/A')} material - "
        f"{product_data.get('insulation', 'None')} insulation - "
        f"{product_data.get('waterproofing', 'None')} waterproofing - "
        f"{product_data.get('season', 'N/A')} season - "
        f"For {product_data.get('primary_purpose', 'general use')} - "
        f"{product_data.get('gender', 'Unisex')}"
    )


def search_and_create_context(test_case: Dict[str, Any]) -> List[str]:
    """
    Execute search query and create retrieval context for DeepEval.

    Args:
        test_case: Test case dictionary with query and filter params

    Returns:
        List of context strings (product descriptions)
    """
    query = test_case.get("query")
    filter_params = test_case.get("filter_params", {})

    # Execute search
    if filter_params:
        result = agent_tools.search_with_filters(
            query=query,
            **filter_params,
            max_results=10
        )
    else:
        result = agent_tools.search_products(query, max_results=10)

    # Convert products to context strings
    if result['success'] and result['products']:
        return [get_product_context(p) for p in result['products']]
    else:
        return []


# Test the test case generator
if __name__ == "__main__":
    print("=" * 70)
    print("DeepEval Test Cases for Product Search Agent")
    print("=" * 70)

    test_cases = create_deepeval_test_cases()

    print(f"\nGenerated {len(test_cases)} test cases:\n")

    # Group by metric type
    by_metric = {}
    for tc in test_cases:
        for metric in tc['metrics']:
            if metric not in by_metric:
                by_metric[metric] = []
            by_metric[metric].append(tc)

    for metric, cases in by_metric.items():
        print(f"\n{metric.upper().replace('_', ' ')} ({len(cases)} cases):")
        for tc in cases:
            print(f"  - {tc['name']}: {tc['description']}")

    # Show example test case with context
    print("\n" + "=" * 70)
    print("Example Test Case with Retrieval Context")
    print("=" * 70)

    example_tc = test_cases[0]  # Skiing jacket test
    print(f"\nTest: {example_tc['name']}")
    print(f"Input: {example_tc['input']}")
    print(f"Query: {example_tc['query']}")
    print(f"Metrics: {example_tc['metrics']}")
    print(f"Threshold: {example_tc['threshold']}")

    print("\nRetrieving products and generating context...")
    context = search_and_create_context(example_tc)

    if context:
        print(f"\nRetrieved {len(context)} products:")
        for i, ctx in enumerate(context[:3], 1):
            print(f"{i}. {ctx}")
        if len(context) > 3:
            print(f"   ... and {len(context) - 3} more")
    else:
        print("\nNo products found!")

    print("\n" + "=" * 70)
    print(f"✓ {len(test_cases)} test cases ready for DeepEval evaluation")
    print("=" * 70)
