"""
Personalization Agent - User-aware styling and preference management.

This agent:
1. Remembers user preferences across sessions (sizing, colors, style, budget)
2. Asks for confirmation when returning users have saved preferences
3. Distinguishes between permanent preference updates and session-only overrides
4. Handles styling, fit/sizing, and feedback

Components:
- Styling: Outfit recommendations based on activity, weather, style
- Fit & Sizing: Size, fit, body shape, comfort preferences
- Feedback: Converts "too flashy", "too tight" into preference signals

Example interactions:
- New user: "What's your name?" → Gather preferences → Save
- Returning user: "Welcome back! Your preferences were X. Same or different?"
- Preference change: "Relaxed fit? Is this your new default or just for today?"
"""

import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

from .memory import get_memory, UserMemory


class Activity(Enum):
    """Supported activities for outfit recommendations."""
    HIKING = "hiking"
    SKIING = "skiing"
    CAMPING = "camping"
    RUNNING = "running"
    CLIMBING = "climbing"
    CASUAL = "casual"
    TRAVEL = "travel"
    EVERYDAY = "everyday"
    UNKNOWN = "unknown"


class Weather(Enum):
    """Weather conditions for outfit selection."""
    COLD = "cold"
    COOL = "cool"
    MILD = "mild"
    WARM = "warm"
    RAINY = "rainy"
    SNOWY = "snowy"
    WINDY = "windy"
    UNKNOWN = "unknown"


class StylePreference(Enum):
    """Style preferences for outfit selection."""
    TECHNICAL = "technical"
    CASUAL = "casual"
    STYLISH = "stylish"
    MINIMALIST = "minimalist"
    COLORFUL = "colorful"
    NEUTRAL = "neutral"


class FitPreference(Enum):
    """Fit preferences for apparel."""
    SLIM = "slim"
    CLASSIC = "classic"
    RELAXED = "relaxed"
    OVERSIZED = "oversized"


@dataclass
class PersonalizationContext:
    """Structured context combining styling intent and user preferences."""
    # User identity
    user_id: Optional[str] = None
    is_returning_user: bool = False

    # Styling context
    activity: Activity = Activity.UNKNOWN
    weather: Weather = Weather.UNKNOWN
    style_preference: StylePreference = StylePreference.NEUTRAL

    # User preferences (from memory or current session)
    fit_preference: FitPreference = FitPreference.CLASSIC
    gender: Optional[str] = None
    budget_max: Optional[float] = None
    colors_preferred: List[str] = field(default_factory=list)
    colors_avoided: List[str] = field(default_factory=list)
    brands_preferred: List[str] = field(default_factory=list)

    # Sizing
    shirt_size: Optional[str] = None
    pants_size: Optional[str] = None
    shoe_size: Optional[str] = None

    # Request details
    specific_items: List[str] = field(default_factory=list)
    occasion: Optional[str] = None
    original_query: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "user_id": self.user_id,
            "is_returning_user": self.is_returning_user,
            "activity": self.activity.value,
            "weather": self.weather.value,
            "style_preference": self.style_preference.value,
            "fit_preference": self.fit_preference.value,
            "gender": self.gender,
            "budget_max": self.budget_max,
            "colors_preferred": self.colors_preferred,
            "colors_avoided": self.colors_avoided,
            "brands_preferred": self.brands_preferred,
            "shirt_size": self.shirt_size,
            "pants_size": self.pants_size,
            "shoe_size": self.shoe_size,
            "specific_items": self.specific_items,
            "occasion": self.occasion,
            "original_query": self.original_query
        }


# Activity to product category mapping
ACTIVITY_CATEGORIES = {
    Activity.HIKING: {
        "required": ["Footwear", "Outerwear"],
        "optional": ["Apparel", "Accessories/Gear"],
        "subcategories": ["Hiking boots/shoes", "Shell Jackets", "Hiking Pants", "Backpacks"]
    },
    Activity.SKIING: {
        "required": ["Outerwear", "Footwear"],
        "optional": ["Accessories/Gear", "Apparel"],
        "subcategories": ["Ski Jackets", "Ski Pants", "Ski Boots", "Gloves", "Goggles"]
    },
    Activity.CAMPING: {
        "required": ["Outerwear", "Footwear"],
        "optional": ["Apparel", "Accessories/Gear"],
        "subcategories": ["Fleece Jackets", "Hiking boots/shoes", "Base Layers"]
    },
    Activity.RUNNING: {
        "required": ["Footwear", "Apparel"],
        "optional": ["Accessories/Gear"],
        "subcategories": ["Running Shoes", "Athletic Wear", "Lightweight Jackets"]
    },
    Activity.CLIMBING: {
        "required": ["Footwear", "Outerwear"],
        "optional": ["Accessories/Gear"],
        "subcategories": ["Climbing Shoes", "Shell Jackets", "Harnesses"]
    },
    Activity.CASUAL: {
        "required": ["Outerwear"],
        "optional": ["Footwear", "Apparel"],
        "subcategories": ["Casual Jackets", "Fleece", "Sneakers"]
    },
    Activity.TRAVEL: {
        "required": ["Outerwear", "Footwear"],
        "optional": ["Apparel", "Accessories/Gear"],
        "subcategories": ["Packable Jackets", "Comfortable Shoes", "Travel Pants"]
    },
    Activity.EVERYDAY: {
        "required": ["Outerwear"],
        "optional": ["Footwear", "Apparel"],
        "subcategories": ["Casual Jackets", "Everyday Shoes"]
    }
}

# Weather to product features mapping
WEATHER_FEATURES = {
    Weather.COLD: {
        "insulation": ["Down", "Synthetic", "Insulated"],
        "season": ["Winter"],
        "keywords": ["warm", "insulated", "thermal"]
    },
    Weather.COOL: {
        "insulation": ["Light Insulation", "Fleece"],
        "season": ["Fall", "Spring"],
        "keywords": ["layering", "mid-weight"]
    },
    Weather.MILD: {
        "insulation": ["None", "Light"],
        "season": ["Spring", "Fall", "All-season"],
        "keywords": ["breathable", "lightweight"]
    },
    Weather.WARM: {
        "insulation": ["None"],
        "season": ["Summer"],
        "keywords": ["ventilated", "moisture-wicking", "cooling"]
    },
    Weather.RAINY: {
        "waterproofing": ["Waterproof", "Water-resistant"],
        "keywords": ["rain", "waterproof", "sealed seams"]
    },
    Weather.SNOWY: {
        "waterproofing": ["Waterproof"],
        "insulation": ["Down", "Synthetic"],
        "season": ["Winter"],
        "keywords": ["snow", "winter", "warm"]
    },
    Weather.WINDY: {
        "keywords": ["windproof", "wind-resistant", "shell"]
    }
}


class PersonalizationAgent:
    """
    Agent that manages user preferences and provides personalized recommendations.

    Handles:
    - User identification and memory
    - Preference gathering and updates
    - Styling recommendations with personalization
    - Feedback processing
    """

    def __init__(self, use_llm: bool = True):
        """
        Initialize the Personalization Agent.

        Args:
            use_llm: Whether to use LLM for intent extraction
        """
        self.memory = get_memory()
        self.use_llm = use_llm and self._check_llm_available()
        self.llm_client = None

        if self.use_llm:
            self._init_llm_client()

    def _check_llm_available(self) -> bool:
        """Check if LLM API is available."""
        return bool(os.environ.get("GITHUB_TOKEN") or
                   os.environ.get("OPENAI_API_KEY") or
                   os.environ.get("AZURE_OPENAI_API_KEY"))

    def _init_llm_client(self):
        """Initialize the LLM client for intent extraction."""
        try:
            from openai import OpenAI

            if os.environ.get("GITHUB_TOKEN"):
                self.llm_client = OpenAI(
                    base_url="https://models.inference.ai.azure.com",
                    api_key=os.environ.get("GITHUB_TOKEN")
                )
                self.model = "gpt-4o-mini"
            elif os.environ.get("OPENAI_API_KEY"):
                self.llm_client = OpenAI()
                self.model = "gpt-4o-mini"
            else:
                self.use_llm = False
        except ImportError:
            self.use_llm = False

    # =========================================================================
    # User Management
    # =========================================================================

    def identify_user(self, user_id: str) -> Dict[str, Any]:
        """
        Identify user and return their status and preferences.

        Args:
            user_id: User's name/identifier

        Returns:
            Dict with is_new, preferences_summary, etc.
        """
        is_new = not self.memory.user_exists(user_id)

        if is_new:
            return {
                "is_new": True,
                "user_id": user_id,
                "message": f"Nice to meet you, {user_id.title()}! I'll remember your preferences."
            }

        # Returning user
        summary = self.memory.get_preferences_summary(user_id)
        return {
            "is_new": False,
            "user_id": user_id,
            "preferences_summary": summary,
            "message": f"Welcome back, {user_id.title()}!"
        }

    def get_returning_user_prompt(self, user_id: str) -> Optional[str]:
        """
        Generate a prompt asking returning user about their preferences.

        Args:
            user_id: User identifier

        Returns:
            Prompt string or None if new user
        """
        if not self.memory.user_exists(user_id):
            return None

        summary = self.memory.get_preferences_summary(user_id)
        if not summary:
            return None

        return f"""Welcome back, {user_id.title()}! Last time your preferences were:

{summary}

Do you want similar preferences today, or would you like to change anything (colors, fit, style, budget)?"""

    # =========================================================================
    # Preference Management
    # =========================================================================

    def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user preferences from memory."""
        return self.memory.get_preferences(user_id)

    def save_user_preferences(
        self,
        user_id: str,
        sizing: Optional[Dict[str, Any]] = None,
        preferences: Optional[Dict[str, Dict[str, Any]]] = None,
        general: Optional[Dict[str, Any]] = None,
        permanent: bool = True
    ) -> Dict[str, Any]:
        """
        Save user preferences.

        Args:
            user_id: User identifier
            sizing: Sizing preferences (fit, shirt, pants, shoes)
            preferences: Category-specific preferences (outerwear, footwear, etc.)
            general: General preferences (budget, brands)
            permanent: If True, save permanently. If False, session only.

        Returns:
            Confirmation dict
        """
        self.memory.save_preferences_bulk(
            user_id=user_id,
            sizing=sizing,
            preferences=preferences,
            general=general,
            permanent=permanent
        )

        persistence = "permanently saved" if permanent else "applied for this session only"
        return {
            "success": True,
            "user_id": user_id,
            "message": f"Preferences {persistence}.",
            "permanent": permanent
        }

    def update_single_preference(
        self,
        user_id: str,
        preference_type: str,
        value: Any,
        category: Optional[str] = None,
        permanent: bool = True
    ) -> Dict[str, Any]:
        """
        Update a single preference.

        Args:
            user_id: User identifier
            preference_type: Type of preference (fit, colors, style, budget, shirt_size, etc.)
            value: New value
            category: For category-specific prefs (outerwear, footwear, etc.)
            permanent: Permanent or session-only

        Returns:
            Confirmation dict
        """
        # Map preference types to storage structure
        sizing_keys = ["fit", "shirt_size", "pants_size", "shoe_size", "shirt", "pants", "shoes"]
        general_keys = ["budget_max", "budget", "brands_liked", "brands_preferred"]

        if preference_type in sizing_keys:
            # Normalize key names
            key = preference_type.replace("_size", "")
            self.memory.update_preference(user_id, "sizing", key, value, permanent)
        elif preference_type in general_keys:
            key = "budget_max" if "budget" in preference_type else preference_type
            if "brands" in preference_type:
                key = "brands_liked"
            self.memory.update_preference(user_id, "general", key, value, permanent)
        elif category:
            # Category-specific preference
            self.memory.update_preference(user_id, "preferences", preference_type, value, permanent, category)
        else:
            return {
                "success": False,
                "message": f"Unknown preference type: {preference_type}. Specify a category for style/color preferences."
            }

        persistence = "saved as new default" if permanent else "applied for this session"
        return {
            "success": True,
            "preference_type": preference_type,
            "value": value,
            "category": category,
            "message": f"{preference_type.replace('_', ' ').title()} {persistence}."
        }

    # =========================================================================
    # Feedback Processing
    # =========================================================================

    def process_feedback(self, user_id: str, feedback_text: str, context: Optional[str] = None) -> Dict[str, Any]:
        """
        Process natural language feedback and extract preference signals.

        Args:
            user_id: User identifier
            feedback_text: Natural language feedback like "too flashy" or "too tight"
            context: Optional context about what the feedback refers to

        Returns:
            Dict with extracted signals and suggested actions
        """
        signals = self.memory.record_feedback(user_id, feedback_text, context)

        # Generate response based on signals
        actions = []
        for signal in signals:
            if signal["type"] == "avoid_style" and signal["value"] == "bright_colors":
                actions.append("I'll recommend more neutral/muted colors")
            elif signal["type"] == "prefer_style" and signal["value"] == "more_color":
                actions.append("I'll show you more colorful options")
            elif signal["type"] == "fit_issue" and signal["value"] == "too_tight":
                actions.append("I'll suggest more relaxed fits")
            elif signal["type"] == "fit_issue" and signal["value"] == "too_loose":
                actions.append("I'll suggest slimmer fits")
            elif signal["type"] == "budget" and signal["value"] == "lower_budget":
                actions.append("I'll focus on more affordable options")

        return {
            "success": True,
            "feedback_recorded": True,
            "signals": signals,
            "actions": actions,
            "message": "Thanks for the feedback! " + " ".join(actions) if actions else "Feedback noted!"
        }

    # =========================================================================
    # Styling Context Extraction
    # =========================================================================

    def extract_context(self, query: str, user_id: Optional[str] = None) -> PersonalizationContext:
        """
        Extract personalization context from query, merging with user preferences.

        Args:
            query: User's natural language query
            user_id: Optional user identifier to load preferences

        Returns:
            PersonalizationContext with merged preferences
        """
        # Start with base context from query
        context = self._extract_from_query(query)
        context.original_query = query

        # Merge with user preferences if available
        if user_id:
            context.user_id = user_id
            context.is_returning_user = self.memory.user_exists(user_id)

            if context.is_returning_user:
                prefs = self.memory.get_preferences(user_id)
                context = self._merge_preferences(context, prefs)

        return context

    def _extract_from_query(self, query: str) -> PersonalizationContext:
        """Extract styling context from query using rules."""
        query_lower = query.lower()
        context = PersonalizationContext()

        # Extract activity
        activity_keywords = {
            Activity.HIKING: ["hiking", "hike", "trail", "trekking"],
            Activity.SKIING: ["skiing", "ski", "slopes", "alpine"],
            Activity.CAMPING: ["camping", "camp", "outdoors", "tent"],
            Activity.RUNNING: ["running", "run", "jogging", "marathon"],
            Activity.CLIMBING: ["climbing", "climb", "bouldering", "rock"],
            Activity.CASUAL: ["casual", "relaxed", "everyday wear"],
            Activity.TRAVEL: ["travel", "trip", "vacation", "flying"],
            Activity.EVERYDAY: ["everyday", "daily", "regular", "normal"]
        }
        for act, keywords in activity_keywords.items():
            if any(kw in query_lower for kw in keywords):
                context.activity = act
                break

        # Extract weather
        weather_keywords = {
            Weather.COLD: ["cold", "freezing", "winter", "frigid", "sub-zero"],
            Weather.COOL: ["cool", "chilly", "brisk", "fall", "autumn", "spring"],
            Weather.MILD: ["mild", "moderate", "pleasant", "temperate"],
            Weather.WARM: ["warm", "hot", "summer", "heat"],
            Weather.RAINY: ["rain", "rainy", "wet", "drizzle", "shower"],
            Weather.SNOWY: ["snow", "snowy", "blizzard", "powder"],
            Weather.WINDY: ["wind", "windy", "breezy", "gusty"]
        }
        for wth, keywords in weather_keywords.items():
            if any(kw in query_lower for kw in keywords):
                context.weather = wth
                break

        # Extract style preference
        style_keywords = {
            StylePreference.TECHNICAL: ["technical", "performance", "professional", "pro"],
            StylePreference.CASUAL: ["casual", "relaxed", "comfortable", "easy"],
            StylePreference.STYLISH: ["stylish", "fashionable", "trendy", "chic"],
            StylePreference.MINIMALIST: ["minimalist", "simple", "clean", "basic"],
            StylePreference.COLORFUL: ["colorful", "bright", "vibrant", "bold"]
        }
        for sty, keywords in style_keywords.items():
            if any(kw in query_lower for kw in keywords):
                context.style_preference = sty
                break

        # Extract fit preference
        fit_keywords = {
            FitPreference.SLIM: ["slim", "fitted", "tight", "athletic"],
            FitPreference.CLASSIC: ["classic", "regular", "standard"],
            FitPreference.RELAXED: ["relaxed", "loose", "comfortable"],
            FitPreference.OVERSIZED: ["oversized", "baggy", "roomy"]
        }
        for fit, keywords in fit_keywords.items():
            if any(kw in query_lower for kw in keywords):
                context.fit_preference = fit
                break

        # Extract gender
        if "women" in query_lower or "woman" in query_lower or "female" in query_lower:
            context.gender = "Women"
        elif "men" in query_lower or "man" in query_lower or "male" in query_lower:
            context.gender = "Men"
        elif "unisex" in query_lower:
            context.gender = "Unisex"

        # Extract budget
        import re
        budget_match = re.search(r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)', query)
        if budget_match:
            context.budget_max = float(budget_match.group(1).replace(",", ""))
        else:
            budget_match = re.search(r'under\s+(\d+)', query_lower)
            if budget_match:
                context.budget_max = float(budget_match.group(1))

        # Extract colors
        color_keywords = ["black", "blue", "red", "green", "gray", "grey", "white",
                         "orange", "yellow", "purple", "navy", "brown"]
        for color in color_keywords:
            if color in query_lower:
                context.colors_preferred.append(color)

        # Extract brands
        brand_keywords = ["northpeak", "alpineco", "trailforge"]
        for brand in brand_keywords:
            if brand in query_lower:
                context.brands_preferred.append(brand.title())

        return context

    def _merge_preferences(self, context: PersonalizationContext, prefs: Dict[str, Any]) -> PersonalizationContext:
        """Merge stored preferences into context (context values take priority)."""
        sizing = prefs.get("sizing", {})
        general = prefs.get("general", {})

        # Only apply stored preferences if not specified in query
        if context.fit_preference == FitPreference.CLASSIC and sizing.get("fit"):
            try:
                context.fit_preference = FitPreference(sizing["fit"])
            except ValueError:
                pass

        if not context.shirt_size and sizing.get("shirt"):
            context.shirt_size = sizing["shirt"]
        if not context.pants_size and sizing.get("pants"):
            context.pants_size = sizing["pants"]
        if not context.shoe_size and sizing.get("shoes"):
            context.shoe_size = sizing["shoes"]

        if not context.budget_max and general.get("budget_max"):
            context.budget_max = general["budget_max"]

        if not context.brands_preferred and general.get("brands_liked"):
            context.brands_preferred = general["brands_liked"]

        return context

    # =========================================================================
    # Outfit Recommendations
    # =========================================================================

    def build_search_parameters(self, context: PersonalizationContext) -> Dict[str, Any]:
        """Build search parameters from personalization context."""
        params = {
            "outfit_searches": [],
            "personalization_context": context.to_dict()
        }

        activity_config = ACTIVITY_CATEGORIES.get(context.activity, ACTIVITY_CATEGORIES[Activity.EVERYDAY])

        for category in activity_config["required"]:
            search = {
                "category": category,
                "query_keywords": [],
                "filters": {}
            }

            # Weather-based keywords
            if context.weather in WEATHER_FEATURES:
                weather_config = WEATHER_FEATURES[context.weather]
                search["query_keywords"].extend(weather_config.get("keywords", []))
                if "season" in weather_config:
                    search["filters"]["season"] = weather_config["season"]
                if "waterproofing" in weather_config:
                    search["filters"]["waterproofing"] = weather_config["waterproofing"]

            search["query_keywords"].append(context.activity.value)

            # User preferences
            if context.gender:
                search["filters"]["gender"] = context.gender
            if context.budget_max:
                search["filters"]["max_price"] = context.budget_max
            if context.brands_preferred:
                search["filters"]["brands"] = context.brands_preferred

            # Category-specific color preferences (not global!)
            # This is handled at recommendation time, not search time

            params["outfit_searches"].append(search)

        return params

    def get_personalized_recommendation(self, query: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get personalized outfit recommendation.

        Args:
            query: User's natural language query
            user_id: Optional user identifier

        Returns:
            Recommendation with personalization context
        """
        context = self.extract_context(query, user_id)
        search_params = self.build_search_parameters(context)

        return {
            "success": True,
            "personalization_context": context.to_dict(),
            "search_parameters": search_params,
            "outfit_categories": ACTIVITY_CATEGORIES.get(context.activity, ACTIVITY_CATEGORIES[Activity.EVERYDAY]),
            "user_identified": user_id is not None,
            "preferences_applied": context.is_returning_user
        }


