"""
Tests for Orchestrator (src/agents/orchestrator.py).

Covers:
- Intent classification (rule-based and LLM)
- Query routing to appropriate handlers
- Filter application
- Output structure
"""

import pytest
from unittest.mock import patch, MagicMock

from src.agents.orchestrator import (
    Orchestrator,
    QueryIntent,
    OrchestratorResult,
    process_user_query
)


# ============================================================================
# ORCHESTRATOR INITIALIZATION TESTS
# ============================================================================

class TestOrchestratorInit:
    """Tests for Orchestrator initialization."""

    def test_init_with_llm_disabled(self):
        """Orchestrator initializes with LLM disabled."""
        with patch('src.agents.orchestrator.ProductSearch'):
            orchestrator = Orchestrator(use_llm=False)
            assert orchestrator.use_llm is False

    def test_init_creates_personalization_agent(self):
        """Orchestrator creates PersonalizationAgent."""
        with patch('src.agents.orchestrator.ProductSearch'):
            orchestrator = Orchestrator(use_llm=False)
            assert orchestrator.personalization_agent is not None

    def test_init_creates_product_search(self):
        """Orchestrator creates ProductSearch."""
        with patch('src.agents.orchestrator.ProductSearch') as mock_search:
            orchestrator = Orchestrator(use_llm=False)
            mock_search.assert_called_once()


# ============================================================================
# RULE-BASED INTENT CLASSIFICATION TESTS
# ============================================================================

