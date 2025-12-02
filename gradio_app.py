"""
Gradio Web Interface for Product Search Agent

A simple web UI for searching products using the AI-powered agent.
Supports simple search, styling recommendations, and conversational mode.
"""

import asyncio
import gradio as gr
from src.product_search_agent import create_product_search_agent
from src.agents import Orchestrator, StylingAgent, Activity, Weather, StylePreference
from tools import agent_tools
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Global agent instance and thread storage
agent = None
user_threads = {}  # Store threads per user session
orchestrator = None
styling_agent = None


async def initialize_agent():
    """Initialize the agent once at startup."""
    global agent
    if agent is None:
        print("Initializing Product Search Agent...")
        agent = await create_product_search_agent()
        print("✓ Agent ready!")
    return agent


def initialize_orchestrator():
    """Initialize the orchestrator and styling agent."""
    global orchestrator, styling_agent
    if orchestrator is None:
        print("Initializing Orchestrator and Styling Agent...")
        orchestrator = Orchestrator()
        styling_agent = StylingAgent()
        print("✓ Orchestrator ready!")


def get_or_create_thread(session_id: str = "default"):
    """Get or create a conversation thread for a user session."""
    global agent, user_threads

    if session_id not in user_threads:
        if agent is None:
            raise RuntimeError("Agent not initialized")
        user_threads[session_id] = agent.get_new_thread()
        print(f"✓ Created new thread for session: {session_id}")

    return user_threads[session_id]


def search_products_simple(query: str, max_results: int = 5) -> str:
    """
    Simple search without agent - just uses search tools directly.
    Faster and no LLM cost.
    """
    if not query.strip():
        return "Please enter a search query."

    try:
        # Use semantic search directly
        result = agent_tools.search_products(query, max_results=max_results)

        if not result['success']:
            return f"Error: {result.get('error', 'Search failed')}"

        if result['total_results'] == 0:
            return "No products found matching your query."

        # Format results
        output = f"**Found {result['total_results']} products for '{query}'**\n\n"

        for i, product in enumerate(result['products'], 1):
            output += f"### {i}. {product['product_name']}\n"
            output += f"- **Brand**: {product['brand']}\n"
            output += f"- **Price**: ${product['price_usd']}\n"
            output += f"- **Rating**: {product['rating']}/5.0 ⭐\n"
            output += f"- **Category**: {product['category']} > {product['subcategory']}\n"
            output += f"- **Features**: {product.get('waterproofing', 'N/A')}, {product.get('insulation', 'N/A')}\n"
            output += f"- **Season**: {product['season']}\n"
            output += f"- **Gender**: {product['gender']}\n"

            if 'similarity_score' in product:
                output += f"- **Relevance**: {product['similarity_score']:.2%}\n"

            output += "\n"

        return output

    except Exception as e:
        return f"Error during search: {str(e)}"


