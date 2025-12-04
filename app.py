"""
Gradio Web Interface for Product Advisor

A web UI for the multi-agent Product Advisor system.
The AI Chat uses a hierarchical multi-agent architecture:
  - Product Advisor Agent (Orchestrator)
  - PersonalizationAgent (User Memory)
  - ProductSearchAgent (Product Search)
"""

import asyncio
import gradio as gr
from src.agents.product_advisor_agent import create_product_advisor_agent
from src.tools import agent_tools
from dotenv import load_dotenv

# Load environment variables (override system env vars)
load_dotenv(override=True)

# Global agent instance and thread storage
agent = None
user_threads = {}  # Store threads per user session


async def initialize_agent():
    """Initialize the Product Advisor agent once at startup."""
    global agent
    if agent is None:
        print("Initializing Product Advisor Agent (Multi-Agent System)...")
        print("  ├── PersonalizationAgent")
        print("  └── ProductSearchAgent")
        agent = await create_product_advisor_agent()
        print("✓ All agents ready!")
    return agent


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
            output += f"- **Rating**: {product['rating']}/5.0\n"
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


async def chat_with_agent(message: str, history: list, session_id: str = "default") -> str:
    """
    Chat with the Product Advisor using the multi-agent system.
    Maintains conversation context via AgentThread.
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

        output = "## Catalog Statistics\n\n"
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
with gr.Blocks(title="Product Advisor") as demo:
    gr.Markdown("""
    # Product Advisor - Multi-Agent System

    AI-powered search for outdoor apparel and gear (300 products from NorthPeak, AlpineCo, TrailForge)

    **Architecture:**
    ```
    Product Advisor (Orchestrator)
      ├── PersonalizationAgent (User Memory & Preferences)
      └── ProductSearchAgent (Product Search & Filtering)
    ```

    **Two modes:**
    - **AI Chat** - Conversational multi-agent system with personalization (uses LLM)
    - **Simple Search** - Fast, free semantic search (no LLM)
    """)

    with gr.Tabs():
        # Tab 1: AI Chat (Main feature - multi-agent)
        with gr.Tab("AI Chat"):
            gr.Markdown("""
            ### Conversational AI with Personalization

            The advisor remembers your preferences and coordinates specialized agents:

            **Try saying:**
            - "Hi, I'm Sarah" (identifies you, recalls preferences if returning)
            - "I need an outfit for winter hiking"
            - "Show me waterproof jackets under $300"
            - "I prefer relaxed fit" (asks: permanent or just today?)
            - "That's too flashy" (records feedback)

            Uses GitHub Models (gpt-4o-mini)
            """)

            chatbot = gr.Chatbot(
                label="Product Advisor",
                height=450
            )

            with gr.Row():
                chat_input = gr.Textbox(
                    label="Message",
                    placeholder="Try: 'Hi, I'm Sarah' or 'I need a warm jacket for hiking'",
                    lines=2,
                    scale=4
                )
                chat_btn = gr.Button("Send", variant="primary", scale=1)

            gr.Examples(
                examples=[
                    "Hi, I'm Sarah",
                    "I need an outfit for winter hiking",
                    "Show me waterproof jackets under $300",
                    "I prefer relaxed fit and blue colors",
                    "Find NorthPeak parkas",
                    "What brands do you carry?",
                    "Compare AlpineCo and TrailForge boots",
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

        # Tab 2: Simple Search (Free, Fast)
        with gr.Tab("Simple Search"):
            gr.Markdown("""
            ### Fast semantic search without LLM
            Search products using natural language. No AI agent, just vector similarity.
            Free and fast, but no personalization or styling recommendations.
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
                    search_btn = gr.Button("Search", variant="primary")

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

        # Tab 3: Catalog Info
        with gr.Tab("Catalog Info"):
            gr.Markdown("### Browse catalog information")

            with gr.Row():
                stats_btn = gr.Button("Get Statistics", variant="primary")
                brands_btn = gr.Button("Show Brands", variant="secondary")

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
    - **Architecture**: Hierarchical Multi-Agent (Advisor → Personalization + Search)
    - **UI**: Gradio

    **Cost**: Simple search is FREE. AI Chat uses LLM for orchestration.
    """)


if __name__ == "__main__":
    print("=" * 70)
    print("PRODUCT ADVISOR - MULTI-AGENT GRADIO INTERFACE")
    print("=" * 70)
    print()
    print("Architecture:")
    print("  Product Advisor (Orchestrator)")
    print("    ├── PersonalizationAgent (User Memory)")
    print("    └── ProductSearchAgent (Product Search)")
    print()
    print("Features:")
    print("  - AI Chat: Multi-agent system with personalization (LLM)")
    print("  - Simple Search: Fast, free semantic search")
    print("  - Catalog Info: Browse products, brands, statistics")
    print()
    print("Launching...")
    print()

    # Launch Gradio
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )
