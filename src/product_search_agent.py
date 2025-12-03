"""
Product Advisor - Multi-Agent System Entry Point

This is the main entry point for the Product Advisor multi-agent system.
It coordinates three LLM-powered agents:

1. Product Advisor Agent (Orchestrator) - Top-level coordinator
2. PersonalizationAgent - User memory and preferences
3. ProductSearchAgent - Product search and filtering

Requirements:
- Microsoft Agent Framework: uv add agent-framework --prerelease=allow
- One of: Azure OpenAI, OpenAI, or GitHub Models credentials
"""

import asyncio
import sys
from dotenv import load_dotenv

# Load environment variables from .env file (override system env vars)
load_dotenv(override=True)

from src.agents.product_advisor_agent import create_product_advisor_agent


async def interactive_mode():
    """Run interactive chat with the Product Advisor agent."""

    print("=" * 70)
    print("PRODUCT ADVISOR - Multi-Agent System")
    print("=" * 70)
    print("\nArchitecture:")
    print("  Product Advisor (Orchestrator)")
    print("    ├── PersonalizationAgent (User Memory)")
    print("    └── ProductSearchAgent (Product Search)")
    print("\nInitializing agents...")

    agent = await create_product_advisor_agent()
    print("✓ All agents ready!")

    # Create a persistent thread for the conversation
    print("Starting conversation thread...")
    thread = agent.get_new_thread()
    print("✓ Thread created! Type your questions or 'quit' to exit.\n")

    while True:
        try:
            user_input = input("\nYou: ").strip()

            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break

            if not user_input:
                continue

            print("\nAdvisor: ", end="", flush=True)
            result = await agent.run(user_input, thread=thread)
            print(result.text)

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\n\nError: {e}")
            print("Please try again.")


def main():
    """Main entry point."""

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

    # Run interactive mode
    asyncio.run(interactive_mode())


if __name__ == "__main__":
    main()