def get_outfit_recommendation(query: str) -> str:
    """
    Get outfit recommendation using the Styling Agent.
    """
    if not query.strip():
        return "Please describe what you need an outfit for."

    try:
        initialize_orchestrator()

        result = orchestrator.process_query(query)

        output = f"## 👗 {result.message}\n\n"

        if result.styling_context:
            ctx = result.styling_context
            output += "### Styling Context\n"
            if ctx.get('activity') != 'unknown':
                output += f"- **Activity**: {ctx['activity'].title()}\n"
            if ctx.get('weather') != 'unknown':
                output += f"- **Weather**: {ctx['weather'].title()}\n"
            if ctx.get('style_preference') != 'neutral':
                output += f"- **Style**: {ctx['style_preference'].title()}\n"
            if ctx.get('gender'):
                output += f"- **Gender**: {ctx['gender']}\n"
            if ctx.get('budget_max'):
                output += f"- **Budget**: Under ${ctx['budget_max']}\n"
            output += "\n"

        if result.outfit_recommendation and result.outfit_recommendation.get('categories'):
            for category, products in result.outfit_recommendation['categories'].items():
                output += f"### {category}\n"
                for i, product in enumerate(products, 1):
                    output += f"**{i}. {product.get('product_name', 'N/A')}**\n"
                    output += f"- Brand: {product.get('brand', 'N/A')}\n"
                    output += f"- Price: ${product.get('price_usd', 0)}\n"
                    output += f"- Rating: {product.get('rating', 'N/A')}/5.0 ⭐\n"
                    output += f"- {product.get('waterproofing', '')}, {product.get('insulation', '')}\n\n"
        elif result.products:
            output += "### Recommended Products\n"
            for i, product in enumerate(result.products[:6], 1):
                output += f"**{i}. {product.get('product_name', 'N/A')}**\n"
                output += f"- Brand: {product.get('brand', 'N/A')} | "
                output += f"Price: ${product.get('price_usd', 0)} | "
                output += f"Rating: {product.get('rating', 'N/A')}/5.0\n\n"

        return output

    except Exception as e:
        return f"Error getting outfit recommendation: {str(e)}"


def get_styling_for_activity(
    activity: str,
    weather: str,
    style: str,
    gender: str,
    budget: float
) -> str:
    """
    Get outfit recommendation for specific parameters.
    """
    try:
        initialize_orchestrator()

        # Build query from parameters
        query_parts = []
        if activity and activity != "Select...":
            query_parts.append(f"outfit for {activity}")
        if weather and weather != "Select...":
            query_parts.append(f"in {weather} weather")
        if style and style != "Select...":
            query_parts.append(f"{style} style")
        if gender and gender != "Select...":
            query_parts.append(f"for {gender}")
        if budget and budget > 0:
            query_parts.append(f"under ${int(budget)}")

        if not query_parts:
            return "Please select at least one option."

        query = " ".join(query_parts)
        return get_outfit_recommendation(query)

    except Exception as e:
        return f"Error: {str(e)}"


async def chat_with_agent(message: str, history: list, session_id: str = "default") -> str:
    """
    Chat with the AI agent using AgentThread for conversation context.
    Agent can use all 9 tools and maintains conversation history.
    """
    if not message.strip():
        return "Please enter a message."

    try:
        # Initialize agent if needed
        await initialize_agent()

        # Get or create thread for this session
        thread = get_or_create_thread(session_id)

        # Run agent with message using thread (maintains context)
        result = await agent.run(message, thread=thread)

        return result.text

    except Exception as e:
        return f"Error: {str(e)}"


def get_catalog_stats() -> str:
    """Get catalog statistics."""
    try:
        result = agent_tools.get_catalog_statistics()

        if not result['success']:
            return "Error fetching catalog statistics."

        output = "## 📊 Catalog Statistics\n\n"
        output += f"**Total Products**: {result['total_products']}\n\n"

        output += "### Brands\n"
        for brand, count in result['brands'].items():
            output += f"- {brand}: {count} products\n"

        output += "\n### Categories\n"
        for category, count in result['categories'].items():
            output += f"- {category}: {count} products\n"

        output += "\n### Price Range\n"
        output += f"- Min: ${result['price_stats']['min']}\n"
        output += f"- Max: ${result['price_stats']['max']}\n"
        output += f"- Average: ${result['price_stats']['avg']}\n"

        output += "\n### Ratings\n"
        output += f"- Min: {result['rating_stats']['min']}/5.0\n"
        output += f"- Max: {result['rating_stats']['max']}/5.0\n"
        output += f"- Average: {result['rating_stats']['avg']}/5.0\n"

        return output

    except Exception as e:
        return f"Error: {str(e)}"


def get_available_brands() -> str:
    """Get list of available brands."""
    try:
        result = agent_tools.get_available_brands()

        if not result['success']:
            return "Error fetching brands."

        return f"**Available Brands** ({result['total_brands']}):\n" + \
               "\n".join([f"- {brand}" for brand in result['brands']])

    except Exception as e:
        return f"Error: {str(e)}"


# Create Gradio Interface
with gr.Blocks(title="Product Search Agent") as demo:
    gr.Markdown("""
    # 🛍️ Product Search Agent

    AI-powered search for outdoor apparel and gear (300 products from NorthPeak, AlpineCo, TrailForge)

    **Three modes:**
    - **Simple Search** - Fast, free semantic search (no LLM)
    - **Styling Agent** - AI-powered outfit recommendations
    - **AI Chat** - Conversational agent with all tools
    """)

    with gr.Tabs():
        # Tab 1: Simple Search (Free, Fast)
        with gr.Tab("🔍 Simple Search"):
            gr.Markdown("""
            ### Fast semantic search without LLM
            Search products using natural language. No AI agent, just vector similarity.
            """)

            with gr.Row():
                with gr.Column():
                    search_input = gr.Textbox(
                        label="Search Query",
                        placeholder="e.g., warm jacket for skiing",
                        lines=2
                    )
                    max_results = gr.Slider(
                        minimum=1,
                        maximum=20,
                        value=5,
                        step=1,
                        label="Number of Results"
                    )
                    search_btn = gr.Button("🔍 Search", variant="primary")

                with gr.Column():
                    search_output = gr.Markdown(label="Results")

            search_btn.click(
                fn=search_products_simple,
                inputs=[search_input, max_results],
                outputs=search_output
            )

            gr.Examples(
                examples=[
                    ["warm jacket for skiing", 5],
                    ["waterproof hiking jacket", 5],
                    ["lightweight travel jacket", 5],
                    ["winter boots for snow", 5],
                ],
                inputs=[search_input, max_results],
            )

        # Tab 2: Styling Agent (NEW!)
        with gr.Tab("👗 Styling Agent"):
            gr.Markdown("""
            ### AI-Powered Outfit Recommendations
            Tell us what you need, and we'll build a complete outfit for you!

            **The Styling Agent understands:**
            - Activities (hiking, skiing, camping, running, etc.)
            - Weather conditions (cold, rainy, warm, etc.)
            - Style preferences (technical, casual, stylish)
            - Budget constraints
            """)

            with gr.Row():
                with gr.Column():
                    # Natural language input
                    styling_query = gr.Textbox(
                        label="Describe your outfit needs",
                        placeholder="e.g., I need an outfit for winter hiking under $500",
                        lines=3
                    )
                    styling_btn = gr.Button("👗 Get Outfit Recommendation", variant="primary")

                    gr.Markdown("**Or use the form below:**")

                    # Structured input
                    with gr.Row():
                        activity_dropdown = gr.Dropdown(
                            choices=["Select...", "hiking", "skiing", "camping", "running", "climbing", "casual", "travel", "everyday"],
                            label="Activity",
                            value="Select..."
                        )
                        weather_dropdown = gr.Dropdown(
                            choices=["Select...", "cold", "cool", "mild", "warm", "rainy", "snowy", "windy"],
                            label="Weather",
                            value="Select..."
                        )

                    with gr.Row():
                        style_dropdown = gr.Dropdown(
                            choices=["Select...", "technical", "casual", "stylish", "minimalist"],
                            label="Style",
                            value="Select..."
                        )
                        gender_dropdown = gr.Dropdown(
                            choices=["Select...", "Men", "Women", "Unisex"],
                            label="Gender",
                            value="Select..."
                        )

                    budget_slider = gr.Slider(
                        minimum=0,
                        maximum=1000,
                        value=0,
                        step=50,
                        label="Max Budget ($) - 0 for no limit"
                    )

                    form_btn = gr.Button("🎯 Get Outfit", variant="secondary")

                with gr.Column():
                    styling_output = gr.Markdown(label="Outfit Recommendation")

            # Connect buttons
            styling_btn.click(
                fn=get_outfit_recommendation,
                inputs=[styling_query],
                outputs=styling_output
            )

            form_btn.click(
                fn=get_styling_for_activity,
                inputs=[activity_dropdown, weather_dropdown, style_dropdown, gender_dropdown, budget_slider],
                outputs=styling_output
            )

            gr.Examples(
                examples=[
                    ["I need an outfit for winter hiking"],
                    ["What should I wear for skiing in cold weather?"],
                    ["Help me dress for a casual weekend outdoors"],
                    ["Women's hiking outfit for rainy weather under $400"],
                    ["Stylish technical outfit for mountain travel"],
                ],
                inputs=[styling_query],
            )

        # Tab 3: AI Chat (Uses LLM)
        with gr.Tab("💬 AI Chat"):
            gr.Markdown("""
            ### Conversational AI agent with all tools
            Chat with the agent using natural language. The agent can:
            - Search products semantically
            - Filter by attributes (brand, price, gender, etc.)
            - Find similar products
            - Compare and recommend

            ⚠️ **Note**: This uses GitHub Models (gpt-4o-mini)
            """)

            chatbot = gr.Chatbot(
                label="Product Search Agent",
                height=400
            )

            with gr.Row():
                chat_input = gr.Textbox(
                    label="Message",
                    placeholder="Ask me anything about products...",
                    lines=2,
                    scale=4
                )
                chat_btn = gr.Button("Send", variant="primary", scale=1)

            gr.Examples(
                examples=[
                    "I need a warm jacket for skiing",
                    "Show me women's jackets under $300",
                    "What brands do you carry?",
                    "Compare AlpineCo and NorthPeak parkas",
                    "Find boots suitable for winter hiking",
                ],
                inputs=chat_input,
            )

            def chat_wrapper(message, history):
                """Wrapper to handle async chat and format for Gradio."""
                response = asyncio.run(chat_with_agent(message, history, session_id="gradio_default"))
                history.append({"role": "user", "content": message})
                history.append({"role": "assistant", "content": response})
                return history, ""

            chat_btn.click(
                fn=chat_wrapper,
                inputs=[chat_input, chatbot],
                outputs=[chatbot, chat_input]
            )

            chat_input.submit(
                fn=chat_wrapper,
                inputs=[chat_input, chatbot],
                outputs=[chatbot, chat_input]
            )

        # Tab 4: Catalog Info
        with gr.Tab("📊 Catalog Info"):
            gr.Markdown("### Browse catalog information")

            with gr.Row():
                stats_btn = gr.Button("📊 Get Statistics", variant="primary")
                brands_btn = gr.Button("🏷️ Show Brands", variant="secondary")

            info_output = gr.Markdown()

            stats_btn.click(
                fn=get_catalog_stats,
                inputs=None,
                outputs=info_output
            )

            brands_btn.click(
                fn=get_available_brands,
                inputs=None,
                outputs=info_output
            )

    gr.Markdown("""
    ---
    **Tech Stack:**
    - **Embeddings**: all-MiniLM-L6-v2 (384 dimensions, local)
    - **Vector DB**: ChromaDB (persistent, 300 products)
    - **LLM**: GitHub Models (gpt-4o-mini)
    - **Agents**: Styling Agent + Orchestrator + Product Search
    - **UI**: Gradio

    **Cost**: Simple search & Styling Agent are FREE. AI chat uses LLM.
    """)


if __name__ == "__main__":
    print("=" * 70)
    print("PRODUCT SEARCH AGENT - GRADIO WEB INTERFACE")
    print("=" * 70)
    print()
    print("Starting Gradio interface...")
    print()
    print("📌 Features:")
    print("  - Simple Search: Fast, free semantic search")
    print("  - Styling Agent: AI-powered outfit recommendations")
    print("  - AI Chat: Conversational agent with GitHub Models")
    print("  - Catalog Info: Browse products, brands, statistics")
    print()
    print("🚀 Launching...")
    print()

    # Launch Gradio
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )
