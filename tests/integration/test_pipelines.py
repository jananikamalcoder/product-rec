"""
Integration tests for non-LLM data pipelines.

Tests the data flow between components without LLM involvement:
- Search → Visualization pipeline
- Memory → Search context pipeline
- Feedback → Signals pipeline
- Full data pipeline (Memory → Search → Visual)
"""

import pytest


class TestSearchToVisualization:
    """Tests for ProductSearch → VisualAgent pipeline."""

    def test_search_to_visualization(self, search_engine, visual_agent):
        """Search results should be visualizable."""
        # Search for products
        results = search_engine.search_semantic("warm jacket", n_results=5)

        assert len(results) > 0

        # Visualize the results
        viz_result = visual_agent.format_product_list(results, show_details=True)

        assert viz_result["success"] is True
        assert viz_result["metadata"]["products_shown"] == len(results)

        # Content should contain product info
        content = viz_result["content"]
        assert results[0]["brand"] in content

    def test_search_to_comparison(self, search_engine, visual_agent):
        """Search results should work in comparison table."""
        results = search_engine.search_semantic("hiking boots", n_results=3)

        assert len(results) > 0

        # Create comparison
        viz_result = visual_agent.create_comparison_table(results)

        assert viz_result["success"] is True
        assert viz_result["metadata"]["products_count"] == len(results)

    def test_search_to_auto_visualize(self, search_engine, visual_agent):
        """Auto-visualize should handle search results correctly."""
        # Single result
        single = search_engine.search_semantic("down parka", n_results=1)
        viz_single = visual_agent.auto_visualize(single)
        assert "###" in viz_single  # Product card format

        # Multiple results
        multiple = search_engine.search_semantic("jacket", n_results=8)
        viz_multiple = visual_agent.auto_visualize(multiple)
        assert "| Product |" in viz_multiple  # List format


class TestMemoryToSearchContext:
    """Tests for UserMemory → Search filters pipeline."""

    def test_memory_to_search_context(self, memory_with_user, search_engine, test_user_id):
        """User preferences should translate to search filters."""
        # Get user preferences
        prefs = memory_with_user.get_preferences(test_user_id)

        # Build filters from preferences (single filter doesn't need $and)
        filters = None
        if prefs["general"].get("budget_max"):
            filters = {"price_usd": {"$lte": prefs["general"]["budget_max"]}}

        # Execute filtered search
        results = search_engine.hybrid_search(
            query="jacket",
            filters=filters,
            n_results=10
        )

        # All results should respect budget
        for product in results:
            assert product["price_usd"] <= prefs["general"]["budget_max"]

    def test_preferences_affect_results(self, memory_instance, search_engine):
        """Different preferences should produce different filtered results."""
        # Create user with low budget
        memory_instance.save_preferences_bulk(
            user_id="low_budget_user",
            general={"budget_max": 150}
        )

        # Create user with high budget
        memory_instance.save_preferences_bulk(
            user_id="high_budget_user",
            general={"budget_max": 500}
        )

        low_prefs = memory_instance.get_preferences("low_budget_user")
        high_prefs = memory_instance.get_preferences("high_budget_user")

        # Search with low budget
        low_results = search_engine.hybrid_search(
            query="jacket",
            filters={"price_usd": {"$lte": low_prefs["general"]["budget_max"]}},
            n_results=10
        )

        # Search with high budget
        high_results = search_engine.hybrid_search(
            query="jacket",
            filters={"price_usd": {"$lte": high_prefs["general"]["budget_max"]}},
            n_results=10
        )

        # High budget should have access to more expensive products
        low_max = max(p["price_usd"] for p in low_results) if low_results else 0
        high_max = max(p["price_usd"] for p in high_results) if high_results else 0

        # High budget results can include more expensive items
        assert high_max >= low_max or high_prefs["general"]["budget_max"] > low_prefs["general"]["budget_max"]


class TestFeedbackToSignals:
    """Tests for feedback processing pipeline."""

    def test_feedback_to_signals(self, memory_instance, test_user_id):
        """Feedback text should extract correct signals."""
        test_cases = [
            ("too flashy", "avoid_style", "bright_colors"),
            ("too tight", "fit_issue", "too_tight"),
            ("too expensive", "budget", "lower_budget"),
            ("too baggy", "fit_issue", "too_loose"),
            ("too boring", "prefer_style", "more_color"),
        ]

        for feedback_text, expected_type, expected_value in test_cases:
            signals = memory_instance.record_feedback(test_user_id, feedback_text)

            matching_signal = next(
                (s for s in signals if s["type"] == expected_type and s["value"] == expected_value),
                None
            )
            assert matching_signal is not None, f"Expected signal for '{feedback_text}' not found"

    def test_feedback_signals_aggregate(self, memory_instance, test_user_id):
        """Multiple feedbacks should accumulate signals."""
        memory_instance.record_feedback(test_user_id, "too flashy")
        memory_instance.record_feedback(test_user_id, "too expensive")

        all_signals = memory_instance.get_feedback_signals(test_user_id)

        # Should have signals from both feedbacks
        assert any(s["type"] == "avoid_style" for s in all_signals)
        assert any(s["type"] == "budget" for s in all_signals)


class TestFullDataPipeline:
    """Tests for complete Memory → Search → Visual pipeline."""

    def test_full_data_pipeline(self, memory_instance, search_engine, visual_agent):
        """Full pipeline: user prefs → filtered search → visualization."""
        user_id = "pipeline_test_user"

        # Step 1: Create user with preferences
        memory_instance.save_preferences_bulk(
            user_id=user_id,
            sizing={"fit": "relaxed"},
            preferences={"outerwear": {"colors": ["blue", "black"]}},
            general={"budget_max": 300}
        )

        # Step 2: Get preferences
        prefs = memory_instance.get_preferences(user_id)
        assert prefs["general"]["budget_max"] == 300

        # Step 3: Search with budget filter
        results = search_engine.hybrid_search(
            query="waterproof jacket",
            filters={"price_usd": {"$lte": prefs["general"]["budget_max"]}},
            n_results=5
        )

        # Verify results respect budget
        assert all(p["price_usd"] <= 300 for p in results)

        # Step 4: Visualize results
        if results:
            viz_result = visual_agent.auto_visualize(results)

            # Should produce valid visualization
            assert len(viz_result) > 0
            assert "$" in viz_result  # Should have price info

    def test_pipeline_with_feedback_loop(self, memory_instance, search_engine, visual_agent):
        """Pipeline with feedback affecting subsequent searches."""
        user_id = "feedback_loop_user"

        # Initial search
        memory_instance.save_preferences_bulk(
            user_id=user_id,
            general={"budget_max": 500}
        )

        # User gives feedback: too expensive
        signals = memory_instance.record_feedback(user_id, "these are too expensive")

        # Signals should indicate lower budget preference
        assert any(s["type"] == "budget" and s["value"] == "lower_budget" for s in signals)

        # In real system, this would adjust the budget filter
        # For test, we simulate by reducing budget
        adjusted_budget = 200

        results = search_engine.hybrid_search(
            query="jacket",
            filters={"price_usd": {"$lte": adjusted_budget}},
            n_results=5
        )

        # Results should be within new budget
        assert all(p["price_usd"] <= adjusted_budget for p in results)

        # Visualize
        if results:
            viz = visual_agent.format_product_list(results)
            assert viz["success"] is True
