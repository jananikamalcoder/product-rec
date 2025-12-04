"""
Unit tests for VisualFormattingTool - Markdown visualization for product data.

Tests the non-LLM visualization component that handles:
- Product cards
- Comparison tables
- Feature matrices
- Price visualizations
- Product lists

Note: The fixture is still named 'visual_agent' for backward compatibility.
"""

import pytest


class TestProductCard:
    """Tests for product card generation."""

    def test_product_card_format(self, visual_agent, sample_product):
        """Single product should generate card with name, brand, price, stars."""
        result = visual_agent.create_product_card(sample_product)

        assert result["success"] is True
        content = result["content"]

        assert sample_product["product_name"] in content
        assert sample_product["brand"] in content
        assert f"${sample_product['price_usd']:.2f}" in content
        assert "⭐" in content  # Rating stars

    def test_product_card_metadata(self, visual_agent, sample_product):
        """Card should have correct visualization_type metadata."""
        result = visual_agent.create_product_card(sample_product)

        assert result["visualization_type"] == "product_card"
        assert "metadata" in result
        assert result["metadata"]["product_name"] == sample_product["product_name"]
        assert result["metadata"]["price"] == sample_product["price_usd"]
        assert result["metadata"]["rating"] == sample_product["rating"]

    def test_product_card_features(self, visual_agent, sample_product):
        """Card should include product features."""
        result = visual_agent.create_product_card(sample_product)

        content = result["content"]
        assert "Waterproofing" in content or "Waterproof" in content
        assert "Insulation" in content or "Down" in content


class TestComparisonTable:
    """Tests for comparison table generation."""

    def test_comparison_table_2_products(self, visual_agent, sample_products_list):
        """2 products should create table with 2 data columns + attribute column."""
        products = sample_products_list[:2]
        result = visual_agent.create_comparison_table(products)

        assert result["success"] is True
        content = result["content"]

        # Should have header row with product names
        assert products[0]["product_name"][:17] in content or products[0]["product_name"] in content
        assert products[1]["product_name"][:17] in content or products[1]["product_name"] in content

        # Should have attribute rows
        assert "Price" in content or "price" in content
        assert "Rating" in content or "rating" in content

    def test_comparison_table_highlights(self, visual_agent, sample_products_varied):
        """Best price and rating should have markers."""
        result = visual_agent.create_comparison_table(sample_products_varied)

        content = result["content"]
        assert "💰" in content  # Best price marker
        assert "⭐" in content  # Best rating marker

    def test_comparison_table_limit_5(self, visual_agent, sample_products_list):
        """7 products input should only show 5 in table."""
        # Create 7 products
        products = sample_products_list.copy()
        for i in range(2):
            p = sample_products_list[0].copy()
            p["product_id"] = f"PRD-EXTRA-{i}"
            p["product_name"] = f"Extra Product {i}"
            products.append(p)

        result = visual_agent.create_comparison_table(products)

        assert result["success"] is True
        assert result["metadata"]["products_count"] == 5

    def test_comparison_table_empty_products(self, visual_agent):
        """Empty products list should return error."""
        result = visual_agent.create_comparison_table([])

        assert result["success"] is False
        assert "error" in result


class TestFeatureMatrix:
    """Tests for feature matrix generation."""

    def test_feature_matrix_defaults(self, visual_agent, sample_products_varied):
        """No features specified should use 6 default features."""
        result = visual_agent.create_feature_matrix(sample_products_varied)

        assert result["success"] is True
        content = result["content"]

        # Default features should be present
        assert "Waterproof" in content
        assert "Under $300" in content

    def test_feature_matrix_scoring(self, visual_agent, sample_products_varied):
        """Products should have feature scores like 'X/6 features'."""
        result = visual_agent.create_feature_matrix(sample_products_varied)

        content = result["content"]
        # Should have score row
        assert "Score" in content
        # Should have format like "3/6"
        assert "/" in content

    def test_feature_matrix_limit_8(self, visual_agent, sample_products_list):
        """10 products input should only show 8 in matrix."""
        # Create 10 products
        products = sample_products_list.copy()
        for i in range(5):
            p = sample_products_list[0].copy()
            p["product_id"] = f"PRD-EXTRA-{i}"
            p["product_name"] = f"Extra Product {i}"
            products.append(p)

        result = visual_agent.create_feature_matrix(products)

        assert result["success"] is True
        assert result["metadata"]["products_count"] == 8

    def test_feature_matrix_checkmarks(self, visual_agent, sample_products_varied):
        """Matrix should have checkmarks for features."""
        result = visual_agent.create_feature_matrix(sample_products_varied)

        content = result["content"]
        assert "✅" in content  # Has feature
        assert "❌" in content  # Missing feature


