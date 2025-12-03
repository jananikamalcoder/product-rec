"""
Tests for UserMemory class (src/agents/memory.py).

Covers:
- Initialization and file I/O
- User CRUD operations
- Preference management (permanent vs session)
- Feedback recording and signal extraction
- Edge cases and error handling
"""

import json
import os
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock

import pytest

from src.agents.memory import UserMemory, get_memory


# ============================================================================
# INITIALIZATION AND FILE I/O TESTS
# ============================================================================

class TestUserMemoryInitialization:
    """Tests for UserMemory initialization and file handling."""

    def test_init_creates_empty_data_for_new_file(self, tmp_path):
        """UserMemory initializes with empty data when file doesn't exist."""
        file_path = tmp_path / "new_prefs.json"
        memory = UserMemory(storage_path=str(file_path))
        assert memory.data == {}
        assert memory.session_overrides == {}

    def test_init_loads_existing_valid_json(self, temp_memory_file_with_data):
        """UserMemory loads existing valid JSON file."""
        memory = UserMemory(storage_path=temp_memory_file_with_data)
        assert "sarah" in memory.data
        assert "john" in memory.data

    def test_init_handles_corrupted_json(self, corrupted_json_file):
        """UserMemory handles corrupted JSON gracefully."""
        memory = UserMemory(storage_path=corrupted_json_file)
        assert memory.data == {}

    def test_init_with_custom_path(self, tmp_path):
        """UserMemory accepts custom storage path."""
        custom_path = tmp_path / "custom" / "path" / "prefs.json"
        custom_path.parent.mkdir(parents=True, exist_ok=True)
        custom_path.write_text("{}")
        memory = UserMemory(storage_path=str(custom_path))
        assert memory.storage_path == custom_path

    def test_save_creates_file(self, tmp_path):
        """UserMemory._save() creates file if doesn't exist."""
        file_path = tmp_path / "new_prefs.json"
        memory = UserMemory(storage_path=str(file_path))
        memory.data = {"test": "data"}
        memory._save()
        assert file_path.exists()
        assert json.loads(file_path.read_text()) == {"test": "data"}

    def test_save_formats_json_with_indent(self, tmp_path):
        """UserMemory._save() formats JSON with indentation."""
        file_path = tmp_path / "formatted.json"
        memory = UserMemory(storage_path=str(file_path))
        memory.data = {"user": {"key": "value"}}
        memory._save()
        content = file_path.read_text()
        assert "\n" in content  # Indented formatting
        assert "  " in content  # 2-space indent


# ============================================================================
# USER EXISTENCE AND CREATION TESTS
# ============================================================================

class TestUserExistence:
    """Tests for user existence checking."""

    def test_user_exists_returns_false_for_new_user(self, memory):
        """user_exists() returns False for unknown user."""
        assert memory.user_exists("newuser") is False

    def test_user_exists_returns_true_for_existing_user(self, memory_with_data):
        """user_exists() returns True for known user."""
        assert memory_with_data.user_exists("sarah") is True

    def test_user_exists_is_case_insensitive(self, memory_with_data):
        """user_exists() is case-insensitive."""
        assert memory_with_data.user_exists("SARAH") is True
        assert memory_with_data.user_exists("Sarah") is True
        assert memory_with_data.user_exists("sArAh") is True

    def test_user_exists_strips_whitespace(self, memory_with_data):
        """user_exists() strips whitespace from user_id."""
        assert memory_with_data.user_exists("  sarah  ") is True
        assert memory_with_data.user_exists("\tsarah\n") is True

    def test_get_user_data_creates_structure_for_new_user(self, memory):
        """_get_user_data() creates proper structure for new users."""
        user_data = memory._get_user_data("newuser")
        assert "sizing" in user_data
        assert "preferences" in user_data
        assert "general" in user_data
        assert "feedback" in user_data
        assert "created_at" in user_data
        assert "last_seen" in user_data

    def test_get_user_data_normalizes_user_id(self, memory):
        """_get_user_data() normalizes user_id to lowercase."""
        memory._get_user_data("TestUser")
        assert "testuser" in memory.data
        assert "TestUser" not in memory.data


# ============================================================================
# GET PREFERENCES TESTS
# ============================================================================

class TestGetPreferences:
    """Tests for getting user preferences."""

    def test_get_preferences_returns_empty_for_new_user(self, memory):
        """get_preferences() returns empty dicts for new user."""
        prefs = memory.get_preferences("newuser")
        assert prefs["sizing"] == {}
        assert prefs["preferences"] == {}
        assert prefs["general"] == {}

    def test_get_preferences_returns_stored_data(self, memory_with_data):
        """get_preferences() returns stored preferences."""
        prefs = memory_with_data.get_preferences("sarah")
        assert prefs["sizing"]["fit"] == "relaxed"
        assert prefs["general"]["budget_max"] == 300

    def test_get_preferences_applies_session_overrides(self, memory_with_data):
        """get_preferences() merges session overrides (overrides take priority)."""
        memory_with_data.session_overrides["sarah"] = {
            "sizing": {"fit": "slim"},  # Override
            "preferences": {},
            "general": {}
        }
        prefs = memory_with_data.get_preferences("sarah")
        assert prefs["sizing"]["fit"] == "slim"  # Session override

    def test_get_preferences_session_override_partial_merge(self, memory_with_data):
        """Session overrides merge with stored, not replace entirely."""
        memory_with_data.session_overrides["sarah"] = {
            "sizing": {"fit": "oversized"},  # Only override fit
            "preferences": {},
            "general": {}
        }
        prefs = memory_with_data.get_preferences("sarah")
        assert prefs["sizing"]["fit"] == "oversized"  # Overridden
        assert prefs["sizing"]["shirt"] == "M"  # Kept from storage

    def test_get_preferences_updates_last_seen(self, memory_with_data):
        """get_preferences() updates last_seen timestamp."""
        original_last_seen = memory_with_data.data["sarah"]["last_seen"]
        memory_with_data.get_preferences("sarah")
        new_last_seen = memory_with_data.data["sarah"]["last_seen"]
        assert new_last_seen != original_last_seen

    def test_get_preferences_is_case_insensitive(self, memory_with_data):
        """get_preferences() is case-insensitive for user_id."""
        prefs = memory_with_data.get_preferences("SARAH")
        assert prefs["sizing"]["fit"] == "relaxed"


# ============================================================================
# GET PREFERENCES SUMMARY TESTS
# ============================================================================

class TestGetPreferencesSummary:
    """Tests for human-readable preference summaries."""

    def test_get_preferences_summary_returns_none_for_new_user(self, memory):
        """get_preferences_summary() returns None for non-existent user."""
        assert memory.get_preferences_summary("unknown") is None

    def test_get_preferences_summary_formats_sizing(self, memory_with_data):
        """get_preferences_summary() includes sizing info."""
        summary = memory_with_data.get_preferences_summary("sarah")
        assert "Fit: relaxed" in summary
        assert "Shirt: M" in summary

    def test_get_preferences_summary_formats_category_preferences(self, memory_with_data):
        """get_preferences_summary() includes category preferences."""
        summary = memory_with_data.get_preferences_summary("sarah")
        assert "Outerwear" in summary
        assert "blue" in summary or "Colors:" in summary

    def test_get_preferences_summary_formats_general_prefs(self, memory_with_data):
        """get_preferences_summary() includes general preferences."""
        summary = memory_with_data.get_preferences_summary("sarah")
        assert "Budget: under $300" in summary

    def test_get_preferences_summary_returns_none_for_empty_prefs(self, memory):
        """get_preferences_summary() returns None if no preferences saved."""
        memory._get_user_data("emptyuser")  # Create user with empty prefs
        summary = memory.get_preferences_summary("emptyuser")
        assert summary is None

    def test_get_preferences_summary_handles_list_colors(self, memory_with_data):
        """get_preferences_summary() handles colors as list."""
        summary = memory_with_data.get_preferences_summary("sarah")
        # Colors should be joined
        assert "blue" in summary


# ============================================================================
# UPDATE PREFERENCE TESTS
# ============================================================================

class TestUpdatePreference:
    """Tests for updating individual preferences."""

    def test_update_preference_permanent_sizing(self, memory):
        """update_preference() saves permanent sizing to disk."""
        memory.update_preference("testuser", "sizing", "fit", "relaxed", permanent=True)
        assert memory.data["testuser"]["sizing"]["fit"] == "relaxed"

    def test_update_preference_permanent_general(self, memory):
        """update_preference() saves permanent general prefs to disk."""
        memory.update_preference("testuser", "general", "budget_max", 500, permanent=True)
        assert memory.data["testuser"]["general"]["budget_max"] == 500

    def test_update_preference_permanent_category(self, memory):
        """update_preference() saves category-specific preferences."""
        memory.update_preference("testuser", "preferences", "colors", ["blue"],
                                permanent=True, category="outerwear")
        assert memory.data["testuser"]["preferences"]["outerwear"]["colors"] == ["blue"]

    def test_update_preference_session_only_sizing(self, memory):
        """update_preference() creates session override for non-permanent."""
        memory.update_preference("testuser", "sizing", "fit", "oversized", permanent=False)
        assert "testuser" in memory.session_overrides
        assert memory.session_overrides["testuser"]["sizing"]["fit"] == "oversized"
        # Should NOT be in permanent storage
        assert memory.data.get("testuser", {}).get("sizing", {}).get("fit") != "oversized"

    def test_update_preference_session_only_category(self, memory):
        """update_preference() creates session override for category prefs."""
        memory.update_preference("testuser", "preferences", "style", "colorful",
                                permanent=False, category="outerwear")
        assert memory.session_overrides["testuser"]["preferences"]["outerwear"]["style"] == "colorful"

    def test_update_preference_normalizes_user_id(self, memory):
        """update_preference() normalizes user_id."""
        memory.update_preference("TestUser", "sizing", "fit", "classic", permanent=True)
        assert "testuser" in memory.data


# ============================================================================
# SAVE PREFERENCES BULK TESTS
# ============================================================================

class TestSavePreferencesBulk:
    """Tests for bulk preference saving."""

    def test_save_preferences_bulk_all_sections(self, memory):
        """save_preferences_bulk() saves all sections at once."""
        memory.save_preferences_bulk(
            user_id="testuser",
            sizing={"fit": "relaxed", "shirt": "L"},
            preferences={"outerwear": {"colors": ["black"]}},
            general={"budget_max": 400},
            permanent=True
        )
        user_data = memory.data["testuser"]
        assert user_data["sizing"]["fit"] == "relaxed"
        assert user_data["sizing"]["shirt"] == "L"
        assert user_data["preferences"]["outerwear"]["colors"] == ["black"]
        assert user_data["general"]["budget_max"] == 400

    def test_save_preferences_bulk_partial(self, memory):
        """save_preferences_bulk() handles partial updates."""
        memory.save_preferences_bulk(user_id="testuser", sizing={"fit": "slim"}, permanent=True)
        assert memory.data["testuser"]["sizing"]["fit"] == "slim"

    def test_save_preferences_bulk_session_only(self, memory):
        """save_preferences_bulk() stores session-only overrides."""
        memory.save_preferences_bulk(
            user_id="testuser",
            sizing={"fit": "oversized"},
            permanent=False
        )
        assert memory.session_overrides["testuser"]["sizing"]["fit"] == "oversized"

    def test_save_preferences_bulk_merges_with_existing(self, memory_with_data):
        """save_preferences_bulk() merges with existing data."""
        memory_with_data.save_preferences_bulk(
            user_id="sarah",
            sizing={"shoes": "8"},  # Add new key
            permanent=True
        )
        assert memory_with_data.data["sarah"]["sizing"]["fit"] == "relaxed"  # Kept
        assert memory_with_data.data["sarah"]["sizing"]["shoes"] == "8"  # Added

    def test_save_preferences_bulk_none_parameters_ignored(self, memory):
        """save_preferences_bulk() ignores None parameters."""
        memory.save_preferences_bulk(
            user_id="testuser",
            sizing={"fit": "classic"},
            preferences=None,
            general=None,
            permanent=True
        )
        assert memory.data["testuser"]["sizing"]["fit"] == "classic"
        assert memory.data["testuser"]["preferences"] == {}


# ============================================================================
# FEEDBACK RECORDING TESTS
# ============================================================================

class TestRecordFeedback:
    """Tests for feedback recording and signal extraction."""

    def test_record_feedback_stores_entry(self, memory):
        """record_feedback() stores feedback entry."""
        memory.record_feedback("testuser", "This jacket is too tight")
        user_data = memory.data["testuser"]
        assert len(user_data["feedback"]) == 1
        assert user_data["feedback"][0]["text"] == "This jacket is too tight"

    def test_record_feedback_stores_context(self, memory):
        """record_feedback() stores context."""
        memory.record_feedback("testuser", "Too flashy", context="Summit Pro Parka")
        assert memory.data["testuser"]["feedback"][0]["context"] == "Summit Pro Parka"

    def test_record_feedback_extracts_tight_signal(self, memory):
        """record_feedback() extracts 'too_tight' signal."""
        signals = memory.record_feedback("testuser", "It's too tight")
        assert any(s["type"] == "fit_issue" and s["value"] == "too_tight" for s in signals)

    def test_record_feedback_extracts_loose_signal(self, memory):
        """record_feedback() extracts 'too_loose' signal."""
        signals = memory.record_feedback("testuser", "Way too loose and baggy")
        assert any(s["type"] == "fit_issue" and s["value"] == "too_loose" for s in signals)

    def test_record_feedback_extracts_flashy_signal(self, memory):
        """record_feedback() extracts 'bright_colors' avoid signal."""
        signals = memory.record_feedback("testuser", "Too flashy for me")
        assert any(s["type"] == "avoid_style" and s["value"] == "bright_colors" for s in signals)

    def test_record_feedback_extracts_boring_signal(self, memory):
        """record_feedback() extracts 'more_color' prefer signal."""
        signals = memory.record_feedback("testuser", "Too boring and plain")
        assert any(s["type"] == "prefer_style" and s["value"] == "more_color" for s in signals)

    def test_record_feedback_extracts_budget_signal(self, memory):
        """record_feedback() extracts budget signals."""
        signals = memory.record_feedback("testuser", "Way too expensive for me")
        assert any(s["type"] == "budget" and s["value"] == "lower_budget" for s in signals)

    def test_record_feedback_extracts_multiple_signals(self, memory):
        """record_feedback() extracts multiple signals from one feedback."""
        signals = memory.record_feedback("testuser", "Too tight and too flashy")
        assert len(signals) >= 2

    def test_record_feedback_no_signals_for_neutral(self, memory):
        """record_feedback() returns empty signals for neutral feedback."""
        signals = memory.record_feedback("testuser", "I like it, thanks!")
        assert signals == []

    def test_record_feedback_limits_to_50_entries(self, memory):
        """record_feedback() keeps only last 50 entries."""
        for i in range(60):
            memory.record_feedback("testuser", f"Feedback {i}")
        assert len(memory.data["testuser"]["feedback"]) == 50
        assert memory.data["testuser"]["feedback"][-1]["text"] == "Feedback 59"

    def test_record_feedback_adds_timestamp(self, memory):
        """record_feedback() adds timestamp to entry."""
        memory.record_feedback("testuser", "Test feedback")
        entry = memory.data["testuser"]["feedback"][0]
        assert "timestamp" in entry
        # Should be ISO format
        datetime.fromisoformat(entry["timestamp"])

    def test_record_feedback_case_insensitive_signals(self, memory):
        """record_feedback() signal extraction is case-insensitive."""
        signals = memory.record_feedback("testuser", "TOO TIGHT AND EXPENSIVE")
        assert any(s["type"] == "fit_issue" for s in signals)
        assert any(s["type"] == "budget" for s in signals)


# ============================================================================
# GET FEEDBACK SIGNALS TESTS
# ============================================================================

class TestGetFeedbackSignals:
    """Tests for aggregating feedback signals."""

    def test_get_feedback_signals_returns_empty_for_new_user(self, memory):
        """get_feedback_signals() returns empty for non-existent user."""
        signals = memory.get_feedback_signals("unknown")
        assert signals == []

    def test_get_feedback_signals_aggregates_all_signals(self, memory):
        """get_feedback_signals() aggregates signals from all feedback."""
        memory.record_feedback("testuser", "Too tight")
        memory.record_feedback("testuser", "Too flashy")
        signals = memory.get_feedback_signals("testuser")
        assert len(signals) >= 2

    def test_get_feedback_signals_is_case_insensitive(self, memory):
        """get_feedback_signals() is case-insensitive for user_id."""
        memory.record_feedback("testuser", "Too tight")
        signals = memory.get_feedback_signals("TESTUSER")
        assert len(signals) >= 1


# ============================================================================
# SESSION OVERRIDE MANAGEMENT TESTS
# ============================================================================

class TestSessionOverrides:
    """Tests for session override management."""

    def test_clear_session_overrides_removes_user(self, memory):
        """clear_session_overrides() removes user's session data."""
        memory.session_overrides["testuser"] = {"sizing": {"fit": "oversized"}}
        memory.clear_session_overrides("testuser")
        assert "testuser" not in memory.session_overrides

    def test_clear_session_overrides_handles_missing_user(self, memory):
        """clear_session_overrides() handles non-existent user gracefully."""
        memory.clear_session_overrides("unknown")  # Should not raise

    def test_clear_session_overrides_normalizes_user_id(self, memory):
        """clear_session_overrides() normalizes user_id."""
        memory.session_overrides["testuser"] = {"sizing": {"fit": "oversized"}}
        memory.clear_session_overrides("  TESTUSER  ")
        assert "testuser" not in memory.session_overrides


# ============================================================================
# DELETE USER TESTS
# ============================================================================

class TestDeleteUser:
    """Tests for user deletion."""

    def test_delete_user_removes_from_data(self, memory_with_data):
        """delete_user() removes user from permanent storage."""
        memory_with_data.delete_user("sarah")
        assert "sarah" not in memory_with_data.data

    def test_delete_user_removes_session_overrides(self, memory_with_data):
        """delete_user() also removes session overrides."""
        memory_with_data.session_overrides["sarah"] = {"sizing": {}}
        memory_with_data.delete_user("sarah")
        assert "sarah" not in memory_with_data.session_overrides

    def test_delete_user_handles_missing_user(self, memory):
        """delete_user() handles non-existent user gracefully."""
        memory.delete_user("unknown")  # Should not raise

    def test_delete_user_normalizes_user_id(self, memory_with_data):
        """delete_user() normalizes user_id."""
        memory_with_data.delete_user("  SARAH  ")
        assert "sarah" not in memory_with_data.data


# ============================================================================
# GLOBAL MEMORY INSTANCE TESTS
# ============================================================================

class TestGetMemory:
    """Tests for global memory instance."""

    def test_get_memory_returns_instance(self):
        """get_memory() returns UserMemory instance."""
        memory = get_memory()
        assert isinstance(memory, UserMemory)

    def test_get_memory_returns_singleton(self):
        """get_memory() returns same instance on subsequent calls."""
        memory1 = get_memory()
        memory2 = get_memory()
        assert memory1 is memory2


# ============================================================================
# EDGE CASE TESTS
# ============================================================================

class TestMemoryEdgeCases:
    """Edge case tests for UserMemory."""

    def test_empty_user_id(self, memory):
        """Empty user_id is handled (becomes empty string)."""
        memory._get_user_data("")
        assert "" in memory.data

    def test_whitespace_only_user_id(self, memory):
        """Whitespace-only user_id is handled."""
        memory._get_user_data("   ")
        assert "" in memory.data

    def test_unicode_user_id(self, memory, unicode_string):
        """Unicode user_id is accepted."""
        memory._get_user_data(unicode_string)
        assert unicode_string.lower().strip() in memory.data

    def test_very_long_user_id(self, memory, long_string):
        """Very long user_id is accepted."""
        memory._get_user_data(long_string)
        assert long_string.lower() in memory.data

    def test_special_characters_in_feedback(self, memory, special_characters):
        """Special characters in feedback are stored correctly."""
        memory.record_feedback("testuser", special_characters)
        assert memory.data["testuser"]["feedback"][0]["text"] == special_characters

    def test_none_value_in_preferences(self, memory):
        """None values can be stored in preferences."""
        memory.update_preference("testuser", "sizing", "fit", None, permanent=True)
        assert memory.data["testuser"]["sizing"]["fit"] is None

    def test_empty_string_value_in_preferences(self, memory):
        """Empty string values can be stored."""
        memory.update_preference("testuser", "sizing", "fit", "", permanent=True)
        assert memory.data["testuser"]["sizing"]["fit"] == ""

    def test_list_value_in_preferences(self, memory):
        """List values can be stored in preferences."""
        colors = ["blue", "black", "gray"]
        memory.update_preference("testuser", "general", "colors", colors, permanent=True)
        assert memory.data["testuser"]["general"]["colors"] == colors

    def test_nested_dict_in_preferences(self, memory):
        """Nested dict values can be stored."""
        nested = {"sub": {"nested": "value"}}
        memory.update_preference("testuser", "general", "complex", nested, permanent=True)
        assert memory.data["testuser"]["general"]["complex"] == nested

    def test_concurrent_access_simulation(self, tmp_path):
        """Simulate concurrent access (reload from disk)."""
        file_path = tmp_path / "concurrent.json"
        file_path.write_text("{}")

        memory1 = UserMemory(storage_path=str(file_path))
        memory2 = UserMemory(storage_path=str(file_path))

        memory1.update_preference("user1", "sizing", "fit", "slim", permanent=True)
        # Memory2 still has old data until reload
        assert "user1" not in memory2.data

        # Reload memory2
        memory2 = UserMemory(storage_path=str(file_path))
        assert memory2.data["user1"]["sizing"]["fit"] == "slim"


# ============================================================================
# INVARIANT TESTS
# ============================================================================

class TestMemoryInvariants:
    """Tests for system invariants."""

    def test_user_id_always_lowercase_in_storage(self, memory):
        """Invariant: user_id is always stored lowercase."""
        memory._get_user_data("MixedCaseUser")
        memory.update_preference("UPPERUSER", "sizing", "fit", "classic", permanent=True)
        memory.save_preferences_bulk(user_id="AnotherUser", sizing={"fit": "slim"}, permanent=True)

        for user_id in memory.data.keys():
            assert user_id == user_id.lower()

    def test_session_overrides_never_saved_to_disk(self, tmp_path):
        """Invariant: session overrides never persist to disk."""
        file_path = tmp_path / "invariant.json"
        file_path.write_text("{}")

        memory = UserMemory(storage_path=str(file_path))
        memory.update_preference("testuser", "sizing", "fit", "oversized", permanent=False)
        memory._save()

        # Reload and check
        disk_data = json.loads(file_path.read_text())
        assert disk_data.get("testuser", {}).get("sizing", {}).get("fit") != "oversized"

    def test_feedback_list_never_exceeds_50(self, memory):
        """Invariant: feedback list never exceeds 50 entries."""
        for i in range(100):
            memory.record_feedback("testuser", f"Feedback {i}")
        assert len(memory.data["testuser"]["feedback"]) <= 50

    def test_user_structure_always_has_required_keys(self, memory):
        """Invariant: user data always has required keys."""
        memory._get_user_data("newuser")
        required_keys = ["sizing", "preferences", "general", "feedback", "created_at", "last_seen"]
        for key in required_keys:
            assert key in memory.data["newuser"]
