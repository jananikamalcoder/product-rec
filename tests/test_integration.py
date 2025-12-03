"""
Integration tests for the multi-agent product recommendation system.

Covers:
- Full user journeys (new user, returning user)
- Multi-agent coordination
- Data flow across components
- End-to-end workflows
"""

import json
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from src.agents.memory import UserMemory
from src.agents.personalization_agent import PersonalizationAgent
from src.agents.visual_agent import VisualAgent
from src.agents.orchestrator import Orchestrator, QueryIntent


# ============================================================================
# NEW USER JOURNEY TESTS
# ============================================================================

@pytest.mark.integration
class TestNewUserJourney:
    """Integration tests for new user flow."""

    def test_new_user_identification_and_save(self, temp_memory_file):
        """Test: identify new user -> save preferences -> verify saved."""
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            memory = UserMemory(storage_path=temp_memory_file)
            mock_get_memory.return_value = memory

            agent = PersonalizationAgent(use_llm=False)

            # Step 1: Identify user (should be new)
            result = agent.identify_user("alice")
            assert result["is_new"] is True

            # Step 2: Save preferences
            save_result = agent.save_user_preferences(
                user_id="alice",
                sizing={"fit": "relaxed", "shirt": "M"},
                preferences={"outerwear": {"colors": ["blue", "black"]}},
                general={"budget_max": 300},
                permanent=True
            )
            assert save_result["success"] is True

            # Step 3: Verify user exists and preferences saved
            verify_result = agent.identify_user("alice")
            assert verify_result["is_new"] is False
            assert verify_result["preferences_summary"] is not None

    def test_new_user_gets_recommendation_without_preferences(self, temp_memory_file):
        """Test: new user can get recommendations without saved preferences."""
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            memory = UserMemory(storage_path=temp_memory_file)
            mock_get_memory.return_value = memory

            agent = PersonalizationAgent(use_llm=False)

            # Get recommendation without any preferences
            result = agent.get_personalized_recommendation(
                "I need hiking gear for cold weather",
                user_id="newbie"
            )

            assert result["success"] is True
            assert result["preferences_applied"] is False
            # Context should still be extracted from query
            assert result["personalization_context"]["activity"] == "hiking"
            assert result["personalization_context"]["weather"] == "cold"


# ============================================================================
# RETURNING USER JOURNEY TESTS
# ============================================================================

@pytest.mark.integration
class TestReturningUserJourney:
    """Integration tests for returning user flow."""

    def test_returning_user_identified_with_preferences(self, temp_memory_file_with_data):
        """Test: returning user is identified with their preferences."""
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            memory = UserMemory(storage_path=temp_memory_file_with_data)
            mock_get_memory.return_value = memory

            agent = PersonalizationAgent(use_llm=False)

            # Identify returning user
            result = agent.identify_user("sarah")
            assert result["is_new"] is False
            assert "preferences_summary" in result

            # Get prompt for confirmation
            prompt = agent.get_returning_user_prompt("sarah")
            assert "Welcome back" in prompt
            assert "relaxed" in prompt.lower()

    def test_returning_user_preferences_applied(self, temp_memory_file_with_data):
        """Test: returning user's preferences are applied to recommendations."""
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            memory = UserMemory(storage_path=temp_memory_file_with_data)
            mock_get_memory.return_value = memory

            agent = PersonalizationAgent(use_llm=False)

            # Get recommendation - should apply stored preferences
            result = agent.get_personalized_recommendation(
                "I need a jacket",
                user_id="sarah"
            )

            assert result["preferences_applied"] is True
            context = result["personalization_context"]
            # Sarah's stored fit preference is "relaxed"
            assert context["fit_preference"] == "relaxed"
            # Sarah's stored budget is 300
            assert context["budget_max"] == 300

    def test_returning_user_query_overrides_stored(self, temp_memory_file_with_data):
        """Test: query values override stored preferences."""
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            memory = UserMemory(storage_path=temp_memory_file_with_data)
            mock_get_memory.return_value = memory

            agent = PersonalizationAgent(use_llm=False)

            # Query specifies different budget than stored
            result = agent.get_personalized_recommendation(
                "Show me jackets under $500",  # Sarah's stored budget is $300
                user_id="sarah"
            )

            context = result["personalization_context"]
            # Query budget should override stored
            assert context["budget_max"] == 500.0


# ============================================================================
# SESSION OVERRIDE WORKFLOW TESTS
# ============================================================================

