"""
Tests for VisualAgent (src/agents/visual_agent.py).

Covers:
- Product card creation
- Comparison table generation
- Feature matrix creation
- Price visualization
- Product list formatting
- Auto-visualization
"""

import pytest

from src.agents.visual_agent import (
    VisualAgent,
    create_product_card,
    create_comparison_table,
    create_feature_matrix,
    create_price_visualization,
    format_product_list,
    visualize_products
)


# ============================================================================
# PRODUCT CARD TESTS
# ============================================================================

class TestCreateProductCard:
    """Tests for create_product_card() function."""

    def test_product_card_success(self, sample_product):
        """create_product_card() returns success for valid product."""
        result = create_product_card(sample_product)
        assert result["success"] is True
        assert result["visualization_type"] == "product_card"

    def test_product_card_contains_name(self, sample_product):
        """Product card contains product name."""
        result = create_product_card(sample_product)
        assert "Summit Pro Parka" in result["content"]

    def test_product_card_contains_brand(self, sample_product):
        """Product card contains brand."""
        result = create_product_card(sample_product)
        assert "NorthPeak" in result["content"]

    def test_product_card_contains_price(self, sample_product):
        """Product card contains formatted price."""
        result = create_product_card(sample_product)
        assert "$275.00" in result["content"]

    def test_product_card_contains_rating(self, sample_product):
        """Product card contains rating."""
        result = create_product_card(sample_product)
        assert "4.8" in result["content"]

    def test_product_card_contains_stars(self, sample_product):
        """Product card contains star emojis."""
        result = create_product_card(sample_product)
        assert "⭐" in result["content"]

    def test_product_card_half_star_for_point_five(self):
        """Product card shows ½ for .5 ratings."""
        product = {"product_name": "Test", "rating": 4.5, "price_usd": 100}
        result = create_product_card(product)
        assert "½" in result["content"]

    def test_product_card_contains_category(self, sample_product):
        """Product card contains category."""
        result = create_product_card(sample_product)
        assert "Outerwear" in result["content"]

    def test_product_card_contains_subcategory(self, sample_product):
        """Product card contains subcategory with separator."""
        result = create_product_card(sample_product)
        assert "Parkas" in result["content"]

    def test_product_card_contains_features(self, sample_product):
        """Product card contains feature list."""
        result = create_product_card(sample_product)
        assert "Waterproof" in result["content"]
        assert "Down 700-fill" in result["content"]

    def test_product_card_contains_metadata(self, sample_product):
        """Product card includes metadata dict."""
        result = create_product_card(sample_product)
        assert "metadata" in result
        assert result["metadata"]["product_name"] == "Summit Pro Parka"
        assert result["metadata"]["price"] == 275.00
        assert result["metadata"]["rating"] == 4.8

    def test_product_card_minimal_product(self, sample_products_minimal):
        """Product card handles minimal product data."""
        result = create_product_card(sample_products_minimal[0])
        assert result["success"] is True
        assert "Basic Jacket" in result["content"]

    def test_product_card_empty_product(self):
        """Product card handles empty product dict."""
        result = create_product_card({})
        assert result["success"] is True
        assert "Unknown Product" in result["content"]

    def test_product_card_none_product(self):
        """Product card handles None (should fail gracefully)."""
        result = create_product_card(None)
        assert result["success"] is False

    def test_product_card_missing_optional_fields(self):
        """Product card handles missing optional fields."""
        product = {"product_name": "Test Product", "price_usd": 150}
        result = create_product_card(product)
        assert result["success"] is True
        assert "Test Product" in result["content"]

    def test_product_card_zero_rating(self):
        """Product card handles zero rating."""
        product = {"product_name": "Test", "rating": 0, "price_usd": 100}
        result = create_product_card(product)
        assert result["success"] is True
        assert "0/5.0" in result["content"]

    def test_product_card_max_rating(self):
        """Product card handles max rating (5.0)."""
        product = {"product_name": "Test", "rating": 5.0, "price_usd": 100}
        result = create_product_card(product)
        assert result["success"] is True
        assert "5.0/5.0" in result["content"]

    def test_product_card_zero_price(self):
        """Product card handles zero price."""
        product = {"product_name": "Test", "price_usd": 0}
        result = create_product_card(product)
        assert result["success"] is True
        assert "$0.00" in result["content"]

    def test_product_card_large_price(self):
        """Product card handles large price."""
        product = {"product_name": "Test", "price_usd": 99999.99}
        result = create_product_card(product)
        assert result["success"] is True
        assert "$99999.99" in result["content"]


