"""
Multi-Agent System for Product Recommendations.

Agents:
- PersonalizationAgent: User-aware styling with memory (preferences, sizing, feedback)
- VisualAgent: Product data visualization (cards, tables, matrices, price analysis)
- Orchestrator: Coordinates between agents, routes queries appropriately

Usage:
    from src.agents import PersonalizationAgent, VisualAgent, Orchestrator

    # Direct personalization queries
    agent = PersonalizationAgent()
    result = agent.get_personalized_recommendation("I need an outfit for hiking", user_id="sarah")

    # Visualization
    visual = VisualAgent()
    card = visual.create_product_card(product_data)
    table = visual.create_comparison_table(products)

    # Full orchestration (auto-routes to appropriate agent)
    orchestrator = Orchestrator()
    result = orchestrator.process_query("Help me dress for skiing")
"""

from src.agents.personalization_agent import (
    PersonalizationAgent,
    PersonalizationContext,
    Activity,
    Weather,
    StylePreference,
    FitPreference,
    get_user_preferences,
    save_user_preferences,
    process_user_feedback,
    check_returning_user,
    get_returning_user_prompt
)

from src.agents.memory import (
    UserMemory,
    get_memory
)

from src.agents.orchestrator import (
    Orchestrator,
    QueryIntent,
    OrchestratorResult,
    process_user_query
)

from src.agents.visual_agent import (
    VisualAgent,
    create_product_card,
    create_comparison_table,
    create_feature_matrix,
    create_price_visualization,
    format_product_list,
    visualize_products
)

__all__ = [
    # Personalization Agent
    "PersonalizationAgent",
    "PersonalizationContext",
    "Activity",
    "Weather",
    "StylePreference",
    "FitPreference",
    "get_user_preferences",
    "save_user_preferences",
    "process_user_feedback",
    "check_returning_user",
    "get_returning_user_prompt",

    # Memory
    "UserMemory",
    "get_memory",

    # Orchestrator
    "Orchestrator",
    "QueryIntent",
    "OrchestratorResult",
    "process_user_query",

    # Visual Agent
    "VisualAgent",
    "create_product_card",
    "create_comparison_table",
    "create_feature_matrix",
    "create_price_visualization",
    "format_product_list",
    "visualize_products"
]