@pytest.mark.integration
class TestSessionOverrideWorkflow:
    """Integration tests for session-only preference overrides."""

    def test_session_override_applied_then_cleared(self, temp_memory_file_with_data):
        """Test: session override is applied but not persisted."""
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            memory = UserMemory(storage_path=temp_memory_file_with_data)
            mock_get_memory.return_value = memory

            agent = PersonalizationAgent(use_llm=False)

            # Save session-only preference
            agent.save_user_preferences(
                user_id="sarah",
                sizing={"fit": "oversized"},  # Different from stored "relaxed"
                permanent=False  # Session only
            )

            # Check session override is applied
            prefs = agent.get_user_preferences("sarah")
            assert prefs["sizing"]["fit"] == "oversized"

            # Clear session overrides
            memory.clear_session_overrides("sarah")

            # Preferences should revert to permanent values
            prefs_after = agent.get_user_preferences("sarah")
            assert prefs_after["sizing"]["fit"] == "relaxed"

    def test_session_override_isolated_between_users(self, temp_memory_file_with_data):
        """Test: session overrides don't affect other users."""
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            memory = UserMemory(storage_path=temp_memory_file_with_data)
            mock_get_memory.return_value = memory

            agent = PersonalizationAgent(use_llm=False)

            # Set session override for sarah
            agent.save_user_preferences(
                user_id="sarah",
                sizing={"fit": "oversized"},
                permanent=False
            )

            # John's preferences should be unaffected
            john_prefs = agent.get_user_preferences("john")
            assert john_prefs["sizing"].get("fit") == "classic"


# ============================================================================
# FEEDBACK TO PREFERENCE UPDATE FLOW TESTS
# ============================================================================

@pytest.mark.integration
class TestFeedbackToPreferenceFlow:
    """Integration tests for feedback processing flow."""

    def test_feedback_recorded_and_signals_extracted(self, temp_memory_file):
        """Test: feedback is recorded and signals are extracted."""
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            memory = UserMemory(storage_path=temp_memory_file)
            mock_get_memory.return_value = memory

            agent = PersonalizationAgent(use_llm=False)

            # Process feedback
            result = agent.process_feedback("testuser", "This is too tight and flashy")

            assert result["success"] is True
            assert len(result["signals"]) >= 2

            # Check signals recorded in memory
            signals = memory.get_feedback_signals("testuser")
            assert any(s["type"] == "fit_issue" for s in signals)
            assert any(s["type"] == "avoid_style" for s in signals)

    def test_multiple_feedback_entries_accumulated(self, temp_memory_file):
        """Test: multiple feedback entries are accumulated."""
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            memory = UserMemory(storage_path=temp_memory_file)
            mock_get_memory.return_value = memory

            agent = PersonalizationAgent(use_llm=False)

            # Process multiple feedback
            agent.process_feedback("testuser", "Too tight")
            agent.process_feedback("testuser", "Too flashy")
            agent.process_feedback("testuser", "Too expensive")

            signals = memory.get_feedback_signals("testuser")
            assert len(signals) >= 3


# ============================================================================
# MULTI-AGENT COORDINATION TESTS
# ============================================================================

@pytest.mark.integration
class TestMultiAgentCoordination:
    """Integration tests for multi-agent coordination."""

    def test_orchestrator_routes_to_personalization_for_styling(self):
        """Test: orchestrator routes styling queries correctly."""
        with patch('src.agents.orchestrator.ProductSearch') as mock_search_class:
            mock_search = MagicMock()
            mock_search.search_semantic.return_value = [
                {"product_name": "Jacket", "category": "Outerwear", "price_usd": 200}
            ]
            mock_search_class.return_value = mock_search

            orchestrator = Orchestrator(use_llm=False)
            result = orchestrator.process_query("I need an outfit for hiking")

            assert result.intent == QueryIntent.STYLING
            assert result.personalization_context is not None
            assert result.outfit_recommendation is not None

    def test_orchestrator_routes_to_search_for_products(self):
        """Test: orchestrator routes product queries correctly."""
        with patch('src.agents.orchestrator.ProductSearch') as mock_search_class:
            mock_search = MagicMock()
            mock_search.search_semantic.return_value = [
                {"product_name": "Waterproof Jacket", "price_usd": 250}
            ]
            mock_search_class.return_value = mock_search

            orchestrator = Orchestrator(use_llm=False)
            result = orchestrator.process_query("Show me waterproof jackets")

            assert result.intent == QueryIntent.PRODUCT_SEARCH
            assert len(result.products) > 0

    def test_visual_agent_formats_orchestrator_results(self, sample_products):
        """Test: visual agent can format orchestrator results."""
        visual_agent = VisualAgent()

        # Simulate orchestrator returning products
        products = sample_products[:3]

        # Visual agent formats them
        result = visual_agent.auto_visualize(products, intent="comparison")

        assert "|" in result  # Table format
        assert "Summit Pro Parka" in result or "Alpine" in result


# ============================================================================
# DATA PERSISTENCE TESTS
# ============================================================================