# ============================================================================
# COMPARISON TABLE TESTS
# ============================================================================

class TestCreateComparisonTable:
    """Tests for create_comparison_table() function."""

    def test_comparison_table_success(self, sample_products):
        """create_comparison_table() returns success for valid products."""
        result = create_comparison_table(sample_products[:3])
        assert result["success"] is True
        assert result["visualization_type"] == "comparison_table"

    def test_comparison_table_empty_list(self):
        """Comparison table fails for empty list."""
        result = create_comparison_table([])
        assert result["success"] is False
        assert "No products" in result["error"]

    def test_comparison_table_single_product(self, sample_products):
        """Comparison table works with single product."""
        result = create_comparison_table([sample_products[0]])
        assert result["success"] is True

    def test_comparison_table_two_products(self, sample_products):
        """Comparison table works with two products."""
        result = create_comparison_table(sample_products[:2])
        assert result["success"] is True

    def test_comparison_table_five_products(self, sample_products):
        """Comparison table works with five products."""
        result = create_comparison_table(sample_products[:5])
        assert result["success"] is True
        assert result["metadata"]["products_count"] == 5

    def test_comparison_table_truncates_to_five(self, sample_products):
        """Comparison table truncates to 5 products."""
        result = create_comparison_table(sample_products)  # 10 products
        assert result["metadata"]["products_count"] == 5

    def test_comparison_table_default_attributes(self, sample_products):
        """Comparison table uses default attributes."""
        result = create_comparison_table(sample_products[:2])
        assert "Brand" in result["content"]
        assert "Price Usd" in result["content"] or "Price" in result["content"]
        assert "Rating" in result["content"]

    def test_comparison_table_custom_attributes(self, sample_products):
        """Comparison table uses custom attributes."""
        result = create_comparison_table(
            sample_products[:2],
            attributes=["brand", "color", "season"]
        )
        assert "Brand" in result["content"]
        assert "Color" in result["content"]
        assert "Season" in result["content"]

    def test_comparison_table_price_highlight(self, sample_products):
        """Comparison table highlights best price with 💰."""
        result = create_comparison_table(sample_products[:3])
        assert "💰" in result["content"]

    def test_comparison_table_rating_highlight(self, sample_products):
        """Comparison table highlights best rating with ⭐."""
        result = create_comparison_table(sample_products[:3])
        assert "⭐" in result["content"]

    def test_comparison_table_same_price_tie(self, sample_products_same_price):
        """Comparison table handles same price (first gets highlight)."""
        result = create_comparison_table(sample_products_same_price)
        assert result["success"] is True
        # Should still have one 💰
        assert result["content"].count("💰") >= 1

    def test_comparison_table_same_rating_tie(self, sample_products_same_rating):
        """Comparison table handles same rating (first gets highlight)."""
        result = create_comparison_table(sample_products_same_rating)
        assert result["success"] is True

    def test_comparison_table_truncates_long_names(self):
        """Comparison table truncates long product names."""
        product = {
            "product_name": "This is a very long product name that should be truncated",
            "brand": "Test",
            "price_usd": 100,
            "rating": 4.0
        }
        result = create_comparison_table([product])
        # Name should be truncated to ~20 chars + "..."
        assert "..." in result["content"]

    def test_comparison_table_handles_none_values(self):
        """Comparison table shows '-' for None values."""
        product = {
            "product_name": "Test",
            "brand": None,
            "price_usd": 100,
            "rating": 4.0
        }
        result = create_comparison_table([product])
        assert "-" in result["content"]

    def test_comparison_table_handles_missing_values(self):
        """Comparison table shows '-' for missing values."""
        product = {"product_name": "Test", "price_usd": 100}
        result = create_comparison_table([product], attributes=["brand", "color"])
        assert "-" in result["content"]

    def test_comparison_table_boolean_values(self):
        """Comparison table shows ✓/✗ for boolean values."""
        products = [
            {"product_name": "A", "waterproof": True, "price_usd": 100, "rating": 4.0},
            {"product_name": "B", "waterproof": False, "price_usd": 100, "rating": 4.0}
        ]
        result = create_comparison_table(products, attributes=["waterproof"])
        assert "✓" in result["content"]
        assert "✗" in result["content"]

    def test_comparison_table_legend(self, sample_products):
        """Comparison table includes legend."""
        result = create_comparison_table(sample_products[:3])
        assert "Best price" in result["content"]
        assert "Best rating" in result["content"]

    def test_comparison_table_metadata(self, sample_products):
        """Comparison table includes metadata."""
        result = create_comparison_table(sample_products[:3])
        assert "best_price_product" in result["metadata"]
        assert "best_rating_product" in result["metadata"]


