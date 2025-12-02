"""
Styling Agent - Understands user styling intent and coordinates outfit recommendations.

This agent:
1. Parses user queries for styling context (activity, occasion, weather, style preferences)
2. Builds outfit recommendations by category
3. Provides structured styling context to the Product Search Agent
4. Uses LLM for natural language understanding when available

Example queries this agent handles:
- "I need an outfit for winter hiking"
- "What should I wear for a casual weekend in the mountains?"
- "Help me dress for skiing in cold weather"
- "I want a stylish look for outdoor activities"
"""

import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


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
    COLD = "cold"           # Below 32°F / 0°C
    COOL = "cool"           # 32-50°F / 0-10°C
    MILD = "mild"           # 50-68°F / 10-20°C
    WARM = "warm"           # Above 68°F / 20°C
    RAINY = "rainy"
    SNOWY = "snowy"
    WINDY = "windy"
    UNKNOWN = "unknown"


class StylePreference(Enum):
    """Style preferences for outfit selection."""
    TECHNICAL = "technical"      # Performance-focused
    CASUAL = "casual"            # Relaxed, everyday
    STYLISH = "stylish"          # Fashion-forward
    MINIMALIST = "minimalist"    # Simple, clean
    COLORFUL = "colorful"        # Bright, vibrant
    NEUTRAL = "neutral"          # Earth tones, muted


@dataclass
class StylingContext:
    """Structured styling context extracted from user query."""
    activity: Activity = Activity.UNKNOWN
    weather: Weather = Weather.UNKNOWN
    style_preference: StylePreference = StylePreference.NEUTRAL
    gender: Optional[str] = None
    budget_max: Optional[float] = None
    specific_items: List[str] = field(default_factory=list)
    colors_preferred: List[str] = field(default_factory=list)
    brands_preferred: List[str] = field(default_factory=list)
    occasion: Optional[str] = None
    original_query: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for passing to other agents."""
        return {
            "activity": self.activity.value,
            "weather": self.weather.value,
            "style_preference": self.style_preference.value,
            "gender": self.gender,
            "budget_max": self.budget_max,
            "specific_items": self.specific_items,
            "colors_preferred": self.colors_preferred,
            "brands_preferred": self.brands_preferred,
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


class StylingAgent:
    """
    Agent that understands user styling intent and builds outfit recommendations.

    Uses LLM when available for natural language understanding,
    falls back to rule-based extraction otherwise.
    """

    def __init__(self, use_llm: bool = True):
        """
        Initialize the Styling Agent.

        Args:
            use_llm: Whether to use LLM for intent extraction (requires API key)
        """
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

            # Try GitHub Models first
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

    def extract_styling_context(self, query: str) -> StylingContext:
        """
        Extract styling context from user query.

        Args:
            query: User's natural language query

        Returns:
            StylingContext with extracted intent
        """
        if self.use_llm and self.llm_client:
            return self._extract_with_llm(query)
        else:
            return self._extract_rule_based(query)

    def _extract_with_llm(self, query: str) -> StylingContext:
        """Use LLM to extract styling context from query."""
        system_prompt = """You are a styling assistant that extracts outfit intent from user queries.

Extract the following from the user's query and return as JSON:
- activity: one of [hiking, skiing, camping, running, climbing, casual, travel, everyday, unknown]
- weather: one of [cold, cool, mild, warm, rainy, snowy, windy, unknown]
- style_preference: one of [technical, casual, stylish, minimalist, colorful, neutral]
- gender: "Men", "Women", "Unisex", or null
- budget_max: number or null
- specific_items: list of specific items mentioned (e.g., ["jacket", "boots"])
- colors_preferred: list of colors mentioned
- brands_preferred: list of brands mentioned
- occasion: specific occasion if mentioned (e.g., "weekend trip", "date night")