@pytest.mark.integration
class TestDataPersistence:
    """Integration tests for data persistence."""

    def test_preferences_persist_across_agent_instances(self, tmp_path):
        """Test: preferences saved by one agent instance are available to another."""
        storage_path = str(tmp_path / "persist_test.json")

        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            # Create first memory and agent
            memory1 = UserMemory(storage_path=storage_path)
            mock_get_memory.return_value = memory1

            agent1 = PersonalizationAgent(use_llm=False)
            agent1.save_user_preferences(
                user_id="persist_user",
                sizing={"fit": "relaxed"},
                permanent=True
            )

        # Create new memory and agent instance
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            memory2 = UserMemory(storage_path=storage_path)
            mock_get_memory.return_value = memory2

            agent2 = PersonalizationAgent(use_llm=False)

            # Should be able to retrieve saved preferences
            result = agent2.identify_user("persist_user")
            assert result["is_new"] is False

            prefs = agent2.get_user_preferences("persist_user")
            assert prefs["sizing"]["fit"] == "relaxed"

    def test_user_data_survives_memory_reload(self, tmp_path):
        """Test: user data survives memory instance reload."""
        storage_path = str(tmp_path / "reload_test.json")

        # First memory instance
        memory1 = UserMemory(storage_path=storage_path)
        memory1.save_preferences_bulk(
            user_id="reload_user",
            sizing={"fit": "slim"},
            general={"budget_max": 500},
            permanent=True
        )
        memory1.record_feedback("reload_user", "Too tight")

        # Reload memory from disk
        memory2 = UserMemory(storage_path=storage_path)

        # Verify all data present
        assert memory2.user_exists("reload_user")
        prefs = memory2.get_preferences("reload_user")
        assert prefs["sizing"]["fit"] == "slim"
        assert prefs["general"]["budget_max"] == 500

        signals = memory2.get_feedback_signals("reload_user")
        assert len(signals) > 0


# ============================================================================
# USER ISOLATION TESTS
# ============================================================================

@pytest.mark.integration
class TestUserIsolation:
    """Integration tests for user data isolation."""

    def test_multiple_users_data_isolated(self, temp_memory_file):
        """Test: different users' data is properly isolated."""
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            memory = UserMemory(storage_path=temp_memory_file)
            mock_get_memory.return_value = memory

            agent = PersonalizationAgent(use_llm=False)

            # Create preferences for user1
            agent.save_user_preferences(
                user_id="user1",
                sizing={"fit": "slim"},
                permanent=True
            )

            # Create different preferences for user2
            agent.save_user_preferences(
                user_id="user2",
                sizing={"fit": "oversized"},
                permanent=True
            )

            # Verify isolation
            user1_prefs = agent.get_user_preferences("user1")
            user2_prefs = agent.get_user_preferences("user2")

            assert user1_prefs["sizing"]["fit"] == "slim"
            assert user2_prefs["sizing"]["fit"] == "oversized"

    def test_feedback_isolated_between_users(self, temp_memory_file):
        """Test: feedback is isolated between users."""
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            memory = UserMemory(storage_path=temp_memory_file)
            mock_get_memory.return_value = memory

            agent = PersonalizationAgent(use_llm=False)

            # User1 gives feedback
            agent.process_feedback("user1", "Too tight")

            # User2 gives different feedback
            agent.process_feedback("user2", "Too flashy")

            # Verify signals are isolated
            user1_signals = memory.get_feedback_signals("user1")
            user2_signals = memory.get_feedback_signals("user2")

            assert any(s["value"] == "too_tight" for s in user1_signals)
            assert not any(s["value"] == "too_tight" for s in user2_signals)

            assert any(s["value"] == "bright_colors" for s in user2_signals)
            assert not any(s["value"] == "bright_colors" for s in user1_signals)


# ============================================================================
# END-TO-END WORKFLOW TESTS
# ============================================================================

@pytest.mark.integration
class TestEndToEndWorkflows:
    """End-to-end integration tests."""

    def test_full_new_user_to_recommendation_flow(self, temp_memory_file):
        """Test: complete flow from new user to getting personalized recommendation."""
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            memory = UserMemory(storage_path=temp_memory_file)
            mock_get_memory.return_value = memory

            agent = PersonalizationAgent(use_llm=False)
            visual = VisualAgent()

            # Step 1: Identify new user
            identify_result = agent.identify_user("complete_user")
            assert identify_result["is_new"] is True

            # Step 2: Save preferences
            agent.save_user_preferences(
                user_id="complete_user",
                sizing={"fit": "relaxed"},
                preferences={"outerwear": {"colors": ["blue"]}},
                general={"budget_max": 300},
                permanent=True
            )

            # Step 3: Get personalized recommendation
            rec_result = agent.get_personalized_recommendation(
                "I need hiking gear for cold weather",
                user_id="complete_user"
            )

            assert rec_result["success"] is True
            assert rec_result["preferences_applied"] is True

            context = rec_result["personalization_context"]
            assert context["activity"] == "hiking"
            assert context["weather"] == "cold"
            assert context["fit_preference"] == "relaxed"
            assert context["budget_max"] == 300

    def test_full_orchestrator_to_visualization_flow(self, sample_products):
        """Test: complete flow from orchestrator to visualization."""
        with patch('src.agents.orchestrator.ProductSearch') as mock_search_class:
            mock_search = MagicMock()
            mock_search.search_semantic.return_value = sample_products[:3]
            mock_search_class.return_value = mock_search

            orchestrator = Orchestrator(use_llm=False)
            visual = VisualAgent()

            # Step 1: Process query through orchestrator
            orch_result = orchestrator.process_query("Show me hiking jackets")

            # Step 2: Visualize results
            viz_output = visual.auto_visualize(
                orch_result.products,
                intent=orch_result.intent.value
            )

            assert viz_output is not None
            assert len(viz_output) > 0