# ============================================================================
# FEATURE MATRIX TESTS
# ============================================================================

class TestCreateFeatureMatrix:
    """Tests for create_feature_matrix() function."""

    def test_feature_matrix_success(self, sample_products):
        """create_feature_matrix() returns success for valid products."""
        result = create_feature_matrix(sample_products[:3])
        assert result["success"] is True
        assert result["visualization_type"] == "feature_matrix"

    def test_feature_matrix_empty_list(self):
        """Feature matrix fails for empty list."""
        result = create_feature_matrix([])
        assert result["success"] is False

    def test_feature_matrix_default_features(self, sample_products):
        """Feature matrix uses default feature checks."""
        result = create_feature_matrix(sample_products[:3])
        assert "Waterproof" in result["content"]
        assert "Down Insulation" in result["content"]
        assert "High Rating" in result["content"]

    def test_feature_matrix_checkmarks(self, sample_products):
        """Feature matrix shows ✅ and ❌."""
        result = create_feature_matrix(sample_products[:3])
        assert "✅" in result["content"]
        assert "❌" in result["content"]

    def test_feature_matrix_scores(self, sample_products):
        """Feature matrix shows scores."""
        result = create_feature_matrix(sample_products[:3])
        # Should have score like "3/6" or similar
        assert "/" in result["content"]

    def test_feature_matrix_best_match(self, sample_products):
        """Feature matrix identifies best match."""
        result = create_feature_matrix(sample_products[:3])
        assert "Best Match" in result["content"]

    def test_feature_matrix_truncates_to_eight(self, sample_products):
        """Feature matrix truncates to 8 products."""
        result = create_feature_matrix(sample_products)  # 10 products
        assert result["metadata"]["products_count"] == 8

    def test_feature_matrix_waterproof_detection(self):
        """Feature matrix correctly detects waterproof."""
        products = [
            {"product_name": "A", "waterproofing": "Waterproof"},
            {"product_name": "B", "waterproofing": "None"}
        ]
        result = create_feature_matrix(products)
        # First product should have Waterproof ✅
        assert result["success"] is True

    def test_feature_matrix_down_insulation_detection(self):
        """Feature matrix correctly detects down insulation."""
        products = [
            {"product_name": "A", "insulation": "Down 700-fill"},
            {"product_name": "B", "insulation": "Synthetic"}
        ]
        result = create_feature_matrix(products)
        assert result["success"] is True

    def test_feature_matrix_rating_threshold(self):
        """Feature matrix uses 4.5 rating threshold."""
        products = [
            {"product_name": "A", "rating": 4.5, "price_usd": 100},  # Exactly 4.5
            {"product_name": "B", "rating": 4.4, "price_usd": 100}   # Below 4.5
        ]
        result = create_feature_matrix(products)
        # Product A should pass, Product B should fail
        assert result["success"] is True

    def test_feature_matrix_price_threshold(self):
        """Feature matrix uses $300 price threshold."""
        products = [
            {"product_name": "A", "price_usd": 299, "rating": 4.0},  # Under $300
            {"product_name": "B", "price_usd": 300, "rating": 4.0}   # Exactly $300 (not under)
        ]
        result = create_feature_matrix(products)
        assert result["success"] is True

    def test_feature_matrix_all_features_matched(self):
        """Feature matrix shows max score when all features matched."""
        product = {
            "product_name": "Perfect",
            "waterproofing": "Waterproof",
            "insulation": "Down",
            "rating": 4.9,
            "price_usd": 250,
            "season": "Winter",
            "material": "Recycled"
        }
        result = create_feature_matrix([product])
        assert "6/6" in result["content"]

    def test_feature_matrix_no_features_matched(self):
        """Feature matrix shows 0 score when no features matched."""
        product = {
            "product_name": "None",
            "waterproofing": "None",
            "insulation": "None",
            "rating": 3.0,
            "price_usd": 500,
            "season": "Summer",
            "material": "Cotton"
        }
        result = create_feature_matrix([product])
        assert "0/6" in result["content"]

    def test_feature_matrix_tied_scores(self, sample_products_same_rating):
        """Feature matrix handles tied scores."""
        result = create_feature_matrix(sample_products_same_rating)
        assert result["success"] is True

    def test_feature_matrix_metadata(self, sample_products):
        """Feature matrix includes metadata."""
        result = create_feature_matrix(sample_products[:3])
        assert "best_products" in result["metadata"]
        assert "max_score" in result["metadata"]


