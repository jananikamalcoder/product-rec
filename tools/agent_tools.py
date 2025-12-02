"""
MS Agent Framework compatible tool functions for product search.

These functions are designed to work as native tools in the Microsoft Agent Framework.
Each function has:
- Clear type hints for all parameters
- Comprehensive docstrings describing purpose, parameters, and return values
- Structured return values (JSON-serializable)
- Error handling
"""

from typing import List, Dict, Any, Optional
from src.product_search import ProductSearch

# Initialize the search engine (singleton pattern)
_search_engine = None


def _get_search_engine() -> ProductSearch:
    """Get or create the ProductSearch engine instance."""
    global _search_engine
    if _search_engine is None:
        _search_engine = ProductSearch(db_path="./chroma_db")
    return _search_engine


# ============================================================================
# SEARCH TOOLS
# ============================================================================

def search_products(
    query: str,
    max_results: int = 10,
    min_similarity: float = 0.0
) -> Dict[str, Any]:
    """
    Search for products using natural language query (semantic search).

    This tool uses AI embeddings to understand the meaning of your query and
    find semantically similar products, even if they don't share the exact keywords.

    Args:
        query: Natural language search query.
               Examples: "warm winter jacket for skiing",
                        "lightweight waterproof hiking gear",
                        "casual bomber jacket for city"
        max_results: Maximum number of products to return (1-50, default: 10)
        min_similarity: Minimum similarity score threshold (0.0-1.0, default: 0.0)
                       Higher values return only very similar products

    Returns:
        Dictionary containing:
        - success (bool): Whether the search succeeded
        - total_results (int): Number of products found
        - products (list): List of matching products with details
        - query (str): The original query

    Example:
        result = search_products("warm jacket for skiing", max_results=5)
        for product in result['products']:
            print(f"{product['product_name']} - ${product['price_usd']}")
    """
    try:
        search = _get_search_engine()
        results = search.search_semantic(query, n_results=min(max_results, 50))

        # Filter by similarity threshold
        if min_similarity > 0:
            results = [
                p for p in results
                if p.get('similarity_score', 0) >= min_similarity
            ]

        return {
            "success": True,
            "query": query,
            "total_results": len(results),
            "products": results
        }
    except Exception as e:
        return {
            "success": False,
            "query": query,
            "total_results": 0,
            "products": [],
            "error": str(e)
        }


def filter_products_by_attributes(
    brand: Optional[str] = None,
    category: Optional[str] = None,
    subcategory: Optional[str] = None,
    gender: Optional[str] = None,
    season: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_rating: Optional[float] = None,
    waterproofing: Optional[str] = None,
    insulation: Optional[str] = None,
    max_results: int = 10
) -> Dict[str, Any]:
    """
    Filter products by specific attributes (exact match filtering).

    Use this tool when you need exact filtering by product attributes like brand,
    category, price range, etc.

    Args:
        brand: Filter by brand (e.g., "NorthPeak", "AlpineCo", "TrailForge")
        category: Filter by category (e.g., "Outerwear", "Footwear", "Apparel")
        subcategory: Filter by subcategory (e.g., "Down Jackets", "Parkas", "Vests")
        gender: Filter by gender (e.g., "Men", "Women", "Unisex")
        season: Filter by season (e.g., "Winter", "All-season")
        min_price: Minimum price in USD
        max_price: Maximum price in USD
        min_rating: Minimum rating (0.0-5.0)
        waterproofing: Filter by waterproofing level (e.g., "Waterproof", "Weather Resistant")
        insulation: Filter by insulation (e.g., "Insulated", "None")
        max_results: Maximum number of products to return (default: 10)

    Returns:
        Dictionary containing:
        - success (bool): Whether the filter succeeded
        - total_results (int): Number of products found
        - products (list): List of matching products
        - filters_applied (dict): The filters that were applied

    Example:
        result = filter_products_by_attributes(
            brand="NorthPeak",
            gender="Women",
            max_price=300
        )
    """
    try:
        search = _get_search_engine()

        # Build filters
        filters = {}
        filter_conditions = []

        if brand:
            filter_conditions.append({"brand": {"$eq": brand}})
        if category:
            filter_conditions.append({"category": {"$eq": category}})
        if subcategory:
            filter_conditions.append({"subcategory": {"$eq": subcategory}})
        if gender:
            filter_conditions.append({"gender": {"$eq": gender}})
        if season:
            filter_conditions.append({"season": {"$eq": season}})
        if waterproofing:
            filter_conditions.append({"waterproofing": {"$eq": waterproofing}})
        if insulation:
            filter_conditions.append({"insulation": {"$eq": insulation}})
        if min_price is not None:
            filter_conditions.append({"price_usd": {"$gte": min_price}})
        if max_price is not None:
            filter_conditions.append({"price_usd": {"$lte": max_price}})
        if min_rating is not None:
            filter_conditions.append({"rating": {"$gte": min_rating}})

        if not filter_conditions:
            return {
                "success": False,
                "total_results": 0,
                "products": [],
                "error": "No filters specified. Please provide at least one filter."
            }

        # Combine filters
        if len(filter_conditions) == 1:
            filters = filter_conditions[0]
        else:
            filters = {"$and": filter_conditions}

        results = search.search_by_filters(filters, n_results=max_results)

        return {
            "success": True,
            "filters_applied": {
                "brand": brand,
                "category": category,
                "subcategory": subcategory,
                "gender": gender,
                "season": season,
                "min_price": min_price,
                "max_price": max_price,
                "min_rating": min_rating,
                "waterproofing": waterproofing,
                "insulation": insulation
            },
            "total_results": len(results),
            "products": results
        }
    except Exception as e:
        return {
            "success": False,
            "filters_applied": {
                "brand": brand,
                "category": category,
                "subcategory": subcategory,
                "gender": gender,
                "season": season,
                "min_price": min_price,
                "max_price": max_price,
                "min_rating": min_rating,
                "waterproofing": waterproofing,
                "insulation": insulation
            },
            "total_results": 0,
            "products": [],
            "error": str(e)
        }


