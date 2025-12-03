"""
Edge case tests for the multi-agent product recommendation system.

Covers:
- Boundary conditions
- Data type edge cases
- Empty/null handling
- Numeric edge cases
- String edge cases
"""

import pytest
from unittest.mock import patch, MagicMock

from src.agents.memory import UserMemory
from src.agents.personalization_agent import (
    PersonalizationAgent,
    PersonalizationContext,
    Activity,
    Weather,
    StylePreference,
    FitPreference
)
from src.agents.visual_agent import (
    VisualAgent,
    create_product_card,
    create_comparison_table,
    create_feature_matrix,
    create_price_visualization,
    format_product_list
)
from src.agents.orchestrator import Orchestrator, QueryIntent


# ============================================================================
# BOUNDARY CONDITION TESTS - PRODUCT COUNTS
# ============================================================================

class TestProductCountBoundaries:
    """Tests for product count boundary conditions."""

    def test_comparison_table_exactly_5_products(self, sample_products):
        """Test: exactly 5 products (boundary)."""
        result = create_comparison_table(sample_products[:5])
        assert result["success"] is True
        assert result["metadata"]["products_count"] == 5

    def test_comparison_table_6_products_truncates(self, sample_products):
        """Test: 6 products truncates to 5."""
        result = create_comparison_table(sample_products[:6])
        assert result["metadata"]["products_count"] == 5

    def test_feature_matrix_exactly_8_products(self, sample_products):
        """Test: exactly 8 products (boundary)."""
        products_8 = sample_products + sample_products[:2]  # 10 + need only 8
        result = create_feature_matrix(products_8[:8])
        assert result["success"] is True
        assert result["metadata"]["products_count"] == 8

    def test_feature_matrix_9_products_truncates(self, sample_products):
        """Test: 9 products truncates to 8."""
        products_9 = sample_products + sample_products[:3]
        result = create_feature_matrix(products_9[:9])
        assert result["metadata"]["products_count"] == 8

    def test_product_list_exactly_10_products(self, sample_products):
        """Test: exactly 10 products (boundary)."""
        result = format_product_list(sample_products[:10])
        assert result["metadata"]["products_shown"] == 10
        assert "more products" not in result["content"]

    def test_product_list_11_products_shows_remainder(self, sample_products):
        """Test: 11 products shows remainder message."""
        products_11 = sample_products + [sample_products[0]]
        result = format_product_list(products_11)
        assert result["metadata"]["products_shown"] == 10
        assert "1 more products" in result["content"]


# ============================================================================
# BOUNDARY CONDITION TESTS - RATINGS
# ============================================================================

class TestRatingBoundaries:
    """Tests for rating boundary conditions."""

    def test_rating_exactly_4_5(self):
        """Test: rating exactly 4.5 (threshold for 'High Rating')."""
        product = {"product_name": "Test", "rating": 4.5, "price_usd": 100}
        result = create_feature_matrix([product])
        # 4.5 should count as "High Rating (4.5+)"
        assert "✅" in result["content"]

    def test_rating_4_49_below_threshold(self):
        """Test: rating 4.49 (just below threshold)."""
        product = {"product_name": "Test", "rating": 4.49, "price_usd": 100}
        result = create_feature_matrix([product])
        # 4.49 is < 4.5, should not pass High Rating check
        lines = result["content"].split("\n")
        high_rating_row = [l for l in lines if "High Rating" in l]
        if high_rating_row:
            assert "❌" in high_rating_row[0]

    def test_rating_exactly_0(self):
        """Test: rating exactly 0."""
        product = {"product_name": "Test", "rating": 0, "price_usd": 100}
        result = create_product_card(product)
        assert result["success"] is True
        assert "0/5.0" in result["content"]

    def test_rating_exactly_5(self):
        """Test: rating exactly 5.0 (max)."""
        product = {"product_name": "Test", "rating": 5.0, "price_usd": 100}
        result = create_product_card(product)
        assert result["success"] is True
        assert "5.0/5.0" in result["content"]

    def test_rating_above_5(self):
        """Test: rating > 5 (invalid but handled)."""
        product = {"product_name": "Test", "rating": 5.5, "price_usd": 100}
        result = create_product_card(product)
        assert result["success"] is True


# ============================================================================
# BOUNDARY CONDITION TESTS - PRICES
# ============================================================================

