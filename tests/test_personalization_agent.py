"""
Tests for PersonalizationAgent (src/agents/personalization_agent.py).

Covers:
- User identification (new vs returning)
- Preference management
- Feedback processing
- Context extraction from queries
- Styling recommendations
"""

import pytest
from unittest.mock import patch, MagicMock

from src.agents.personalization_agent import (
    PersonalizationAgent,
    PersonalizationContext,
    Activity,
    Weather,
    StylePreference,
    FitPreference,
    ACTIVITY_CATEGORIES,
    WEATHER_FEATURES,
    get_user_preferences,
    save_user_preferences,
    process_user_feedback,
    check_returning_user,
    get_returning_user_prompt
)
from src.agents.memory import UserMemory


# ============================================================================
# PERSONALIZATION AGENT INITIALIZATION TESTS
# ============================================================================

class TestPersonalizationAgentInit:
    """Tests for PersonalizationAgent initialization."""

    def test_init_with_llm_disabled(self, temp_memory_file):
        """Agent initializes with LLM disabled."""
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            mock_get_memory.return_value = UserMemory(storage_path=temp_memory_file)
            agent = PersonalizationAgent(use_llm=False)
            assert agent.use_llm is False

    def test_init_with_llm_enabled_but_unavailable(self, temp_memory_file):
        """Agent falls back to no LLM when not available."""
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            mock_get_memory.return_value = UserMemory(storage_path=temp_memory_file)
            with patch.dict('os.environ', {}, clear=True):
                agent = PersonalizationAgent(use_llm=True)
                # Should fall back to False when no API keys
                assert agent.use_llm is False

    def test_init_creates_memory_reference(self, temp_memory_file):
        """Agent creates memory reference."""
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            mock_memory = UserMemory(storage_path=temp_memory_file)
            mock_get_memory.return_value = mock_memory
            agent = PersonalizationAgent(use_llm=False)
            assert agent.memory is mock_memory


# ============================================================================
# USER IDENTIFICATION TESTS
# ============================================================================

class TestIdentifyUser:
    """Tests for user identification."""

    def test_identify_new_user(self, temp_memory_file):
        """identify_user() correctly identifies new user."""
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            mock_get_memory.return_value = UserMemory(storage_path=temp_memory_file)
            agent = PersonalizationAgent(use_llm=False)
            result = agent.identify_user("newuser")
            assert result["is_new"] is True
            assert result["user_id"] == "newuser"
            assert "Nice to meet you" in result["message"]

    def test_identify_returning_user(self, temp_memory_file_with_data):
        """identify_user() correctly identifies returning user."""
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            mock_get_memory.return_value = UserMemory(storage_path=temp_memory_file_with_data)
            agent = PersonalizationAgent(use_llm=False)
            result = agent.identify_user("sarah")
            assert result["is_new"] is False
            assert "Welcome back" in result["message"]

    def test_identify_user_returns_preferences_summary(self, temp_memory_file_with_data):
        """identify_user() includes preferences summary for returning user."""
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            mock_get_memory.return_value = UserMemory(storage_path=temp_memory_file_with_data)
            agent = PersonalizationAgent(use_llm=False)
            result = agent.identify_user("sarah")
            assert "preferences_summary" in result

    def test_identify_user_case_insensitive(self, temp_memory_file_with_data):
        """identify_user() is case-insensitive."""
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            mock_get_memory.return_value = UserMemory(storage_path=temp_memory_file_with_data)
            agent = PersonalizationAgent(use_llm=False)
            result = agent.identify_user("SARAH")
            assert result["is_new"] is False

    def test_identify_user_title_cases_name(self, temp_memory_file):
        """identify_user() title-cases name in message."""
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            mock_get_memory.return_value = UserMemory(storage_path=temp_memory_file)
            agent = PersonalizationAgent(use_llm=False)
            result = agent.identify_user("john")
            assert "John" in result["message"]


# ============================================================================
# RETURNING USER PROMPT TESTS
# ============================================================================