class TestRuleBasedClassification:
    """Tests for rule-based intent classification."""

    def test_classify_styling_outfit(self):
        """classify_intent() detects STYLING for 'outfit'."""
        with patch('src.agents.orchestrator.ProductSearch'):
            orchestrator = Orchestrator(use_llm=False)
            intent = orchestrator.classify_intent("I need an outfit for hiking")
            assert intent == QueryIntent.STYLING

    def test_classify_styling_wear(self):
        """classify_intent() detects STYLING for 'wear'."""
        with patch('src.agents.orchestrator.ProductSearch'):
            orchestrator = Orchestrator(use_llm=False)
            intent = orchestrator.classify_intent("What should I wear for skiing?")
            assert intent == QueryIntent.STYLING

    def test_classify_styling_dress(self):
        """classify_intent() detects STYLING for 'dress'."""
        with patch('src.agents.orchestrator.ProductSearch'):
            orchestrator = Orchestrator(use_llm=False)
            intent = orchestrator.classify_intent("Help me dress for cold weather")
            assert intent == QueryIntent.STYLING

    def test_classify_styling_style(self):
        """classify_intent() detects STYLING for 'style'."""
        with patch('src.agents.orchestrator.ProductSearch'):
            orchestrator = Orchestrator(use_llm=False)
            intent = orchestrator.classify_intent("I want a technical style look")
            assert intent == QueryIntent.STYLING

    def test_classify_styling_look(self):
        """classify_intent() detects STYLING for 'look'."""
        with patch('src.agents.orchestrator.ProductSearch'):
            orchestrator = Orchestrator(use_llm=False)
            intent = orchestrator.classify_intent("Create a hiking look for me")
            assert intent == QueryIntent.STYLING

    def test_classify_comparison_compare(self):
        """classify_intent() detects COMPARISON for 'compare'."""
        with patch('src.agents.orchestrator.ProductSearch'):
            orchestrator = Orchestrator(use_llm=False)
            intent = orchestrator.classify_intent("Compare these jackets")
            assert intent == QueryIntent.COMPARISON

    def test_classify_comparison_versus(self):
        """classify_intent() detects COMPARISON for 'versus'."""
        with patch('src.agents.orchestrator.ProductSearch'):
            orchestrator = Orchestrator(use_llm=False)
            intent = orchestrator.classify_intent("NorthPeak versus AlpineCo")
            assert intent == QueryIntent.COMPARISON

    def test_classify_comparison_vs(self):
        """classify_intent() detects COMPARISON for 'vs'."""
        with patch('src.agents.orchestrator.ProductSearch'):
            orchestrator = Orchestrator(use_llm=False)
            intent = orchestrator.classify_intent("Jacket A vs Jacket B")
            assert intent == QueryIntent.COMPARISON

    def test_classify_comparison_better(self):
        """classify_intent() detects COMPARISON for 'better'."""
        with patch('src.agents.orchestrator.ProductSearch'):
            orchestrator = Orchestrator(use_llm=False)
            intent = orchestrator.classify_intent("Which is better for hiking?")
            assert intent == QueryIntent.COMPARISON

    def test_classify_info_brands(self):
        """classify_intent() detects INFO for 'brands'."""
        with patch('src.agents.orchestrator.ProductSearch'):
            orchestrator = Orchestrator(use_llm=False)
            intent = orchestrator.classify_intent("What brands do you have?")
            assert intent == QueryIntent.INFO

    def test_classify_info_categories(self):
        """classify_intent() detects INFO for 'categories'."""
        with patch('src.agents.orchestrator.ProductSearch'):
            orchestrator = Orchestrator(use_llm=False)
            intent = orchestrator.classify_intent("Show me your categories")
            assert intent == QueryIntent.INFO

    def test_classify_info_statistics(self):
        """classify_intent() detects INFO for 'statistics'."""
        with patch('src.agents.orchestrator.ProductSearch'):
            orchestrator = Orchestrator(use_llm=False)
            intent = orchestrator.classify_intent("What are your catalog statistics?")
            assert intent == QueryIntent.INFO

    def test_classify_info_how_many(self):
        """classify_intent() detects INFO for 'how many'."""
        with patch('src.agents.orchestrator.ProductSearch'):
            orchestrator = Orchestrator(use_llm=False)
            intent = orchestrator.classify_intent("How many products do you have?")
            assert intent == QueryIntent.INFO

    def test_classify_default_product_search(self):
        """classify_intent() defaults to PRODUCT_SEARCH."""
        with patch('src.agents.orchestrator.ProductSearch'):
            orchestrator = Orchestrator(use_llm=False)
            intent = orchestrator.classify_intent("Show me waterproof jackets")
            assert intent == QueryIntent.PRODUCT_SEARCH

    def test_classify_case_insensitive(self):
        """classify_intent() is case-insensitive."""
        with patch('src.agents.orchestrator.ProductSearch'):
            orchestrator = Orchestrator(use_llm=False)
            intent = orchestrator.classify_intent("WHAT SHOULD I WEAR")
            assert intent == QueryIntent.STYLING

    def test_classify_empty_query(self):
        """classify_intent() handles empty query."""
        with patch('src.agents.orchestrator.ProductSearch'):
            orchestrator = Orchestrator(use_llm=False)
            intent = orchestrator.classify_intent("")
            assert intent == QueryIntent.PRODUCT_SEARCH

    def test_classify_whitespace_query(self):
        """classify_intent() handles whitespace query."""
        with patch('src.agents.orchestrator.ProductSearch'):
            orchestrator = Orchestrator(use_llm=False)
            intent = orchestrator.classify_intent("   ")
            assert intent == QueryIntent.PRODUCT_SEARCH


# ============================================================================
# LLM-BASED INTENT CLASSIFICATION TESTS
# ============================================================================

