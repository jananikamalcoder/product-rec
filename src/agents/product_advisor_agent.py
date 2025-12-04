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
from typing import Dict, List, Any, Optional

from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# Try to import agent framework
try:
    from agent_framework.openai import OpenAIChatClient
    AGENT_FRAMEWORK_AVAILABLE = True
except ImportError:
    AGENT_FRAMEWORK_AVAILABLE = False

from src.agents.personalization_agent import create_personalization_agent
from src.agents.product_search_agent import create_product_search_agent


def _create_chat_client():
    """Create a chat client based on available credentials."""
    if not AGENT_FRAMEWORK_AVAILABLE:
        raise RuntimeError("Microsoft Agent Framework not installed. Run: pip install agent-framework")

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


# Initialize visual agent singleton
_visual_agent = None


def _log_tool_call(tool_name: str, inputs: dict, output: any):
    """Log tool calls to terminal with inputs and outputs."""
    print(f"\n{'='*60}")
    print(f"🔧 TOOL CALL: {tool_name}")
    print(f"{'='*60}")
    print(f"📥 INPUTS:")
    for key, value in inputs.items():
        # Truncate long values
        str_value = str(value)
        if len(str_value) > 200:
            str_value = str_value[:200] + "..."
        print(f"   {key}: {str_value}")
    print(f"\n📤 OUTPUT:")
    str_output = str(output)
    if len(str_output) > 500:
        str_output = str_output[:500] + "..."
    print(f"   {str_output}")
    print(f"{'='*60}\n")


def _get_visual_agent():
    """Get or create the VisualAgent instance."""
    global _visual_agent
    if _visual_agent is None:
        from src.agents.visual_agent import VisualAgent
        _visual_agent = VisualAgent()
    return _visual_agent


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
        _log_tool_call("call_personalization_agent", {"task": task}, "[calling sub-agent...]")
        result = await personalization_agent.run(task, thread=personalization_thread)
        _log_tool_call("call_personalization_agent [RESULT]", {"task": task}, result.text)
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
        _log_tool_call("call_product_search_agent", {"query": query, "user_context": user_context}, "[calling sub-agent...]")
        prompt = f"Search: {query}"
        if user_context:
            prompt += f"\n\nApply these user preferences when filtering:\n{json.dumps(user_context, indent=2)}"

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
        _log_tool_call("format_search_results", {"products_count": len(products), "show_details": show_details}, "[processing...]")
        try:
            agent = _get_visual_agent()
            result = agent.format_product_list(products, show_details)
            _log_tool_call("format_search_results [RESULT]", {"products_count": len(products)}, result)
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
        _log_tool_call("create_comparison_table", {"product_ids": product_ids, "attributes": attributes}, "[processing...]")
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

            agent = _get_visual_agent()
            result = agent.create_comparison_table(products, attributes)
            _log_tool_call("create_comparison_table [RESULT]", {"product_ids": product_ids}, result)
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
                return {"success": False, "content": "", "error": result.get('error', 'Product not found')}

            agent = _get_visual_agent()
            card_result = agent.create_product_card(result['product'])
            _log_tool_call("create_product_card [RESULT]", {"product_id": product_id}, card_result)
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
        _log_tool_call("create_feature_matrix", {"product_ids": product_ids, "features": features}, "[processing...]")
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

            agent = _get_visual_agent()
            matrix_result = agent.create_feature_matrix(products, features)
            _log_tool_call("create_feature_matrix [RESULT]", {"product_ids": product_ids}, matrix_result)
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

            agent = _get_visual_agent()
            price_result = agent.create_price_visualization(products, show_distribution)
            _log_tool_call("create_price_analysis [RESULT]", {"products_count": len(products)}, price_result)
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

1. WHEN USER INTRODUCES THEMSELVES ("Hi, I'm Sarah"):
   → call_personalization_agent("identify user [name]")
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

5. WHEN USER VOLUNTEERS PREFERENCES ("I like slim fit"):
   → Acknowledge briefly and save as their new default (permanent=True)
   → DON'T ask "is this your default or just for today?" - assume it's their new preference
   → Only use session-only (permanent=False) if user explicitly says "just for today" or similar

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
