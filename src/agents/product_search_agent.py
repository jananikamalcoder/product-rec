"""
Product Search Agent - LLM-powered product search specialist.

This agent handles:
1. Semantic product search (natural language queries)
2. Attribute-based filtering
3. Hybrid search (semantic + filters)
4. Finding similar products
5. Catalog information

Uses the Microsoft Agent Framework to create an LLM-based agent
with search tools.
"""

import os
from typing import Any, Dict, Optional

from dotenv import load_dotenv

from src.product_search import ProductSearch

# Load environment variables
load_dotenv(override=True)

# Try to import agent framework
try:
    from agent_framework.openai import OpenAIChatClient
    AGENT_FRAMEWORK_AVAILABLE = True
except ImportError:
    AGENT_FRAMEWORK_AVAILABLE = False


# Initialize the search engine (singleton pattern)
_search_engine = None


def _get_search_engine() -> ProductSearch:
    """Get or create the ProductSearch engine instance."""
    global _search_engine
    if _search_engine is None:
        try:
            _search_engine = ProductSearch(db_path="./chroma_db")
        except Exception as e:
            raise RuntimeError(
                f"Failed to initialize ProductSearch. Ensure ChromaDB is set up. "
                f"Run 'python src/load_products.py' first. Error: {e}"
            ) from e
    return _search_engine


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