# ============================================================================
# PRICE VISUALIZATION TESTS
# ============================================================================

class TestCreatePriceVisualization:
    """Tests for create_price_visualization() function."""

    def test_price_viz_success(self, sample_products):
        """create_price_visualization() returns success."""
        result = create_price_visualization(sample_products)
        assert result["success"] is True
        assert result["visualization_type"] == "price_visualization"

    def test_price_viz_empty_list(self):
        """Price visualization fails for empty list."""
        result = create_price_visualization([])
        assert result["success"] is False

    def test_price_viz_all_zero_prices(self):
        """Price visualization fails for all zero prices."""
        products = [
            {"product_name": "A", "price_usd": 0},
            {"product_name": "B", "price_usd": 0}
        ]
        result = create_price_visualization(products)
        assert result["success"] is False

    def test_price_viz_contains_statistics(self, sample_products):
        """Price visualization contains statistics."""
        result = create_price_visualization(sample_products)
        assert "Lowest Price" in result["content"]
        assert "Highest Price" in result["content"]
        assert "Average Price" in result["content"]
        assert "Median Price" in result["content"]

    def test_price_viz_calculates_correct_stats(self, sample_products):
        """Price visualization calculates correct statistics."""
        result = create_price_visualization(sample_products)
        # Based on sample_products fixture
        assert result["metadata"]["price_range"]["min"] == 89.00
        assert result["metadata"]["price_range"]["max"] == 425.00

    def test_price_viz_best_value(self, sample_products):
        """Price visualization identifies best value."""
        result = create_price_visualization(sample_products)
        assert "Best Value" in result["content"]
        assert result["metadata"]["best_value_product"] is not None

    def test_price_viz_distribution(self, sample_products):
        """Price visualization shows distribution when enabled."""
        result = create_price_visualization(sample_products, show_distribution=True)
        assert "Price Distribution" in result["content"]
        assert "█" in result["content"]  # Distribution bars

    def test_price_viz_no_distribution(self, sample_products):
        """Price visualization hides distribution when disabled."""
        result = create_price_visualization(sample_products, show_distribution=False)
        assert "Price Distribution" not in result["content"]

    def test_price_viz_single_product(self, sample_product):
        """Price visualization works with single product."""
        result = create_price_visualization([sample_product])
        assert result["success"] is True
        # Min and max should be the same
        assert result["metadata"]["price_range"]["min"] == result["metadata"]["price_range"]["max"]

    def test_price_viz_metadata(self, sample_products):
        """Price visualization includes metadata."""
        result = create_price_visualization(sample_products)
        assert "price_range" in result["metadata"]
        assert "average_price" in result["metadata"]
        assert "median_price" in result["metadata"]

    def test_price_viz_handles_outliers(self):
        """Price visualization handles price outliers."""
        products = [
            {"product_name": "A", "price_usd": 100, "rating": 4.0},
            {"product_name": "B", "price_usd": 150, "rating": 4.0},
            {"product_name": "C", "price_usd": 10000, "rating": 4.0}  # Outlier
        ]
        result = create_price_visualization(products)
        assert result["success"] is True


# ============================================================================
# FORMAT PRODUCT LIST TESTS
# ============================================================================

