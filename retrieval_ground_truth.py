"""
Ground Truth Dataset for Retrieval Evaluation

This file defines query-product relevance pairs for evaluating
the quality of the Product Search Agent's retrieval capabilities.

Each query has:
- query: The search query string
- relevant_products: List of product IDs that are relevant (in order of relevance)
- category: Type of search (semantic, filter, hybrid, category)
- description: What we're testing

Relevance is determined by:
- Semantic similarity (meaning match)
- Attribute match (exact criteria)
- User intent match (purpose/use case)
"""

from typing import List, Dict, Any
import agent_tools

# Helper function to find product IDs by criteria
def find_product_ids(
    brand: str = None,
    category: str = None,
    subcategory: str = None,
    gender: str = None,
    min_price: float = None,
    max_price: float = None,
    query: str = None,
    limit: int = 20
) -> List[str]:
    """Find product IDs matching criteria."""
    if query:
        result = agent_tools.search_with_filters(
            query=query,
            brand=brand,
            category=category,
            gender=gender,
            min_price=min_price,
            max_price=max_price,
            max_results=limit
        )
    else:
        result = agent_tools.filter_products_by_attributes(
            brand=brand,
            category=category,
            subcategory=subcategory,
            gender=gender,
            min_price=min_price,
            max_price=max_price,
            max_results=limit
        )

    if result['success']:
        return [p['product_id'] for p in result['products']]
    return []


