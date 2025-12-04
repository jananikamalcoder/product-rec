"""
Product Advisor Agent - Top-level orchestrator for the multi-agent system.

This agent coordinates:
1. PersonalizationAgent - for user memory and preferences
2. ProductSearchAgent - for product search

The Advisor decides when to:
- Identify users (delegate to PersonalizationAgent)
- Search for products (delegate to ProductSearchAgent)
- Format and visualize results

Uses the Microsoft Agent Framework to create the orchestrator.
"""

import json
import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

from src.agents.personalization_agent import create_personalization_agent
from src.agents.product_search_agent import create_product_search_agent

# Load environment variables
load_dotenv(override=True)

# Try to import agent framework
try:
    from agent_framework.openai import OpenAIChatClient
    AGENT_FRAMEWORK_AVAILABLE = True
except ImportError:
    AGENT_FRAMEWORK_AVAILABLE = False


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


# Initialize visual formatting tool singleton
_visual_formatting_tool = None


def _log_tool_call(tool_name: str, inputs: dict, output: any):
    """Log tool calls to terminal with inputs and outputs."""
    separator = "=" * 60
    print(f"\n{separator}")
    print(f"🔧 TOOL CALL: {tool_name}")
    print(separator)
    print("📥 INPUTS:")
    for key, value in inputs.items():
        # Truncate long values
        str_value = str(value)
        if len(str_value) > 200:
            str_value = str_value[:200] + "..."
        print(f"   {key}: {str_value}")
    print("\n📤 OUTPUT:")
    str_output = str(output)
    if len(str_output) > 500:
        str_output = str_output[:500] + "..."
    print(f"   {str_output}")
    print(f"{separator}\n")


def _get_visual_formatting_tool():
    """Get or create the VisualFormattingTool instance."""
    global _visual_formatting_tool
    if _visual_formatting_tool is None:
        from src.agents.visual_formatting_tool import VisualFormattingTool
        _visual_formatting_tool = VisualFormattingTool()
    return _visual_formatting_tool


