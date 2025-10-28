"""
Product Search Agent using Microsoft Agent Framework

A working AI agent that can search products using the 9 tool functions
from agent_tools.py. Supports both demo mode and interactive chat.

Requirements:
- Microsoft Agent Framework installed: uv add agent-framework --prerelease=allow
- One of: Azure OpenAI, OpenAI, or GitHub Models credentials configured
"""

import asyncio
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Option 1: Azure OpenAI (recommended for production)
try:
    from agent_framework.azure import AzureOpenAIChatClient
    from azure.identity import AzureCliCredential
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False

# Option 2: OpenAI
try:
    from agent_framework.openai import OpenAIChatClient
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

import agent_tools


def create_chat_client():
    """
    Create a chat client based on available credentials.

    Priority:
    1. GitHub Models (if GITHUB_TOKEN set)
    2. Azure OpenAI (if configured)
    3. OpenAI (if API key set)
    """

    # Try GitHub Models first (uses GITHUB_TOKEN from .env)
    github_token = os.getenv("GITHUB_TOKEN")
    if github_token and OPENAI_AVAILABLE:
        try:
            print("Using GitHub Models with OpenAI-compatible API...")
            # GitHub Models uses OpenAI-compatible endpoint
            # Set as environment variables for OpenAI client
            os.environ["OPENAI_API_KEY"] = github_token
            os.environ["OPENAI_BASE_URL"] = "https://models.inference.ai.azure.com"
            os.environ["OPENAI_CHAT_MODEL_ID"] = "gpt-4o-mini"  # Model to use

            client = OpenAIChatClient()
            print("✅ Connected to GitHub Models (using gpt-4o-mini)")
            return client
        except Exception as e:
            print(f"GitHub Models failed: {e}")
            print("Falling back to other providers...")

    # Try Azure OpenAI
    if AZURE_AVAILABLE:
        try:
            print("Attempting to use Azure OpenAI...")
            endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
            deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")

            if endpoint and deployment:
                return AzureOpenAIChatClient(
                    credential=AzureCliCredential(),
                    endpoint=endpoint,
                    deployment=deployment
                )
        except Exception as e:
            print(f"Azure OpenAI not configured: {e}")

    # Fall back to OpenAI
    if OPENAI_AVAILABLE and os.getenv("OPENAI_API_KEY"):
        print("Using OpenAI...")
        return OpenAIChatClient()

    raise RuntimeError(
        "No AI provider configured. Please set up one of:\n"
        "1. GitHub Models: Set GITHUB_TOKEN in .env file (current setup)\n"
        "2. Azure OpenAI: Set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_DEPLOYMENT\n"
        "3. OpenAI: Set OPENAI_API_KEY environment variable"
    )


async def create_product_search_agent():
    """
    Create a product search agent with all 9 tool functions.

    The agent can:
    - Search products semantically ("warm jacket for skiing")
    - Filter by attributes (brand, price, gender, etc.)
    - Find similar products
    - Get catalog information
    """

    chat_client = create_chat_client()

    # Create agent with all tools
    agent = chat_client.create_agent(
        instructions="""You are a helpful product search assistant for an outdoor
        apparel e-commerce store. You help customers find the perfect outdoor gear
        using semantic search and filtering capabilities.

        Available product categories:
        - Outerwear: Parkas, Down Jackets, Raincoats/Shell Jackets, Vests, Bombers, Fleece
        - Apparel: Shirts, Pants, Shorts, Base Layers, Knitwear
        - Footwear: Hiking boots, Winter boots, Trail running shoes, Water sports shoes

        Brands: NorthPeak, AlpineCo, TrailForge
        Price range: $26 - $775
        Total products: 300

        When searching for products:
        1. Use search_products() for natural language queries
        2. Use filter_products_by_attributes() for exact criteria
        3. Use search_with_filters() for combination of both
        4. Always present products with name, brand, price, and key features
        5. Mention ratings when available
        6. Suggest similar products when appropriate

        Be conversational, helpful, and make recommendations based on user needs.
        """,
        tools=[
            # Search tools
            agent_tools.search_products,
            agent_tools.filter_products_by_attributes,
            agent_tools.search_with_filters,
            agent_tools.search_products_by_category,
            agent_tools.find_similar_products,

            # Catalog information tools
            agent_tools.get_product_details,
            agent_tools.get_available_brands,
            agent_tools.get_available_categories,
            agent_tools.get_catalog_statistics,
        ]
    )

    return agent


async def demo_conversation():
    """Run a demo conversation with the agent."""

    print("=" * 70)
    print("PRODUCT SEARCH AGENT - Microsoft Agent Framework Demo")
    print("=" * 70)
    print()

    # Create agent
    print("Creating product search agent...")
    agent = await create_product_search_agent()
    print("✓ Agent created with 8 tools\n")

    # Demo queries
    queries = [
        "I need a warm jacket for skiing",
        "Show me women's jackets under $300",
        "What brands do you carry?",
    ]

    for i, query in enumerate(queries, 1):
        print(f"\n{'='*70}")
        print(f"Query {i}: {query}")
        print('='*70)

        result = await agent.run(query)
        print(f"\nAgent Response:")
        print(result.text)
        print()

    print("\n" + "="*70)
    print("Demo completed successfully!")
    print("="*70)


async def interactive_mode():
    """Run interactive chat with the agent."""

    print("=" * 70)
    print("INTERACTIVE PRODUCT SEARCH AGENT")
    print("=" * 70)
    print("\nCreating agent...")

    agent = await create_product_search_agent()
    print("✓ Agent ready! Type your questions or 'quit' to exit.\n")

    while True:
        try:
            user_input = input("\nYou: ").strip()

            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break

            if not user_input:
                continue

            print("\nAgent: ", end="", flush=True)
            result = await agent.run(user_input)
            print(result.text)

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\n\nError: {e}")
            print("Please try again.")


def main():
    """Main entry point."""
    import sys

    # Check if products are loaded
    try:
        import chromadb
        client = chromadb.PersistentClient(path="./chroma_db")
        collection = client.get_collection(name="outdoor_products")
        count = collection.count()
        if count == 0:
            print("ERROR: No products found in database!")
            print("Please run: uv run python load_products.py")
            sys.exit(1)
        print(f"✓ {count} products loaded in ChromaDB\n")
    except Exception as e:
        print(f"ERROR: Cannot access ChromaDB: {e}")
        print("Please run: uv run python load_products.py")
        sys.exit(1)

    # Choose mode
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        asyncio.run(interactive_mode())
    else:
        print("Running demo conversation...")
        print("(Use --interactive for chat mode)\n")
        asyncio.run(demo_conversation())


if __name__ == "__main__":
    main()