class TestGetReturningUserPrompt:
    """Tests for returning user prompt generation."""

    def test_returns_none_for_new_user(self, temp_memory_file):
        """get_returning_user_prompt() returns None for new user."""
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            mock_get_memory.return_value = UserMemory(storage_path=temp_memory_file)
            agent = PersonalizationAgent(use_llm=False)
            result = agent.get_returning_user_prompt("unknown")
            assert result is None

    def test_returns_prompt_for_returning_user(self, temp_memory_file_with_data):
        """get_returning_user_prompt() returns prompt for returning user."""
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            mock_get_memory.return_value = UserMemory(storage_path=temp_memory_file_with_data)
            agent = PersonalizationAgent(use_llm=False)
            result = agent.get_returning_user_prompt("sarah")
            assert result is not None
            assert "Welcome back" in result
            assert "Sarah" in result

    def test_prompt_includes_preferences(self, temp_memory_file_with_data):
        """get_returning_user_prompt() includes preference summary."""
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            mock_get_memory.return_value = UserMemory(storage_path=temp_memory_file_with_data)
            agent = PersonalizationAgent(use_llm=False)
            result = agent.get_returning_user_prompt("sarah")
            assert "relaxed" in result.lower() or "fit" in result.lower()

    def test_returns_none_for_user_without_prefs(self, temp_memory_file_with_data):
        """get_returning_user_prompt() returns None if user has no preferences."""
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            memory = UserMemory(storage_path=temp_memory_file_with_data)
            # John has minimal preferences
            memory.data["emptyprefs"] = {
                "sizing": {},
                "preferences": {},
                "general": {},
                "feedback": [],
                "created_at": "2025-01-01T00:00:00",
                "last_seen": "2025-01-01T00:00:00"
            }
            mock_get_memory.return_value = memory
            agent = PersonalizationAgent(use_llm=False)
            result = agent.get_returning_user_prompt("emptyprefs")
            assert result is None


# ============================================================================
# PREFERENCE MANAGEMENT TESTS
# ============================================================================

class TestPreferenceManagement:
    """Tests for preference management."""

    def test_get_user_preferences(self, temp_memory_file_with_data):
        """get_user_preferences() returns preferences."""
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            mock_get_memory.return_value = UserMemory(storage_path=temp_memory_file_with_data)
            agent = PersonalizationAgent(use_llm=False)
            prefs = agent.get_user_preferences("sarah")
            assert "sizing" in prefs
            assert prefs["sizing"]["fit"] == "relaxed"

    def test_save_user_preferences_permanent(self, temp_memory_file):
        """save_user_preferences() saves permanent preferences."""
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            memory = UserMemory(storage_path=temp_memory_file)
            mock_get_memory.return_value = memory
            agent = PersonalizationAgent(use_llm=False)
            result = agent.save_user_preferences(
                user_id="testuser",
                sizing={"fit": "classic"},
                permanent=True
            )
            assert result["success"] is True
            assert "permanently saved" in result["message"]

    def test_save_user_preferences_session(self, temp_memory_file):
        """save_user_preferences() saves session-only preferences."""
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            memory = UserMemory(storage_path=temp_memory_file)
            mock_get_memory.return_value = memory
            agent = PersonalizationAgent(use_llm=False)
            result = agent.save_user_preferences(
                user_id="testuser",
                sizing={"fit": "oversized"},
                permanent=False
            )
            assert result["success"] is True
            assert "session only" in result["message"]


# ============================================================================
# UPDATE SINGLE PREFERENCE TESTS
# ============================================================================

