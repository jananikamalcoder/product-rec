"""
Gradio Web Interface for Product Search Agent

A simple web UI for searching products using the AI-powered agent.
Supports both simple search and conversational mode.
"""

import asyncio
import gradio as gr
from product_search_agent import create_product_search_agent
import agent_tools
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Global agent instance
agent = None


async def initialize_agent():
    """Initialize the agent once at startup."""
    global agent
    if agent is None:
        print("Initializing Product Search Agent...")
        agent = await create_product_search_agent()
        print("✓ Agent ready!")
    return agent


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


async def chat_with_agent(message: str, history: list) -> str:
    """
    Chat with the AI agent (uses LLM - costs money).
    Agent can use all 9 tools and have conversations.
    """
    if not message.strip():
        return "Please enter a message."

    try:
        # Initialize agent if needed
        current_agent = await initialize_agent()

        # Run agent with message
        result = await current_agent.run(message)

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
with gr.Blocks(title="Product Search Agent", theme=gr.themes.Soft()) as demo:
    gr.Markdown("""
    # 🛍️ Product Search Agent

    AI-powered search for outdoor apparel and gear (300 products from NorthPeak, AlpineCo, TrailForge)

    **Two modes:**
    - **Simple Search** - Fast, free semantic search (no LLM)
    - **AI Chat** - Conversational agent with all 9 tools (uses GitHub Models)
    """)

    with gr.Tabs():
        # Tab 1: Simple Search (Free, Fast)
        with gr.Tab("🔍 Simple Search (Free)"):
            gr.Markdown("""
            ### Fast semantic search without LLM
            Search products using natural language. No AI agent, just vector similarity.

            **Examples:**
            - "warm jacket for skiing"
            - "waterproof hiking boots"
            - "lightweight jacket for travel"
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

            # Quick search examples
            gr.Examples(
                examples=[
                    ["warm jacket for skiing", 5],
                    ["waterproof hiking jacket", 5],
                    ["lightweight travel jacket", 5],
                    ["winter boots for snow", 5],
                    ["down insulated parka", 3],
                ],
                inputs=[search_input, max_results],
            )

        # Tab 2: AI Chat (Uses LLM)
        with gr.Tab("💬 AI Chat (Uses GitHub Models)"):
            gr.Markdown("""
            ### Conversational AI agent with 9 tools
            Chat with the agent using natural language. The agent can:
            - Search products semantically
            - Filter by attributes (brand, price, gender, etc.)
            - Find similar products
            - Compare and recommend

            ⚠️ **Note**: This uses GitHub Models (gpt-4o-mini) and incurs small costs (~$0.0002 per message)
            """)

            chatbot = gr.Chatbot(
                label="Product Search Agent",
                height=400,
                type="messages"
            )

            with gr.Row():
                chat_input = gr.Textbox(
                    label="Message",
                    placeholder="Ask me anything about products...",
                    lines=2,
                    scale=4
                )
                chat_btn = gr.Button("Send", variant="primary", scale=1)

            # Chat examples
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
                response = asyncio.run(chat_with_agent(message, history))
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

        # Tab 3: Catalog Info
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
    - **LLM**: GitHub Models (gpt-4o-mini, for AI chat only)
    - **Framework**: Microsoft Agent Framework
    - **UI**: Gradio

    **Cost**: Simple search is FREE. AI chat costs ~$0.0002 per message.
    """)


if __name__ == "__main__":
    print("=" * 70)
    print("PRODUCT SEARCH AGENT - GRADIO WEB INTERFACE")
    print("=" * 70)
    print()
    print("Starting Gradio interface...")
    print("The interface will open in your browser automatically.")
    print()
    print("📌 Features:")
    print("  - Simple Search: Fast, free semantic search")
    print("  - AI Chat: Conversational agent with GitHub Models")
    print("  - Catalog Info: Browse products, brands, statistics")
    print()
    print("🚀 Launching...")
    print()

    # Launch Gradio
    demo.launch(
        server_name="0.0.0.0",  # Allow external access (for Codespaces)
        server_port=7860,
        share=False,  # Set to True to create public link
        show_error=True
    )