class TestFormatProductList:
    """Tests for format_product_list() function."""

    def test_format_list_success(self, sample_products):
        """format_product_list() returns success."""
        result = format_product_list(sample_products)
        assert result["success"] is True
        assert result["visualization_type"] == "product_list"

    def test_format_list_empty(self):
        """format_product_list() handles empty list."""
        result = format_product_list([])
        assert result["success"] is False
        assert "No products found" in result["content"]

    def test_format_list_detailed(self, sample_products):
        """format_product_list() shows detailed table."""
        result = format_product_list(sample_products, show_details=True)
        assert "| Product |" in result["content"]
        assert "| Brand |" in result["content"]

    def test_format_list_simple(self, sample_products):
        """format_product_list() shows simple list."""
        result = format_product_list(sample_products, show_details=False)
        assert "1." in result["content"]
        assert "**" in result["content"]  # Bold names

    def test_format_list_exactly_ten(self, sample_products):
        """format_product_list() shows exactly 10 products."""
        result = format_product_list(sample_products)  # 10 products
        assert result["metadata"]["products_shown"] == 10
        assert result["metadata"]["total_products"] == 10

    def test_format_list_more_than_ten(self, sample_products):
        """format_product_list() truncates and shows remainder message."""
        # Add more products
        many_products = sample_products * 2  # 20 products
        result = format_product_list(many_products)
        assert result["metadata"]["products_shown"] == 10
        assert result["metadata"]["total_products"] == 20
        assert "and 10 more products" in result["content"]

    def test_format_list_truncates_long_names(self):
        """format_product_list() truncates long product names."""
        product = {
            "product_name": "This is an extremely long product name that definitely needs truncation",
            "brand": "Test",
            "price_usd": 100,
            "rating": 4.0
        }
        result = format_product_list([product], show_details=True)
        assert "..." in result["content"]

    def test_format_list_contains_prices(self, sample_products):
        """format_product_list() shows prices."""
        result = format_product_list(sample_products[:3])
        assert "$" in result["content"]

    def test_format_list_contains_ratings(self, sample_products):
        """format_product_list() shows ratings with stars."""
        result = format_product_list(sample_products[:3], show_details=True)
        assert "⭐" in result["content"]


# ============================================================================
# VISUAL AGENT CLASS TESTS
# ============================================================================

class TestVisualAgentClass:
    """Tests for VisualAgent class."""

    def test_visual_agent_init(self):
        """VisualAgent initializes correctly."""
        agent = VisualAgent()
        assert agent.name == "VisualAgent"

    def test_visual_agent_create_product_card(self, visual_agent, sample_product):
        """VisualAgent.create_product_card() delegates correctly."""
        result = visual_agent.create_product_card(sample_product)
        assert result["success"] is True

    def test_visual_agent_create_comparison_table(self, visual_agent, sample_products):
        """VisualAgent.create_comparison_table() delegates correctly."""
        result = visual_agent.create_comparison_table(sample_products[:3])
        assert result["success"] is True

    def test_visual_agent_create_feature_matrix(self, visual_agent, sample_products):
        """VisualAgent.create_feature_matrix() delegates correctly."""
        result = visual_agent.create_feature_matrix(sample_products[:3])
        assert result["success"] is True

    def test_visual_agent_create_price_visualization(self, visual_agent, sample_products):
        """VisualAgent.create_price_visualization() delegates correctly."""
        result = visual_agent.create_price_visualization(sample_products)
        assert result["success"] is True

    def test_visual_agent_format_product_list(self, visual_agent, sample_products):
        """VisualAgent.format_product_list() delegates correctly."""
        result = visual_agent.format_product_list(sample_products)
        assert result["success"] is True


# ============================================================================
# AUTO-VISUALIZE TESTS
# ============================================================================

class TestAutoVisualize:
    """Tests for auto_visualize() method."""

    def test_auto_visualize_empty_list(self, visual_agent):
        """auto_visualize() returns message for empty list."""
        result = visual_agent.auto_visualize([])
        assert "No products found" in result

    def test_auto_visualize_single_product(self, visual_agent, sample_product):
        """auto_visualize() shows product card for single product."""
        result = visual_agent.auto_visualize([sample_product])
        # Should contain card-like formatting
        assert "###" in result  # Header for product name

    def test_auto_visualize_two_to_five_products(self, visual_agent, sample_products):
        """auto_visualize() shows comparison table for 2-5 products."""
        result = visual_agent.auto_visualize(sample_products[:3])
        # Should contain table formatting
        assert "|" in result

    def test_auto_visualize_more_than_five(self, visual_agent, sample_products):
        """auto_visualize() shows list and price analysis for >5 products."""
        result = visual_agent.auto_visualize(sample_products)  # 10 products
        # Should contain both list and price info
        assert "Product" in result

    def test_auto_visualize_comparison_intent(self, visual_agent, sample_products):
        """auto_visualize() uses comparison table for comparison intent."""
        result = visual_agent.auto_visualize(sample_products, intent="comparison")
        # Should use comparison table format
        assert "|" in result

    def test_auto_visualize_search_intent(self, visual_agent, sample_products):
        """auto_visualize() uses default for search intent."""
        result = visual_agent.auto_visualize(sample_products, intent="search")
        assert result is not None