class TestUpdateSinglePreference:
    """Tests for updating single preferences."""

    def test_update_fit_preference(self, temp_memory_file):
        """update_single_preference() updates fit."""
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            memory = UserMemory(storage_path=temp_memory_file)
            mock_get_memory.return_value = memory
            agent = PersonalizationAgent(use_llm=False)
            result = agent.update_single_preference("testuser", "fit", "relaxed", permanent=True)
            assert result["success"] is True

    def test_update_shirt_size(self, temp_memory_file):
        """update_single_preference() updates shirt size."""
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            memory = UserMemory(storage_path=temp_memory_file)
            mock_get_memory.return_value = memory
            agent = PersonalizationAgent(use_llm=False)
            result = agent.update_single_preference("testuser", "shirt_size", "L", permanent=True)
            assert result["success"] is True

    def test_update_budget(self, temp_memory_file):
        """update_single_preference() updates budget."""
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            memory = UserMemory(storage_path=temp_memory_file)
            mock_get_memory.return_value = memory
            agent = PersonalizationAgent(use_llm=False)
            result = agent.update_single_preference("testuser", "budget_max", 500, permanent=True)
            assert result["success"] is True

    def test_update_category_specific_preference(self, temp_memory_file):
        """update_single_preference() updates category-specific preferences."""
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            memory = UserMemory(storage_path=temp_memory_file)
            mock_get_memory.return_value = memory
            agent = PersonalizationAgent(use_llm=False)
            result = agent.update_single_preference(
                "testuser", "colors", ["blue", "black"],
                category="outerwear", permanent=True
            )
            assert result["success"] is True

    def test_update_unknown_preference_without_category(self, temp_memory_file):
        """update_single_preference() fails for unknown type without category."""
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            memory = UserMemory(storage_path=temp_memory_file)
            mock_get_memory.return_value = memory
            agent = PersonalizationAgent(use_llm=False)
            result = agent.update_single_preference("testuser", "unknown_pref", "value")
            assert result["success"] is False


# ============================================================================
# FEEDBACK PROCESSING TESTS
# ============================================================================

class TestProcessFeedback:
    """Tests for feedback processing."""

    def test_process_feedback_records_and_extracts(self, temp_memory_file):
        """process_feedback() records feedback and extracts signals."""
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            memory = UserMemory(storage_path=temp_memory_file)
            mock_get_memory.return_value = memory
            agent = PersonalizationAgent(use_llm=False)
            result = agent.process_feedback("testuser", "Too tight")
            assert result["success"] is True
            assert result["feedback_recorded"] is True
            assert len(result["signals"]) > 0

    def test_process_feedback_generates_actions_for_tight(self, temp_memory_file):
        """process_feedback() generates actions for 'too tight'."""
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            memory = UserMemory(storage_path=temp_memory_file)
            mock_get_memory.return_value = memory
            agent = PersonalizationAgent(use_llm=False)
            result = agent.process_feedback("testuser", "Too tight")
            assert any("relaxed" in action.lower() for action in result["actions"])

    def test_process_feedback_generates_actions_for_flashy(self, temp_memory_file):
        """process_feedback() generates actions for 'too flashy'."""
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            memory = UserMemory(storage_path=temp_memory_file)
            mock_get_memory.return_value = memory
            agent = PersonalizationAgent(use_llm=False)
            result = agent.process_feedback("testuser", "Too flashy")
            assert any("neutral" in action.lower() or "muted" in action.lower() for action in result["actions"])

    def test_process_feedback_no_actions_for_positive(self, temp_memory_file):
        """process_feedback() has no actions for positive feedback."""
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            memory = UserMemory(storage_path=temp_memory_file)
            mock_get_memory.return_value = memory
            agent = PersonalizationAgent(use_llm=False)
            result = agent.process_feedback("testuser", "Perfect, I love it!")
            assert len(result["actions"]) == 0

    def test_process_feedback_with_context(self, temp_memory_file):
        """process_feedback() accepts context parameter."""
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            memory = UserMemory(storage_path=temp_memory_file)
            mock_get_memory.return_value = memory
            agent = PersonalizationAgent(use_llm=False)
            result = agent.process_feedback("testuser", "Too tight", context="Summit Pro Parka")
            assert result["success"] is True


# ============================================================================
# CONTEXT EXTRACTION TESTS
# ============================================================================

