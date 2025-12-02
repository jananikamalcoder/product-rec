"""Detailed test output showing full results for all 9 Product Search Agent tools."""

import agent_tools
import json

def print_json(data, indent=2):
    """Pretty print JSON data."""
    print(json.dumps(data, indent=indent, default=str))

print("=" * 70)
print("PRODUCT SEARCH AGENT - DETAILED TEST RESULTS")
print("=" * 70)

# Test 1: search_products() - Semantic search
print("\n" + "=" * 70)
print("TEST 1: search_products() - SEMANTIC SEARCH")
print("=" * 70)
result = agent_tools.search_products("warm jacket for skiing", max_results=3)
print_json(result)

# Test 2: filter_products_by_attributes() - Exact filtering
print("\n" + "=" * 70)
print("TEST 2: filter_products_by_attributes() - EXACT FILTERING")
print("=" * 70)
result = agent_tools.filter_products_by_attributes(
    gender="Women",
    category="Outerwear",
    max_price=300,
    max_results=3
)
print_json(result)

# Test 3: search_with_filters() - Hybrid search
print("\n" + "=" * 70)
print("TEST 3: search_with_filters() - HYBRID SEARCH")
print("=" * 70)
result = agent_tools.search_with_filters(
    query="waterproof jacket",
    gender="Men",
    max_price=250,
    max_results=3
)
print_json(result)

# Test 4: search_products_by_category() - Category browsing
print("\n" + "=" * 70)
print("TEST 4: search_products_by_category() - CATEGORY BROWSING")
print("=" * 70)
result = agent_tools.search_products_by_category(
    category="Outerwear",
    subcategory="Down Jackets",
    gender="Men",
    max_price=400,
    max_results=2
)
print_json(result)

# Test 5: find_similar_products() - Similarity search
print("\n" + "=" * 70)
print("TEST 5: find_similar_products() - SIMILARITY SEARCH")
print("=" * 70)
# First, get a product ID
sample_result = agent_tools.search_products("parka", max_results=1)
if sample_result['success'] and sample_result['products']:
    sample_product_id = sample_result['products'][0]['product_id']
    print(f"Reference Product ID: {sample_product_id}\n")
    result = agent_tools.find_similar_products(sample_product_id, max_results=3)
    print_json(result)

# Test 6: get_product_details() - Single product lookup
print("\n" + "=" * 70)
print("TEST 6: get_product_details() - PRODUCT LOOKUP")
print("=" * 70)
if sample_result['success'] and sample_result['products']:
    sample_product_id = sample_result['products'][0]['product_id']
    result = agent_tools.get_product_details(sample_product_id)
    print_json(result)

# Test 7: get_available_brands() - List brands
print("\n" + "=" * 70)
print("TEST 7: get_available_brands() - BRAND LISTING")
print("=" * 70)
result = agent_tools.get_available_brands()
print_json(result)

# Test 8: get_available_categories() - List categories
print("\n" + "=" * 70)
print("TEST 8: get_available_categories() - CATEGORY LISTING")
print("=" * 70)
result = agent_tools.get_available_categories()
print_json(result)

# Test 9: get_catalog_statistics() - Catalog overview
print("\n" + "=" * 70)
print("TEST 9: get_catalog_statistics() - CATALOG OVERVIEW")
print("=" * 70)
result = agent_tools.get_catalog_statistics()
print_json(result)

print("\n" + "=" * 70)
print("ALL TESTS COMPLETED - FULL JSON OUTPUT SHOWN ABOVE")
print("=" * 70)