async def create_product_advisor_agent():
    """
    Create the Product Advisor Agent (top-level orchestrator).

    This agent coordinates the PersonalizationAgent and ProductSearchAgent,
    and handles visualization of results.

    Returns:
        Agent instance with orchestration and visualization tools
    """
    chat_client = _create_chat_client()

    # Create sub-agents
    print("Creating sub-agents...")
    personalization_agent = await create_personalization_agent()
    search_agent = await create_product_search_agent()
    print("✓ Sub-agents created")

    # Create threads for sub-agents
    personalization_thread = personalization_agent.get_new_thread()
    search_thread = search_agent.get_new_thread()

    # Track current user for auto-applying preferences
    current_user_id = None

    def _extract_user_id_from_response(response_text: str) -> Optional[str]:
        """Extract user_id from personalization agent response."""
        try:
            # Try to parse as JSON
            import re
            # Look for "user_id": "name" pattern
            match = re.search(r'"user_id":\s*"([^"]+)"', response_text)
            if match:
                return match.group(1).lower().strip()
        except Exception:
            pass
        return None

    # Define direct personalization tools (bypass sub-agent for common tasks)
    def identify_user(user_name: str, location: Optional[str] = None) -> Dict[str, Any]:
        """
        Identify a user and check if they have saved preferences.

        Call this when a user introduces themselves (e.g., "Hi, I'm Sarah from Seattle").
        If they mention a location, pass it to save automatically.

        Args:
            user_name: The user's name
            location: Optional location (city, state, country) for climate-aware recommendations

        Returns:
            Dictionary with is_new, user_id, message, and location info if provided
        """
        nonlocal current_user_id
        from src.tools.agent_tools import identify_user as _identify_user
        _log_tool_call("identify_user", {"user_name": user_name, "location": location}, "[processing...]")
        result = _identify_user(user_name, location=location)
        if result.get("user_id"):
            current_user_id = result["user_id"]
            print(f"📍 Tracking user: {current_user_id}")
        _log_tool_call("identify_user [RESULT]", {"user_name": user_name}, result)
        return result

    def save_user_preferences(
        user_id: str,
        fit: Optional[str] = None,
        location: Optional[str] = None,
        outerwear_colors: Optional[List[str]] = None,
        budget_max: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Save user preferences to memory.

        Args:
            user_id: User identifier
            fit: Fit preference (slim, classic, relaxed, oversized)
            location: User's location for climate-aware recommendations
            outerwear_colors: Preferred colors for outerwear
            budget_max: Maximum budget in USD

        Returns:
            Confirmation message
        """
        from src.tools.agent_tools import save_user_preferences as _save_user_preferences
        _log_tool_call("save_user_preferences", {"user_id": user_id, "fit": fit, "location": location}, "[processing...]")
        result = _save_user_preferences(
            user_id=user_id,
            fit=fit,
            location=location,
            outerwear_colors=outerwear_colors,
            budget_max=budget_max,
            permanent=True
        )
        _log_tool_call("save_user_preferences [RESULT]", {"user_id": user_id}, result)
        return result

    # Define orchestration tools
    async def call_personalization_agent(task: str) -> str:
        """
        Delegate personalization tasks to the PersonalizationAgent.

        Use this for:
        - Identifying users ("identify user Sarah")
        - Getting user preferences ("get preferences for Sarah")
        - Saving preferences ("save Sarah's preferences: fit=relaxed, budget=$200")
        - Recording feedback ("record feedback: too flashy")

        Args:
            task: Description of the personalization task

        Returns:
            Result from the PersonalizationAgent
        """
        nonlocal current_user_id
        _log_tool_call("call_personalization_agent", {"task": task}, "[calling sub-agent...]")
        result = await personalization_agent.run(task, thread=personalization_thread)
        _log_tool_call("call_personalization_agent [RESULT]", {"task": task}, result.text)

        # Track user_id if this was an identify task
        if "identify" in task.lower():
            extracted_id = _extract_user_id_from_response(result.text)
            if extracted_id:
                current_user_id = extracted_id
                print(f"📍 Tracking user: {current_user_id}")

        return result.text

    async def call_product_search_agent(
        query: str,
        user_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Delegate search tasks to the ProductSearchAgent.

        Use this for:
        - Searching products ("find warm jackets")
        - Filtering products ("show NorthPeak products under $300")
        - Finding similar products ("find alternatives to PRD-123")

        Args:
            query: Search query or task description
            user_context: Optional user preferences to apply
                         (fit, sizes, budget, colors, brands)

        Returns:
            Search results from the ProductSearchAgent
        """
        nonlocal current_user_id

        # AUTO-FETCH user preferences if we have a tracked user and no explicit context
        if user_context is None and current_user_id:
            try:
                from src.agents.personalization_agent import get_user_preferences
                user_prefs = get_user_preferences(current_user_id)
                if user_prefs:
                    # Build user_context from preferences
                    user_context = {}
                    sizing = user_prefs.get("sizing", {})
                    if sizing.get("fit"):
                        user_context["fit"] = sizing["fit"]

                    prefs = user_prefs.get("preferences", {})
                    colors = prefs.get("outerwear", {}).get("colors", [])
                    if colors:
                        user_context["colors"] = colors

                    general = user_prefs.get("general", {})
                    if general.get("budget_max"):
                        user_context["budget_max"] = general["budget_max"]
                    if general.get("brands_liked"):
                        user_context["brands"] = general["brands_liked"]

                    location = user_prefs.get("location", {})
                    if location.get("climate") in ("cold", "very_cold"):
                        user_context["weather"] = "cold"
                    if location.get("city"):
                        user_context["user_location"] = location["city"]

                    print(f"📦 Auto-applied preferences for {current_user_id}: {user_context}")
            except Exception as e:
                print(f"⚠️ Could not auto-fetch preferences: {e}")

        _log_tool_call(
            "call_product_search_agent",
            {"query": query, "user_context": user_context},
            "[calling sub-agent...]"
        )
        prompt = f"Search: {query}"
        if user_context:
            prefs_json = json.dumps(user_context, indent=2)
            prompt += f"\n\nApply these user preferences when filtering:\n{prefs_json}"

        result = await search_agent.run(prompt, thread=search_thread)
        _log_tool_call("call_product_search_agent [RESULT]", {"query": query}, result.text)
        return result.text

    # Define visualization tools
    def format_search_results(
        products: List[Dict[str, Any]],
        show_details: bool = True
    ) -> Dict[str, Any]:
        """
        Format a list of products as a markdown table.

        Args:
            products: List of product dictionaries (from search)
            show_details: If True, show detailed table; if False, simple list

        Returns:
            Formatted markdown content
        """
        _log_tool_call(
            "format_search_results",
            {"products_count": len(products), "show_details": show_details},
            "[processing...]"
        )
        try:
            agent = _get_visual_formatting_tool()
            result = agent.format_product_list(products, show_details)
            _log_tool_call(
                "format_search_results [RESULT]",
                {"products_count": len(products)},
                result
            )
            return result
        except Exception as e:
            return {"success": False, "content": "", "error": str(e)}

    def create_comparison_table(
        product_ids: List[str],
        attributes: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a comparison table for multiple products.

        Args:
            product_ids: List of product IDs to compare (2-5)
            attributes: Optional specific attributes to compare

        Returns:
            Markdown comparison table
        """
        _log_tool_call(
            "create_comparison_table",
            {"product_ids": product_ids, "attributes": attributes},
            "[processing...]"
        )
        try:
            from src.tools.search_tools import get_product_details

            products = []
            for pid in product_ids[:5]:
                result = get_product_details(pid)
                if result['success']:
                    product = result['product']
                    product['product_id'] = pid
                    products.append(product)

            if not products:
                return {"success": False, "content": "", "error": "No valid products found"}

            agent = _get_visual_formatting_tool()
            result = agent.create_comparison_table(products, attributes)
            _log_tool_call(
                "create_comparison_table [RESULT]",
                {"product_ids": product_ids},
                result
            )
            return result
        except Exception as e:
            return {"success": False, "content": "", "error": str(e)}

    def create_product_card(product_id: str) -> Dict[str, Any]:
        """
        Create a detailed product card for a single product.

        Args:
            product_id: The product ID

        Returns:
            Markdown product card
        """
        _log_tool_call("create_product_card", {"product_id": product_id}, "[processing...]")
        try:
            from src.tools.search_tools import get_product_details

            result = get_product_details(product_id)
            if not result['success']:
                error_msg = result.get('error', 'Product not found')
                return {"success": False, "content": "", "error": error_msg}

            agent = _get_visual_formatting_tool()
            card_result = agent.create_product_card(result['product'])
            _log_tool_call(
                "create_product_card [RESULT]",
                {"product_id": product_id},
                card_result
            )
            return card_result
        except Exception as e:
            return {"success": False, "content": "", "error": str(e)}

    def create_feature_matrix(
        product_ids: List[str],
        features: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a feature matrix showing which products have which features.

        Args:
            product_ids: List of product IDs (up to 8)
            features: Optional specific features to check

        Returns:
            Markdown feature matrix with checkmarks
        """
        _log_tool_call(
            "create_feature_matrix",
            {"product_ids": product_ids, "features": features},
            "[processing...]"
        )
        try:
            from src.tools.search_tools import get_product_details

            products = []
            for pid in product_ids[:8]:
                result = get_product_details(pid)
                if result['success']:
                    product = result['product']
                    product['product_id'] = pid
                    products.append(product)

            if not products:
                return {"success": False, "content": "", "error": "No valid products found"}

            agent = _get_visual_formatting_tool()
            matrix_result = agent.create_feature_matrix(products, features)
            _log_tool_call(
                "create_feature_matrix [RESULT]",
                {"product_ids": product_ids},
                matrix_result
            )
            return matrix_result
        except Exception as e:
            return {"success": False, "content": "", "error": str(e)}

    def create_price_analysis(
        product_ids: Optional[List[str]] = None,
        search_query: Optional[str] = None,
        category: Optional[str] = None,
        show_distribution: bool = True
    ) -> Dict[str, Any]:
        """
        Create a price analysis visualization.

        Args:
            product_ids: Specific products to analyze
            search_query: Or search for products to analyze
            category: Or analyze a category
            show_distribution: Show distribution chart

        Returns:
            Price analysis with statistics
        """
        _log_tool_call("create_price_analysis", {
            "product_ids": product_ids,
            "search_query": search_query,
            "category": category,
            "show_distribution": show_distribution
        }, "[processing...]")
        try:
            from src.tools.search_tools import get_product_details, search_products

            products = []

            if product_ids:
                for pid in product_ids:
                    result = get_product_details(pid)
                    if result['success']:
                        products.append(result['product'])
            elif search_query:
                result = search_products(search_query, max_results=50)
                if result['success']:
                    products = result['products']
            elif category:
                result = search_products(f"{category} products", max_results=50)
                if result['success']:
                    products = [p for p in result['products'] if p.get('category') == category]

            if not products:
                return {"success": False, "content": "", "error": "No products found"}

            agent = _get_visual_formatting_tool()
            price_result = agent.create_price_visualization(products, show_distribution)
            _log_tool_call(
                "create_price_analysis [RESULT]",
                {"products_count": len(products)},
                price_result
            )
            return price_result
        except Exception as e:
            return {"success": False, "content": "", "error": str(e)}

    # Create the orchestrator agent
    agent = chat_client.create_agent(
        instructions="""You are a Product Advisor - a friendly personal stylist for an outdoor apparel store.

You coordinate two specialized agents:
1. PersonalizationAgent - handles user memory and preferences
2. ProductSearchAgent - handles product search

CONVERSATION STYLE:
- Be conversational and natural, NOT an interrogation
- NEVER ask more than 1 question at a time
- If user gives partial info, work with what you have
- Prioritize helping with their request over gathering all preferences first

FLOW:

1. WHEN USER INTRODUCES THEMSELVES ("Hi, I'm Sarah" or "Hi, I'm Sarah from Seattle"):
   → Use identify_user(user_name, location) - extract name AND location if mentioned
   → Examples: "Hi, I'm Sarah from Seattle" → identify_user("Sarah", location="Seattle")
             "I'm John, I live in Minnesota" → identify_user("John", location="Minnesota")
             "Hi, I'm Maya" → identify_user("Maya")
   → If returning: briefly mention saved preferences, ask what they need today
   → If new: welcome them warmly, ask what brings them in (NOT a list of preference questions)

2. WHEN USER ASKS FOR PRODUCTS ("I need a jacket for hiking"):
   → Call call_product_search_agent(query) - it returns JSON with products
   → Parse the JSON to extract the products array
   → Call format_search_results(products) to create a nice formatted table
   → DON'T stop to ask about fit, size, budget, colors first
   → If results would benefit from filters, ask ONE clarifying question naturally

3. WHEN USER WANTS TO COMPARE PRODUCTS:
   → Use create_comparison_table(product_ids) with the product IDs
   → Use create_feature_matrix(product_ids) to show feature checkmarks

4. WHEN USER ASKS ABOUT A SPECIFIC PRODUCT:
   → Use create_product_card(product_id) for detailed view

5. WHEN USER VOLUNTEERS PREFERENCES ("I like slim fit", "I'm from Seattle"):
   → Use save_user_preferences(user_id, fit, location, outerwear_colors, budget_max) directly
   → Examples: "I like slim fit" → save_user_preferences(user_id, fit="slim")
             "I'm from Seattle" → save_user_preferences(user_id, location="Seattle")
             "I prefer blue colors" → save_user_preferences(user_id, outerwear_colors=["blue"])
   → Acknowledge briefly - don't ask "is this your default?"

6. WHEN USER GIVES FEEDBACK ("too flashy", "too expensive"):
   → Record via personalization agent
   → Immediately show alternatives that address the feedback

VISUALIZATION TOOLS (use these to format output!):
- format_search_results(products) → formats product list as table
- create_comparison_table(product_ids) → side-by-side comparison
- create_product_card(product_id) → detailed single product view
- create_feature_matrix(product_ids) → feature checkmark grid
- create_price_analysis(...) → price statistics

IMPORTANT RULES:
- ALWAYS use visualization tools to format search results - don't just echo the JSON
- Help first, gather preferences naturally through the conversation
- One question at a time, max
- If user skips a question, don't repeat it - move forward

Be helpful, not bureaucratic!""",
        tools=[
            identify_user,
            save_user_preferences,
            call_personalization_agent,
            call_product_search_agent,
            format_search_results,
            create_comparison_table,
            create_product_card,
            create_feature_matrix,
            create_price_analysis,
        ]
    )

    return agent