class TestExtractContext:
    """Tests for context extraction from queries."""

    def test_extract_activity_hiking(self, temp_memory_file):
        """extract_context() detects hiking activity."""
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            mock_get_memory.return_value = UserMemory(storage_path=temp_memory_file)
            agent = PersonalizationAgent(use_llm=False)
            context = agent.extract_context("I need gear for hiking")
            assert context.activity == Activity.HIKING

    def test_extract_activity_skiing(self, temp_memory_file):
        """extract_context() detects skiing activity."""
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            mock_get_memory.return_value = UserMemory(storage_path=temp_memory_file)
            agent = PersonalizationAgent(use_llm=False)
            context = agent.extract_context("Going skiing this weekend")
            assert context.activity == Activity.SKIING

    def test_extract_weather_cold(self, temp_memory_file):
        """extract_context() detects cold weather."""
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            mock_get_memory.return_value = UserMemory(storage_path=temp_memory_file)
            agent = PersonalizationAgent(use_llm=False)
            context = agent.extract_context("Need something warm for cold weather")
            assert context.weather == Weather.COLD

    def test_extract_weather_rainy(self, temp_memory_file):
        """extract_context() detects rainy weather."""
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            mock_get_memory.return_value = UserMemory(storage_path=temp_memory_file)
            agent = PersonalizationAgent(use_llm=False)
            context = agent.extract_context("Need a jacket for rainy days")
            assert context.weather == Weather.RAINY

    def test_extract_style_technical(self, temp_memory_file):
        """extract_context() detects technical style."""
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            mock_get_memory.return_value = UserMemory(storage_path=temp_memory_file)
            agent = PersonalizationAgent(use_llm=False)
            context = agent.extract_context("Looking for technical performance gear")
            assert context.style_preference == StylePreference.TECHNICAL

    def test_extract_fit_relaxed(self, temp_memory_file):
        """extract_context() detects relaxed fit."""
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            mock_get_memory.return_value = UserMemory(storage_path=temp_memory_file)
            agent = PersonalizationAgent(use_llm=False)
            context = agent.extract_context("I prefer relaxed comfortable fit")
            assert context.fit_preference == FitPreference.RELAXED

    def test_extract_gender_women(self, temp_memory_file):
        """extract_context() detects women's gender."""
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            mock_get_memory.return_value = UserMemory(storage_path=temp_memory_file)
            agent = PersonalizationAgent(use_llm=False)
            context = agent.extract_context("Looking for women's jackets")
            assert context.gender == "Women"

    def test_extract_gender_men(self, temp_memory_file):
        """extract_context() detects men's gender."""
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            mock_get_memory.return_value = UserMemory(storage_path=temp_memory_file)
            agent = PersonalizationAgent(use_llm=False)
            context = agent.extract_context("Men's hiking boots")
            assert context.gender == "Men"

    def test_extract_budget_with_dollar_sign(self, temp_memory_file):
        """extract_context() extracts budget with $ sign."""
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            mock_get_memory.return_value = UserMemory(storage_path=temp_memory_file)
            agent = PersonalizationAgent(use_llm=False)
            context = agent.extract_context("Something under $300")
            assert context.budget_max == 300.0

    def test_extract_budget_under_keyword(self, temp_memory_file):
        """extract_context() extracts budget with 'under' keyword."""
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            mock_get_memory.return_value = UserMemory(storage_path=temp_memory_file)
            agent = PersonalizationAgent(use_llm=False)
            context = agent.extract_context("Jacket under 200 please")
            assert context.budget_max == 200.0

    def test_extract_colors(self, temp_memory_file):
        """extract_context() extracts color preferences."""
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            mock_get_memory.return_value = UserMemory(storage_path=temp_memory_file)
            agent = PersonalizationAgent(use_llm=False)
            context = agent.extract_context("Looking for blue or black jackets")
            assert "blue" in context.colors_preferred
            assert "black" in context.colors_preferred

    def test_extract_brands(self, temp_memory_file):
        """extract_context() extracts brand preferences."""
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            mock_get_memory.return_value = UserMemory(storage_path=temp_memory_file)
            agent = PersonalizationAgent(use_llm=False)
            context = agent.extract_context("Show me NorthPeak jackets")
            assert "Northpeak" in context.brands_preferred

    def test_extract_context_stores_original_query(self, temp_memory_file):
        """extract_context() stores original query."""
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            mock_get_memory.return_value = UserMemory(storage_path=temp_memory_file)
            agent = PersonalizationAgent(use_llm=False)
            query = "I need hiking gear for cold weather"
            context = agent.extract_context(query)
            assert context.original_query == query

    def test_extract_context_case_insensitive(self, temp_memory_file):
        """extract_context() is case-insensitive."""
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            mock_get_memory.return_value = UserMemory(storage_path=temp_memory_file)
            agent = PersonalizationAgent(use_llm=False)
            context = agent.extract_context("HIKING in COLD weather")
            assert context.activity == Activity.HIKING
            assert context.weather == Weather.COLD


