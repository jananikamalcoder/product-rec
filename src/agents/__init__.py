"""
Multi-Agent System for Product Recommendations.

Architecture:
    Product Advisor Agent (Orchestrator)
      ├── PersonalizationAgent (User Memory & Preferences)
      └── ProductSearchAgent (Product Search & Filtering)

Agents:
- ProductAdvisorAgent: Top-level orchestrator that coordinates other agents
- PersonalizationAgent: User-aware preference management with memory
- ProductSearchAgent: Semantic and filtered product search
- VisualFormattingTool: Product data visualization (cards, tables, matrices)

Usage:
    from src.agents.product_advisor_agent import create_product_advisor_agent

    # Create the multi-agent system
    agent = await create_product_advisor_agent()
    thread = agent.get_new_thread()
    result = await agent.run("Hi, I'm Sarah. I need a warm jacket", thread=thread)
"""

from src.agents.personalization_agent import (
    PersonalizationAgent,
    create_personalization_agent,
    get_user_preferences,
    save_user_preferences,
    process_user_feedback,
    check_returning_user,
    get_returning_user_prompt
)

from src.agents.product_search_agent import (
    create_product_search_agent
)

from src.agents.product_advisor_agent import (
    create_product_advisor_agent
)

from src.agents.memory import (
    UserMemory,
    get_memory
)

from src.agents.visual_formatting_tool import (
    VisualFormattingTool,
    VisualAgent,  # Backward compatibility alias
    create_product_card,
    create_comparison_table,
    create_feature_matrix,
    create_price_visualization,
    format_product_list,
    visualize_products
)

__all__ = [
    # Product Advisor Agent (Main Entry Point)
    "create_product_advisor_agent",

    # Sub-Agents
    "create_personalization_agent",
    "create_product_search_agent",

    # Personalization Agent (class + convenience functions)
    "PersonalizationAgent",
    "get_user_preferences",
    "save_user_preferences",
    "process_user_feedback",
    "check_returning_user",
    "get_returning_user_prompt",

    # Memory
    "UserMemory",
    "get_memory",

    # Visual Formatting Tool
    "VisualFormattingTool",
    "VisualAgent",  # Backward compatibility alias
    "create_product_card",
    "create_comparison_table",
    "create_feature_matrix",
    "create_price_visualization",
    "format_product_list",
    "visualize_products"
]