async def create_product_search_agent():
    """
    Create a ProductSearchAgent as an LLM-powered agent.

    Returns:
        Agent instance with product search tools
    """
    chat_client = _create_chat_client()

    # Define search tool functions
    def search_products(
        query: str,
        max_results: int = 10,
        min_similarity: float = 0.0
    ) -> Dict[str, Any]:
        """
        Search for products using natural language query (semantic search).

        This tool uses AI embeddings to understand the meaning of your query.

        Args:
            query: Natural language search query
                   Examples: "warm winter jacket for skiing",
                            "lightweight waterproof hiking gear"
            max_results: Maximum products to return (1-50, default: 10)
            min_similarity: Minimum similarity threshold (0.0-1.0)

        Returns:
            Dictionary with success, query, total_results, products list
        """
        try:
            search = _get_search_engine()
            results = search.search_semantic(query, n_results=min(max_results, 50))

            if min_similarity > 0:
                results = [p for p in results if p.get('similarity_score', 0) >= min_similarity]

            return {
                "success": True,
                "query": query,
                "total_results": len(results),
                "products": results
            }
        except Exception as e:
            return {
                "success": False,
                "query": query,
                "total_results": 0,
                "products": [],
                "error": str(e)
            }

    def filter_products_by_attributes(
        brand: Optional[str] = None,
        category: Optional[str] = None,
        subcategory: Optional[str] = None,
        gender: Optional[str] = None,
        season: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_rating: Optional[float] = None,
        waterproofing: Optional[str] = None,
        insulation: Optional[str] = None,
        max_results: int = 10
    ) -> Dict[str, Any]:
        """
        Filter products by specific attributes (exact match).

        Args:
            brand: Filter by brand (e.g., "NorthPeak", "AlpineCo")
            category: Filter by category (e.g., "Outerwear", "Footwear")
            subcategory: Filter by subcategory (e.g., "Down Jackets", "Parkas")
            gender: Filter by gender ("Men", "Women", "Unisex")
            season: Filter by season ("Winter", "All-season")
            min_price: Minimum price in USD
            max_price: Maximum price in USD
            min_rating: Minimum rating (0.0-5.0)
            waterproofing: Filter by waterproofing level
            insulation: Filter by insulation type
            max_results: Maximum products to return (default: 10)

        Returns:
            Dictionary with success, filters_applied, total_results, products
        """
        try:
            search = _get_search_engine()
            filter_conditions = []

            if brand:
                filter_conditions.append({"brand": {"$eq": brand}})
            if category:
                filter_conditions.append({"category": {"$eq": category}})
            if subcategory:
                filter_conditions.append({"subcategory": {"$eq": subcategory}})
            if gender:
                filter_conditions.append({"gender": {"$eq": gender}})
            if season:
                filter_conditions.append({"season": {"$eq": season}})
            if waterproofing:
                filter_conditions.append({"waterproofing": {"$eq": waterproofing}})
            if insulation:
                filter_conditions.append({"insulation": {"$eq": insulation}})
            if min_price is not None:
                filter_conditions.append({"price_usd": {"$gte": min_price}})
            if max_price is not None:
                filter_conditions.append({"price_usd": {"$lte": max_price}})
            if min_rating is not None:
                filter_conditions.append({"rating": {"$gte": min_rating}})

            if not filter_conditions:
                return {"success": False, "total_results": 0, "products": [],
                        "error": "No filters specified."}

            if len(filter_conditions) == 1:
                filters = filter_conditions[0]
            else:
                filters = {"$and": filter_conditions}
            results = search.search_by_filters(filters, n_results=max_results)

            return {
                "success": True,
                "filters_applied": {
                    "brand": brand, "category": category, "subcategory": subcategory,
                    "gender": gender, "season": season, "min_price": min_price,
                    "max_price": max_price, "min_rating": min_rating,
                    "waterproofing": waterproofing, "insulation": insulation
                },
                "total_results": len(results),
                "products": results
            }
        except Exception as e:
            return {
                "success": False,
                "total_results": 0,
                "products": [],
                "error": str(e)
            }

    def search_with_filters(
        query: str,
        brand: Optional[str] = None,
        category: Optional[str] = None,
        gender: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        max_results: int = 10
    ) -> Dict[str, Any]:
        """
        Hybrid search: semantic search with attribute filters.

        Combines natural language understanding with exact filters.

        Args:
            query: Natural language search query
            brand: Filter by brand
            category: Filter by category
            gender: Filter by gender
            min_price: Minimum price in USD
            max_price: Maximum price in USD
            max_results: Maximum results (default: 10)

        Returns:
            Dictionary with results matching both query AND filters
        """
        try:
            search = _get_search_engine()
            filter_conditions = []

            if brand:
                filter_conditions.append({"brand": {"$eq": brand}})
            if category:
                filter_conditions.append({"category": {"$eq": category}})
            if gender:
                filter_conditions.append({"gender": {"$eq": gender}})
            if min_price is not None:
                filter_conditions.append({"price_usd": {"$gte": min_price}})
            if max_price is not None:
                filter_conditions.append({"price_usd": {"$lte": max_price}})

            filters = None
            if filter_conditions:
                if len(filter_conditions) == 1:
                    filters = filter_conditions[0]
                else:
                    filters = {"$and": filter_conditions}

            results = search.hybrid_search(query, filters=filters, n_results=max_results)

            return {
                "success": True,
                "query": query,
                "filters_applied": {
                    "brand": brand, "category": category, "gender": gender,
                    "min_price": min_price, "max_price": max_price
                },
                "total_results": len(results),
                "products": results
            }
        except Exception as e:
            return {
                "success": False,
                "query": query,
                "total_results": 0,
                "products": [],
                "error": str(e)
            }

    def find_similar_products(product_id: str, max_results: int = 5) -> Dict[str, Any]:
        """
        Find products similar to a specific product.

        Args:
            product_id: The ID of the reference product (e.g., "PRD-6A6DD909")
            max_results: Number of similar products to return (default: 5)

        Returns:
            Dictionary with reference_product_id, total_results, products
        """
        try:
            search = _get_search_engine()
            results = search.get_similar_products(product_id, n_results=max_results)
            return {
                "success": True,
                "reference_product_id": product_id,
                "total_results": len(results),
                "products": results
            }
        except Exception as e:
            return {
                "success": False,
                "reference_product_id": product_id,
                "total_results": 0,
                "products": [],
                "error": str(e)
            }

    def get_product_details(product_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific product.

        Args:
            product_id: The product ID (e.g., "PRD-6A6DD909")

        Returns:
            Dictionary with success, product_id, and product details
        """
        try:
            search = _get_search_engine()
            result = search.collection.get(ids=[product_id], include=["metadatas"])

            if result['metadatas']:
                return {
                    "success": True,
                    "product_id": product_id,
                    "product": result['metadatas'][0]
                }
            return {
                "success": False,
                "product_id": product_id,
                "product": None,
                "error": f"Product '{product_id}' not found"
            }
        except Exception as e:
            return {
                "success": False,
                "product_id": product_id,
                "product": None,
                "error": str(e)
            }

    def get_available_brands() -> Dict[str, Any]:
        """
        Get list of all available brands in the catalog.

        Returns:
            Dictionary with success, total_brands, brands list
        """
        try:
            search = _get_search_engine()
            all_products = search.collection.get(limit=1000)
            brands = sorted(set(m['brand'] for m in all_products['metadatas']))
            return {"success": True, "total_brands": len(brands), "brands": brands}
        except Exception as e:
            return {"success": False, "total_brands": 0, "brands": [], "error": str(e)}

    def get_available_categories() -> Dict[str, Any]:
        """
        Get list of all categories and subcategories.

        Returns:
            Dictionary with success and categories mapping
        """
        try:
            search = _get_search_engine()
            all_products = search.collection.get(limit=1000)

            categories = {}
            for m in all_products['metadatas']:
                cat = m['category']
                subcat = m['subcategory']
                if cat not in categories:
                    categories[cat] = set()
                categories[cat].add(subcat)

            categories = {k: sorted(list(v)) for k, v in categories.items()}
            return {"success": True, "categories": categories}
        except Exception as e:
            return {"success": False, "categories": {}, "error": str(e)}

    # Create the agent
    agent = chat_client.create_agent(
        instructions="""You are a product search specialist for an outdoor apparel store.

Your job is to:
1. Search for products based on user queries (use search_products for semantic search)
2. Apply filters when user specifies constraints (brand, price, gender, etc.)
3. Use search_with_filters for combined semantic + filter searches
4. Find similar products when requested
5. Provide product details when asked about specific items

SEARCH STRATEGY:
- For vague queries ("warm jacket") → use search_products
- For specific constraints ("women's jacket under $200") → use search_with_filters
- For browsing ("show me NorthPeak products") → use filter_products_by_attributes
- For alternatives ("something like this one") → use find_similar_products

CRITICAL - OUTPUT FORMAT:
- Return the RAW JSON output from search tools directly
- Do NOT format results as markdown, tables, or bullet points
- Do NOT add commentary or descriptions around the JSON
- Just return the tool's JSON output as-is
- The Advisor agent will handle all formatting and visualization

Example response (just return this, nothing else):
{"success": true, "total_results": 5, "products": [...]}

IMPORTANT:
- You will receive user context (preferences, sizing, budget) from the Advisor
- Apply this context to your searches using filters
- Focus ONLY on search tasks - don't handle personalization""",
        tools=[
            search_products,
            filter_products_by_attributes,
            search_with_filters,
            find_similar_products,
            get_product_details,
            get_available_brands,
            get_available_categories,
        ]
    )

    return agent