# ============================================================================
# CONTEXT MERGING WITH USER PREFERENCES TESTS
# ============================================================================

class TestContextMerging:
    """Tests for merging context with stored preferences."""

    def test_merge_applies_stored_fit(self, temp_memory_file_with_data):
        """extract_context() applies stored fit preference."""
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            mock_get_memory.return_value = UserMemory(storage_path=temp_memory_file_with_data)
            agent = PersonalizationAgent(use_llm=False)
            context = agent.extract_context("I need a jacket", user_id="sarah")
            assert context.fit_preference == FitPreference.RELAXED

    def test_merge_applies_stored_budget(self, temp_memory_file_with_data):
        """extract_context() applies stored budget."""
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            mock_get_memory.return_value = UserMemory(storage_path=temp_memory_file_with_data)
            agent = PersonalizationAgent(use_llm=False)
            context = agent.extract_context("Show me jackets", user_id="sarah")
            assert context.budget_max == 300

    def test_merge_query_overrides_stored(self, temp_memory_file_with_data):
        """Query values override stored preferences."""
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            mock_get_memory.return_value = UserMemory(storage_path=temp_memory_file_with_data)
            agent = PersonalizationAgent(use_llm=False)
            # Sarah has budget 300, but query specifies $500
            context = agent.extract_context("Something around $500", user_id="sarah")
            assert context.budget_max == 500.0

    def test_merge_identifies_returning_user(self, temp_memory_file_with_data):
        """extract_context() identifies returning user."""
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            mock_get_memory.return_value = UserMemory(storage_path=temp_memory_file_with_data)
            agent = PersonalizationAgent(use_llm=False)
            context = agent.extract_context("Show me jackets", user_id="sarah")
            assert context.is_returning_user is True

    def test_merge_identifies_new_user(self, temp_memory_file):
        """extract_context() identifies new user."""
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            mock_get_memory.return_value = UserMemory(storage_path=temp_memory_file)
            agent = PersonalizationAgent(use_llm=False)
            context = agent.extract_context("Show me jackets", user_id="newuser")
            assert context.is_returning_user is False


# ============================================================================
# PERSONALIZATION CONTEXT TESTS
# ============================================================================

class TestPersonalizationContext:
    """Tests for PersonalizationContext dataclass."""

    def test_context_defaults(self):
        """PersonalizationContext has correct defaults."""
        context = PersonalizationContext()
        assert context.user_id is None
        assert context.is_returning_user is False
        assert context.activity == Activity.UNKNOWN
        assert context.weather == Weather.UNKNOWN
        assert context.fit_preference == FitPreference.CLASSIC
        assert context.colors_preferred == []

    def test_context_to_dict(self):
        """PersonalizationContext.to_dict() serializes correctly."""
        context = PersonalizationContext(
            user_id="testuser",
            activity=Activity.HIKING,
            weather=Weather.COLD
        )
        result = context.to_dict()
        assert result["user_id"] == "testuser"
        assert result["activity"] == "hiking"
        assert result["weather"] == "cold"

    def test_context_to_dict_all_fields(self):
        """PersonalizationContext.to_dict() includes all fields."""
        context = PersonalizationContext()
        result = context.to_dict()
        expected_keys = [
            "user_id", "is_returning_user", "activity", "weather",
            "style_preference", "fit_preference", "gender", "budget_max",
            "colors_preferred", "colors_avoided", "brands_preferred",
            "shirt_size", "pants_size", "shoe_size", "specific_items",
            "occasion", "original_query"
        ]
        for key in expected_keys:
            assert key in result