class TestPriceVisualization:
    """Tests for price visualization generation."""

    def test_price_visualization_stats(self, visual_agent, sample_products_varied):
        """Should include min, max, avg, median prices."""
        result = visual_agent.create_price_visualization(sample_products_varied)

        assert result["success"] is True
        content = result["content"]

        assert "Lowest Price" in content
        assert "Highest Price" in content
        assert "Average Price" in content
        assert "Median Price" in content

    def test_price_distribution_buckets(self, visual_agent, sample_products_varied):
        """Should show price distribution buckets."""
        result = visual_agent.create_price_visualization(sample_products_varied, show_distribution=True)

        content = result["content"]
        assert "Price Distribution" in content
        assert "Price Range" in content
        assert "█" in content  # Bar chart character

    def test_price_best_value(self, visual_agent, sample_products_varied):
        """Should identify best value product (highest rating/price ratio)."""
        result = visual_agent.create_price_visualization(sample_products_varied)

        content = result["content"]
        assert "Best Value" in content
        assert result["metadata"]["best_value_product"] is not None

    def test_price_visualization_metadata(self, visual_agent, sample_products_varied):
        """Should have correct metadata."""
        result = visual_agent.create_price_visualization(sample_products_varied)

        assert "price_range" in result["metadata"]
        assert "min" in result["metadata"]["price_range"]
        assert "max" in result["metadata"]["price_range"]
        assert "average_price" in result["metadata"]
        assert "median_price" in result["metadata"]


class TestProductList:
    """Tests for product list formatting."""

    def test_format_list_detailed(self, visual_agent, sample_products_list):
        """show_details=True should create table format."""
        result = visual_agent.format_product_list(sample_products_list, show_details=True)

        assert result["success"] is True
        content = result["content"]

        # Table format with headers
        assert "| Product |" in content
        assert "| Brand |" in content
        assert "| Price |" in content
        assert "| Rating |" in content

    def test_format_list_simple(self, visual_agent, sample_products_list):
        """show_details=False should create numbered list."""
        result = visual_agent.format_product_list(sample_products_list, show_details=False)

        assert result["success"] is True
        content = result["content"]

        # Simple numbered list
        assert "1." in content
        assert "2." in content
        assert "$" in content  # Price still shown

    def test_format_list_limit_10(self, visual_agent):
        """More than 10 products should show '...and X more'."""
        # Create 15 products
        products = []
        for i in range(15):
            products.append({
                "product_id": f"PRD-{i}",
                "product_name": f"Product {i}",
                "brand": "TestBrand",
                "price_usd": 100.0,
                "rating": 4.0
            })

        result = visual_agent.format_product_list(products)

        content = result["content"]
        assert "...and 5 more products" in content
        assert result["metadata"]["products_shown"] == 10
        assert result["metadata"]["total_products"] == 15

    def test_empty_products_error(self, visual_agent):
        """Empty list should indicate no products found."""
        result = visual_agent.format_product_list([])

        # Note: The implementation returns success=False but with a message
        assert "No products found" in result["content"] or result["success"] is False


class TestAutoVisualize:
    """Tests for automatic visualization selection."""

    def test_auto_visualize_1_product(self, visual_agent, sample_product):
        """1 product should return product card."""
        result = visual_agent.auto_visualize([sample_product])

        # Should be a card format (has ### header)
        assert "###" in result
        assert sample_product["product_name"] in result

    def test_auto_visualize_3_products(self, visual_agent, sample_products_list):
        """3 products should return comparison table."""
        products = sample_products_list[:3]
        result = visual_agent.auto_visualize(products)

        # Should be table format with | characters
        assert "| Attribute |" in result

    def test_auto_visualize_10_products(self, visual_agent):
        """10 products should return list + price analysis."""
        products = []
        for i in range(10):
            products.append({
                "product_id": f"PRD-{i}",
                "product_name": f"Product {i}",
                "brand": "TestBrand",
                "price_usd": 100.0 + i * 20,
                "rating": 4.0
            })

        result = visual_agent.auto_visualize(products)

        # Should have both list and price analysis
        assert "| Product |" in result  # List table
        assert "Price Analysis" in result  # Price stats


class TestEdgeCases:
    """Tests for edge cases and name truncation."""

    def test_name_truncation(self, visual_agent, sample_products_varied):
        """Long product names should be truncated."""
        result = visual_agent.create_comparison_table(sample_products_varied)

        # The product with very long name should be truncated
        content = result["content"]
        # Original long name: "Technical Shell with Very Long Product Name for Testing"
        # Should be truncated
        assert "Technical Shell with Very Long Product Name for Testing" not in content

    def test_missing_attributes(self, visual_agent):
        """Products with missing attributes should handle gracefully."""
        product = {
            "product_id": "MINIMAL",
            "product_name": "Minimal Product"
            # Missing: brand, price_usd, rating, etc.
        }

        result = visual_agent.create_product_card(product)

        assert result["success"] is True
        assert "Minimal Product" in result["content"]

    def test_zero_price_products(self, visual_agent):
        """Products with zero price should be handled in price visualization."""
        products = [
            {"product_id": "1", "product_name": "Free Product", "price_usd": 0, "rating": 4.0},
            {"product_id": "2", "product_name": "Paid Product", "price_usd": 100, "rating": 4.0},
        ]

        result = visual_agent.create_price_visualization(products)

        # Should still work (zero prices filtered or handled)
        assert result["success"] is True