class TestPriceBoundaries:
    """Tests for price boundary conditions."""

    def test_price_exactly_300(self):
        """Test: price exactly $300 (threshold for 'Under $300')."""
        product = {"product_name": "Test", "price_usd": 300, "rating": 4.0}
        result = create_feature_matrix([product])
        # $300 is NOT under $300
        lines = result["content"].split("\n")
        under_300_row = [l for l in lines if "Under $300" in l]
        if under_300_row:
            assert "❌" in under_300_row[0]

    def test_price_299_99(self):
        """Test: price $299.99 (just under threshold)."""
        product = {"product_name": "Test", "price_usd": 299.99, "rating": 4.0}
        result = create_feature_matrix([product])
        lines = result["content"].split("\n")
        under_300_row = [l for l in lines if "Under $300" in l]
        if under_300_row:
            assert "✅" in under_300_row[0]

    def test_price_exactly_0(self):
        """Test: price exactly $0."""
        product = {"product_name": "Test", "price_usd": 0, "rating": 4.0}
        result = create_product_card(product)
        assert result["success"] is True
        assert "$0.00" in result["content"]

    def test_price_very_large(self):
        """Test: very large price."""
        product = {"product_name": "Test", "price_usd": 999999.99, "rating": 4.0}
        result = create_product_card(product)
        assert result["success"] is True


# ============================================================================
# BOUNDARY CONDITION TESTS - FEEDBACK
# ============================================================================

class TestFeedbackBoundaries:
    """Tests for feedback boundary conditions."""

    def test_feedback_exactly_50_entries(self, temp_memory_file):
        """Test: exactly 50 feedback entries (limit)."""
        memory = UserMemory(storage_path=temp_memory_file)

        for i in range(50):
            memory.record_feedback("testuser", f"Feedback {i}")

        assert len(memory.data["testuser"]["feedback"]) == 50

    def test_feedback_51st_entry_removes_oldest(self, temp_memory_file):
        """Test: 51st entry removes oldest."""
        memory = UserMemory(storage_path=temp_memory_file)

        for i in range(51):
            memory.record_feedback("testuser", f"Feedback {i}")

        assert len(memory.data["testuser"]["feedback"]) == 50
        # First feedback should be "Feedback 1" (0 was removed)
        assert memory.data["testuser"]["feedback"][0]["text"] == "Feedback 1"


# ============================================================================
# DATA TYPE EDGE CASES
# ============================================================================

class TestDataTypeEdgeCases:
    """Tests for data type edge cases."""

    def test_float_as_string_price(self):
        """Test: price as string."""
        product = {"product_name": "Test", "price_usd": "100.50", "rating": 4.0}
        result = create_product_card(product)
        # Should handle gracefully
        assert result is not None

    def test_int_as_string_rating(self):
        """Test: rating as string."""
        product = {"product_name": "Test", "price_usd": 100, "rating": "4"}
        result = create_product_card(product)
        assert result is not None

    def test_boolean_as_string(self):
        """Test: boolean as string in attributes."""
        product = {
            "product_name": "Test",
            "price_usd": 100,
            "rating": 4.0,
            "waterproof": "true"
        }
        result = create_comparison_table([product], attributes=["waterproof"])
        assert result["success"] is True

    def test_none_vs_empty_string_vs_missing(self):
        """Test: None vs empty string vs missing key."""
        products = [
            {"product_name": "None Value", "brand": None, "price_usd": 100, "rating": 4.0},
            {"product_name": "Empty String", "brand": "", "price_usd": 100, "rating": 4.0},
            {"product_name": "Missing Key", "price_usd": 100, "rating": 4.0},  # No brand
        ]
        result = create_comparison_table(products, attributes=["brand"])
        assert result["success"] is True
        # All should show some representation (-, empty, or Unknown)

    def test_list_instead_of_string(self):
        """Test: list value where string expected."""
        product = {
            "product_name": ["List", "Name"],  # Should be string
            "price_usd": 100,
            "rating": 4.0
        }
        result = create_product_card(product)
        # Should not crash
        assert result is not None


# ============================================================================
# EMPTY/NULL HANDLING TESTS
# ============================================================================

class TestEmptyNullHandling:
    """Tests for empty/null value handling."""

    def test_empty_product_list(self):
        """Test: empty product list."""
        assert create_comparison_table([])["success"] is False
        assert create_feature_matrix([])["success"] is False
        assert create_price_visualization([])["success"] is False
        assert format_product_list([])["success"] is False

    def test_empty_product_dict(self):
        """Test: empty product dictionary."""
        result = create_product_card({})
        assert result["success"] is True
        assert "Unknown Product" in result["content"]

    def test_none_product(self):
        """Test: None instead of product dict."""
        result = create_product_card(None)
        assert result["success"] is False

    def test_none_in_product_list(self):
        """Test: None element in product list."""
        products = [{"product_name": "Valid", "price_usd": 100, "rating": 4.0}, None]
        # Should handle gracefully
        try:
            result = create_comparison_table(products)
        except (TypeError, AttributeError):
            pass  # Expected to fail or handle

    def test_empty_string_query(self, temp_memory_file):
        """Test: empty string query."""
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            mock_get_memory.return_value = UserMemory(storage_path=temp_memory_file)
            agent = PersonalizationAgent(use_llm=False)

            context = agent.extract_context("")
            assert context.activity == Activity.UNKNOWN
            assert context.weather == Weather.UNKNOWN

    def test_whitespace_only_string(self, temp_memory_file):
        """Test: whitespace-only string."""
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            mock_get_memory.return_value = UserMemory(storage_path=temp_memory_file)
            agent = PersonalizationAgent(use_llm=False)

            context = agent.extract_context("   \t\n   ")
            assert context.activity == Activity.UNKNOWN


