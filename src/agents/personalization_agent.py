"""
Personalization Agent - LLM-powered user preference management.

This agent handles:
1. User identification (new vs returning)
2. Preference gathering through conversation
3. Preference storage (permanent vs session-only)
4. Feedback processing

Uses the Microsoft Agent Framework to create an LLM-based agent
with tools for memory operations.
"""

import os
import re
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

from .memory import get_memory

# Load environment variables
load_dotenv(override=True)

# Cold climate location mapping for weather inference
COLD_CLIMATE_LOCATIONS = {
    # Cities
    "fargo": "cold", "minneapolis": "cold", "chicago": "cold",
    "denver": "cold", "boston": "cold", "detroit": "cold",
    "milwaukee": "cold", "buffalo": "cold", "cleveland": "cold",
    "anchorage": "very_cold", "fairbanks": "very_cold",
    # States/Regions
    "north dakota": "cold", "minnesota": "cold", "montana": "cold",
    "wisconsin": "cold", "michigan": "cold", "maine": "cold",
    "alaska": "very_cold", "wyoming": "cold", "vermont": "cold",
    "new hampshire": "cold", "idaho": "cold", "colorado": "cold"
}


def infer_climate(city: Optional[str] = None, region: Optional[str] = None) -> Optional[str]:
    """Infer climate from city or region name."""
    if city:
        climate = COLD_CLIMATE_LOCATIONS.get(city.lower().strip())
        if climate:
            return climate
    if region:
        climate = COLD_CLIMATE_LOCATIONS.get(region.lower().strip())
        if climate:
            return climate
    return None

# Try to import agent framework
try:
    from agent_framework.openai import OpenAIChatClient
    AGENT_FRAMEWORK_AVAILABLE = True
except ImportError:
    AGENT_FRAMEWORK_AVAILABLE = False