Return ONLY valid JSON, no explanation."""

        try:
            response = self.llm_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                temperature=0.1,
                max_tokens=500
            )

            import json
            result = json.loads(response.choices[0].message.content)

            return StylingContext(
                activity=Activity(result.get("activity", "unknown")),
                weather=Weather(result.get("weather", "unknown")),
                style_preference=StylePreference(result.get("style_preference", "neutral")),
                gender=result.get("gender"),
                budget_max=result.get("budget_max"),
                specific_items=result.get("specific_items", []),
                colors_preferred=result.get("colors_preferred", []),
                brands_preferred=result.get("brands_preferred", []),
                occasion=result.get("occasion"),
                original_query=query
            )
        except Exception as e:
            print(f"LLM extraction failed: {e}, falling back to rule-based")
            return self._extract_rule_based(query)

    def _extract_rule_based(self, query: str) -> StylingContext:
        """Rule-based extraction of styling context."""
        query_lower = query.lower()

        # Extract activity
        activity = Activity.UNKNOWN
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
                activity = act
                break

        # Extract weather
        weather = Weather.UNKNOWN
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
                weather = wth
                break

        # Extract style preference
        style = StylePreference.NEUTRAL
        style_keywords = {
            StylePreference.TECHNICAL: ["technical", "performance", "professional", "pro"],
            StylePreference.CASUAL: ["casual", "relaxed", "comfortable", "easy"],
            StylePreference.STYLISH: ["stylish", "fashionable", "trendy", "chic"],
            StylePreference.MINIMALIST: ["minimalist", "simple", "clean", "basic"],
            StylePreference.COLORFUL: ["colorful", "bright", "vibrant", "bold"]
        }
        for sty, keywords in style_keywords.items():
            if any(kw in query_lower for kw in keywords):
                style = sty
                break

        # Extract gender
        gender = None
        if "women" in query_lower or "woman" in query_lower or "female" in query_lower:
            gender = "Women"
        elif "men" in query_lower or "man" in query_lower or "male" in query_lower:
            gender = "Men"
        elif "unisex" in query_lower:
            gender = "Unisex"

        # Extract budget
        budget_max = None
        import re
        budget_match = re.search(r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)', query)
        if budget_match:
            budget_max = float(budget_match.group(1).replace(",", ""))
        else:
            budget_match = re.search(r'under\s+(\d+)', query_lower)
            if budget_match:
                budget_max = float(budget_match.group(1))

        # Extract specific items
        specific_items = []
        item_keywords = ["jacket", "coat", "pants", "boots", "shoes", "gloves",
                        "hat", "backpack", "fleece", "shell", "base layer"]
        for item in item_keywords:
            if item in query_lower:
                specific_items.append(item)

        # Extract colors
        colors = []
        color_keywords = ["black", "blue", "red", "green", "gray", "grey", "white",
                         "orange", "yellow", "purple", "navy", "brown"]
        for color in color_keywords:
            if color in query_lower:
                colors.append(color)

        # Extract brands
        brands = []
        brand_keywords = ["northpeak", "alpineco", "trailforge"]
        for brand in brand_keywords:
            if brand in query_lower:
                brands.append(brand.title())

        return StylingContext(
            activity=activity,
            weather=weather,
            style_preference=style,
            gender=gender,
            budget_max=budget_max,
            specific_items=specific_items,
            colors_preferred=colors,
            brands_preferred=brands,
            original_query=query
        )

    def build_search_parameters(self, context: StylingContext) -> Dict[str, Any]:
        """
        Build search parameters for the Product Search Agent.

        Args:
            context: Extracted styling context

        Returns:
            Dictionary of search parameters for each outfit category
        """
        params = {
            "outfit_searches": [],
            "styling_context": context.to_dict()
        }

        # Get categories for the activity
        activity_config = ACTIVITY_CATEGORIES.get(context.activity, ACTIVITY_CATEGORIES[Activity.EVERYDAY])

        # Build search for each required category
        for category in activity_config["required"]:
            search = {
                "category": category,
                "query_keywords": [],
                "filters": {}
            }

            # Add weather-based keywords
            if context.weather in WEATHER_FEATURES:
                weather_config = WEATHER_FEATURES[context.weather]
                search["query_keywords"].extend(weather_config.get("keywords", []))
                if "season" in weather_config:
                    search["filters"]["season"] = weather_config["season"]
                if "waterproofing" in weather_config:
                    search["filters"]["waterproofing"] = weather_config["waterproofing"]

            # Add activity keywords
            search["query_keywords"].append(context.activity.value)

            # Add filters from context
            if context.gender:
                search["filters"]["gender"] = context.gender
            if context.budget_max:
                search["filters"]["max_price"] = context.budget_max
            if context.brands_preferred:
                search["filters"]["brands"] = context.brands_preferred

            params["outfit_searches"].append(search)

        # Add optional categories
        for category in activity_config.get("optional", []):
            search = {
                "category": category,
                "query_keywords": [context.activity.value],
                "filters": {},
                "optional": True
            }
            if context.gender:
                search["filters"]["gender"] = context.gender
            if context.budget_max:
                search["filters"]["max_price"] = context.budget_max
            params["outfit_searches"].append(search)

        return params

    def generate_outfit_prompt(self, context: StylingContext) -> str:
        """
        Generate a natural language prompt for the Product Search Agent.

        Args:
            context: Extracted styling context

        Returns:
            Natural language search prompt
        """
        parts = []

        # Activity
        if context.activity != Activity.UNKNOWN:
            parts.append(f"for {context.activity.value}")

        # Weather
        if context.weather != Weather.UNKNOWN:
            parts.append(f"in {context.weather.value} weather")

        # Style
        if context.style_preference != StylePreference.NEUTRAL:
            parts.append(f"{context.style_preference.value} style")

        # Gender
        if context.gender:
            parts.append(f"for {context.gender}")

        # Budget
        if context.budget_max:
            parts.append(f"under ${context.budget_max}")

        # Specific items
        if context.specific_items:
            parts.append(f"including {', '.join(context.specific_items)}")

        if parts:
            return f"Complete outfit {' '.join(parts)}"
        else:
            return "Recommend an outdoor outfit"

    def get_outfit_recommendation(self, query: str) -> Dict[str, Any]:
        """
        Main entry point: Get outfit recommendation from user query.

        Args:
            query: User's natural language query

        Returns:
            Outfit recommendation with search parameters
        """
        # Step 1: Extract styling context
        context = self.extract_styling_context(query)

        # Step 2: Build search parameters
        search_params = self.build_search_parameters(context)

        # Step 3: Generate prompt for product search
        prompt = self.generate_outfit_prompt(context)

        return {
            "success": True,
            "styling_context": context.to_dict(),
            "search_parameters": search_params,
            "search_prompt": prompt,
            "outfit_categories": {
                "required": ACTIVITY_CATEGORIES.get(context.activity, {}).get("required", []),
                "optional": ACTIVITY_CATEGORIES.get(context.activity, {}).get("optional", [])
            },
            "recommendations": {
                "activity": context.activity.value,
                "weather_appropriate": context.weather != Weather.UNKNOWN,
                "style": context.style_preference.value
            }
        }


# Convenience functions for tool integration
def extract_styling_intent(query: str) -> Dict[str, Any]:
    """
    Extract styling intent from user query.

    Args:
        query: Natural language query about outfit/styling

    Returns:
        Structured styling context
    """
    agent = StylingAgent()
    context = agent.extract_styling_context(query)
    return context.to_dict()


def get_outfit_search_params(query: str) -> Dict[str, Any]:
    """
    Get search parameters for outfit recommendation.

    Args:
        query: Natural language query about outfit/styling

    Returns:
        Search parameters for Product Search Agent
    """
    agent = StylingAgent()
    return agent.get_outfit_recommendation(query)


def build_outfit_for_activity(
    activity: str,
    weather: str = "unknown",
    gender: Optional[str] = None,
    budget_max: Optional[float] = None,
    style: str = "neutral"
) -> Dict[str, Any]:
    """
    Build outfit recommendation for specific activity.

    Args:
        activity: Activity type (hiking, skiing, camping, etc.)
        weather: Weather condition
        gender: Gender preference
        budget_max: Maximum budget
        style: Style preference

    Returns:
        Outfit recommendation with search parameters
    """
    agent = StylingAgent(use_llm=False)  # Use rule-based for direct calls

    context = StylingContext(
        activity=Activity(activity) if activity in [a.value for a in Activity] else Activity.UNKNOWN,
        weather=Weather(weather) if weather in [w.value for w in Weather] else Weather.UNKNOWN,
        style_preference=StylePreference(style) if style in [s.value for s in StylePreference] else StylePreference.NEUTRAL,
        gender=gender,
        budget_max=budget_max
    )

    search_params = agent.build_search_parameters(context)
    prompt = agent.generate_outfit_prompt(context)

    return {
        "success": True,
        "styling_context": context.to_dict(),
        "search_parameters": search_params,
        "search_prompt": prompt,
        "outfit_categories": ACTIVITY_CATEGORIES.get(context.activity, ACTIVITY_CATEGORIES[Activity.EVERYDAY])
    }


if __name__ == "__main__":
    # Test the styling agent
    agent = StylingAgent()

    test_queries = [
        "I need an outfit for winter hiking",
        "What should I wear for skiing in cold weather?",
        "Help me dress for a casual weekend in the mountains",
        "I want a stylish look for outdoor activities under $500",
        "Women's hiking outfit for rainy weather"
    ]

    print("=" * 70)
    print("STYLING AGENT TEST")
    print("=" * 70)

    for query in test_queries:
        print(f"\nQuery: {query}")
        print("-" * 50)
        result = agent.get_outfit_recommendation(query)
        print(f"Activity: {result['styling_context']['activity']}")
        print(f"Weather: {result['styling_context']['weather']}")
        print(f"Style: {result['styling_context']['style_preference']}")
        print(f"Search Prompt: {result['search_prompt']}")
        print(f"Categories: {result['outfit_categories']}")
