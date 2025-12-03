"""
Personalization tool functions for the PersonalizationAgent.

These functions handle user identification, preference management,
and feedback processing.
"""

from typing import List, Dict, Any, Optional


# Initialize personalization agent (singleton pattern)
_personalization_agent = None


def _get_personalization_agent():
    """Get or create the PersonalizationAgent instance."""
    global _personalization_agent
    if _personalization_agent is None:
        from src.agents.personalization_agent import PersonalizationAgent
        _personalization_agent = PersonalizationAgent()
    return _personalization_agent


def identify_user(user_name: str) -> Dict[str, Any]:
    """
    Identify a user and check if they have saved preferences.

    Call this when a user introduces themselves (e.g., "Hi, I'm Sarah").
    Returns whether they're a new or returning user, and their saved preferences.

    Args:
        user_name: The user's name/identifier

    Returns:
        Dictionary containing:
        - is_new (bool): True if this is a new user
        - user_id (str): The user identifier
        - preferences_summary (str): Summary of saved preferences (if returning user)
        - message (str): Welcome message

    Example:
        result = identify_user("sarah")
        if result['is_new']:
            # Ask for preferences
        else:
            # Show saved preferences and ask for confirmation
    """
    try:
        agent = _get_personalization_agent()
        return agent.identify_user(user_name)
    except Exception as e:
        return {
            "is_new": True,
            "user_id": user_name,
            "error": str(e)
        }


def get_user_preferences(user_id: str) -> Dict[str, Any]:
    """
    Get saved preferences for a user.

    Args:
        user_id: User identifier (their name)

    Returns:
        Dictionary containing user preferences:
        - sizing (dict): Fit, shirt size, pants size, shoe size
        - preferences (dict): Category-specific preferences (colors, style per category)
        - general (dict): Budget, preferred brands

    Example:
        prefs = get_user_preferences("sarah")
        print(f"Sarah prefers {prefs['sizing']['fit']} fit")
    """
    try:
        agent = _get_personalization_agent()
        return agent.get_user_preferences(user_id)
    except Exception as e:
        return {"error": str(e)}


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
        outerwear_style: Style for outerwear (technical, casual, stylish, etc.)
        footwear_colors: Preferred colors for footwear
        permanent: True to save as default, False for session only

    Returns:
        Confirmation message

    Example:
        save_user_preferences(
            user_id="sarah",
            fit="relaxed",
            shirt_size="M",
            outerwear_colors=["blue", "black"],
            permanent=True
        )
    """
    try:
        agent = _get_personalization_agent()

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

        return agent.save_user_preferences(
            user_id=user_id,
            sizing=sizing if sizing else None,
            preferences=preferences if preferences else None,
            general=general if general else None,
            permanent=permanent
        )
    except Exception as e:
        return {"success": False, "error": str(e)}


def record_user_feedback(
    user_id: str,
    feedback: str,
    context: Optional[str] = None
) -> Dict[str, Any]:
    """
    Record natural language feedback from user and extract preference signals.

    Use this when a user gives feedback like "too flashy", "too tight",
    "too expensive", etc. The system will extract signals and adjust
    future recommendations.

    Args:
        user_id: User identifier
        feedback: Natural language feedback (e.g., "that's too flashy",
                 "I prefer less tight fits", "too expensive for me")
        context: Optional context about what the feedback refers to

    Returns:
        Dictionary with:
        - success (bool): Whether feedback was recorded
        - signals (list): Extracted preference signals
        - actions (list): How this will affect recommendations
        - message (str): Confirmation message

    Example:
        result = record_user_feedback("sarah", "that jacket is too flashy")
        # Returns: {"signals": [{"type": "avoid_style", "value": "bright_colors"}],
        #          "actions": ["I'll recommend more neutral/muted colors"]}
    """
    try:
        agent = _get_personalization_agent()
        return agent.process_feedback(user_id, feedback, context)
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_returning_user_prompt(user_id: str) -> Dict[str, Any]:
    """
    Get a prompt to ask a returning user about their preferences.

    This generates a message like:
    "Welcome back Sarah! Last time your preferences were:
    - Fit: Relaxed, Size M
    - Colors: Blue for outerwear
    Do you want similar preferences today, or would you like to change anything?"

    Args:
        user_id: User identifier

    Returns:
        Dictionary with:
        - has_preferences (bool): Whether user has saved preferences
        - prompt (str): The prompt to show the user (None if new user)

    Example:
        result = get_returning_user_prompt("sarah")
        if result['has_preferences']:
            # Show result['prompt'] to user
    """
    try:
        agent = _get_personalization_agent()
        prompt = agent.get_returning_user_prompt(user_id)
        return {
            "has_preferences": prompt is not None,
            "prompt": prompt
        }
    except Exception as e:
        return {"has_preferences": False, "prompt": None, "error": str(e)}
