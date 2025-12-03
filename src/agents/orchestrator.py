"""
Orchestrator Agent - Coordinates between Personalization Agent and Product Search Agent.

This agent:
1. Receives user queries
2. Determines if it's a styling/outfit query or a direct product search
3. Routes to appropriate agent(s)
4. Combines results into a coherent response
"""

import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

from src.agents.personalization_agent import PersonalizationAgent, PersonalizationContext
from src.product_search import ProductSearch


class QueryIntent(Enum):
    """Types of user query intents."""
    STYLING = "styling"           # Outfit/styling recommendations
    PRODUCT_SEARCH = "search"     # Direct product search
    COMPARISON = "comparison"     # Compare products
    INFO = "info"                 # Catalog info (brands, categories)
    UNKNOWN = "unknown"


@dataclass
class OrchestratorResult:
    """Result from orchestrator processing."""
    intent: QueryIntent
    personalization_context: Optional[Dict] = None
    products: List[Dict] = None
    outfit_recommendation: Dict = None
    message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "intent": self.intent.value,
            "personalization_context": self.personalization_context,
            "products": self.products or [],
            "outfit_recommendation": self.outfit_recommendation,
            "message": self.message
        }


class Orchestrator:
    """
    Main orchestrator that coordinates Personalization Agent and Product Search.

    Flow:
    1. User query → Orchestrator
    2. Orchestrator → Classify intent
    3. If styling intent → Personalization Agent → Get outfit params → Product Search
    4. If search intent → Product Search directly
    5. Combine and return results
    """

    def __init__(self, use_llm: bool = True):
        """
        Initialize the Orchestrator.

        Args:
            use_llm: Whether to use LLM for intent classification
        """
        self.personalization_agent = PersonalizationAgent(use_llm=use_llm)
        self.product_search = ProductSearch(db_path="./chroma_db")
        self.use_llm = use_llm and self._check_llm_available()
        self.llm_client = None

        if self.use_llm:
            self._init_llm_client()

    def _check_llm_available(self) -> bool:
        """Check if LLM API is available."""
        return bool(os.environ.get("GITHUB_TOKEN") or
                   os.environ.get("OPENAI_API_KEY"))

    def _init_llm_client(self):
        """Initialize LLM client for intent classification."""
        try:
            from openai import OpenAI

            if os.environ.get("GITHUB_TOKEN"):
                self.llm_client = OpenAI(
                    base_url="https://models.inference.ai.azure.com",
                    api_key=os.environ.get("GITHUB_TOKEN")
                )
                self.model = "gpt-4o-mini"
            elif os.environ.get("OPENAI_API_KEY"):
                self.llm_client = OpenAI()
                self.model = "gpt-4o-mini"
        except ImportError:
            self.use_llm = False

    def classify_intent(self, query: str) -> QueryIntent:
        """
        Classify the user's query intent.

        Args:
            query: User's natural language query

        Returns:
            QueryIntent enum
        """
        if self.use_llm and self.llm_client:
            return self._classify_with_llm(query)
        return self._classify_rule_based(query)

    def _classify_with_llm(self, query: str) -> QueryIntent:
        """Use LLM to classify query intent."""
        try:
            response = self.llm_client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """Classify the user query into one of these categories:
- STYLING: User wants outfit recommendations, what to wear, styling advice
- SEARCH: User wants to find specific products
- COMPARISON: User wants to compare products
- INFO: User wants catalog info (brands, categories, stats)

Return ONLY one word: STYLING, SEARCH, COMPARISON, or INFO"""
                    },
                    {"role": "user", "content": query}
                ],
                temperature=0,
                max_tokens=20
            )

            result = response.choices[0].message.content.strip().upper()
            intent_map = {
                "STYLING": QueryIntent.STYLING,
                "SEARCH": QueryIntent.PRODUCT_SEARCH,
                "COMPARISON": QueryIntent.COMPARISON,
                "INFO": QueryIntent.INFO
            }
            return intent_map.get(result, QueryIntent.UNKNOWN)
        except Exception:
            return self._classify_rule_based(query)

    def _classify_rule_based(self, query: str) -> QueryIntent:
        """Rule-based query classification."""
        query_lower = query.lower()

        # Styling keywords
        styling_keywords = [
            "outfit", "wear", "dress", "style", "look", "fashion",
            "complete", "matching", "coordinate", "wardrobe",
            "what should i", "help me dress", "recommend an outfit"
        ]
        if any(kw in query_lower for kw in styling_keywords):
            return QueryIntent.STYLING

        # Comparison keywords
        comparison_keywords = ["compare", "versus", "vs", "difference", "better"]
        if any(kw in query_lower for kw in comparison_keywords):
            return QueryIntent.COMPARISON

        # Info keywords
        info_keywords = ["brands", "categories", "how many", "statistics", "catalog"]
        if any(kw in query_lower for kw in info_keywords):
            return QueryIntent.INFO

        # Default to product search
        return QueryIntent.PRODUCT_SEARCH

    def process_query(self, query: str) -> OrchestratorResult:
        """
        Main entry point: Process user query and return results.

        Args:
            query: User's natural language query

        Returns:
            OrchestratorResult with products and recommendations
        """
        intent = self.classify_intent(query)

        if intent == QueryIntent.STYLING:
            return self._handle_styling_query(query)
        elif intent == QueryIntent.PRODUCT_SEARCH:
            return self._handle_search_query(query)
        elif intent == QueryIntent.COMPARISON:
            return self._handle_comparison_query(query)
        elif intent == QueryIntent.INFO:
            return self._handle_info_query(query)
        else:
            return self._handle_search_query(query)

    def _handle_styling_query(self, query: str, user_id: Optional[str] = None) -> OrchestratorResult:
        """
        Handle styling/outfit queries.

        Flow:
        1. Personalization Agent extracts context (with user preferences if available)
        2. Build search params for each outfit category
        3. Search products for each category
        4. Return combined outfit recommendation
        """
        # Get personalized recommendation
        outfit_result = self.personalization_agent.get_personalized_recommendation(query, user_id)
        context = outfit_result["personalization_context"]

        # Search products for each outfit category
        all_products = []
        outfit_items = {}

        for search_config in outfit_result["search_parameters"]["outfit_searches"]:
            category = search_config["category"]
            keywords = " ".join(search_config.get("query_keywords", []))
            filters = search_config.get("filters", {})

            # Build search query
            search_query = f"{keywords} {category}"

            # Search with filters
            products = self.product_search.search_semantic(
                query=search_query,
                n_results=5
            )

            # Apply additional filters
            filtered_products = self._apply_filters(products, filters)

            if filtered_products:
                outfit_items[category] = filtered_products[:2]  # Top 2 per category
                all_products.extend(filtered_products[:2])

        # Generate response message
        message = self._generate_outfit_message(context, outfit_items)

        return OrchestratorResult(
            intent=QueryIntent.STYLING,
            personalization_context=context,
            products=all_products,
            outfit_recommendation={
                "categories": outfit_items,
                "total_items": len(all_products),
                "preferences_applied": outfit_result.get("preferences_applied", False)
            },
            message=message
        )

    def _handle_search_query(self, query: str) -> OrchestratorResult:
        """Handle direct product search queries."""
        products = self.product_search.search_semantic(query, n_results=10)

        return OrchestratorResult(
            intent=QueryIntent.PRODUCT_SEARCH,
            products=products,
            message=f"Found {len(products)} products matching your search."
        )

    def _handle_comparison_query(self, query: str) -> OrchestratorResult:
        """Handle product comparison queries."""
        # Extract product type from query and search
        products = self.product_search.search_semantic(query, n_results=5)

        return OrchestratorResult(
            intent=QueryIntent.COMPARISON,
            products=products,
            message=f"Here are {len(products)} products to compare."
        )

    def _handle_info_query(self, query: str) -> OrchestratorResult:
        """Handle catalog info queries."""
        # Get catalog stats
        stats = self.product_search.collection.count()

        return OrchestratorResult(
            intent=QueryIntent.INFO,
            message=f"Our catalog contains {stats} products from brands like NorthPeak, AlpineCo, and TrailForge."
        )

    def _apply_filters(self, products: List[Dict], filters: Dict) -> List[Dict]:
        """Apply filters to product list."""
        filtered = products

        if "gender" in filters:
            gender = filters["gender"]
            filtered = [p for p in filtered if p.get("gender") == gender or p.get("gender") == "Unisex"]

        if "max_price" in filters:
            max_price = filters["max_price"]
            filtered = [p for p in filtered if p.get("price_usd", 0) <= max_price]

        if "season" in filters:
            seasons = filters["season"]
            filtered = [p for p in filtered if p.get("season") in seasons or p.get("season") == "All-season"]

        if "brands" in filters:
            brands = [b.lower() for b in filters["brands"]]
            filtered = [p for p in filtered if (p.get("brand") or "").lower() in brands]

        if "colors" in filters:
            colors = [c.lower() for c in filters["colors"]]
            filtered = [p for p in filtered if any(
                c in (p.get("color") or "").lower() for c in colors
            )]

        return filtered

    def _generate_outfit_message(self, context: Dict, outfit_items: Dict) -> str:
        """Generate natural language response for outfit recommendation."""
        parts = []

        activity = context.get("activity", "unknown")
        weather = context.get("weather", "unknown")

        if activity != "unknown":
            parts.append(f"For {activity}")
        if weather != "unknown":
            parts.append(f"in {weather} weather")

        intro = " ".join(parts) if parts else "Here's a recommended outfit"

        categories_found = list(outfit_items.keys())
        total_items = sum(len(items) for items in outfit_items.values())

        message = f"{intro}, I've found {total_items} items across {len(categories_found)} categories: {', '.join(categories_found)}."

        return message


# Convenience function for direct use
def process_user_query(query: str) -> Dict[str, Any]:
    """
    Process a user query through the orchestrator.

    Args:
        query: User's natural language query

    Returns:
        Dictionary with results
    """
    orchestrator = Orchestrator()
    result = orchestrator.process_query(query)
    return result.to_dict()


if __name__ == "__main__":
    # Test the orchestrator
    orchestrator = Orchestrator()

    test_queries = [
        "I need an outfit for winter hiking",
        "Show me waterproof jackets under $300",
        "What brands do you have?",
        "Compare NorthPeak parkas",
        "Help me dress for a ski trip"
    ]

    print("=" * 70)
    print("ORCHESTRATOR TEST")
    print("=" * 70)

    for query in test_queries:
        print(f"\nQuery: {query}")
        print("-" * 50)
        result = orchestrator.process_query(query)
        print(f"Intent: {result.intent.value}")
        print(f"Message: {result.message}")
        if result.products:
            print(f"Products found: {len(result.products)}")
            for p in result.products[:2]:
                print(f"  - {p.get('product_name', 'N/A')} (${p.get('price_usd', 0)})")
