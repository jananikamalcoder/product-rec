"""
DeepEval configuration and fixtures for LLM agent evaluations.

This module provides:
- DeepEval configuration
- Async fixtures for LLM agents
- Ground truth fixtures for evaluation
- Cleanup of test users created during evals
"""

import pytest
import pytest_asyncio
import asyncio
import os

from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# Track users created during evals for cleanup
_eval_test_users = set()


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "eval: marks tests as LLM evaluations (may be slow)")
    config.addinivalue_line("markers", "asyncio: marks tests as async")


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="module")
async def personalization_agent():
    """Create PersonalizationAgent for evals."""
    from src.agents.personalization_agent import create_personalization_agent
    agent = await create_personalization_agent()
    return agent


@pytest_asyncio.fixture(scope="module")
async def search_agent():
    """Create ProductSearchAgent for evals."""
    from src.agents.product_search_agent import create_product_search_agent
    agent = await create_product_search_agent()
    return agent


@pytest_asyncio.fixture(scope="module")
async def advisor_agent():
    """Create ProductAdvisorAgent for evals."""
    from src.agents.product_advisor_agent import create_product_advisor_agent
    agent = await create_product_advisor_agent()
    return agent


@pytest.fixture
def search_engine():
    """ProductSearch for ground truth data."""
    from src.product_search import ProductSearch
    return ProductSearch(db_path="./chroma_db")


@pytest.fixture
def test_user_id():
    """Test user identifier for evals."""
    return "eval_test_user"


@pytest.fixture
def sample_search_query():
    """Sample search query for evals."""
    return "waterproof jacket for hiking"


@pytest.fixture
def sample_user_context():
    """Sample user context for search evals."""
    return {
        "fit": "relaxed",
        "budget_max": 300,
        "colors": ["blue", "black"]
    }


@pytest.fixture(autouse=True)
def cleanup_eval_users():
    """Clean up any test users created during evals."""
    # Run the test
    yield

    # Cleanup after test: remove users created during evals
    try:
        from src.agents.memory import get_memory
        memory = get_memory()

        # List of known eval test user patterns
        eval_patterns = [
            "evaltestuser", "evaltest", "newtestuser", "partialuser",
            "feedbackuser", "teststructureuser", "newpersonforeval",
            "feedback_loop_user", "pipeline_test_user", "sarah", "alex"
        ]

        for user_id in list(memory.data.keys()):
            user_lower = user_id.lower()
            if any(pattern in user_lower for pattern in eval_patterns):
                memory.delete_user(user_id)
    except Exception:
        pass  # Ignore cleanup errors