class TestLLMClassification:
    """Tests for LLM-based intent classification."""

    def test_classify_with_llm_styling(self):
        """_classify_with_llm() parses STYLING response."""
        with patch('src.agents.orchestrator.ProductSearch'):
            orchestrator = Orchestrator(use_llm=False)
            # Mock the LLM client
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "STYLING"
            mock_client.chat.completions.create.return_value = mock_response

            orchestrator.llm_client = mock_client
            orchestrator.model = "gpt-4o-mini"  # Required for _classify_with_llm
            result = orchestrator._classify_with_llm("outfit query")
            assert result == QueryIntent.STYLING

    def test_classify_with_llm_search(self):
        """_classify_with_llm() parses SEARCH response."""
        with patch('src.agents.orchestrator.ProductSearch'):
            orchestrator = Orchestrator(use_llm=False)
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "SEARCH"
            mock_client.chat.completions.create.return_value = mock_response

            orchestrator.llm_client = mock_client
            orchestrator.model = "gpt-4o-mini"  # Required for _classify_with_llm
            result = orchestrator._classify_with_llm("find jackets")
            assert result == QueryIntent.PRODUCT_SEARCH

    def test_classify_with_llm_comparison(self):
        """_classify_with_llm() parses COMPARISON response."""
        with patch('src.agents.orchestrator.ProductSearch'):
            orchestrator = Orchestrator(use_llm=False)
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "COMPARISON"
            mock_client.chat.completions.create.return_value = mock_response

            orchestrator.llm_client = mock_client
            orchestrator.model = "gpt-4o-mini"  # Required for _classify_with_llm
            result = orchestrator._classify_with_llm("compare products")
            assert result == QueryIntent.COMPARISON

    def test_classify_with_llm_info(self):
        """_classify_with_llm() parses INFO response."""
        with patch('src.agents.orchestrator.ProductSearch'):
            orchestrator = Orchestrator(use_llm=False)
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "INFO"
            mock_client.chat.completions.create.return_value = mock_response

            orchestrator.llm_client = mock_client
            orchestrator.model = "gpt-4o-mini"  # Required for _classify_with_llm
            result = orchestrator._classify_with_llm("catalog info")
            assert result == QueryIntent.INFO

    def test_classify_with_llm_unknown_response(self):
        """_classify_with_llm() returns UNKNOWN for unrecognized response."""
        with patch('src.agents.orchestrator.ProductSearch'):
            orchestrator = Orchestrator(use_llm=False)
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "INVALID_RESPONSE"
            mock_client.chat.completions.create.return_value = mock_response

            orchestrator.llm_client = mock_client
            orchestrator.model = "gpt-4o-mini"  # Required for _classify_with_llm
            result = orchestrator._classify_with_llm("random query")
            assert result == QueryIntent.UNKNOWN

    def test_classify_with_llm_fallback_on_error(self):
        """_classify_with_llm() falls back to rule-based on error."""
        with patch('src.agents.orchestrator.ProductSearch'):
            orchestrator = Orchestrator(use_llm=False)
            mock_client = MagicMock()
            mock_client.chat.completions.create.side_effect = Exception("API Error")

            orchestrator.llm_client = mock_client
            orchestrator.model = "gpt-4o-mini"  # Required for _classify_with_llm
            # Should fall back to rule-based
            result = orchestrator._classify_with_llm("I need an outfit")
            assert result == QueryIntent.STYLING  # Rule-based would catch "outfit"


# ============================================================================
# PROCESS QUERY TESTS
# ============================================================================

