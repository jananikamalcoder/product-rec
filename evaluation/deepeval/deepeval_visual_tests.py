"""
DeepEval Test Cases for VisualAgent

LLM-as-judge evaluation for:
1. Visualization Appropriateness - Does auto_visualize() select correct format?
2. Content Quality - Does visualization accurately represent product data?

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


def create_visual_test_cases() -> List[Dict[str, Any]]:
    """
    Create DeepEval test cases for VisualAgent evaluation.

    Returns:
        List of test case dictionaries with:
        - name: Test case identifier
        - input: Description of input scenario
        - product_count: Number of products to visualize
        - intent: Query intent (for auto_visualize routing)
        - expected_format: Expected visualization type
        - metrics: Which DeepEval metrics to apply
        - threshold: Expected score threshold
        - description: What this test validates
        - test_type: Type of test (format_selection, content_quality)
    """

    test_cases = []

    # ========================================================================
    # VISUALIZATION FORMAT SELECTION TESTS (Answer Relevancy)
    # Measures: Does auto_visualize() select the appropriate format?
    # ========================================================================

    test_cases.append({
        "name": "VE1_format_single_product",
        "input": "Visualize a single product",
        "product_count": 1,
        "intent": "search",
        "expected_format": "product_card",
        "metrics": ["answer_relevancy"],
        "threshold": 0.9,
        "description": "Single product should render as product card",
        "test_type": "format_selection"
    })

    test_cases.append({
        "name": "VE2_format_few_products",
        "input": "Visualize 3 products",
        "product_count": 3,
        "intent": "search",
        "expected_format": "comparison_table",
        "metrics": ["answer_relevancy"],
        "threshold": 0.85,
        "description": "2-5 products should render as comparison table",
        "test_type": "format_selection"
    })

    test_cases.append({
        "name": "VE3_format_many_products",
        "input": "Visualize 8 products",
        "product_count": 8,
        "intent": "search",
        "expected_format": "feature_matrix_and_list",
        "metrics": ["answer_relevancy"],
        "threshold": 0.85,
        "description": "6+ products should render as feature matrix + list",
        "test_type": "format_selection"
    })

    test_cases.append({
        "name": "VE4_format_comparison_intent",
        "input": "Visualize products with comparison intent",
        "product_count": 4,
        "intent": "comparison",
        "expected_format": "comparison_table",
        "expected_features": ["price_highlight", "rating_highlight"],
        "metrics": ["answer_relevancy"],
        "threshold": 0.9,
        "description": "Comparison intent should always use comparison table with highlights",
        "test_type": "format_selection"
    })

    test_cases.append({
        "name": "VE5_format_search_intent",
        "input": "Visualize products with search intent",
        "product_count": 6,
        "intent": "search",
        "expected_format": "product_list",
        "metrics": ["answer_relevancy"],
        "threshold": 0.85,
        "description": "Search intent with many products uses list format",
        "test_type": "format_selection"
    })

    # ========================================================================
    # CONTENT QUALITY TESTS (Faithfulness)
    # Measures: Does visualization accurately represent product data?
    # ========================================================================

    test_cases.append({
        "name": "VE6_content_price_accuracy",
        "input": "Verify prices in visualization match source data",
        "test_scenario": {
            "products": [
                {"product_name": "Test Jacket A", "price_usd": 199.99},
                {"product_name": "Test Jacket B", "price_usd": 299.99}
            ]
        },
        "expected_behavior": "Visualization contains exact prices $199.99 and $299.99",
        "metrics": ["faithfulness"],
        "threshold": 0.95,
        "description": "Prices in output must match input data exactly",
        "test_type": "content_quality"
    })

    test_cases.append({
        "name": "VE7_content_rating_format",
        "input": "Verify ratings are formatted correctly",
        "test_scenario": {
            "products": [
                {"product_name": "Test A", "rating": 4.5},
                {"product_name": "Test B", "rating": 3.0}
            ]
        },
        "expected_behavior": "Rating 4.5 shows as stars (4.5/5 or equivalent), 3.0 shows correctly",
        "metrics": ["faithfulness"],
        "threshold": 0.9,
        "description": "Ratings displayed with proper star formatting",
        "test_type": "content_quality"
    })

    test_cases.append({
        "name": "VE8_content_name_integrity",
        "input": "Verify product names are not incorrectly truncated",
        "test_scenario": {
            "products": [
                {"product_name": "Alpine Explorer Pro Waterproof Shell Jacket"},
                {"product_name": "Summit"}
            ]
        },
        "expected_behavior": "Long names may be truncated with ellipsis, short names shown in full",
        "metrics": ["faithfulness"],
        "threshold": 0.85,
        "description": "Product names handled appropriately",
        "test_type": "content_quality"
    })

    test_cases.append({
        "name": "VE9_content_highlight_accuracy",
        "input": "Verify best price/rating highlighted correctly",
        "test_scenario": {
            "products": [
                {"product_name": "A", "price_usd": 100, "rating": 4.0},
                {"product_name": "B", "price_usd": 200, "rating": 4.5},
                {"product_name": "C", "price_usd": 150, "rating": 3.5}
            ]
        },
        "expected_behavior": "Product A highlighted as best price, Product B highlighted as best rating",
        "metrics": ["faithfulness"],
        "threshold": 0.9,
        "description": "Best price and rating products correctly identified",
        "test_type": "content_quality"
    })

    test_cases.append({
        "name": "VE10_content_feature_matrix_scoring",
        "input": "Verify feature matrix scores calculated correctly",
        "test_scenario": {
            "products": [
                {"product_name": "A", "waterproofing": "Waterproof", "rating": 4.6, "price_usd": 250},
                {"product_name": "B", "waterproofing": "Weather Resistant", "rating": 4.2, "price_usd": 350}
            ],
            "features": ["waterproof", "high_rating", "under_300"]
        },
        "expected_behavior": "Product A scores higher (waterproof, high rating, under $300)",
        "metrics": ["faithfulness"],
        "threshold": 0.85,
        "description": "Feature matrix scores reflect actual product attributes",
        "test_type": "content_quality"
    })

    return test_cases


def get_format_selection_context(
    product_count: int,
    intent: str,
    selected_format: str,
    visualization_preview: str
) -> List[str]:
    """
    Create retrieval context for format selection tests.

    Args:
        product_count: Number of products
        intent: Query intent
        selected_format: Format chosen by auto_visualize
        visualization_preview: Preview of the output

    Returns:
        List of context strings describing the format selection
    """
    context_items = []

    context_items.append(f"Product count: {product_count}")
    context_items.append(f"Intent: {intent}")
    context_items.append(f"Selected format: {selected_format}")

    # Format selection rules
    context_items.append("Format selection rules:")
    context_items.append("  - 0 products: empty message")
    context_items.append("  - 1 product: product_card")
    context_items.append("  - 2-5 products: comparison_table")
    context_items.append("  - 6+ products: feature_matrix + product_list")
    context_items.append("  - comparison intent: always comparison_table")

    if visualization_preview:
        preview = visualization_preview[:200] + "..." if len(visualization_preview) > 200 else visualization_preview
        context_items.append(f"Output preview: {preview}")

    return context_items


def get_content_quality_context(
    input_products: List[Dict],
    output_visualization: str,
    validation_checks: List[Dict]
) -> List[str]:
    """
    Create retrieval context for content quality tests.

    Args:
        input_products: Source product data
        output_visualization: Generated visualization
        validation_checks: Results of data validation checks

    Returns:
        List of context strings describing the content quality
    """
    context_items = []

    context_items.append(f"Input products: {len(input_products)}")

    for p in input_products:
        context_items.append(
            f"  - {p.get('product_name', 'Unknown')}: "
            f"${p.get('price_usd', 0)}, "
            f"rating={p.get('rating', 'N/A')}"
        )

    context_items.append("Validation results:")
    for check in validation_checks:
        status = "PASS" if check.get("passed", False) else "FAIL"
        context_items.append(f"  [{status}] {check.get('check', 'unknown')}: {check.get('detail', '')}")

    return context_items


# Sample products for testing
SAMPLE_PRODUCTS = [
    {
        "product_name": "Summit Pro Parka",
        "brand": "NorthPeak",
        "price_usd": 275.0,
        "rating": 4.6,
        "category": "Outerwear",
        "subcategory": "Parkas",
        "gender": "Men",
        "waterproofing": "Waterproof",
        "insulation": "Insulated",
        "season": "Winter"
    },
    {
        "product_name": "Alpine Explorer",
        "brand": "AlpineCo",
        "price_usd": 325.0,
        "rating": 4.8,
        "category": "Outerwear",
        "subcategory": "Parkas",
        "gender": "Unisex",
        "waterproofing": "Waterproof",
        "insulation": "Insulated",
        "season": "Winter"
    },
    {
        "product_name": "TrailBlazer Light",
        "brand": "TrailForge",
        "price_usd": 189.0,
        "rating": 4.3,
        "category": "Outerwear",
        "subcategory": "Lightweight Jackets",
        "gender": "Women",
        "waterproofing": "Weather Resistant",
        "insulation": "Non-insulated",
        "season": "All-season"
    }
]


# Test the test case generator
if __name__ == "__main__":
    print("=" * 70)
    print("DeepEval Test Cases for VisualAgent")
    print("=" * 70)

    test_cases = create_visual_test_cases()

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
    print(f"Total: {len(test_cases)} VisualAgent test cases ready")
    print("=" * 70)