# ============================================================================
# BUILD SEARCH PARAMETERS TESTS
# ============================================================================

class TestBuildSearchParameters:
    """Tests for building search parameters from context."""

    def test_build_search_parameters_includes_activity(self, temp_memory_file):
        """build_search_parameters() includes activity in query."""
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            mock_get_memory.return_value = UserMemory(storage_path=temp_memory_file)
            agent = PersonalizationAgent(use_llm=False)
            context = PersonalizationContext(activity=Activity.HIKING)
            params = agent.build_search_parameters(context)
            assert "hiking" in str(params).lower()

    def test_build_search_parameters_includes_weather_keywords(self, temp_memory_file):
        """build_search_parameters() includes weather keywords."""
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            mock_get_memory.return_value = UserMemory(storage_path=temp_memory_file)
            agent = PersonalizationAgent(use_llm=False)
            context = PersonalizationContext(activity=Activity.HIKING, weather=Weather.COLD)
            params = agent.build_search_parameters(context)
            # Should include cold weather keywords
            assert any("warm" in str(s).lower() or "insulated" in str(s).lower()
                      for s in params.get("outfit_searches", []))

    def test_build_search_parameters_applies_filters(self, temp_memory_file):
        """build_search_parameters() applies user filters."""
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            mock_get_memory.return_value = UserMemory(storage_path=temp_memory_file)
            agent = PersonalizationAgent(use_llm=False)
            context = PersonalizationContext(
                activity=Activity.HIKING,
                gender="Women",
                budget_max=300
            )
            params = agent.build_search_parameters(context)
            # Check filters in outfit_searches
            for search in params.get("outfit_searches", []):
                filters = search.get("filters", {})
                if "gender" in filters:
                    assert filters["gender"] == "Women"


# ============================================================================
# PERSONALIZED RECOMMENDATION TESTS
# ============================================================================

class TestGetPersonalizedRecommendation:
    """Tests for personalized recommendations."""

    def test_get_personalized_recommendation_returns_context(self, temp_memory_file):
        """get_personalized_recommendation() returns personalization context."""
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            mock_get_memory.return_value = UserMemory(storage_path=temp_memory_file)
            agent = PersonalizationAgent(use_llm=False)
            result = agent.get_personalized_recommendation("hiking gear")
            assert "personalization_context" in result
            assert "search_parameters" in result

    def test_get_personalized_recommendation_with_user(self, temp_memory_file_with_data):
        """get_personalized_recommendation() applies user preferences."""
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            mock_get_memory.return_value = UserMemory(storage_path=temp_memory_file_with_data)
            agent = PersonalizationAgent(use_llm=False)
            result = agent.get_personalized_recommendation("hiking gear", user_id="sarah")
            assert result["preferences_applied"] is True

    def test_get_personalized_recommendation_success_flag(self, temp_memory_file):
        """get_personalized_recommendation() returns success flag."""
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            mock_get_memory.return_value = UserMemory(storage_path=temp_memory_file)
            agent = PersonalizationAgent(use_llm=False)
            result = agent.get_personalized_recommendation("jackets")
            assert result["success"] is True


# ============================================================================
# CONVENIENCE FUNCTION TESTS
# ============================================================================