class TestProcessQuery:
    """Tests for process_query() method."""

    def test_process_query_styling(self):
        """process_query() handles styling queries."""
        with patch('src.agents.orchestrator.ProductSearch') as mock_search_class:
            mock_search = MagicMock()
            mock_search.search_semantic.return_value = [
                {"product_name": "Test Jacket", "category": "Outerwear", "price_usd": 200}
            ]
            mock_search_class.return_value = mock_search

            orchestrator = Orchestrator(use_llm=False)
            result = orchestrator.process_query("I need an outfit for hiking")

            assert result.intent == QueryIntent.STYLING
            assert isinstance(result, OrchestratorResult)

    def test_process_query_search(self):
        """process_query() handles search queries."""
        with patch('src.agents.orchestrator.ProductSearch') as mock_search_class:
            mock_search = MagicMock()
            mock_search.search_semantic.return_value = [
                {"product_name": "Test Jacket", "price_usd": 200}
            ]
            mock_search_class.return_value = mock_search

            orchestrator = Orchestrator(use_llm=False)
            result = orchestrator.process_query("Show me waterproof jackets")

            assert result.intent == QueryIntent.PRODUCT_SEARCH

    def test_process_query_comparison(self):
        """process_query() handles comparison queries."""
        with patch('src.agents.orchestrator.ProductSearch') as mock_search_class:
            mock_search = MagicMock()
            mock_search.search_semantic.return_value = [
                {"product_name": "Jacket A", "price_usd": 200},
                {"product_name": "Jacket B", "price_usd": 300}
            ]
            mock_search_class.return_value = mock_search

            orchestrator = Orchestrator(use_llm=False)
            result = orchestrator.process_query("Compare NorthPeak jackets")

            assert result.intent == QueryIntent.COMPARISON

    def test_process_query_info(self):
        """process_query() handles info queries."""
        with patch('src.agents.orchestrator.ProductSearch') as mock_search_class:
            mock_search = MagicMock()
            mock_collection = MagicMock()
            mock_collection.count.return_value = 300
            mock_search.collection = mock_collection
            mock_search_class.return_value = mock_search

            orchestrator = Orchestrator(use_llm=False)
            result = orchestrator.process_query("What brands do you have?")

            assert result.intent == QueryIntent.INFO

    def test_process_query_unknown_defaults_to_search(self):
        """process_query() defaults unknown to search."""
        with patch('src.agents.orchestrator.ProductSearch') as mock_search_class:
            mock_search = MagicMock()
            mock_search.search_semantic.return_value = []
            mock_search_class.return_value = mock_search

            orchestrator = Orchestrator(use_llm=False)
            # Manually set intent to UNKNOWN for testing
            with patch.object(orchestrator, 'classify_intent', return_value=QueryIntent.UNKNOWN):
                result = orchestrator.process_query("random gibberish")
                # Should default to search handler
                assert isinstance(result, OrchestratorResult)


# ============================================================================
# HANDLER TESTS
# ============================================================================

class TestHandlers:
    """Tests for individual query handlers."""

    def test_handle_styling_query_returns_products(self):
        """_handle_styling_query() returns products."""
        with patch('src.agents.orchestrator.ProductSearch') as mock_search_class:
            mock_search = MagicMock()
            mock_search.search_semantic.return_value = [
                {"product_name": "Jacket", "category": "Outerwear", "price_usd": 200}
            ]
            mock_search_class.return_value = mock_search

            orchestrator = Orchestrator(use_llm=False)
            result = orchestrator._handle_styling_query("outfit for hiking")

            assert result.products is not None

    def test_handle_styling_query_includes_context(self):
        """_handle_styling_query() includes personalization context."""
        with patch('src.agents.orchestrator.ProductSearch') as mock_search_class:
            mock_search = MagicMock()
            mock_search.search_semantic.return_value = []
            mock_search_class.return_value = mock_search

            orchestrator = Orchestrator(use_llm=False)
            result = orchestrator._handle_styling_query("outfit for hiking")

            assert result.personalization_context is not None

    def test_handle_styling_query_includes_outfit_recommendation(self):
        """_handle_styling_query() includes outfit recommendation."""
        with patch('src.agents.orchestrator.ProductSearch') as mock_search_class:
            mock_search = MagicMock()
            mock_search.search_semantic.return_value = [
                {"product_name": "Jacket", "category": "Outerwear", "price_usd": 200}
            ]
            mock_search_class.return_value = mock_search

            orchestrator = Orchestrator(use_llm=False)
            result = orchestrator._handle_styling_query("outfit for hiking")

            assert result.outfit_recommendation is not None

    def test_handle_search_query_returns_products(self):
        """_handle_search_query() returns products."""
        with patch('src.agents.orchestrator.ProductSearch') as mock_search_class:
            mock_search = MagicMock()
            mock_search.search_semantic.return_value = [
                {"product_name": "Jacket", "price_usd": 200}
            ]
            mock_search_class.return_value = mock_search

            orchestrator = Orchestrator(use_llm=False)
            result = orchestrator._handle_search_query("waterproof jackets")

            assert len(result.products) > 0

    def test_handle_search_query_message(self):
        """_handle_search_query() includes message with count."""
        with patch('src.agents.orchestrator.ProductSearch') as mock_search_class:
            mock_search = MagicMock()
            mock_search.search_semantic.return_value = [
                {"product_name": "Jacket", "price_usd": 200}
            ] * 5
            mock_search_class.return_value = mock_search

            orchestrator = Orchestrator(use_llm=False)
            result = orchestrator._handle_search_query("jackets")

            assert "5 products" in result.message

    def test_handle_comparison_query_returns_products(self):
        """_handle_comparison_query() returns products."""
        with patch('src.agents.orchestrator.ProductSearch') as mock_search_class:
            mock_search = MagicMock()
            mock_search.search_semantic.return_value = [
                {"product_name": "A", "price_usd": 200},
                {"product_name": "B", "price_usd": 300}
            ]
            mock_search_class.return_value = mock_search

            orchestrator = Orchestrator(use_llm=False)
            result = orchestrator._handle_comparison_query("compare jackets")

            assert len(result.products) > 0

    def test_handle_info_query_returns_message(self):
        """_handle_info_query() returns catalog info message."""
        with patch('src.agents.orchestrator.ProductSearch') as mock_search_class:
            mock_search = MagicMock()
            mock_collection = MagicMock()
            mock_collection.count.return_value = 300
            mock_search.collection = mock_collection
            mock_search_class.return_value = mock_search

            orchestrator = Orchestrator(use_llm=False)
            result = orchestrator._handle_info_query("what brands")

            assert "300 products" in result.message


