"""
User Memory - Local JSON-based persistent storage for user preferences.

Stores user preferences with intent-aware updates:
- Permanent preferences: Saved to disk, persist across sessions
- Session overrides: Temporary changes for current session only

Example usage:
    memory = UserMemory()

    # Get user preferences
    prefs = memory.get_preferences("sarah")

    # Update permanent preference
    memory.update_preference("sarah", "sizing", "fit", "classic", permanent=True)

    # Session-only override
    memory.update_preference("sarah", "sizing", "fit", "relaxed", permanent=False)
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List


class UserMemory:
    """
    Manages user preferences with local JSON storage.

    Supports:
    - Permanent preferences (persisted to disk)
    - Session overrides (temporary, not saved)
    - Feedback history
    - Category-specific preferences (outerwear colors ≠ footwear colors)
    """

    def __init__(self, storage_path: str = "data/user_preferences.json"):
        """
        Initialize UserMemory.

        Args:
            storage_path: Path to JSON file for persistent storage
        """
        self.storage_path = Path(storage_path)
        self.data = self._load()
        self.session_overrides: Dict[str, Dict[str, Any]] = {}  # Not persisted

    def _load(self) -> Dict[str, Any]:
        """Load preferences from disk."""
        if self.storage_path.exists():
            try:
                return json.loads(self.storage_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, IOError, PermissionError) as e:
                print(f"Warning: Could not load {self.storage_path}: {e}, starting fresh")
                return {}
        return {}

    def _save(self):
        """Save preferences to disk."""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.storage_path.write_text(json.dumps(self.data, indent=2), encoding="utf-8")

    def _get_user_data(self, user_id: str) -> Dict[str, Any]:
        """Get or create user data structure."""
        user_id = user_id.lower().strip()
        if user_id not in self.data:
            self.data[user_id] = {
                "sizing": {},
                "preferences": {},
                "general": {},
                "feedback": [],
                "created_at": datetime.now().isoformat(),
                "last_seen": datetime.now().isoformat()
            }
        return self.data[user_id]

    def user_exists(self, user_id: str) -> bool:
        """Check if user has saved preferences."""
        return user_id.lower().strip() in self.data

    def get_preferences(self, user_id: str) -> Dict[str, Any]:
        """
        Get user preferences with session overrides applied.

        Session overrides take priority over permanent preferences.

        Args:
            user_id: User identifier

        Returns:
            Merged preferences dict
        """
        user_id = user_id.lower().strip()
        user_data = self._get_user_data(user_id)

        # Update last seen
        user_data["last_seen"] = datetime.now().isoformat()
        self._save()

        # Merge with session overrides (overrides take priority)
        result = {
            "sizing": {**user_data.get("sizing", {})},
            "preferences": {},
            "general": {**user_data.get("general", {})}
        }

        # Deep merge preferences by category
        for category, prefs in user_data.get("preferences", {}).items():
            result["preferences"][category] = {**prefs}

        # Apply session overrides
        if user_id in self.session_overrides:
            overrides = self.session_overrides[user_id]

            if "sizing" in overrides:
                result["sizing"].update(overrides["sizing"])
            if "general" in overrides:
                result["general"].update(overrides["general"])
            if "preferences" in overrides:
                for category, prefs in overrides["preferences"].items():
                    if category not in result["preferences"]:
                        result["preferences"][category] = {}
                    result["preferences"][category].update(prefs)

        return result

    def get_preferences_summary(self, user_id: str) -> Optional[str]:
        """
        Get a human-readable summary of user preferences.

        Args:
            user_id: User identifier

        Returns:
            Formatted string summary, or None if no preferences
        """
        if not self.user_exists(user_id):
            return None

        prefs = self.get_preferences(user_id)
        parts = []

        # Sizing
        sizing = prefs.get("sizing", {})
        if sizing:
            sizing_parts = []
            if sizing.get("fit"):
                sizing_parts.append(f"Fit: {sizing['fit']}")
            if sizing.get("shirt"):
                sizing_parts.append(f"Shirt: {sizing['shirt']}")
            if sizing.get("pants"):
                sizing_parts.append(f"Pants: {sizing['pants']}")
            if sizing.get("shoes"):
                sizing_parts.append(f"Shoes: {sizing['shoes']}")
            if sizing_parts:
                parts.append("**Sizing:** " + ", ".join(sizing_parts))

        # Category preferences
        for category, cat_prefs in prefs.get("preferences", {}).items():
            cat_parts = []
            if cat_prefs.get("colors"):
                colors = cat_prefs["colors"]
                if isinstance(colors, list):
                    cat_parts.append(f"Colors: {', '.join(colors)}")
                else:
                    cat_parts.append(f"Colors: {colors}")
            if cat_prefs.get("style"):
                cat_parts.append(f"Style: {cat_prefs['style']}")
            if cat_parts:
                parts.append(f"**{category.title()}:** " + ", ".join(cat_parts))

        # General
        general = prefs.get("general", {})
        if general:
            gen_parts = []
            if general.get("budget_max"):
                gen_parts.append(f"Budget: under ${general['budget_max']}")
            if general.get("brands_liked"):
                brands = general["brands_liked"]
                if isinstance(brands, list):
                    gen_parts.append(f"Preferred brands: {', '.join(brands)}")
            if gen_parts:
                parts.append("**General:** " + ", ".join(gen_parts))

        if not parts:
            return None

        return "\n".join(parts)

    def update_preference(
        self,
        user_id: str,
        section: str,
        key: str,
        value: Any,
        permanent: bool = True,
        category: Optional[str] = None
    ):
        """
        Update a user preference.

        Args:
            user_id: User identifier
            section: One of "sizing", "preferences", "general"
            key: Preference key (e.g., "fit", "colors", "budget_max")
            value: New value
            permanent: If True, save to disk. If False, session-only.
            category: For section="preferences", the category (e.g., "outerwear")
        """
        user_id = user_id.lower().strip()

        if permanent:
            user_data = self._get_user_data(user_id)

            if section == "preferences" and category:
                if category not in user_data["preferences"]:
                    user_data["preferences"][category] = {}
                user_data["preferences"][category][key] = value
            elif section in ["sizing", "general"]:
                user_data[section][key] = value

            self._save()
        else:
            # Session override
            if user_id not in self.session_overrides:
                self.session_overrides[user_id] = {
                    "sizing": {},
                    "preferences": {},
                    "general": {}
                }

            if section == "preferences" and category:
                if category not in self.session_overrides[user_id]["preferences"]:
                    self.session_overrides[user_id]["preferences"][category] = {}
                self.session_overrides[user_id]["preferences"][category][key] = value
            elif section in ["sizing", "general"]:
                self.session_overrides[user_id][section][key] = value

    def save_preferences_bulk(
        self,
        user_id: str,
        sizing: Optional[Dict[str, Any]] = None,
        preferences: Optional[Dict[str, Dict[str, Any]]] = None,
        general: Optional[Dict[str, Any]] = None,
        permanent: bool = True
    ):
        """
        Save multiple preferences at once.

        Args:
            user_id: User identifier
            sizing: Sizing preferences dict
            preferences: Category preferences dict
            general: General preferences dict
            permanent: If True, save to disk
        """
        user_id = user_id.lower().strip()

        if permanent:
            user_data = self._get_user_data(user_id)

            if sizing:
                user_data["sizing"].update(sizing)
            if preferences:
                for category, prefs in preferences.items():
                    if category not in user_data["preferences"]:
                        user_data["preferences"][category] = {}
                    user_data["preferences"][category].update(prefs)
            if general:
                user_data["general"].update(general)

            self._save()
        else:
            if user_id not in self.session_overrides:
                self.session_overrides[user_id] = {
                    "sizing": {},
                    "preferences": {},
                    "general": {}
                }

            if sizing:
                self.session_overrides[user_id]["sizing"].update(sizing)
            if preferences:
                for category, prefs in preferences.items():
                    if category not in self.session_overrides[user_id]["preferences"]:
                        self.session_overrides[user_id]["preferences"][category] = {}
                    self.session_overrides[user_id]["preferences"][category].update(prefs)
            if general:
                self.session_overrides[user_id]["general"].update(general)

    def record_feedback(self, user_id: str, feedback_text: str, context: Optional[str] = None):
        """
        Record natural language feedback and extract preference signals.

        Parses feedback like "too flashy" or "too expensive" into actionable signals.

        Args:
            user_id: User identifier
            feedback_text: Natural language feedback
            context: Optional context (e.g., what product/recommendation)
        """
        user_id = user_id.lower().strip()
        user_data = self._get_user_data(user_id)

        feedback_lower = feedback_text.lower()

        # Extract signals from feedback
        signals = []

        # Color/style signals
        if "flashy" in feedback_lower or "bright" in feedback_lower:
            signals.append({"type": "avoid_style", "value": "bright_colors"})
        if "boring" in feedback_lower or "plain" in feedback_lower:
            signals.append({"type": "prefer_style", "value": "more_color"})
        if "loud" in feedback_lower:
            signals.append({"type": "avoid_style", "value": "bold_patterns"})

        # Fit signals
        if "tight" in feedback_lower:
            signals.append({"type": "fit_issue", "value": "too_tight"})
        if "loose" in feedback_lower or "baggy" in feedback_lower:
            signals.append({"type": "fit_issue", "value": "too_loose"})
        if "short" in feedback_lower:
            signals.append({"type": "fit_issue", "value": "too_short"})
        if "long" in feedback_lower:
            signals.append({"type": "fit_issue", "value": "too_long"})

        # Budget signals
        if "expensive" in feedback_lower or "pricey" in feedback_lower:
            signals.append({"type": "budget", "value": "lower_budget"})
        if "cheap" in feedback_lower:
            signals.append({"type": "budget", "value": "higher_quality"})

        # Store feedback with signals
        feedback_entry = {
            "text": feedback_text,
            "context": context,
            "signals": signals,
            "timestamp": datetime.now().isoformat()
        }

        user_data["feedback"].append(feedback_entry)

        # Keep only last 50 feedback entries
        if len(user_data["feedback"]) > 50:
            user_data["feedback"] = user_data["feedback"][-50:]

        self._save()

        return signals

    def get_feedback_signals(self, user_id: str) -> List[Dict[str, str]]:
        """
        Get aggregated feedback signals for a user.

        Returns:
            List of signal dicts with type and value
        """
        user_id = user_id.lower().strip()
        if not self.user_exists(user_id):
            return []

        user_data = self.data[user_id]
        all_signals = []

        for feedback in user_data.get("feedback", []):
            all_signals.extend(feedback.get("signals", []))

        return all_signals

    def clear_session_overrides(self, user_id: str):
        """Clear session overrides for a user."""
        user_id = user_id.lower().strip()
        if user_id in self.session_overrides:
            del self.session_overrides[user_id]

    def delete_user(self, user_id: str):
        """Delete all data for a user."""
        user_id = user_id.lower().strip()
        if user_id in self.data:
            del self.data[user_id]
            self._save()
        if user_id in self.session_overrides:
            del self.session_overrides[user_id]

    def reset_all(self):
        """Delete all user data and reset to empty state."""
        self.data = {}
        self.session_overrides = {}
        self._save()

    def list_users(self) -> List[str]:
        """List all user IDs in memory."""
        return list(self.data.keys())


# Global instance for easy access
_memory_instance: Optional[UserMemory] = None


def get_memory() -> UserMemory:
    """Get or create the global UserMemory instance."""
    global _memory_instance
    if _memory_instance is None:
        _memory_instance = UserMemory()
    return _memory_instance


def reset_memory():
    """Reset all user data in the global memory instance."""
    memory = get_memory()
    memory.reset_all()
    return {"success": True, "message": "All user data has been reset"}