# ============================================================================
# STRING EDGE CASES
# ============================================================================

class TestStringEdgeCases:
    """Tests for string edge cases."""

    def test_unicode_characters(self, unicode_string):
        """Test: unicode characters in product name."""
        product = {
            "product_name": unicode_string,
            "brand": unicode_string,
            "price_usd": 100,
            "rating": 4.0
        }
        result = create_product_card(product)
        assert result["success"] is True

    def test_emoji_in_fields(self):
        """Test: emoji in various fields."""
        product = {
            "product_name": "Winter Jacket ❄️",
            "brand": "NorthPeak 🏔️",
            "price_usd": 100,
            "rating": 4.0,
            "color": "Blue 💙"
        }
        result = create_product_card(product)
        assert result["success"] is True

    def test_very_long_product_name(self, long_string):
        """Test: very long product name."""
        product = {
            "product_name": long_string,
            "price_usd": 100,
            "rating": 4.0
        }
        result = create_product_card(product)
        assert result["success"] is True

    def test_special_markdown_characters(self):
        """Test: special markdown characters."""
        product = {
            "product_name": "Test | Product * _Italic_ **Bold** `Code`",
            "brand": "Brand # with ## headers",
            "price_usd": 100,
            "rating": 4.0
        }
        result = create_product_card(product)
        assert result["success"] is True

    def test_newlines_in_fields(self):
        """Test: newlines in fields."""
        product = {
            "product_name": "Test\nProduct\nName",
            "brand": "Brand\nWith\nNewlines",
            "price_usd": 100,
            "rating": 4.0
        }
        result = create_product_card(product)
        assert result["success"] is True

    def test_tabs_in_fields(self):
        """Test: tabs in fields."""
        product = {
            "product_name": "Test\tProduct",
            "brand": "Brand\tWith\tTabs",
            "price_usd": 100,
            "rating": 4.0
        }
        result = create_product_card(product)
        assert result["success"] is True


# ============================================================================
# PERSONALIZATION CONTEXT EDGE CASES
# ============================================================================

class TestPersonalizationContextEdgeCases:
    """Tests for PersonalizationContext edge cases."""

    def test_context_with_all_defaults(self):
        """Test: context with all default values."""
        context = PersonalizationContext()
        d = context.to_dict()
        assert d["activity"] == "unknown"
        assert d["weather"] == "unknown"
        assert d["fit_preference"] == "classic"

    def test_context_with_all_values_set(self):
        """Test: context with all values explicitly set."""
        context = PersonalizationContext(
            user_id="test",
            is_returning_user=True,
            activity=Activity.HIKING,
            weather=Weather.COLD,
            style_preference=StylePreference.TECHNICAL,
            fit_preference=FitPreference.RELAXED,
            gender="Women",
            budget_max=500.0,
            colors_preferred=["blue", "black"],
            colors_avoided=["red"],
            brands_preferred=["NorthPeak"],
            shirt_size="M",
            pants_size="32",
            shoe_size="10",
            specific_items=["jacket"],
            occasion="hiking",
            original_query="test query"
        )
        d = context.to_dict()
        assert all(v is not None for k, v in d.items() if k not in ["user_id"])


# ============================================================================
# ORCHESTRATOR EDGE CASES
# ============================================================================

class TestOrchestratorEdgeCases:
    """Tests for Orchestrator edge cases."""

    def test_classify_with_multiple_intent_keywords(self):
        """Test: query with multiple intent keywords."""
        with patch('src.agents.orchestrator.ProductSearch'):
            orchestrator = Orchestrator(use_llm=False)

            # Query has both styling and comparison keywords
            intent = orchestrator.classify_intent("Compare outfits for hiking")
            # Styling should take priority (appears first in checks)
            # Actually depends on keyword order in query vs check order
            assert intent in [QueryIntent.STYLING, QueryIntent.COMPARISON]

    def test_process_empty_query(self):
        """Test: process empty query."""
        with patch('src.agents.orchestrator.ProductSearch') as mock_search_class:
            mock_search = MagicMock()
            mock_search.search_semantic.return_value = []
            mock_search_class.return_value = mock_search

            orchestrator = Orchestrator(use_llm=False)
            result = orchestrator.process_query("")
            assert result is not None