# ============================================================================
# FILTER APPLICATION TESTS
# ============================================================================

class TestApplyFilters:
    """Tests for _apply_filters() method."""

    def test_apply_filter_gender(self):
        """_apply_filters() filters by gender."""
        with patch('src.agents.orchestrator.ProductSearch'):
            orchestrator = Orchestrator(use_llm=False)
            products = [
                {"product_name": "A", "gender": "Women"},
                {"product_name": "B", "gender": "Men"},
                {"product_name": "C", "gender": "Unisex"}
            ]
            filtered = orchestrator._apply_filters(products, {"gender": "Women"})
            # Should include Women and Unisex
            assert len(filtered) == 2
            assert all(p["gender"] in ["Women", "Unisex"] for p in filtered)

    def test_apply_filter_max_price(self):
        """_apply_filters() filters by max price."""
        with patch('src.agents.orchestrator.ProductSearch'):
            orchestrator = Orchestrator(use_llm=False)
            products = [
                {"product_name": "A", "price_usd": 100},
                {"product_name": "B", "price_usd": 200},
                {"product_name": "C", "price_usd": 300}
            ]
            filtered = orchestrator._apply_filters(products, {"max_price": 200})
            assert len(filtered) == 2
            assert all(p["price_usd"] <= 200 for p in filtered)

    def test_apply_filter_season(self):
        """_apply_filters() filters by season."""
        with patch('src.agents.orchestrator.ProductSearch'):
            orchestrator = Orchestrator(use_llm=False)
            products = [
                {"product_name": "A", "season": "Winter"},
                {"product_name": "B", "season": "Summer"},
                {"product_name": "C", "season": "All-season"}
            ]
            filtered = orchestrator._apply_filters(products, {"season": ["Winter"]})
            # Should include Winter and All-season
            assert len(filtered) == 2

    def test_apply_filter_brands(self):
        """_apply_filters() filters by brands."""
        with patch('src.agents.orchestrator.ProductSearch'):
            orchestrator = Orchestrator(use_llm=False)
            products = [
                {"product_name": "A", "brand": "NorthPeak"},
                {"product_name": "B", "brand": "AlpineCo"},
                {"product_name": "C", "brand": "TrailForge"}
            ]
            filtered = orchestrator._apply_filters(products, {"brands": ["NorthPeak", "AlpineCo"]})
            assert len(filtered) == 2

    def test_apply_filter_brands_case_insensitive(self):
        """_apply_filters() brand filter is case-insensitive."""
        with patch('src.agents.orchestrator.ProductSearch'):
            orchestrator = Orchestrator(use_llm=False)
            products = [
                {"product_name": "A", "brand": "NorthPeak"},
                {"product_name": "B", "brand": "alpineco"}
            ]
            filtered = orchestrator._apply_filters(products, {"brands": ["NORTHPEAK"]})
            assert len(filtered) == 1

    def test_apply_filter_colors(self):
        """_apply_filters() filters by colors."""
        with patch('src.agents.orchestrator.ProductSearch'):
            orchestrator = Orchestrator(use_llm=False)
            products = [
                {"product_name": "A", "color": "Navy Blue"},
                {"product_name": "B", "color": "Black"},
                {"product_name": "C", "color": "Red"}
            ]
            filtered = orchestrator._apply_filters(products, {"colors": ["blue", "black"]})
            assert len(filtered) == 2

    def test_apply_filter_colors_partial_match(self):
        """_apply_filters() color filter is partial match."""
        with patch('src.agents.orchestrator.ProductSearch'):
            orchestrator = Orchestrator(use_llm=False)
            products = [
                {"product_name": "A", "color": "Navy Blue"},
                {"product_name": "B", "color": "Light Blue"}
            ]
            filtered = orchestrator._apply_filters(products, {"colors": ["blue"]})
            assert len(filtered) == 2

    def test_apply_filter_combined(self):
        """_apply_filters() applies multiple filters."""
        with patch('src.agents.orchestrator.ProductSearch'):
            orchestrator = Orchestrator(use_llm=False)
            products = [
                {"product_name": "A", "gender": "Women", "price_usd": 200, "brand": "NorthPeak"},
                {"product_name": "B", "gender": "Men", "price_usd": 150, "brand": "NorthPeak"},
                {"product_name": "C", "gender": "Women", "price_usd": 400, "brand": "AlpineCo"}
            ]
            filtered = orchestrator._apply_filters(products, {
                "gender": "Women",
                "max_price": 300
            })
            assert len(filtered) == 1
            assert filtered[0]["product_name"] == "A"

    def test_apply_filter_empty_filters(self):
        """_apply_filters() returns all products for empty filters."""
        with patch('src.agents.orchestrator.ProductSearch'):
            orchestrator = Orchestrator(use_llm=False)
            products = [
                {"product_name": "A"},
                {"product_name": "B"}
            ]
            filtered = orchestrator._apply_filters(products, {})
            assert len(filtered) == 2

    def test_apply_filter_none_filters(self):
        """_apply_filters() handles None values in filters."""
        with patch('src.agents.orchestrator.ProductSearch'):
            orchestrator = Orchestrator(use_llm=False)
            products = [{"product_name": "A", "gender": "Women"}]
            # Missing gender key in product shouldn't crash
            filtered = orchestrator._apply_filters(products, {"gender": "Men"})
            assert len(filtered) == 0