# =========================================================================
# Convenience Functions for Tool Integration
# =========================================================================

def get_user_preferences(user_id: str) -> Dict[str, Any]:
    """Get user preferences from memory."""
    agent = PersonalizationAgent(use_llm=False)
    return agent.get_user_preferences(user_id)


def save_user_preferences(
    user_id: str,
    sizing: Optional[Dict[str, Any]] = None,
    preferences: Optional[Dict[str, Dict[str, Any]]] = None,
    general: Optional[Dict[str, Any]] = None,
    permanent: bool = True
) -> Dict[str, Any]:
    """Save user preferences."""
    agent = PersonalizationAgent(use_llm=False)
    return agent.save_user_preferences(user_id, sizing, preferences, general, permanent)


def process_user_feedback(user_id: str, feedback: str, context: Optional[str] = None) -> Dict[str, Any]:
    """Process user feedback."""
    agent = PersonalizationAgent(use_llm=False)
    return agent.process_feedback(user_id, feedback, context)


def check_returning_user(user_id: str) -> Dict[str, Any]:
    """Check if user exists and get their preference summary."""
    agent = PersonalizationAgent(use_llm=False)
    return agent.identify_user(user_id)


def get_returning_user_prompt(user_id: str) -> Optional[str]:
    """Get prompt for returning user confirmation."""
    agent = PersonalizationAgent(use_llm=False)
    return agent.get_returning_user_prompt(user_id)