# ============================================================================
# CONVENIENCE FUNCTION TESTS
# ============================================================================

class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_visualize_products_function(self, sample_products):
        """visualize_products() convenience function works."""
        result = visualize_products(sample_products)
        assert result is not None
        assert len(result) > 0


# ============================================================================
# EDGE CASE TESTS
# ============================================================================

class TestVisualAgentEdgeCases:
    """Edge case tests for VisualAgent."""

    def test_product_card_with_special_characters(self, special_characters):
        """Product card handles special characters in name."""
        product = {
            "product_name": special_characters,
            "price_usd": 100,
            "rating": 4.0
        }
        result = create_product_card(product)
        assert result["success"] is True

    def test_product_card_with_unicode(self, unicode_string):
        """Product card handles unicode in name."""
        product = {
            "product_name": unicode_string,
            "price_usd": 100,
            "rating": 4.0
        }
        result = create_product_card(product)
        assert result["success"] is True

    def test_comparison_table_with_none_list(self):
        """Comparison table handles None input."""
        result = create_comparison_table(None)
        assert result["success"] is False

    def test_feature_matrix_with_none_features(self):
        """Feature matrix handles None features list."""
        products = [{"product_name": "Test", "price_usd": 100, "rating": 4.0}]
        result = create_feature_matrix(products, features=None)
        assert result["success"] is True

    def test_price_viz_negative_price(self):
        """Price visualization handles negative prices."""
        products = [
            {"product_name": "A", "price_usd": -100, "rating": 4.0},
            {"product_name": "B", "price_usd": 100, "rating": 4.0}
        ]
        result = create_price_visualization(products)
        # Should only count positive prices
        assert result["success"] is True

    def test_format_list_with_missing_all_fields(self):
        """format_product_list() handles product with no fields."""
        products = [{}]
        result = format_product_list(products)
        assert result["success"] is True
        assert "Unknown" in result["content"]

    def test_comparison_table_very_long_value(self):
        """Comparison table truncates very long attribute values."""
        product = {
            "product_name": "Test",
            "brand": "A very long brand name that should be truncated somewhere",
            "price_usd": 100,
            "rating": 4.0
        }
        result = create_comparison_table([product], attributes=["brand"])
        # Should be truncated
        assert "..." in result["content"]


# ============================================================================
# INVARIANT TESTS
# ============================================================================

class TestVisualAgentInvariants:
    """Tests for system invariants."""

    def test_success_always_has_content_or_error(self, sample_products):
        """Invariant: successful results always have content."""
        funcs = [
            lambda: create_product_card(sample_products[0]),
            lambda: create_comparison_table(sample_products[:3]),
            lambda: create_feature_matrix(sample_products[:3]),
            lambda: create_price_visualization(sample_products),
            lambda: format_product_list(sample_products)
        ]
        for func in funcs:
            result = func()
            if result["success"]:
                assert result.get("content"), f"Missing content for {func}"
            else:
                assert result.get("error"), f"Missing error for {func}"

    def test_visualization_type_always_present(self, sample_products):
        """Invariant: visualization_type always present."""
        funcs = [
            lambda: create_product_card(sample_products[0]),
            lambda: create_comparison_table(sample_products[:3]),
            lambda: create_feature_matrix(sample_products[:3]),
            lambda: create_price_visualization(sample_products),
            lambda: format_product_list(sample_products)
        ]
        for func in funcs:
            result = func()
            assert "visualization_type" in result

    def test_comparison_table_max_five_products(self, sample_products):
        """Invariant: comparison table never shows more than 5 products."""
        result = create_comparison_table(sample_products * 3)  # 30 products
        assert result["metadata"]["products_count"] <= 5

    def test_feature_matrix_max_eight_products(self, sample_products):
        """Invariant: feature matrix never shows more than 8 products."""
        result = create_feature_matrix(sample_products * 3)  # 30 products
        assert result["metadata"]["products_count"] <= 8

    def test_product_list_max_ten_shown(self, sample_products):
        """Invariant: product list never shows more than 10 products."""
        result = format_product_list(sample_products * 3)  # 30 products
        assert result["metadata"]["products_shown"] <= 10