class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_get_user_preferences_function(self, temp_memory_file_with_data):
        """get_user_preferences() convenience function works."""
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            mock_get_memory.return_value = UserMemory(storage_path=temp_memory_file_with_data)
            prefs = get_user_preferences("sarah")
            assert "sizing" in prefs

    def test_save_user_preferences_function(self, temp_memory_file):
        """save_user_preferences() convenience function works."""
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            mock_get_memory.return_value = UserMemory(storage_path=temp_memory_file)
            result = save_user_preferences("testuser", sizing={"fit": "slim"}, permanent=True)
            assert result["success"] is True

    def test_process_user_feedback_function(self, temp_memory_file):
        """process_user_feedback() convenience function works."""
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            mock_get_memory.return_value = UserMemory(storage_path=temp_memory_file)
            result = process_user_feedback("testuser", "Too tight")
            assert result["success"] is True

    def test_check_returning_user_function(self, temp_memory_file_with_data):
        """check_returning_user() convenience function works."""
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            mock_get_memory.return_value = UserMemory(storage_path=temp_memory_file_with_data)
            result = check_returning_user("sarah")
            assert result["is_new"] is False

    def test_get_returning_user_prompt_function(self, temp_memory_file_with_data):
        """get_returning_user_prompt() convenience function works."""
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            mock_get_memory.return_value = UserMemory(storage_path=temp_memory_file_with_data)
            result = get_returning_user_prompt("sarah")
            assert result is not None


# ============================================================================
# EDGE CASE TESTS
# ============================================================================

class TestPersonalizationAgentEdgeCases:
    """Edge case tests for PersonalizationAgent."""

    def test_empty_query(self, temp_memory_file):
        """extract_context() handles empty query."""
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            mock_get_memory.return_value = UserMemory(storage_path=temp_memory_file)
            agent = PersonalizationAgent(use_llm=False)
            context = agent.extract_context("")
            assert context.activity == Activity.UNKNOWN
            assert context.weather == Weather.UNKNOWN

    def test_very_long_query(self, temp_memory_file, long_string):
        """extract_context() handles very long query."""
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            mock_get_memory.return_value = UserMemory(storage_path=temp_memory_file)
            agent = PersonalizationAgent(use_llm=False)
            context = agent.extract_context(long_string)
            assert context is not None

    def test_special_characters_in_query(self, temp_memory_file, special_characters):
        """extract_context() handles special characters."""
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            mock_get_memory.return_value = UserMemory(storage_path=temp_memory_file)
            agent = PersonalizationAgent(use_llm=False)
            context = agent.extract_context(special_characters)
            assert context is not None

    def test_none_user_id(self, temp_memory_file):
        """extract_context() handles None user_id."""
        with patch('src.agents.personalization_agent.get_memory') as mock_get_memory:
            mock_get_memory.return_value = UserMemory(storage_path=temp_memory_file)
            agent = PersonalizationAgent(use_llm=False)
            context = agent.extract_context("hiking gear", user_id=None)
            assert context.user_id is None


# ============================================================================
# ACTIVITY AND WEATHER MAPPING TESTS
# ============================================================================

class TestActivityWeatherMappings:
    """Tests for activity and weather mapping constants."""

    def test_all_activities_have_categories(self):
        """All Activity enum values have category mappings."""
        for activity in Activity:
            if activity != Activity.UNKNOWN:
                assert activity in ACTIVITY_CATEGORIES

    def test_activity_categories_have_required_keys(self):
        """Activity categories have required and optional keys."""
        for activity, config in ACTIVITY_CATEGORIES.items():
            assert "required" in config
            assert "optional" in config

    def test_all_weathers_have_features(self):
        """Most Weather enum values have feature mappings."""
        mapped_weathers = [w for w in Weather if w in WEATHER_FEATURES]
        assert len(mapped_weathers) > 5  # Most should be mapped

    def test_weather_features_have_keywords(self):
        """Weather features have keywords."""
        for weather, config in WEATHER_FEATURES.items():
            assert "keywords" in config