# ============================================================================
# ORCHESTRATOR RESULT TESTS
# ============================================================================

class TestOrchestratorResult:
    """Tests for OrchestratorResult dataclass."""

    def test_result_to_dict(self):
        """OrchestratorResult.to_dict() serializes correctly."""
        result = OrchestratorResult(
            intent=QueryIntent.STYLING,
            products=[{"name": "Test"}],
            message="Test message"
        )
        d = result.to_dict()
        assert d["intent"] == "styling"
        assert d["products"] == [{"name": "Test"}]
        assert d["message"] == "Test message"

    def test_result_to_dict_none_products(self):
        """OrchestratorResult.to_dict() handles None products."""
        result = OrchestratorResult(
            intent=QueryIntent.INFO,
            products=None,
            message="Info"
        )
        d = result.to_dict()
        assert d["products"] == []

    def test_result_to_dict_all_fields(self):
        """OrchestratorResult.to_dict() includes all fields."""
        result = OrchestratorResult(
            intent=QueryIntent.STYLING,
            personalization_context={"activity": "hiking"},
            products=[],
            outfit_recommendation={"categories": {}},
            message="Test"
        )
        d = result.to_dict()
        assert "intent" in d
        assert "personalization_context" in d
        assert "products" in d
        assert "outfit_recommendation" in d
        assert "message" in d