class PersonalizationAgent:
    """
    LLM-powered agent for user preference management.

    This class provides tool functions for the LLM agent to use,
    and creates the agent with the Microsoft Agent Framework.
    """

    def __init__(self):
        """Initialize the PersonalizationAgent."""
        self.memory = get_memory()

    # =========================================================================
    # Tool Functions (called by LLM agent)
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

        return (
            f"Welcome back, {user_id.title()}! Last time your preferences were:\n\n"
            f"{summary}\n\n"
            "Do you want similar preferences today, or would you like to change "
            "anything (colors, fit, style, budget)?"
        )

    def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user preferences from memory."""
        return self.memory.get_preferences(user_id)

    def save_user_preferences(
        self,
        user_id: str,
        sizing: Optional[Dict[str, Any]] = None,
        preferences: Optional[Dict[str, Dict[str, Any]]] = None,
        general: Optional[Dict[str, Any]] = None,
        location: Optional[Dict[str, Any]] = None,
        permanent: bool = True
    ) -> Dict[str, Any]:
        """
        Save user preferences.

        Args:
            user_id: User identifier
            sizing: Sizing preferences (fit, shirt, pants, shoes)
            preferences: Category-specific preferences (outerwear, footwear, etc.)
            general: General preferences (budget, brands)
            location: Location dict with city, region, climate
            permanent: If True, save permanently. If False, session only.

        Returns:
            Confirmation dict
        """
        self.memory.save_preferences_bulk(
            user_id=user_id,
            sizing=sizing,
            preferences=preferences,
            general=general,
            location=location,
            permanent=permanent
        )

        persistence = "permanently saved" if permanent else "applied for this session only"
        return {
            "success": True,
            "user_id": user_id,
            "message": f"Preferences {persistence}.",
            "permanent": permanent
        }

    def process_feedback(
        self,
        user_id: str,
        feedback_text: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
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

        if actions:
            message = "Thanks for the feedback! " + " ".join(actions)
        else:
            message = "Feedback noted!"
        return {
            "success": True,
            "feedback_recorded": True,
            "signals": signals,
            "actions": actions,
            "message": message
        }

    def get_personalized_recommendation(
        self,
        query: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get personalized outfit recommendation by parsing query and applying user preferences.

        Args:
            query: Natural language styling request
            user_id: Optional user identifier for applying saved preferences

        Returns:
            Dict with personalization_context, search_parameters, and preferences_applied
        """
        # Parse context from query
        context = self._parse_query_context(query)

        # Apply user preferences if available
        preferences_applied = False
        if user_id and self.memory.user_exists(user_id):
            user_prefs = self.memory.get_preferences(user_id)
            context = self._merge_user_preferences(context, user_prefs)
            preferences_applied = True

        # Generate search parameters for each outfit category
        outfit_searches = self._generate_outfit_searches(context)

        return {
            "personalization_context": context,
            "search_parameters": {"outfit_searches": outfit_searches},
            "preferences_applied": preferences_applied
        }

    def _parse_query_context(self, query: str) -> Dict[str, Any]:
        """Parse natural language query to extract context."""
        query_lower = query.lower()
        context = {
            "activity": "unknown",
            "weather": "unknown",
            "style": "casual",
            "gender": None,
            "budget": None,
            "colors": []
        }

        # Activity detection
        activities = {
            "hiking": ["hiking", "trail", "hike"],
            "skiing": ["skiing", "ski", "slopes"],
            "travel": ["travel", "trip", "vacation", "airport"],
            "casual": ["casual", "everyday", "daily"],
            "climbing": ["climbing", "climb", "alpine"],
        }
        for activity, keywords in activities.items():
            if any(kw in query_lower for kw in keywords):
                context["activity"] = activity
                break

        # Weather detection
        if any(w in query_lower for w in ["winter", "cold", "snow", "freezing"]):
            context["weather"] = "cold"
        elif any(w in query_lower for w in ["rain", "wet", "rainy"]):
            context["weather"] = "rainy"
        elif any(w in query_lower for w in ["summer", "hot", "warm"]):
            context["weather"] = "warm"

        # Gender detection
        if any(g in query_lower for g in ["women", "woman", "female", "ladies"]):
            context["gender"] = "Women"
        elif any(g in query_lower for g in ["men", "man", "male", "guys"]):
            context["gender"] = "Men"

        # Budget detection
        budget_match = re.search(r'\$(\d+)', query)
        if budget_match:
            context["budget"] = float(budget_match.group(1))
        elif "under" in query_lower:
            budget_match = re.search(r'under\s+(\d+)', query_lower)
            if budget_match:
                context["budget"] = float(budget_match.group(1))

        # Color detection
        colors = ["blue", "black", "red", "green", "navy", "gray", "grey", "white", "brown"]
        context["colors"] = [c for c in colors if c in query_lower]

        return context

    def _merge_user_preferences(
        self,
        context: Dict[str, Any],
        user_prefs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Merge user preferences into context."""
        # Apply budget from general preferences
        general_prefs = user_prefs.get("general", {})
        if not context.get("budget") and general_prefs.get("budget_max"):
            context["budget"] = general_prefs["budget_max"]

        # Apply colors from category preferences
        if not context.get("colors"):
            prefs = user_prefs.get("preferences", {})
            outerwear_colors = prefs.get("outerwear", {}).get("colors", [])
            if outerwear_colors:
                context["colors"] = outerwear_colors

        # Add fit preference
        if user_prefs.get("sizing", {}).get("fit"):
            context["fit"] = user_prefs["sizing"]["fit"]

        # Add preferred brands
        if user_prefs.get("general", {}).get("brands_liked"):
            context["brands"] = user_prefs["general"]["brands_liked"]

        # Apply location-based weather inference
        location = user_prefs.get("location", {})
        if location and context.get("weather") == "unknown":
            climate = location.get("climate")
            if climate in ("cold", "very_cold"):
                context["weather"] = "cold"
            context["user_location"] = location.get("city", location.get("region"))

        return context

    def _generate_outfit_searches(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate search configurations for each outfit category."""
        searches = []

        # Determine categories based on activity
        activity = context.get("activity", "casual")
        weather = context.get("weather", "unknown")

        # Always include outerwear for cold/rainy weather
        if weather in ["cold", "rainy", "unknown"]:
            searches.append({
                "category": "jacket",
                "query_keywords": self._get_jacket_keywords(activity, weather),
                "filters": self._build_filters(context)
            })

        # Add pants/bottoms
        searches.append({
            "category": "pants",
            "query_keywords": self._get_pants_keywords(activity),
            "filters": self._build_filters(context)
        })

        # Add footwear
        searches.append({
            "category": "footwear",
            "query_keywords": self._get_footwear_keywords(activity),
            "filters": self._build_filters(context)
        })

        return searches

    def _get_jacket_keywords(self, activity: str, weather: str) -> List[str]:
        """Get jacket search keywords based on activity and weather."""
        keywords = []
        if weather == "cold":
            keywords.extend(["insulated", "warm", "down"])
        if weather == "rainy":
            keywords.extend(["waterproof", "rain"])
        if activity == "hiking":
            keywords.extend(["hiking", "outdoor"])
        elif activity == "skiing":
            keywords.extend(["ski", "snow"])
        return keywords if keywords else ["jacket", "outerwear"]

    def _get_pants_keywords(self, activity: str) -> List[str]:
        """Get pants search keywords based on activity."""
        if activity == "hiking":
            return ["hiking", "pants", "outdoor"]
        if activity == "skiing":
            return ["ski", "pants", "snow"]
        return ["pants", "outdoor"]

    def _get_footwear_keywords(self, activity: str) -> List[str]:
        """Get footwear search keywords based on activity."""
        if activity == "hiking":
            return ["hiking", "boots", "trail"]
        if activity == "skiing":
            return ["boots", "winter"]
        return ["boots", "shoes", "outdoor"]

    def _build_filters(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Build search filters from context."""
        filters = {}
        if context.get("gender"):
            filters["gender"] = context["gender"]
        if context.get("budget"):
            filters["max_price"] = context["budget"]
        if context.get("colors"):
            filters["colors"] = context["colors"]
        if context.get("brands"):
            filters["brands"] = context["brands"]
        if context.get("weather") == "cold":
            filters["season"] = ["Winter", "All-season"]
        return filters


def _create_chat_client():
    """Create a chat client based on available credentials."""
    if not AGENT_FRAMEWORK_AVAILABLE:
        raise RuntimeError(
            "Microsoft Agent Framework not installed. Run: pip install agent-framework"
        )

    # Try OpenAI first (preferred - higher rate limits)
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key and not openai_key.startswith("ghp_"):
        # Clear any GitHub Models settings
        if "OPENAI_BASE_URL" in os.environ:
            del os.environ["OPENAI_BASE_URL"]
        os.environ["OPENAI_CHAT_MODEL_ID"] = "gpt-4o-mini"
        return OpenAIChatClient()

    # Fall back to GitHub Models (lower rate limits - 150/day)
    github_token = os.getenv("GITHUB_TOKEN")
    if github_token:
        os.environ["OPENAI_API_KEY"] = github_token
        os.environ["OPENAI_BASE_URL"] = "https://models.inference.ai.azure.com"
        os.environ["OPENAI_CHAT_MODEL_ID"] = "gpt-4o-mini"
        return OpenAIChatClient()

    raise RuntimeError(
        "No AI provider configured. Set OPENAI_API_KEY (preferred) or GITHUB_TOKEN."
    )


# Singleton instance
_agent_instance = None


def _get_agent_instance() -> PersonalizationAgent:
    """Get or create the PersonalizationAgent singleton."""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = PersonalizationAgent()
    return _agent_instance


async def create_personalization_agent():
    """
    Create a PersonalizationAgent as an LLM-powered agent.

    Returns:
        Agent instance with personalization tools
    """
    chat_client = _create_chat_client()
    agent_instance = _get_agent_instance()

    # Create tool functions that use the agent instance
    def identify_user(user_name: str) -> Dict[str, Any]:
        """
        Identify a user and check if they have saved preferences.

        Call this when a user introduces themselves.
        Returns whether they're a new or returning user.

        Args:
            user_name: The user's name/identifier

        Returns:
            Dictionary with is_new, user_id, preferences_summary, message
        """
        return agent_instance.identify_user(user_name)

    def get_user_preferences(user_id: str) -> Dict[str, Any]:
        """
        Get saved preferences for a user.

        Args:
            user_id: User identifier (their name)

        Returns:
            Dictionary containing sizing, preferences, general settings
        """
        return agent_instance.get_user_preferences(user_id)

    def save_user_preferences(
        user_id: str,
        fit: Optional[str] = None,
        shirt_size: Optional[str] = None,
        pants_size: Optional[str] = None,
        shoe_size: Optional[str] = None,
        budget_max: Optional[float] = None,
        brands_liked: Optional[List[str]] = None,
        outerwear_colors: Optional[List[str]] = None,
        outerwear_style: Optional[str] = None,
        footwear_colors: Optional[List[str]] = None,
        location_city: Optional[str] = None,
        location_region: Optional[str] = None,
        permanent: bool = True
    ) -> Dict[str, Any]:
        """
        Save user preferences to memory.

        IMPORTANT: Before saving, ask the user:
        "Is this your new default, or just for today?"
        - If new default: permanent=True
        - If just for today: permanent=False

        Args:
            user_id: User identifier
            fit: Fit preference (slim, classic, relaxed, oversized)
            shirt_size: Shirt size (XS, S, M, L, XL, XXL)
            pants_size: Pants size (e.g., "32", "8", "M")
            shoe_size: Shoe size (e.g., "10", "42")
            budget_max: Maximum budget in USD
            brands_liked: List of preferred brands
            outerwear_colors: Preferred colors for outerwear
            outerwear_style: Style for outerwear
            footwear_colors: Preferred colors for footwear
            location_city: User's city (e.g., "Fargo", "Denver")
            location_region: User's state/region (e.g., "North Dakota")
            permanent: True for default, False for session only

        Returns:
            Confirmation message
        """
        # Build preference structures
        sizing = {}
        if fit:
            sizing["fit"] = fit
        if shirt_size:
            sizing["shirt"] = shirt_size
        if pants_size:
            sizing["pants"] = pants_size
        if shoe_size:
            sizing["shoes"] = shoe_size

        preferences = {}
        if outerwear_colors or outerwear_style:
            preferences["outerwear"] = {}
            if outerwear_colors:
                preferences["outerwear"]["colors"] = outerwear_colors
            if outerwear_style:
                preferences["outerwear"]["style"] = outerwear_style
        if footwear_colors:
            preferences["footwear"] = {"colors": footwear_colors}

        general = {}
        if budget_max:
            general["budget_max"] = budget_max
        if brands_liked:
            general["brands_liked"] = brands_liked

        # Build location with climate inference
        location = None
        if location_city or location_region:
            location = {}
            if location_city:
                location["city"] = location_city
            if location_region:
                location["region"] = location_region
            # Infer climate from location
            climate = infer_climate(location_city, location_region)
            if climate:
                location["climate"] = climate

        return agent_instance.save_user_preferences(
            user_id=user_id,
            sizing=sizing if sizing else None,
            preferences=preferences if preferences else None,
            general=general if general else None,
            location=location,
            permanent=permanent
        )

    def record_user_feedback(
        user_id: str,
        feedback: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Record natural language feedback and extract preference signals.

        Use when user gives feedback like "too flashy", "too tight", etc.

        Args:
            user_id: User identifier
            feedback: Natural language feedback
            context: Optional context about what feedback refers to

        Returns:
            Extracted signals and how they'll affect recommendations
        """
        return agent_instance.process_feedback(user_id, feedback, context)

    def get_returning_user_prompt(user_id: str) -> Dict[str, Any]:
        """
        Get a prompt to ask a returning user about their preferences.

        Args:
            user_id: User identifier

        Returns:
            has_preferences (bool) and prompt (str)
        """
        prompt = agent_instance.get_returning_user_prompt(user_id)
        return {
            "has_preferences": prompt is not None,
            "prompt": prompt
        }

    # Create the agent
    agent = chat_client.create_agent(
        instructions="""You are a personalization data specialist. You manage user preferences as DATA.

CRITICAL: Return STRUCTURED DATA only - do NOT ask questions or have conversations.
The Product Advisor handles all user interaction. You just manage data.

YOUR TASKS:

1. IDENTIFY USER ("identify user Sarah"):
   → Call identify_user(user_name)
   → Return JSON with: is_new, user_id, and preferences if returning user
   → Do NOT ask preference questions - just return what you have

2. GET PREFERENCES ("get preferences for Sarah"):
   → Call get_user_preferences(user_id)
   → Return the raw preferences JSON

3. SAVE PREFERENCES ("save Sarah's preferences: fit=slim, budget=500"):
   → Parse the preferences from the request
   → If location mentioned (city/state), use location_city and location_region params
   → Call save_user_preferences() with permanent=True (default)
   → Only use permanent=False if request says "just for today" or "session only"
   → Return confirmation JSON

4. RECORD FEEDBACK ("record feedback: too flashy"):
   → Call record_user_feedback(user_id, feedback)
   → Return the extracted signals

OUTPUT FORMAT - Always return JSON:
{"action": "identify", "is_new": true, "user_id": "sarah", "preferences": null}
{"action": "identify", "is_new": false, "user_id": "sarah", "preferences": {"fit": "slim", "budget_max": 500}}
{"action": "save", "success": true, "saved": {"fit": "relaxed"}}
{"action": "feedback", "signals": [{"type": "avoid_style", "value": "bright_colors"}]}

NEVER:
- Ask questions back to the user
- Generate preference questionnaires
- Add commentary or conversation
- Format as markdown or bullet points""",
        tools=[
            identify_user,
            get_user_preferences,
            save_user_preferences,
            record_user_feedback,
            get_returning_user_prompt,
        ]
    )

    return agent


# =========================================================================
# Synchronous convenience functions for direct tool access
# =========================================================================

def get_user_preferences(user_id: str) -> Dict[str, Any]:
    """Get user preferences from memory."""
    agent = _get_agent_instance()
    return agent.get_user_preferences(user_id)


def save_user_preferences(
    user_id: str,
    sizing: Optional[Dict[str, Any]] = None,
    preferences: Optional[Dict[str, Dict[str, Any]]] = None,
    general: Optional[Dict[str, Any]] = None,
    permanent: bool = True
) -> Dict[str, Any]:
    """Save user preferences."""
    agent = _get_agent_instance()
    return agent.save_user_preferences(user_id, sizing, preferences, general, permanent)


def process_user_feedback(user_id: str, feedback: str, context: Optional[str] = None) -> Dict[str, Any]:
    """Process user feedback."""
    agent = _get_agent_instance()
    return agent.process_feedback(user_id, feedback, context)


def check_returning_user(user_id: str) -> Dict[str, Any]:
    """Check if user exists and get their preference summary."""
    agent = _get_agent_instance()
    return agent.identify_user(user_id)


def get_returning_user_prompt(user_id: str) -> Optional[str]:
    """Get prompt for returning user confirmation."""
    agent = _get_agent_instance()
    return agent.get_returning_user_prompt(user_id)
