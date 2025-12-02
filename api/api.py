"""
Agent-friendly API for product search system.

This module provides a simple, structured interface for AI agents and external
systems to interact with the product search engine.
"""

from typing import List, Dict, Any, Optional
from product_search import ProductSearch
import json


class ProductSearchAPI:
    """
    Agent-friendly API for product search.

    All methods return structured dictionaries with clear fields,
    making it easy for AI agents to parse and use the data.
    """

    def __init__(self, db_path: str = "./chroma_db"):
        """Initialize the API with a ProductSearch instance."""
        self.search = ProductSearch(db_path=db_path)

    def search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        max_results: int = 10,
        min_similarity: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Search for products using natural language query.

        Args:
            query: Natural language search query (e.g., "warm winter jacket")
            filters: Optional filters (e.g., {"brand": "NorthPeak", "gender": "Women"})
            max_results: Maximum number of results to return (default: 10)
            min_similarity: Minimum similarity score threshold (0-1, optional)

        Returns:
            Dictionary with:
            {
                "success": True/False,
                "query": original query,
                "total_results": number of results,
                "products": [list of product dictionaries],
                "error": error message if any
            }
        """
        try:
            if filters:
                results = self.search.hybrid_search(query, filters, max_results)
            else:
                results = self.search.search_semantic(query, max_results)

            # Apply similarity threshold if specified
            if min_similarity is not None:
                results = [
                    p for p in results
                    if p.get('similarity_score', 0) >= min_similarity
                ]

            return {
                "success": True,
                "query": query,
                "filters": filters,
                "total_results": len(results),
                "products": results,
                "error": None
            }
        except Exception as e:
            return {
                "success": False,
                "query": query,
                "filters": filters,
                "total_results": 0,
                "products": [],
                "error": str(e)
            }

    def filter_products(
        self,
        filters: Dict[str, Any],
        max_results: int = 10
    ) -> Dict[str, Any]:
        """
        Filter products by exact attributes.

        Args:
            filters: Filter dictionary (e.g., {"brand": "NorthPeak", "price_usd": 200})
            max_results: Maximum number of results

        Returns:
            Dictionary with success status and results
        """
        try:
            results = self.search.search_by_filters(filters, max_results)

            return {
                "success": True,
                "filters": filters,
                "total_results": len(results),
                "products": results,
                "error": None
            }
        except Exception as e:
            return {
                "success": False,
                "filters": filters,
                "total_results": 0,
                "products": [],
                "error": str(e)
            }

    def get_similar(
        self,
        product_id: str,
        max_results: int = 5
    ) -> Dict[str, Any]:
        """
        Find products similar to a given product.

        Args:
            product_id: ID of the reference product
            max_results: Maximum number of similar products to return

        Returns:
            Dictionary with success status and similar products
        """
        try:
            results = self.search.get_similar_products(product_id, max_results)

            return {
                "success": True,
                "reference_product_id": product_id,
                "total_results": len(results),
                "products": results,
                "error": None
            }
        except Exception as e:
            return {
                "success": False,
                "reference_product_id": product_id,
                "total_results": 0,
                "products": [],
                "error": str(e)
            }

    def get_product_by_id(
        self,
        product_id: str
    ) -> Dict[str, Any]:
        """
        Get a specific product by its ID.

        Args:
            product_id: Product ID

        Returns:
            Dictionary with product data
        """
        try:
            result = self.search.collection.get(
                ids=[product_id],
                include=["metadatas"]
            )

            if result['metadatas']:
                return {
                    "success": True,
                    "product_id": product_id,
                    "product": result['metadatas'][0],
                    "error": None
                }
            else:
                return {
                    "success": False,
                    "product_id": product_id,
                    "product": None,
                    "error": f"Product {product_id} not found"
                }
        except Exception as e:
            return {
                "success": False,
                "product_id": product_id,
                "product": None,
                "error": str(e)
            }

    def get_all_brands(self) -> Dict[str, Any]:
        """
        Get list of all unique brands.

        Returns:
            Dictionary with list of brands
        """
        try:
            all_products = self.search.collection.get(limit=1000)
            brands = sorted(set(m['brand'] for m in all_products['metadatas']))

            return {
                "success": True,
                "total_brands": len(brands),
                "brands": brands,
                "error": None
            }
        except Exception as e:
            return {
                "success": False,
                "total_brands": 0,
                "brands": [],
                "error": str(e)
            }

    def get_all_categories(self) -> Dict[str, Any]:
        """
        Get list of all unique categories and subcategories.

        Returns:
            Dictionary with categories structure
        """
        try:
            all_products = self.search.collection.get(limit=1000)

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
                "categories": categories,
                "error": None
            }
        except Exception as e:
            return {
                "success": False,
                "categories": {},
                "error": str(e)
            }

    def get_price_range(self) -> Dict[str, Any]:
        """
        Get the overall price range of products.

        Returns:
            Dictionary with min, max, and average prices
        """
        try:
            all_products = self.search.collection.get(limit=1000)
            prices = [m['price_usd'] for m in all_products['metadatas']]

            return {
                "success": True,
                "min_price": min(prices),
                "max_price": max(prices),
                "avg_price": sum(prices) / len(prices),
                "total_products": len(prices),
                "error": None
            }
        except Exception as e:
            return {
                "success": False,
                "min_price": None,
                "max_price": None,
                "avg_price": None,
                "total_products": 0,
                "error": str(e)
            }

    def get_stats(self) -> Dict[str, Any]:
        """
        Get overall statistics about the product catalog.

        Returns:
            Dictionary with comprehensive statistics
        """
        try:
            all_products = self.search.collection.get(limit=1000)
            metadata_list = all_products['metadatas']

            # Count by various dimensions
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
                },
                "error": None
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


def main():
    """Demo the agent-friendly API."""
    api = ProductSearchAPI()

    print("=" * 70)
    print("AGENT-FRIENDLY PRODUCT SEARCH API DEMO")
    print("=" * 70)

    # 1. Get catalog statistics
    print("\n1. CATALOG STATISTICS")
    print("-" * 70)
    stats = api.get_stats()
    if stats['success']:
        print(f"Total Products: {stats['total_products']}")
        print(f"\nBrands: {', '.join(stats['brands'].keys())}")
        print(f"Price Range: ${stats['price_stats']['min']} - ${stats['price_stats']['max']}")
        print(f"Average Price: ${stats['price_stats']['avg']}")
        print(f"Average Rating: {stats['rating_stats']['avg']}")

    # 2. Search query
    print("\n\n2. SEMANTIC SEARCH")
    print("-" * 70)
    result = api.search("waterproof jacket for hiking", max_results=3)
    print(f"Query: '{result['query']}'")
    print(f"Results Found: {result['total_results']}\n")

    for i, product in enumerate(result['products'], 1):
        print(f"{i}. {product['product_name']}")
        print(f"   Brand: {product['brand']} | ${product['price_usd']}")
        print(f"   Similarity: {product['similarity_score']:.3f}")

    # 3. Filter search
    print("\n\n3. FILTER SEARCH")
    print("-" * 70)
    result = api.filter_products(
        filters={"gender": "Women", "category": "Outerwear"},
        max_results=3
    )
    print(f"Filters: {result['filters']}")
    print(f"Results Found: {result['total_results']}\n")

    for i, product in enumerate(result['products'], 1):
        print(f"{i}. {product['product_name']}")
        print(f"   {product['subcategory']} | ${product['price_usd']}")

    # 4. Get product by ID
    print("\n\n4. GET PRODUCT BY ID")
    print("-" * 70)
    result = api.get_product_by_id("PRD-6A6DD909")
    if result['success']:
        product = result['product']
        print(f"ID: {product['product_id']}")
        print(f"Name: {product['product_name']}")
        print(f"Brand: {product['brand']}")
        print(f"Price: ${product['price_usd']}")
        print(f"Rating: {product['rating']}")

    # 5. Get all categories
    print("\n\n5. AVAILABLE CATEGORIES")
    print("-" * 70)
    result = api.get_all_categories()
    if result['success']:
        for category, subcategories in result['categories'].items():
            print(f"\n{category}:")
            for subcat in subcategories:
                print(f"  - {subcat}")

    print("\n" + "=" * 70)
    print("API returns structured JSON-friendly dictionaries")
    print("Perfect for AI agents, web services, and automation!")
    print("=" * 70)


if __name__ == "__main__":
    main()