# ============================================================================
# QUERY INTENT ENUM TESTS
# ============================================================================

class TestQueryIntent:
    """Tests for QueryIntent enum."""

    def test_query_intent_values(self):
        """QueryIntent has expected values."""
        assert QueryIntent.STYLING.value == "styling"
        assert QueryIntent.PRODUCT_SEARCH.value == "search"
        assert QueryIntent.COMPARISON.value == "comparison"
        assert QueryIntent.INFO.value == "info"
        assert QueryIntent.UNKNOWN.value == "unknown"


# ============================================================================
# CONVENIENCE FUNCTION TESTS
# ============================================================================

class TestConvenienceFunction:
    """Tests for process_user_query() convenience function."""

    def test_process_user_query_returns_dict(self):
        """process_user_query() returns dictionary."""
        with patch('src.agents.orchestrator.ProductSearch') as mock_search_class:
            mock_search = MagicMock()
            mock_search.search_semantic.return_value = []
            mock_search_class.return_value = mock_search

            result = process_user_query("test query")
            assert isinstance(result, dict)

    def test_process_user_query_has_required_keys(self):
        """process_user_query() result has required keys."""
        with patch('src.agents.orchestrator.ProductSearch') as mock_search_class:
            mock_search = MagicMock()
            mock_search.search_semantic.return_value = []
            mock_search_class.return_value = mock_search

            result = process_user_query("show me jackets")
            assert "intent" in result
            assert "products" in result
            assert "message" in result


# ============================================================================
# MESSAGE GENERATION TESTS
# ============================================================================

class TestMessageGeneration:
    """Tests for message generation."""

    def test_generate_outfit_message_with_activity(self):
        """_generate_outfit_message() includes activity."""
        with patch('src.agents.orchestrator.ProductSearch'):
            orchestrator = Orchestrator(use_llm=False)
            context = {"activity": "hiking", "weather": "unknown"}
            outfit_items = {"Outerwear": [{"product_name": "Jacket"}]}
            message = orchestrator._generate_outfit_message(context, outfit_items)
            assert "hiking" in message

    def test_generate_outfit_message_with_weather(self):
        """_generate_outfit_message() includes weather."""
        with patch('src.agents.orchestrator.ProductSearch'):
            orchestrator = Orchestrator(use_llm=False)
            context = {"activity": "unknown", "weather": "cold"}
            outfit_items = {"Outerwear": [{"product_name": "Jacket"}]}
            message = orchestrator._generate_outfit_message(context, outfit_items)
            assert "cold" in message

    def test_generate_outfit_message_counts_items(self):
        """_generate_outfit_message() counts total items."""
        with patch('src.agents.orchestrator.ProductSearch'):
            orchestrator = Orchestrator(use_llm=False)
            context = {"activity": "hiking", "weather": "cold"}
            outfit_items = {
                "Outerwear": [{"name": "J1"}, {"name": "J2"}],
                "Footwear": [{"name": "B1"}]
            }
            message = orchestrator._generate_outfit_message(context, outfit_items)
            assert "3 items" in message

    def test_generate_outfit_message_lists_categories(self):
        """_generate_outfit_message() lists categories."""
        with patch('src.agents.orchestrator.ProductSearch'):
            orchestrator = Orchestrator(use_llm=False)
            context = {"activity": "hiking", "weather": "cold"}
            outfit_items = {
                "Outerwear": [{"name": "Jacket"}],
                "Footwear": [{"name": "Boots"}]
            }
            message = orchestrator._generate_outfit_message(context, outfit_items)
            assert "Outerwear" in message
            assert "Footwear" in message