def get_ground_truth() -> List[Dict[str, Any]]:
    """
    Generate ground truth dataset for retrieval evaluation.

    Returns:
        List of test cases with queries and relevant product IDs
    """

    ground_truth = []

    # ========================================================================
    # SEMANTIC SEARCH TESTS
    # ========================================================================

    # Test 1: Winter sports - skiing
    ground_truth.append({
        "query": "warm jacket for skiing",
        "relevant_products": find_product_ids(
            query="skiing winter jacket warm",
            category="Outerwear",
            limit=10
        ),
        "category": "semantic",
        "description": "Semantic search for skiing jackets",
        "expected_attributes": {
            "season": "Winter",
            "insulation": "Insulated",
            "category": "Outerwear"
        }
    })

    # Test 2: Waterproof hiking gear
    ground_truth.append({
        "query": "waterproof jacket for hiking",
        "relevant_products": find_product_ids(
            query="waterproof hiking",
            category="Outerwear",
            limit=10
        ),
        "category": "semantic",
        "description": "Semantic search for waterproof hiking jackets",
        "expected_attributes": {
            "waterproofing": "Waterproof",
            "primary_purpose": ["Trail Hiking", "Backpacking"]
        }
    })

    # Test 3: Lightweight travel jacket
    ground_truth.append({
        "query": "lightweight jacket for travel",
        "relevant_products": find_product_ids(
            query="lightweight travel",
            category="Outerwear",
            limit=10
        ),
        "category": "semantic",
        "description": "Semantic search for travel jackets",
        "expected_attributes": {
            "primary_purpose": "Travel",
            "subcategory": ["Lightweight Jackets", "Bombers/Softshell"]
        }
    })

    # Test 4: Winter boots for snow
    ground_truth.append({
        "query": "boots for snow and ice",
        "relevant_products": find_product_ids(
            query="winter boots snow ice",
            category="Footwear",
            limit=10
        ),
        "category": "semantic",
        "description": "Semantic search for winter boots",
        "expected_attributes": {
            "season": "Winter",
            "category": "Footwear",
            "subcategory": "Winter boots"
        }
    })

    # Test 5: Down insulated parka
    ground_truth.append({
        "query": "down insulated parka for extreme cold",
        "relevant_products": find_product_ids(
            query="down parka extreme cold",
            subcategory="Parkas",
            limit=10
        ),
        "category": "semantic",
        "description": "Semantic search for extreme cold parkas",
        "expected_attributes": {
            "subcategory": "Parkas",
            "insulation": "Insulated",
            "season": "Winter"
        }
    })

    # ========================================================================
    # FILTER-BASED TESTS
    # ========================================================================

    # Test 6: Women's outerwear under $300
    ground_truth.append({
        "query": None,  # Pure filter test
        "filters": {
            "gender": "Women",
            "category": "Outerwear",
            "max_price": 300
        },
        "relevant_products": find_product_ids(
            gender="Women",
            category="Outerwear",
            max_price=300,
            limit=20
        ),
        "category": "filter",
        "description": "Filter: Women's outerwear under $300",
        "expected_attributes": {
            "gender": "Women",
            "category": "Outerwear",
            "price_range": (0, 300)
        }
    })

    # Test 7: NorthPeak winter jackets
    ground_truth.append({
        "query": None,
        "filters": {
            "brand": "NorthPeak",
            "category": "Outerwear",
            "season": "Winter"
        },
        "relevant_products": find_product_ids(
            brand="NorthPeak",
            category="Outerwear",
            limit=20
        )[:15],  # Get Winter items
        "category": "filter",
        "description": "Filter: NorthPeak winter outerwear",
        "expected_attributes": {
            "brand": "NorthPeak",
            "category": "Outerwear",
            "season": "Winter"
        }
    })

    # Test 8: Men's hiking boots
    ground_truth.append({
        "query": None,
        "filters": {
            "gender": "Men",
            "category": "Footwear",
            "subcategory": "Hiking boots/shoes"
        },
        "relevant_products": find_product_ids(
            gender="Men",
            category="Footwear",
            subcategory="Hiking boots/shoes",
            limit=20
        ),
        "category": "filter",
        "description": "Filter: Men's hiking boots",
        "expected_attributes": {
            "gender": "Men",
            "category": "Footwear",
            "subcategory": "Hiking boots/shoes"
        }
    })

    # ========================================================================
    # HYBRID SEARCH TESTS (Semantic + Filters)
    # ========================================================================

    # Test 9: Waterproof men's jackets under $250
    ground_truth.append({
        "query": "waterproof jacket",
        "filters": {
            "gender": "Men",
            "max_price": 250
        },
        "relevant_products": find_product_ids(
            query="waterproof",
            gender="Men",
            max_price=250,
            limit=10
        ),
        "category": "hybrid",
        "description": "Hybrid: Waterproof men's jackets under $250",
        "expected_attributes": {
            "waterproofing": ["Waterproof", "Weather Resistant"],
            "gender": "Men",
            "price_range": (0, 250)
        }
    })

    # Test 10: AlpineCo hiking gear
    ground_truth.append({
        "query": "hiking jacket",
        "filters": {
            "brand": "AlpineCo"
        },
        "relevant_products": find_product_ids(
            query="hiking",
            brand="AlpineCo",
            limit=10
        ),
        "category": "hybrid",
        "description": "Hybrid: AlpineCo hiking jackets",
        "expected_attributes": {
            "brand": "AlpineCo",
            "primary_purpose": ["Trail Hiking", "Backpacking"]
        }
    })

    # Test 11: Women's winter jackets from TrailForge
    ground_truth.append({
        "query": "winter jacket",
        "filters": {
            "gender": "Women",
            "brand": "TrailForge"
        },
        "relevant_products": find_product_ids(
            query="winter",
            gender="Women",
            brand="TrailForge",
            limit=10
        ),
        "category": "hybrid",
        "description": "Hybrid: TrailForge women's winter jackets",
        "expected_attributes": {
            "gender": "Women",
            "brand": "TrailForge",
            "season": "Winter"
        }
    })

    # ========================================================================
    # CATEGORY BROWSING TESTS
    # ========================================================================

    # Test 12: Browse parkas
    parkas = find_product_ids(
        category="Outerwear",
        subcategory="Parkas",
        limit=20
    )
    ground_truth.append({
        "query": None,
        "filters": {
            "category": "Outerwear",
            "subcategory": "Parkas"
        },
        "relevant_products": parkas,
        "category": "category_browse",
        "description": "Browse: All parkas",
        "expected_attributes": {
            "category": "Outerwear",
            "subcategory": "Parkas"
        }
    })

    # Test 13: Browse men's down jackets
    ground_truth.append({
        "query": None,
        "filters": {
            "category": "Outerwear",
            "subcategory": "Down Jackets",
            "gender": "Men"
        },
        "relevant_products": find_product_ids(
            category="Outerwear",
            subcategory="Down Jackets",
            gender="Men",
            limit=20
        ),
        "category": "category_browse",
        "description": "Browse: Men's down jackets",
        "expected_attributes": {
            "category": "Outerwear",
            "subcategory": "Down Jackets",
            "gender": "Men"
        }
    })

    # ========================================================================
    # EDGE CASES
    # ========================================================================

    # Test 14: Very specific query
    ground_truth.append({
        "query": "waterproof down jacket for alpine mountaineering",
        "relevant_products": find_product_ids(
            query="waterproof down alpine mountaineering",
            category="Outerwear",
            limit=5
        ),
        "category": "semantic",
        "description": "Edge case: Very specific multi-attribute query",
        "expected_attributes": {
            "waterproofing": "Waterproof",
            "insulation": "Insulated",
            "primary_purpose": ["Alpine Mountaineering", "Alpine Climbing"]
        }
    })

    # Test 15: Budget shopping
    ground_truth.append({
        "query": "affordable jacket under 150",
        "filters": {
            "max_price": 150
        },
        "relevant_products": find_product_ids(
            query="jacket",
            max_price=150,
            limit=15
        ),
        "category": "hybrid",
        "description": "Edge case: Budget-focused search",
        "expected_attributes": {
            "price_range": (0, 150),
            "category": "Outerwear"
        }
    })

    return ground_truth


if __name__ == "__main__":
    """Generate and display ground truth dataset."""
    print("=" * 70)
    print("RETRIEVAL EVALUATION - GROUND TRUTH DATASET")
    print("=" * 70)

    gt = get_ground_truth()

    print(f"\nTotal test cases: {len(gt)}")
    print(f"\nBreakdown by category:")

    from collections import Counter
    categories = Counter(tc['category'] for tc in gt)
    for cat, count in categories.items():
        print(f"  {cat}: {count} tests")

    print("\n" + "=" * 70)
    print("SAMPLE TEST CASES")
    print("=" * 70)

    for i, tc in enumerate(gt[:3], 1):
        print(f"\nTest {i}: {tc['description']}")
        print(f"Category: {tc['category']}")
        if tc['query']:
            print(f"Query: '{tc['query']}'")
        if 'filters' in tc:
            print(f"Filters: {tc['filters']}")
        print(f"Relevant products: {len(tc['relevant_products'])} items")
        print(f"Product IDs (first 5): {tc['relevant_products'][:5]}")

    print("\n" + "=" * 70)
    print("Ground truth dataset ready for evaluation!")
    print("=" * 70)