def search_with_filters(
    query: str,
    brand: Optional[str] = None,
    category: Optional[str] = None,
    gender: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    max_results: int = 10
) -> Dict[str, Any]:
    """
    Hybrid search: Combine natural language query with attribute filters.

    This is the most powerful search - it uses semantic understanding (like search_products)
    but also applies exact filters (like filter_products_by_attributes).

    Args:
        query: Natural language search query
        brand: Filter by brand
        category: Filter by category
        gender: Filter by gender
        min_price: Minimum price in USD
        max_price: Maximum price in USD
        max_results: Maximum number of results (default: 10)

    Returns:
        Dictionary with search results matching both query AND filters

    Example:
        result = search_with_filters(
            query="warm jacket",
            gender="Women",
            max_price=300
        )
    """
    try:
        search = _get_search_engine()

        # Build filters
        filter_conditions = []
        if brand:
            filter_conditions.append({"brand": {"$eq": brand}})
        if category:
            filter_conditions.append({"category": {"$eq": category}})
        if gender:
            filter_conditions.append({"gender": {"$eq": gender}})
        if min_price is not None:
            filter_conditions.append({"price_usd": {"$gte": min_price}})
        if max_price is not None:
            filter_conditions.append({"price_usd": {"$lte": max_price}})

        filters = None
        if filter_conditions:
            filters = {"$and": filter_conditions} if len(filter_conditions) > 1 else filter_conditions[0]

        results = search.hybrid_search(query, filters=filters, n_results=max_results)

        return {
            "success": True,
            "query": query,
            "filters_applied": {
                "brand": brand,
                "category": category,
                "gender": gender,
                "min_price": min_price,
                "max_price": max_price
            },
            "total_results": len(results),
            "products": results
        }
    except Exception as e:
        return {
            "success": False,
            "query": query,
            "filters_applied": {
                "brand": brand,
                "category": category,
                "gender": gender,
                "min_price": min_price,
                "max_price": max_price
            },
            "total_results": 0,
            "products": [],
            "error": str(e)
        }


def search_products_by_category(
    category: str,
    subcategory: Optional[str] = None,
    gender: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_rating: Optional[float] = None,
    max_results: int = 10
) -> Dict[str, Any]:
    """
    Search for products within a specific category or subcategory.

    This is a specialized search tool optimized for browsing products by category.
    It's more convenient than filter_products_by_attributes when the primary
    filter is category-based.

    Args:
        category: The product category (e.g., "Outerwear", "Footwear", "Apparel")
        subcategory: Optional subcategory (e.g., "Down Jackets", "Parkas", "Hiking Boots")
        gender: Optional gender filter (e.g., "Men", "Women", "Unisex")
        min_price: Minimum price in USD
        max_price: Maximum price in USD
        min_rating: Minimum rating (0.0-5.0)
        max_results: Maximum number of products to return (default: 10)

    Returns:
        Dictionary containing:
        - success (bool): Whether the search succeeded
        - category (str): The category searched
        - subcategory (str): The subcategory searched (if specified)
        - total_results (int): Number of products found
        - products (list): List of matching products

    Example:
        # Browse all parkas
        result = search_products_by_category("Outerwear", subcategory="Parkas")

        # Browse women's hiking boots under $200
        result = search_products_by_category(
            "Footwear",
            subcategory="Hiking Boots",
            gender="Women",
            max_price=200
        )
    """
    try:
        search = _get_search_engine()

        # Build filters
        filter_conditions = [{"category": {"$eq": category}}]

        if subcategory:
            filter_conditions.append({"subcategory": {"$eq": subcategory}})
        if gender:
            filter_conditions.append({"gender": {"$eq": gender}})
        if min_price is not None:
            filter_conditions.append({"price_usd": {"$gte": min_price}})
        if max_price is not None:
            filter_conditions.append({"price_usd": {"$lte": max_price}})
        if min_rating is not None:
            filter_conditions.append({"rating": {"$gte": min_rating}})

        # Combine filters
        filters = {"$and": filter_conditions} if len(filter_conditions) > 1 else filter_conditions[0]

        results = search.search_by_filters(filters, n_results=max_results)

        return {
            "success": True,
            "category": category,
            "subcategory": subcategory,
            "filters_applied": {
                "gender": gender,
                "min_price": min_price,
                "max_price": max_price,
                "min_rating": min_rating
            },
            "total_results": len(results),
            "products": results
        }
    except Exception as e:
        return {
            "success": False,
            "category": category,
            "subcategory": subcategory,
            "filters_applied": {
                "gender": gender,
                "min_price": min_price,
                "max_price": max_price,
                "min_rating": min_rating
            },
            "total_results": 0,
            "products": [],
            "error": str(e)
        }


def find_similar_products(
    product_id: str,
    max_results: int = 5
) -> Dict[str, Any]:
    """
    Find products similar to a specific product.

    Use this tool when you have a product ID and want to find similar alternatives.

    Args:
        product_id: The ID of the reference product (e.g., "PRD-6A6DD909")
        max_results: Maximum number of similar products to return (default: 5)

    Returns:
        Dictionary containing:
        - success (bool): Whether the search succeeded
        - reference_product_id (str): The input product ID
        - total_results (int): Number of similar products found
        - products (list): List of similar products

    Example:
        result = find_similar_products("PRD-6A6DD909", max_results=3)
    """
    try:
        search = _get_search_engine()
        results = search.get_similar_products(product_id, n_results=max_results)

        return {
            "success": True,
            "reference_product_id": product_id,
            "total_results": len(results),
            "products": results
        }
    except Exception as e:
        return {
            "success": False,
            "reference_product_id": product_id,
            "total_results": 0,
            "products": [],
            "error": str(e)
        }


# ============================================================================
# CATALOG INFORMATION TOOLS
# ============================================================================

def get_product_details(product_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific product by its ID.

    Args:
        product_id: The product ID (e.g., "PRD-6A6DD909")

    Returns:
        Dictionary containing:
        - success (bool): Whether the product was found
        - product_id (str): The product ID
        - product (dict): Complete product information with all attributes

    Example:
        result = get_product_details("PRD-6A6DD909")
        if result['success']:
            print(result['product']['product_name'])
    """
    try:
        search = _get_search_engine()
        result = search.collection.get(
            ids=[product_id],
            include=["metadatas"]
        )

        if result['metadatas']:
            return {
                "success": True,
                "product_id": product_id,
                "product": result['metadatas'][0]
            }
        else:
            return {
                "success": False,
                "product_id": product_id,
                "product": None,
                "error": f"Product '{product_id}' not found"
            }
    except Exception as e:
        return {
            "success": False,
            "product_id": product_id,
            "product": None,
            "error": str(e)
        }


def get_available_brands() -> Dict[str, Any]:
    """
    Get list of all available brands in the catalog.

    Returns:
        Dictionary containing:
        - success (bool): Whether the operation succeeded
        - total_brands (int): Number of unique brands
        - brands (list): Sorted list of brand names

    Example:
        result = get_available_brands()
        print(f"Available brands: {', '.join(result['brands'])}")
    """
    try:
        search = _get_search_engine()
        all_products = search.collection.get(limit=1000)
        brands = sorted(set(m['brand'] for m in all_products['metadatas']))

        return {
            "success": True,
            "total_brands": len(brands),
            "brands": brands
        }
    except Exception as e:
        return {
            "success": False,
            "total_brands": 0,
            "brands": [],
            "error": str(e)
        }


def get_available_categories() -> Dict[str, Any]:
    """
    Get list of all available categories and subcategories.

    Returns:
        Dictionary containing:
        - success (bool): Whether the operation succeeded
        - categories (dict): Dictionary mapping categories to their subcategories

    Example:
        result = get_available_categories()
        for category, subcats in result['categories'].items():
            print(f"{category}: {', '.join(subcats)}")
    """
    try:
        search = _get_search_engine()
        all_products = search.collection.get(limit=1000)

        categories = {}
        for m in all_products['metadatas']:
            cat = m['category']
            subcat = m['subcategory']
            if cat not in categories:
                categories[cat] = set()
            categories[cat].add(subcat)

        # Convert sets to sorted lists
        categories = {k: sorted(list(v)) for k, v in categories.items()}

        return {
            "success": True,
            "categories": categories
        }
    except Exception as e:
        return {
            "success": False,
            "categories": {},
            "error": str(e)
        }


def get_catalog_statistics() -> Dict[str, Any]:
    """
    Get comprehensive statistics about the product catalog.

    This provides an overview of the entire product database including counts,
    price ranges, ratings, and distributions across various dimensions.

    Returns:
        Dictionary containing:
        - success (bool): Whether the operation succeeded
        - total_products (int): Total number of products
        - brands (dict): Count of products per brand
        - categories (dict): Count of products per category
        - subcategories (dict): Count of products per subcategory
        - genders (dict): Count of products per gender
        - seasons (dict): Count of products per season
        - price_stats (dict): Min, max, and average prices
        - rating_stats (dict): Min, max, and average ratings

    Example:
        stats = get_catalog_statistics()
        print(f"Total products: {stats['total_products']}")
        print(f"Price range: ${stats['price_stats']['min']} - ${stats['price_stats']['max']}")
    """
    try:
        search = _get_search_engine()
        all_products = search.collection.get(limit=1000)
        metadata_list = all_products['metadatas']

        from collections import Counter

        brands = Counter(m['brand'] for m in metadata_list)
        categories = Counter(m['category'] for m in metadata_list)
        subcategories = Counter(m['subcategory'] for m in metadata_list)
        genders = Counter(m['gender'] for m in metadata_list)
        seasons = Counter(m['season'] for m in metadata_list)

        prices = [m['price_usd'] for m in metadata_list]
        ratings = [m['rating'] for m in metadata_list]

        return {
            "success": True,
            "total_products": len(metadata_list),
            "brands": dict(brands),
            "categories": dict(categories),
            "subcategories": dict(subcategories),
            "genders": dict(genders),
            "seasons": dict(seasons),
            "price_stats": {
                "min": min(prices),
                "max": max(prices),
                "avg": round(sum(prices) / len(prices), 2)
            },
            "rating_stats": {
                "min": min(ratings),
                "max": max(ratings),
                "avg": round(sum(ratings) / len(ratings), 2)
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("MS AGENT FRAMEWORK - PRODUCT SEARCH TOOLS")
    print("=" * 70)

    # Example 1: Semantic search
    print("\n1. SEMANTIC SEARCH")
    print("-" * 70)
    result = search_products("warm jacket for skiing", max_results=3)
    print(f"Found {result['total_results']} products")
    for p in result['products']:
        print(f"  - {p['product_name']} (${p['price_usd']})")

    # Example 2: Filter by attributes
    print("\n2. FILTER BY ATTRIBUTES")
    print("-" * 70)
    result = filter_products_by_attributes(
        gender="Women",
        category="Outerwear",
        max_price=300,
        max_results=3
    )
    print(f"Found {result['total_results']} products")
    for p in result['products']:
        print(f"  - {p['product_name']} (${p['price_usd']})")

    # Example 3: Hybrid search
    print("\n3. HYBRID SEARCH")
    print("-" * 70)
    result = search_with_filters(
        query="waterproof jacket",
        gender="Men",
        max_price=250,
        max_results=3
    )
    print(f"Found {result['total_results']} products")
    for p in result['products']:
        print(f"  - {p['product_name']} (${p['price_usd']})")

    # Example 4: Search by category
    print("\n4. SEARCH BY CATEGORY")
    print("-" * 70)
    result = search_products_by_category(
        category="Outerwear",
        subcategory="Parkas",
        max_results=3
    )
    print(f"Found {result['total_results']} products in {result['category']} > {result['subcategory']}")
    for p in result['products']:
        print(f"  - {p['product_name']} (${p['price_usd']})")

    # Example 5: Get statistics
    print("\n5. CATALOG STATISTICS")
    print("-" * 70)
    stats = get_catalog_statistics()
    print(f"Total Products: {stats['total_products']}")
    print(f"Brands: {', '.join(stats['brands'].keys())}")
    print(f"Price Range: ${stats['price_stats']['min']} - ${stats['price_stats']['max']}")

    print("\n" + "=" * 70)
    print("All functions are ready to use as MS Agent Framework tools!")
    print("=" * 70)
