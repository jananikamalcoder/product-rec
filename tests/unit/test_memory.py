"""
Unit tests for UserMemory - JSON-based user preference storage.

Tests the non-LLM memory component that handles:
- User creation and existence checking
- Preference save/load with permanent vs session-only modes
- Feedback signal extraction
- JSON persistence and recovery
"""

import pytest
import os
import json


class TestUserCreation:
    """Tests for user creation and existence checking."""

    def test_new_user_creation(self, memory_instance):
        """Create new user, verify structure."""
        user_id = "new_test_user"

        # Get preferences triggers user creation
        prefs = memory_instance.get_preferences(user_id)

        assert "sizing" in prefs
        assert "preferences" in prefs
        assert "general" in prefs
        assert prefs["sizing"] == {}
        assert prefs["preferences"] == {}
        assert prefs["general"] == {}

    def test_user_exists_check(self, memory_instance, test_user_id):
        """Check existing vs non-existing users."""
        # Non-existing user
        assert memory_instance.user_exists("nonexistent_user") is False

        # Create user
        memory_instance.get_preferences(test_user_id)

        # Now user exists
        assert memory_instance.user_exists(test_user_id) is True

    def test_user_id_normalization(self, memory_instance):
        """User IDs should be normalized (lowercase, stripped)."""
        memory_instance.save_preferences_bulk(
            user_id="  TestUser  ",
            sizing={"fit": "slim"}
        )

        # Should find with normalized ID
        assert memory_instance.user_exists("testuser") is True
        prefs = memory_instance.get_preferences("TESTUSER")
        assert prefs["sizing"]["fit"] == "slim"


class TestPreferenceSaving:
    """Tests for preference save operations."""

    def test_preference_save_permanent(self, memory_instance, test_user_id, temp_storage_path):
        """Save with permanent=True should write to JSON file."""
        memory_instance.save_preferences_bulk(
            user_id=test_user_id,
            sizing={"fit": "classic"},
            permanent=True
        )

        # Verify written to disk
        with open(temp_storage_path) as f:
            data = json.load(f)

        assert test_user_id in data
        assert data[test_user_id]["sizing"]["fit"] == "classic"

    def test_preference_save_session(self, memory_instance, test_user_id, temp_storage_path):
        """Save with permanent=False should only be in session_overrides."""
        # First save permanent preference
        memory_instance.save_preferences_bulk(
            user_id=test_user_id,
            sizing={"fit": "classic"},
            permanent=True
        )

        # Save session override
        memory_instance.save_preferences_bulk(
            user_id=test_user_id,
            sizing={"fit": "relaxed"},
            permanent=False
        )

        # Session override should be applied
        prefs = memory_instance.get_preferences(test_user_id)
        assert prefs["sizing"]["fit"] == "relaxed"

        # But permanent storage should still have original
        with open(temp_storage_path) as f:
            data = json.load(f)
        assert data[test_user_id]["sizing"]["fit"] == "classic"

    def test_session_override_merge(self, memory_with_user, test_user_id):
        """Session overrides should merge with permanent preferences."""
        # Add session override for fit only
        memory_with_user.save_preferences_bulk(
            user_id=test_user_id,
            sizing={"fit": "slim"},
            permanent=False
        )

        prefs = memory_with_user.get_preferences(test_user_id)

        # Fit should be overridden
        assert prefs["sizing"]["fit"] == "slim"
        # Shirt should still be from permanent
        assert prefs["sizing"]["shirt"] == "L"

    def test_bulk_preferences_save(self, memory_instance, test_user_id):
        """Save multiple preference categories at once."""
        memory_instance.save_preferences_bulk(
            user_id=test_user_id,
            sizing={"fit": "relaxed", "shirt": "M", "pants": "32"},
            preferences={
                "outerwear": {"colors": ["blue", "green"], "style": "technical"},
                "footwear": {"colors": ["black"]}
            },
            general={"budget_max": 500, "brands_liked": ["NorthPeak", "AlpineCo"]}
        )

        prefs = memory_instance.get_preferences(test_user_id)

        assert prefs["sizing"]["fit"] == "relaxed"
        assert prefs["sizing"]["shirt"] == "M"
        assert prefs["sizing"]["pants"] == "32"
        assert prefs["preferences"]["outerwear"]["colors"] == ["blue", "green"]
        assert prefs["preferences"]["outerwear"]["style"] == "technical"
        assert prefs["preferences"]["footwear"]["colors"] == ["black"]
        assert prefs["general"]["budget_max"] == 500
        assert "NorthPeak" in prefs["general"]["brands_liked"]