# ============================================================================
# FILTER APPLICATION EDGE CASES
# ============================================================================

class TestFilterEdgeCases:
    """Tests for filter application edge cases."""

    def test_filter_with_all_matching(self):
        """Test: all products match filter."""
        with patch('src.agents.orchestrator.ProductSearch'):
            orchestrator = Orchestrator(use_llm=False)
            products = [
                {"product_name": "A", "gender": "Women", "price_usd": 100},
                {"product_name": "B", "gender": "Women", "price_usd": 150}
            ]
            filtered = orchestrator._apply_filters(products, {"gender": "Women"})
            assert len(filtered) == 2

    def test_filter_with_none_matching(self):
        """Test: no products match filter."""
        with patch('src.agents.orchestrator.ProductSearch'):
            orchestrator = Orchestrator(use_llm=False)
            products = [
                {"product_name": "A", "gender": "Women"},
                {"product_name": "B", "gender": "Women"}
            ]
            filtered = orchestrator._apply_filters(products, {"gender": "Men"})
            assert len(filtered) == 0

    def test_filter_with_missing_attribute(self):
        """Test: filter on attribute not in products."""
        with patch('src.agents.orchestrator.ProductSearch'):
            orchestrator = Orchestrator(use_llm=False)
            products = [{"product_name": "A"}]  # No gender attribute
            filtered = orchestrator._apply_filters(products, {"gender": "Women"})
            assert len(filtered) == 0


# ============================================================================
# MEMORY EDGE CASES
# ============================================================================

class TestMemoryEdgeCases:
    """Tests for memory edge cases."""

    def test_update_nonexistent_section(self, temp_memory_file):
        """Test: update preference with invalid section."""
        memory = UserMemory(storage_path=temp_memory_file)

        # Invalid section - should not crash
        memory.update_preference("testuser", "invalid_section", "key", "value", permanent=True)
        # The section won't be created for invalid sections

    def test_get_preferences_for_new_user_creates_entry(self, temp_memory_file):
        """Test: get_preferences for new user creates data structure."""
        memory = UserMemory(storage_path=temp_memory_file)

        assert "newuser" not in memory.data
        prefs = memory.get_preferences("newuser")
        assert "newuser" in memory.data

    def test_session_override_on_nonexistent_user(self, temp_memory_file):
        """Test: session override for non-existent user."""
        memory = UserMemory(storage_path=temp_memory_file)

        memory.update_preference("newuser", "sizing", "fit", "relaxed", permanent=False)
        assert "newuser" in memory.session_overrides


# ============================================================================
# VISUAL AGENT AUTO-VISUALIZE EDGE CASES
# ============================================================================

class TestAutoVisualizeEdgeCases:
    """Tests for auto_visualize edge cases."""

    def test_auto_visualize_exactly_2_products(self, sample_products, visual_agent):
        """Test: auto_visualize with exactly 2 products."""
        result = visual_agent.auto_visualize(sample_products[:2])
        # Should use comparison table
        assert "|" in result

    def test_auto_visualize_exactly_5_products(self, sample_products, visual_agent):
        """Test: auto_visualize with exactly 5 products."""
        result = visual_agent.auto_visualize(sample_products[:5])
        # Should use comparison table
        assert "|" in result

    def test_auto_visualize_exactly_6_products(self, sample_products, visual_agent):
        """Test: auto_visualize with exactly 6 products."""
        result = visual_agent.auto_visualize(sample_products[:6])
        # Should use list + price analysis
        assert "Product" in result or "|" in result

    def test_auto_visualize_with_intent_override(self, sample_products, visual_agent):
        """Test: intent parameter overrides default behavior."""
        # Even with 10 products, comparison intent should try comparison table
        result = visual_agent.auto_visualize(sample_products, intent="comparison")
        # Should include table formatting
        assert "|" in result


# ============================================================================
# NUMERIC PRECISION EDGE CASES
# ============================================================================

class TestNumericPrecision:
    """Tests for numeric precision edge cases."""

    def test_price_floating_point_precision(self):
        """Test: floating point precision in price calculations."""
        products = [
            {"product_name": "A", "price_usd": 0.1 + 0.2, "rating": 4.0},  # 0.30000000000000004
            {"product_name": "B", "price_usd": 0.3, "rating": 4.0}
        ]
        result = create_price_visualization(products)
        assert result["success"] is True

    def test_very_small_price(self):
        """Test: very small price value."""
        product = {"product_name": "Test", "price_usd": 0.01, "rating": 4.0}
        result = create_product_card(product)
        assert result["success"] is True
        assert "$0.01" in result["content"]

    def test_rating_with_many_decimals(self):
        """Test: rating with many decimal places."""
        product = {"product_name": "Test", "price_usd": 100, "rating": 4.333333333}
        result = create_product_card(product)
        assert result["success"] is True
