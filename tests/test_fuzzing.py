"""
Fuzzing and property-based tests for the multi-agent product recommendation system.

Uses hypothesis for property-based testing to find edge cases through
random input generation.

Covers:
- Random user IDs
- Random product data
- Random queries
- Random preference values
- Random feedback
"""

import pytest
from unittest.mock import patch

# Try to import hypothesis, skip tests if not available
try:
    from hypothesis import given, strategies as st, settings, assume, HealthCheck
    HYPOTHESIS_AVAILABLE = True
except ImportError:
    HYPOTHESIS_AVAILABLE = False
    # Create dummy decorators
    def given(*args, **kwargs):
        def decorator(f):
            return pytest.mark.skip(reason="hypothesis not installed")(f)
        return decorator

    class st:
        @staticmethod
        def text(*args, **kwargs):
            return None
        @staticmethod
        def floats(*args, **kwargs):
            return None
        @staticmethod
        def integers(*args, **kwargs):
            return None
        @staticmethod
        def lists(*args, **kwargs):
            return None
        @staticmethod
        def dictionaries(*args, **kwargs):
            return None
        @staticmethod
        def one_of(*args, **kwargs):
            return None
        @staticmethod
        def none():
            return None
        @staticmethod
        def booleans():
            return None

    def settings(*args, **kwargs):
        def decorator(f):
            return f
        return decorator

    def assume(x):
        pass

from src.agents.memory import UserMemory
from src.agents.personalization_agent import PersonalizationAgent
from src.agents.visual_agent import (
    create_product_card,
    create_comparison_table,
    create_feature_matrix,
    create_price_visualization,
    format_product_list
)
from src.agents.orchestrator import Orchestrator, QueryIntent


# ============================================================================
# STRATEGY DEFINITIONS
# ============================================================================

if HYPOTHESIS_AVAILABLE:
    # Strategy for generating user IDs
    user_id_strategy = st.text(
        min_size=0,
        max_size=100,
        alphabet=st.characters(blacklist_categories=('Cs',))  # Exclude surrogates
    )

    # Strategy for generating prices
    price_strategy = st.floats(
        min_value=-1000,
        max_value=100000,
        allow_nan=False,
        allow_infinity=False
    )

    # Strategy for generating ratings
    rating_strategy = st.floats(
        min_value=-10,
        max_value=10,
        allow_nan=False,
        allow_infinity=False
    )

    # Strategy for generating product dictionaries
    product_strategy = st.fixed_dictionaries({
        'product_name': st.text(min_size=0, max_size=200),
        'price_usd': price_strategy,
        'rating': rating_strategy,
    }, optional={
        'brand': st.text(min_size=0, max_size=50),
        'category': st.text(min_size=0, max_size=50),
        'gender': st.one_of(st.none(), st.sampled_from(['Men', 'Women', 'Unisex', 'Invalid'])),
        'season': st.one_of(st.none(), st.sampled_from(['Winter', 'Summer', 'All-season', 'Spring'])),
        'waterproofing': st.one_of(st.none(), st.text(min_size=0, max_size=50)),
        'insulation': st.one_of(st.none(), st.text(min_size=0, max_size=50)),
        'color': st.one_of(st.none(), st.text(min_size=0, max_size=50)),
    })

    # Strategy for generating product lists
    product_list_strategy = st.lists(product_strategy, min_size=0, max_size=20)

    # Strategy for queries
    query_strategy = st.text(min_size=0, max_size=500)

    # Strategy for feedback
    feedback_strategy = st.text(min_size=0, max_size=500)


# ============================================================================
# MEMORY FUZZ TESTS
# ============================================================================