class TestFeedbackProcessing:
    """Tests for feedback signal extraction."""

    def test_feedback_signal_extraction_flashy(self, memory_instance, test_user_id):
        """'too flashy' should extract avoid_style signal."""
        signals = memory_instance.record_feedback(test_user_id, "too flashy")

        assert len(signals) >= 1
        assert any(s["type"] == "avoid_style" and s["value"] == "bright_colors" for s in signals)

    def test_feedback_signal_extraction_tight(self, memory_instance, test_user_id):
        """'too tight' should extract fit_issue signal."""
        signals = memory_instance.record_feedback(test_user_id, "too tight")

        assert len(signals) >= 1
        assert any(s["type"] == "fit_issue" and s["value"] == "too_tight" for s in signals)

    def test_feedback_signal_extraction_expensive(self, memory_instance, test_user_id):
        """'too expensive' should extract budget signal."""
        signals = memory_instance.record_feedback(test_user_id, "too expensive")

        assert len(signals) >= 1
        assert any(s["type"] == "budget" and s["value"] == "lower_budget" for s in signals)

    def test_feedback_limit_50(self, memory_instance, test_user_id):
        """Feedback should be limited to last 50 entries."""
        # Add 60 feedback entries
        for i in range(60):
            memory_instance.record_feedback(test_user_id, f"feedback {i}")

        user_data = memory_instance.data[test_user_id]
        assert len(user_data["feedback"]) == 50

        # Should keep the most recent
        assert "feedback 59" in user_data["feedback"][-1]["text"]


class TestPreferencesSummary:
    """Tests for preferences summary generation."""

    def test_preferences_summary_format(self, memory_with_user, test_user_id):
        """Summary should include sizing, budget, colors."""
        summary = memory_with_user.get_preferences_summary(test_user_id)

        assert summary is not None
        assert "Fit: relaxed" in summary
        assert "Shirt: L" in summary
        assert "blue" in summary.lower() or "black" in summary.lower()
        assert "$300" in summary

    def test_preferences_summary_nonexistent_user(self, memory_instance):
        """Summary for nonexistent user should return None."""
        summary = memory_instance.get_preferences_summary("nonexistent_user")
        assert summary is None


class TestUserDeletion:
    """Tests for user data deletion."""

    def test_user_deletion(self, memory_with_user, test_user_id):
        """Delete user data should remove from data."""
        assert memory_with_user.user_exists(test_user_id) is True

        memory_with_user.delete_user(test_user_id)

        assert memory_with_user.user_exists(test_user_id) is False


class TestJSONPersistence:
    """Tests for JSON file persistence and recovery."""

    def test_json_persistence(self, temp_storage_path):
        """Data should survive save, reload cycle."""
        from src.agents.memory import UserMemory

        # Create memory and save data
        memory1 = UserMemory(storage_path=temp_storage_path)
        memory1.save_preferences_bulk(
            user_id="persist_test",
            sizing={"fit": "slim"},
            general={"budget_max": 200}
        )

        # Create new memory instance (simulates restart)
        memory2 = UserMemory(storage_path=temp_storage_path)

        # Data should be loaded
        assert memory2.user_exists("persist_test") is True
        prefs = memory2.get_preferences("persist_test")
        assert prefs["sizing"]["fit"] == "slim"
        assert prefs["general"]["budget_max"] == 200

    def test_corrupted_json_recovery(self, corrupted_json_file):
        """Malformed JSON file should start fresh."""
        from src.agents.memory import UserMemory

        # Should not raise, starts fresh
        memory = UserMemory(storage_path=corrupted_json_file)

        assert memory.data == {}

        # Should be able to use normally
        memory.save_preferences_bulk(
            user_id="recovery_test",
            sizing={"fit": "classic"}
        )
        assert memory.user_exists("recovery_test") is True
