"""
Multi-Agent System for Product Recommendations.

Agents:
- StylingAgent: Understands user styling intent, builds outfit recommendations
- Orchestrator: Coordinates between agents, routes queries appropriately

Usage:
    from src.agents import StylingAgent, Orchestrator

    # Direct styling queries
    styling_agent = StylingAgent()
    result = styling_agent.get_outfit_recommendation("I need an outfit for hiking")

    # Full orchestration (auto-routes to appropriate agent)
    orchestrator = Orchestrator()
    result = orchestrator.process_query("Help me dress for skiing")
"""

from src.agents.styling_agent import (
    StylingAgent,
    StylingContext,
    Activity,
    Weather,
    StylePreference,
    extract_styling_intent,
    get_outfit_search_params,
    build_outfit_for_activity
)

from src.agents.orchestrator import (
    Orchestrator,
    QueryIntent,
    OrchestratorResult,
    process_user_query
)

__all__ = [
    # Styling Agent
    "StylingAgent",
    "StylingContext",
    "Activity",
    "Weather",
    "StylePreference",
    "extract_styling_intent",
    "get_outfit_search_params",
    "build_outfit_for_activity",

    # Orchestrator
    "Orchestrator",
    "QueryIntent",
    "OrchestratorResult",
    "process_user_query"
]