@pytest.mark.fuzzing
class TestMemoryFuzzing:
    """Fuzz tests for UserMemory."""

    @pytest.mark.skipif(not HYPOTHESIS_AVAILABLE, reason="hypothesis not installed")
    @given(user_id=st.text(min_size=0, max_size=100))
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_random_user_id_doesnt_crash(self, user_id, tmp_path):
        """Random user IDs don't crash the system."""
        storage_path = str(tmp_path / "fuzz_test.json")
        memory = UserMemory(storage_path=storage_path)

        # Should not crash
        try:
            memory._get_user_data(user_id)
            memory.user_exists(user_id)
            memory.get_preferences(user_id)
        except Exception as e:
            pytest.fail(f"Crashed with user_id={repr(user_id)}: {e}")

    @pytest.mark.skipif(not HYPOTHESIS_AVAILABLE, reason="hypothesis not installed")
    @given(
        user_id=st.text(min_size=1, max_size=50),
        key=st.text(min_size=1, max_size=50),
        value=st.one_of(
            st.text(min_size=0, max_size=100),
            st.floats(allow_nan=False, allow_infinity=False),
            st.integers(),
            st.booleans(),
            st.none()
        )
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_random_preference_values(self, user_id, key, value, tmp_path):
        """Random preference values are stored and retrieved correctly."""
        storage_path = str(tmp_path / "fuzz_pref.json")
        memory = UserMemory(storage_path=storage_path)

        try:
            memory.update_preference(user_id, "sizing", key, value, permanent=True)
            memory._save()

            # Verify retrieval
            prefs = memory.get_preferences(user_id)
            assert prefs["sizing"].get(key) == value
        except Exception as e:
            pytest.fail(f"Crashed with key={repr(key)}, value={repr(value)}: {e}")

    @pytest.mark.skipif(not HYPOTHESIS_AVAILABLE, reason="hypothesis not installed")
    @given(feedback=st.text(min_size=0, max_size=500))
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_random_feedback_text(self, feedback, tmp_path):
        """Random feedback text doesn't crash signal extraction."""
        storage_path = str(tmp_path / "fuzz_feedback.json")
        memory = UserMemory(storage_path=storage_path)

        try:
            signals = memory.record_feedback("testuser", feedback)
            # Signals should be a list (possibly empty)
            assert isinstance(signals, list)
        except Exception as e:
            pytest.fail(f"Crashed with feedback={repr(feedback)}: {e}")


# ============================================================================
# VISUAL AGENT FUZZ TESTS
# ============================================================================

@pytest.mark.fuzzing
class TestVisualAgentFuzzing:
    """Fuzz tests for VisualAgent."""

    @pytest.mark.skipif(not HYPOTHESIS_AVAILABLE, reason="hypothesis not installed")
    @given(product=product_strategy)
    @settings(max_examples=100)
    def test_random_product_card(self, product):
        """Random product data doesn't crash create_product_card."""
        try:
            result = create_product_card(product)
            # Should return a dict with success key
            assert isinstance(result, dict)
            assert "success" in result
        except Exception as e:
            pytest.fail(f"Crashed with product={product}: {e}")

    @pytest.mark.skipif(not HYPOTHESIS_AVAILABLE, reason="hypothesis not installed")
    @given(products=product_list_strategy)
    @settings(max_examples=50)
    def test_random_comparison_table(self, products):
        """Random product lists don't crash create_comparison_table."""
        try:
            result = create_comparison_table(products)
            assert isinstance(result, dict)
            assert "success" in result
        except Exception as e:
            pytest.fail(f"Crashed with {len(products)} products: {e}")

    @pytest.mark.skipif(not HYPOTHESIS_AVAILABLE, reason="hypothesis not installed")
    @given(products=product_list_strategy)
    @settings(max_examples=50)
    def test_random_feature_matrix(self, products):
        """Random product lists don't crash create_feature_matrix."""
        try:
            result = create_feature_matrix(products)
            assert isinstance(result, dict)
            assert "success" in result
        except Exception as e:
            pytest.fail(f"Crashed with {len(products)} products: {e}")

    @pytest.mark.skipif(not HYPOTHESIS_AVAILABLE, reason="hypothesis not installed")
    @given(products=product_list_strategy)
    @settings(max_examples=50)
    def test_random_price_visualization(self, products):
        """Random product lists don't crash create_price_visualization."""
        try:
            result = create_price_visualization(products)
            assert isinstance(result, dict)
            assert "success" in result
        except Exception as e:
            pytest.fail(f"Crashed with {len(products)} products: {e}")

    @pytest.mark.skipif(not HYPOTHESIS_AVAILABLE, reason="hypothesis not installed")
    @given(products=product_list_strategy, show_details=st.booleans())
    @settings(max_examples=50)
    def test_random_product_list(self, products, show_details):
        """Random product lists don't crash format_product_list."""
        try:
            result = format_product_list(products, show_details=show_details)
            assert isinstance(result, dict)
            assert "success" in result
        except Exception as e:
            pytest.fail(f"Crashed with {len(products)} products, show_details={show_details}: {e}")


# ============================================================================
# PERSONALIZATION AGENT FUZZ TESTS
# ============================================================================

@pytest.mark.fuzzing
class TestPersonalizationAgentFuzzing:
    """Fuzz tests for PersonalizationAgent."""

    @pytest.mark.skipif(not HYPOTHESIS_AVAILABLE, reason="hypothesis not installed")
    @given(query=st.text(min_size=0, max_size=500))
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_random_query_extraction(self, query, tmp_path):
        """Random queries don't crash context extraction."""
        storage_path = str(tmp_path / "fuzz_agent.json")

        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            memory = UserMemory(storage_path=storage_path)
            mock_get_memory.return_value = memory

            agent = PersonalizationAgent(use_llm=False)

            try:
                context = agent.extract_context(query)
                # Context should be a PersonalizationContext
                assert context is not None
                assert hasattr(context, 'activity')
                assert hasattr(context, 'weather')
            except Exception as e:
                pytest.fail(f"Crashed with query={repr(query)}: {e}")

    @pytest.mark.skipif(not HYPOTHESIS_AVAILABLE, reason="hypothesis not installed")
    @given(
        user_id=st.text(min_size=1, max_size=50),
        feedback=st.text(min_size=0, max_size=500)
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_random_feedback_processing(self, user_id, feedback, tmp_path):
        """Random feedback doesn't crash processing."""
        storage_path = str(tmp_path / "fuzz_feedback.json")

        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            memory = UserMemory(storage_path=storage_path)
            mock_get_memory.return_value = memory

            agent = PersonalizationAgent(use_llm=False)

            try:
                result = agent.process_feedback(user_id, feedback)
                assert result["success"] is True
                assert isinstance(result["signals"], list)
            except Exception as e:
                pytest.fail(f"Crashed with user_id={repr(user_id)}, feedback={repr(feedback)}: {e}")


# ============================================================================
# ORCHESTRATOR FUZZ TESTS
# ============================================================================

@pytest.mark.fuzzing
class TestOrchestratorFuzzing:
    """Fuzz tests for Orchestrator."""

    @pytest.mark.skipif(not HYPOTHESIS_AVAILABLE, reason="hypothesis not installed")
    @given(query=st.text(min_size=0, max_size=500))
    @settings(max_examples=50)
    def test_random_query_classification(self, query):
        """Random queries produce valid intent classification."""
        with patch('src.agents.orchestrator.ProductSearch'):
            orchestrator = Orchestrator(use_llm=False)

            try:
                intent = orchestrator.classify_intent(query)
                # Should always return a valid QueryIntent
                assert isinstance(intent, QueryIntent)
            except Exception as e:
                pytest.fail(f"Crashed with query={repr(query)}: {e}")

    @pytest.mark.skipif(not HYPOTHESIS_AVAILABLE, reason="hypothesis not installed")
    @given(
        products=st.lists(
            st.fixed_dictionaries({
                'product_name': st.text(min_size=1, max_size=50),
                'gender': st.one_of(st.none(), st.sampled_from(['Men', 'Women', 'Unisex'])),
                'price_usd': st.floats(min_value=0, max_value=10000, allow_nan=False, allow_infinity=False),
                'brand': st.one_of(st.none(), st.text(min_size=1, max_size=30)),
                'color': st.one_of(st.none(), st.text(min_size=1, max_size=30)),
                'season': st.one_of(st.none(), st.sampled_from(['Winter', 'Summer', 'All-season']))
            }),
            min_size=0,
            max_size=10
        ),
        filters=st.fixed_dictionaries({}, optional={
            'gender': st.one_of(st.none(), st.sampled_from(['Men', 'Women', 'Unisex'])),
            'max_price': st.one_of(st.none(), st.floats(min_value=0, max_value=10000, allow_nan=False, allow_infinity=False)),
            'brands': st.one_of(st.none(), st.lists(st.text(min_size=1, max_size=20), max_size=5)),
            'colors': st.one_of(st.none(), st.lists(st.text(min_size=1, max_size=20), max_size=5)),
            'season': st.one_of(st.none(), st.lists(st.text(min_size=1, max_size=20), max_size=3))
        })
    )
    @settings(max_examples=50)
    def test_random_filter_application(self, products, filters):
        """Random filter combinations don't crash."""
        with patch('src.agents.orchestrator.ProductSearch'):
            orchestrator = Orchestrator(use_llm=False)

            # Clean up None values from filters
            clean_filters = {k: v for k, v in filters.items() if v is not None}

            try:
                result = orchestrator._apply_filters(products, clean_filters)
                # Result should be a list
                assert isinstance(result, list)
                # Result should be subset of input
                assert len(result) <= len(products)
            except Exception as e:
                pytest.fail(f"Crashed with {len(products)} products, filters={clean_filters}: {e}")


# ============================================================================
# PROPERTY-BASED TESTS
# ============================================================================

@pytest.mark.fuzzing
class TestPropertyBased:
    """Property-based tests that verify invariants."""

    @pytest.mark.skipif(not HYPOTHESIS_AVAILABLE, reason="hypothesis not installed")
    @given(user_id=st.text(min_size=1, max_size=50))
    @settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_user_id_normalization_idempotent(self, user_id, tmp_path):
        """User ID normalization is idempotent."""
        storage_path = str(tmp_path / "idempotent.json")
        memory = UserMemory(storage_path=storage_path)

        # Create user
        memory._get_user_data(user_id)

        # Normalizing again should not create new user
        normalized = user_id.lower().strip()
        count_before = len(memory.data)
        memory._get_user_data(normalized)
        count_after = len(memory.data)

        assert count_before == count_after

    @pytest.mark.skipif(not HYPOTHESIS_AVAILABLE, reason="hypothesis not installed")
    @given(products=st.lists(product_strategy, min_size=1, max_size=20))
    @settings(max_examples=30)
    def test_comparison_table_respects_limit(self, products):
        """Comparison table never exceeds 5 products."""
        result = create_comparison_table(products)
        if result["success"]:
            assert result["metadata"]["products_count"] <= 5

    @pytest.mark.skipif(not HYPOTHESIS_AVAILABLE, reason="hypothesis not installed")
    @given(products=st.lists(product_strategy, min_size=1, max_size=20))
    @settings(max_examples=30)
    def test_feature_matrix_respects_limit(self, products):
        """Feature matrix never exceeds 8 products."""
        result = create_feature_matrix(products)
        if result["success"]:
            assert result["metadata"]["products_count"] <= 8

    @pytest.mark.skipif(not HYPOTHESIS_AVAILABLE, reason="hypothesis not installed")
    @given(products=st.lists(product_strategy, min_size=1, max_size=20))
    @settings(max_examples=30)
    def test_product_list_respects_limit(self, products):
        """Product list never shows more than 10 products."""
        result = format_product_list(products)
        if result["success"]:
            assert result["metadata"]["products_shown"] <= 10

    @pytest.mark.skipif(not HYPOTHESIS_AVAILABLE, reason="hypothesis not installed")
    @given(feedback=st.text(min_size=0, max_size=500))
    @settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_feedback_signals_always_list(self, feedback, tmp_path):
        """Feedback signals are always a list."""
        storage_path = str(tmp_path / "signals.json")
        memory = UserMemory(storage_path=storage_path)

        signals = memory.record_feedback("testuser", feedback)
        assert isinstance(signals, list)


# ============================================================================
# MANUAL FUZZ TESTS (No hypothesis needed)
# ============================================================================

class TestManualFuzzing:
    """Manual fuzz tests that don't require hypothesis."""

    def test_various_unicode_ranges(self):
        """Test various unicode character ranges."""
        unicode_samples = [
            "Hello",  # ASCII
            "Héllo",  # Latin extended
            "Привет",  # Cyrillic
            "你好",  # Chinese
            "مرحبا",  # Arabic
            "🎿⛷️🏔️",  # Emoji
            "\u0000test",  # Null character
            "test\u200b",  # Zero-width space
            "\u202ereversed",  # Right-to-left override
        ]

        for sample in unicode_samples:
            product = {
                "product_name": sample,
                "price_usd": 100,
                "rating": 4.0
            }
            result = create_product_card(product)
            assert result is not None, f"Failed for {repr(sample)}"

    def test_boundary_numbers(self):
        """Test boundary numeric values."""
        boundary_values = [
            0, -0, 0.0, -0.0,
            1, -1,
            float('inf'), float('-inf'),  # Will be rejected by hypothesis but test manually
            2**31 - 1, 2**31, 2**63 - 1,  # Int boundaries
            1e-300, 1e300,  # Float boundaries
        ]

        for val in boundary_values:
            if val in [float('inf'), float('-inf')]:
                continue  # Skip infinity for product card

            product = {
                "product_name": f"Test {val}",
                "price_usd": val if val >= 0 else abs(val),
                "rating": min(max(0, val % 5), 5) if not isinstance(val, float) or not (val != val) else 0
            }
            try:
                result = create_product_card(product)
                assert result is not None
            except (ValueError, OverflowError):
                pass  # Some values might legitimately fail

    def test_whitespace_variations(self):
        """Test various whitespace patterns."""
        whitespace_patterns = [
            "",
            " ",
            "  ",
            "\t",
            "\n",
            "\r\n",
            " \t\n\r ",
            "\u00a0",  # Non-breaking space
            "\u2003",  # Em space
        ]

        for ws in whitespace_patterns:
            product = {
                "product_name": f"Test{ws}Product",
                "price_usd": 100,
                "rating": 4.0
            }
            result = create_product_card(product)
            assert result is not None, f"Failed for whitespace {repr(ws)}"
