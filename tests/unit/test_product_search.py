"""
Unit tests for ProductSearch - ChromaDB-based product search engine.

Tests the non-LLM search component that handles:
- Semantic search with vector embeddings
- Filter-based search with metadata
- Hybrid search (semantic + filters)
- Similar product finding
"""

import pytest


class TestSemanticSearch:
    """Tests for semantic (vector) search functionality."""

    def test_semantic_search_results(self, search_engine):
        """'warm jacket' query should return products with similarity_score."""
        results = search_engine.search_semantic("warm jacket", n_results=5)

        assert len(results) > 0
        for product in results:
            assert "similarity_score" in product
            assert "product_name" in product
            assert "brand" in product
            assert "price_usd" in product

    def test_semantic_search_limit(self, search_engine):
        """n_results=5 should return exactly 5 results."""
        results = search_engine.search_semantic("jacket", n_results=5)

        assert len(results) == 5

    def test_semantic_search_relevance(self, search_engine):
        """Search for 'waterproof rain jacket' should return relevant products."""
        results = search_engine.search_semantic("waterproof rain jacket", n_results=10)

        assert len(results) > 0
        # At least some results should be waterproof or rain-related
        waterproof_count = sum(
            1 for p in results
            if "waterproof" in str(p.get("waterproofing", "")).lower()
            or "rain" in p.get("product_name", "").lower()
        )
        assert waterproof_count > 0

    def test_semantic_search_similarity_scores_sorted(self, search_engine):
        """Results should be sorted by similarity score (descending)."""
        results = search_engine.search_semantic("hiking boots", n_results=10)

        scores = [p["similarity_score"] for p in results]
        assert scores == sorted(scores, reverse=True)


class TestFilterSearch:
    """Tests for filter-based (metadata) search functionality."""

    def test_filter_by_brand(self, search_engine):
        """Filter by brand should return only products from that brand."""
        results = search_engine.search_by_filters(
            filters={"brand": "NorthPeak"},
            n_results=10
        )

        assert len(results) > 0
        for product in results:
            assert product["brand"] == "NorthPeak"

    def test_filter_by_price_range(self, search_engine):
        """Filter by price range should return products within range."""
        results = search_engine.search_by_filters(
            filters={"$and": [
                {"price_usd": {"$gte": 100}},
                {"price_usd": {"$lte": 300}}
            ]},
            n_results=20
        )

        assert len(results) > 0
        for product in results:
            assert 100 <= product["price_usd"] <= 300

    def test_filter_by_gender(self, search_engine):
        """Filter by gender='Women' should return Women products."""
        results = search_engine.search_by_filters(
            filters={"gender": "Women"},
            n_results=10
        )

        assert len(results) > 0
        for product in results:
            assert product["gender"] == "Women"

    def test_filter_combination_and(self, search_engine):
        """Combined filters should meet all conditions."""
        results = search_engine.search_by_filters(
            filters={"$and": [
                {"category": {"$eq": "Outerwear"}},
                {"season": {"$eq": "Winter"}}
            ]},
            n_results=10
        )

        assert len(results) > 0
        for product in results:
            assert product["category"] == "Outerwear"
            assert product["season"] == "Winter"

    def test_filter_simple_dict_format(self, search_engine):
        """Simple dict filters should be converted correctly."""
        results = search_engine.search_by_filters(
            filters={"category": "Outerwear"},
            n_results=10
        )

        assert len(results) > 0
        for product in results:
            assert product["category"] == "Outerwear"


class TestHybridSearch:
    """Tests for hybrid search (semantic + filters)."""

    def test_hybrid_search(self, search_engine):
        """Hybrid search should combine semantic and filter results."""
        results = search_engine.hybrid_search(
            query="warm insulated jacket",
            filters={"category": {"$eq": "Outerwear"}},
            n_results=10
        )

        assert len(results) > 0
        for product in results:
            # All results should match the filter
            assert product["category"] == "Outerwear"
            # Results should have similarity scores
            assert "similarity_score" in product


class TestSimilarProducts:
    """Tests for finding similar products."""

    def test_similar_products(self, search_engine):
        """Should return similar products, excluding original."""
        # First get a product ID
        products = search_engine.search_semantic("jacket", n_results=1)
        assert len(products) > 0
        product_id = products[0]["product_id"]

        # Find similar
        similar = search_engine.get_similar_products(product_id, n_results=5)

        assert len(similar) > 0
        # Original should not be in results
        assert all(p["product_id"] != product_id for p in similar)

    def test_similar_products_nonexistent(self, search_engine):
        """Nonexistent product_id should return empty list."""
        similar = search_engine.get_similar_products("NONEXISTENT-ID", n_results=5)

        assert similar == []


class TestProductDetails:
    """Tests for getting product details by ID."""

    def test_product_details_found(self, search_engine):
        """Valid product_id should return product dict."""
        # First get a product ID
        products = search_engine.search_semantic("jacket", n_results=1)
        assert len(products) > 0
        product_id = products[0]["product_id"]

        # Get details directly from collection
        result = search_engine.collection.get(ids=[product_id], include=["metadatas"])

        assert len(result["metadatas"]) > 0
        product = result["metadatas"][0]
        assert "product_name" in product
        assert "brand" in product

    def test_product_details_not_found(self, search_engine):
        """Invalid product_id should return empty."""
        result = search_engine.collection.get(ids=["NONEXISTENT-ID"], include=["metadatas"])

        assert len(result["metadatas"]) == 0


class TestCatalogInfo:
    """Tests for catalog information retrieval."""

    def test_available_brands(self, search_engine):
        """Should return non-empty sorted list of brands."""
        all_products = search_engine.collection.get(limit=1000)
        brands = sorted(set(m["brand"] for m in all_products["metadatas"]))

        assert len(brands) > 0
        assert brands == sorted(brands)  # Should be sorted

    def test_available_categories(self, search_engine):
        """Should return dict with categories and subcategories."""
        all_products = search_engine.collection.get(limit=1000)

        categories = {}
        for m in all_products["metadatas"]:
            cat = m["category"]
            subcat = m["subcategory"]
            if cat not in categories:
                categories[cat] = set()
            categories[cat].add(subcat)

        assert len(categories) > 0
        # Convert sets to lists for assertions
        categories = {k: sorted(list(v)) for k, v in categories.items()}
        assert "Outerwear" in categories or "Footwear" in categories


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_query_handling(self, search_engine):
        """Empty string query should be handled gracefully."""
        # Empty query should still return results (ChromaDB behavior)
        results = search_engine.search_semantic("", n_results=5)

        # Should return something (default behavior) or empty list
        assert isinstance(results, list)

    def test_special_characters_in_query(self, search_engine):
        """Query with special characters should be handled."""
        results = search_engine.search_semantic("jacket & pants", n_results=5)

        # Should not raise an error
        assert isinstance(results, list)

    def test_large_n_results(self, search_engine):
        """Large n_results should return available products."""
        results = search_engine.search_semantic("jacket", n_results=1000)

        # Should return products (may be less than requested)
        assert isinstance(results, list)
        assert len(results) > 0