# ============================================================================
# EDGE CASE TESTS
# ============================================================================

class TestOrchestratorEdgeCases:
    """Edge case tests for Orchestrator."""

    def test_empty_search_results(self):
        """Orchestrator handles empty search results."""
        with patch('src.agents.orchestrator.ProductSearch') as mock_search_class:
            mock_search = MagicMock()
            mock_search.search_semantic.return_value = []
            mock_search_class.return_value = mock_search

            orchestrator = Orchestrator(use_llm=False)
            result = orchestrator.process_query("nonexistent product xyz")

            assert result.products == []
            assert "0 products" in result.message

    def test_very_long_query(self, long_string):
        """Orchestrator handles very long query."""
        with patch('src.agents.orchestrator.ProductSearch') as mock_search_class:
            mock_search = MagicMock()
            mock_search.search_semantic.return_value = []
            mock_search_class.return_value = mock_search

            orchestrator = Orchestrator(use_llm=False)
            result = orchestrator.process_query(long_string)

            assert isinstance(result, OrchestratorResult)

    def test_special_characters_in_query(self, special_characters):
        """Orchestrator handles special characters in query."""
        with patch('src.agents.orchestrator.ProductSearch') as mock_search_class:
            mock_search = MagicMock()
            mock_search.search_semantic.return_value = []
            mock_search_class.return_value = mock_search

            orchestrator = Orchestrator(use_llm=False)
            result = orchestrator.process_query(special_characters)

            assert isinstance(result, OrchestratorResult)


# ============================================================================
# INVARIANT TESTS
# ============================================================================

class TestOrchestratorInvariants:
    """Tests for system invariants."""

    def test_result_always_has_intent(self):
        """Invariant: result always has intent."""
        with patch('src.agents.orchestrator.ProductSearch') as mock_search_class:
            mock_search = MagicMock()
            mock_search.search_semantic.return_value = []
            mock_collection = MagicMock()
            mock_collection.count.return_value = 0
            mock_search.collection = mock_collection
            mock_search_class.return_value = mock_search

            orchestrator = Orchestrator(use_llm=False)

            queries = [
                "outfit for hiking",
                "waterproof jackets",
                "compare products",
                "what brands"
            ]
            for query in queries:
                result = orchestrator.process_query(query)
                assert result.intent is not None

    def test_result_products_always_list(self):
        """Invariant: result.products is always list or None."""
        with patch('src.agents.orchestrator.ProductSearch') as mock_search_class:
            mock_search = MagicMock()
            mock_search.search_semantic.return_value = []
            mock_collection = MagicMock()
            mock_collection.count.return_value = 0
            mock_search.collection = mock_collection
            mock_search_class.return_value = mock_search

            orchestrator = Orchestrator(use_llm=False)

            for query in ["jackets", "outfit", "compare", "brands"]:
                result = orchestrator.process_query(query)
                assert result.products is None or isinstance(result.products, list)

    def test_result_message_always_string(self):
        """Invariant: result.message is always string."""
        with patch('src.agents.orchestrator.ProductSearch') as mock_search_class:
            mock_search = MagicMock()
            mock_search.search_semantic.return_value = []
            mock_collection = MagicMock()
            mock_collection.count.return_value = 0
            mock_search.collection = mock_collection
            mock_search_class.return_value = mock_search

            orchestrator = Orchestrator(use_llm=False)

            for query in ["jackets", "outfit", "compare", "brands"]:
                result = orchestrator.process_query(query)
                assert isinstance(result.message, str)
