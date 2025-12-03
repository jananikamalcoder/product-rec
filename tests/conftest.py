"""
Pytest configuration and fixtures for multi-agent product recommendation tests.

Fixtures:
- temp_memory_file: Temporary JSON file for UserMemory
- sample_products: List of sample product dictionaries
- sample_user_preferences: Valid user preference structure
- memory: UserMemory instance with temp file
- personalization_agent: PersonalizationAgent (no LLM)
- visual_agent: VisualAgent instance
- orchestrator: Orchestrator (no LLM)
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Any
from unittest.mock import MagicMock, patch

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


# ============================================================================
# TEMPORARY FILE FIXTURES
# ============================================================================

@pytest.fixture
def temp_memory_file(tmp_path):
    """Create a temporary JSON file for UserMemory."""
    file_path = tmp_path / "test_user_preferences.json"
    file_path.write_text("{}")
    return str(file_path)


@pytest.fixture
def temp_memory_file_with_data(tmp_path):
    """Create a temporary JSON file with pre-existing user data."""
    file_path = tmp_path / "test_user_preferences.json"
    data = {
        "sarah": {
            "sizing": {"fit": "relaxed", "shirt": "M", "pants": "32"},
            "preferences": {
                "outerwear": {"colors": ["blue", "black"], "style": "technical"}
            },
            "general": {"budget_max": 300, "brands_liked": ["NorthPeak"]},
            "feedback": [],
            "created_at": "2025-01-01T00:00:00",
            "last_seen": "2025-01-01T00:00:00"
        },
        "john": {
            "sizing": {"fit": "classic", "shirt": "L"},
            "preferences": {},
            "general": {},
            "feedback": [],
            "created_at": "2025-01-01T00:00:00",
            "last_seen": "2025-01-01T00:00:00"
        }
    }
    file_path.write_text(json.dumps(data, indent=2))
    return str(file_path)


@pytest.fixture
def corrupted_json_file(tmp_path):
    """Create a corrupted JSON file."""
    file_path = tmp_path / "corrupted.json"
    file_path.write_text("{invalid json: }")
    return str(file_path)


# ============================================================================
# SAMPLE DATA FIXTURES
# ============================================================================

@pytest.fixture
def sample_product():
    """Single sample product with all fields."""
    return {
        "product_id": "PROD001",
        "product_name": "Summit Pro Parka",
        "brand": "NorthPeak",
        "category": "Outerwear",
        "subcategory": "Parkas",
        "price_usd": 275.00,
        "rating": 4.8,
        "gender": "Women",
        "season": "Winter",
        "waterproofing": "Waterproof",
        "insulation": "Down 700-fill",
        "material": "Recycled Nylon",
        "color": "Navy Blue",
        "primary_purpose": "Cold weather exploration"
    }


@pytest.fixture
def sample_products():
    """List of 10 sample products with varied attributes."""
    return [
        {
            "product_id": "PROD001",
            "product_name": "Summit Pro Parka",
            "brand": "NorthPeak",
            "category": "Outerwear",
            "subcategory": "Parkas",
            "price_usd": 275.00,
            "rating": 4.8,
            "gender": "Women",
            "season": "Winter",
            "waterproofing": "Waterproof",
            "insulation": "Down 700-fill",
            "material": "Recycled Nylon",
            "color": "Navy Blue",
            "primary_purpose": "Cold weather exploration"
        },
        {
            "product_id": "PROD002",
            "product_name": "Alpine Shell Jacket",
            "brand": "AlpineCo",
            "category": "Outerwear",
            "subcategory": "Shell Jackets",
            "price_usd": 320.00,
            "rating": 4.6,
            "gender": "Men",
            "season": "All-season",
            "waterproofing": "Waterproof",
            "insulation": "None",
            "material": "Gore-Tex",
            "color": "Black",
            "primary_purpose": "Technical climbing"
        },
        {
            "product_id": "PROD003",
            "product_name": "Peak Insulator",
            "brand": "TrailForge",
            "category": "Outerwear",
            "subcategory": "Insulated Jackets",
            "price_usd": 245.00,
            "rating": 4.7,
            "gender": "Unisex",
            "season": "Winter",
            "waterproofing": "Water-resistant",
            "insulation": "Synthetic",
            "material": "Polyester",
            "color": "Red",
            "primary_purpose": "Everyday warmth"
        },
        {
            "product_id": "PROD004",
            "product_name": "Trail Runner Pro",
            "brand": "NorthPeak",
            "category": "Footwear",
            "subcategory": "Running Shoes",
            "price_usd": 145.00,
            "rating": 4.5,
            "gender": "Men",
            "season": "All-season",
            "waterproofing": "None",
            "insulation": "None",
            "material": "Mesh",
            "color": "Gray/Green",
            "primary_purpose": "Trail running"
        },
        {
            "product_id": "PROD005",
            "product_name": "Winter Hiking Boot",
            "brand": "AlpineCo",
            "category": "Footwear",
            "subcategory": "Hiking Boots",
            "price_usd": 225.00,
            "rating": 4.9,
            "gender": "Women",
            "season": "Winter",
            "waterproofing": "Waterproof",
            "insulation": "Thinsulate",
            "material": "Leather/Synthetic",
            "color": "Brown",
            "primary_purpose": "Winter hiking"
        },
        {
            "product_id": "PROD006",
            "product_name": "Fleece Midlayer",
            "brand": "TrailForge",
            "category": "Apparel",
            "subcategory": "Fleece",
            "price_usd": 89.00,
            "rating": 4.3,
            "gender": "Unisex",
            "season": "All-season",
            "waterproofing": "None",
            "insulation": "Fleece",
            "material": "Recycled Polyester",
            "color": "Blue",
            "primary_purpose": "Layering"
        },
        {
            "product_id": "PROD007",
            "product_name": "Technical Hiking Pants",
            "brand": "NorthPeak",
            "category": "Apparel",
            "subcategory": "Pants",
            "price_usd": 125.00,
            "rating": 4.4,
            "gender": "Men",
            "season": "All-season",
            "waterproofing": "Water-resistant",
            "insulation": "None",
            "material": "Nylon Stretch",
            "color": "Charcoal",
            "primary_purpose": "Hiking"
        },
        {
            "product_id": "PROD008",
            "product_name": "Down Expedition Jacket",
            "brand": "AlpineCo",
            "category": "Outerwear",
            "subcategory": "Down Jackets",
            "price_usd": 425.00,
            "rating": 4.9,
            "gender": "Unisex",
            "season": "Winter",
            "waterproofing": "Water-resistant",
            "insulation": "Down 850-fill",
            "material": "Ripstop Nylon",
            "color": "Orange",
            "primary_purpose": "Extreme cold"
        },
        {
            "product_id": "PROD009",
            "product_name": "Casual Everyday Jacket",
            "brand": "TrailForge",
            "category": "Outerwear",
            "subcategory": "Casual Jackets",
            "price_usd": 165.00,
            "rating": 4.2,
            "gender": "Women",
            "season": "Spring",
            "waterproofing": "Water-resistant",
            "insulation": "Light",
            "material": "Cotton Blend",
            "color": "Olive",
            "primary_purpose": "Casual wear"
        },
        {
            "product_id": "PROD010",
            "product_name": "Ultralight Backpack 35L",
            "brand": "NorthPeak",
            "category": "Accessories/Gear",
            "subcategory": "Backpacks",
            "price_usd": 189.00,
            "rating": 4.6,
            "gender": "Unisex",
            "season": "All-season",
            "waterproofing": "Water-resistant",
            "insulation": "None",
            "material": "Dyneema",
            "color": "Black/Gray",
            "primary_purpose": "Multi-day hiking"
        }
    ]


@pytest.fixture
def sample_products_minimal():
    """Products with minimal required fields only."""
    return [
        {"product_name": "Basic Jacket", "price_usd": 100.00, "rating": 4.0},
        {"product_name": "Basic Shoes", "price_usd": 80.00, "rating": 3.5},
    ]


@pytest.fixture
def sample_products_same_price():
    """Products with identical prices for tie-testing."""
    return [
        {"product_id": "P1", "product_name": "Product A", "price_usd": 200.00, "rating": 4.0, "brand": "A"},
        {"product_id": "P2", "product_name": "Product B", "price_usd": 200.00, "rating": 4.5, "brand": "B"},
        {"product_id": "P3", "product_name": "Product C", "price_usd": 200.00, "rating": 4.0, "brand": "C"},
    ]


@pytest.fixture
def sample_products_same_rating():
    """Products with identical ratings for tie-testing."""
    return [
        {"product_id": "P1", "product_name": "Product A", "price_usd": 150.00, "rating": 4.5, "brand": "A"},
        {"product_id": "P2", "product_name": "Product B", "price_usd": 200.00, "rating": 4.5, "brand": "B"},
        {"product_id": "P3", "product_name": "Product C", "price_usd": 250.00, "rating": 4.5, "brand": "C"},
    ]


@pytest.fixture
def sample_user_preferences():
    """Valid user preferences structure."""
    return {
        "sizing": {
            "fit": "relaxed",
            "shirt": "M",
            "pants": "32",
            "shoes": "10"
        },
        "preferences": {
            "outerwear": {
                "colors": ["blue", "black", "gray"],
                "style": "technical"
            },
            "footwear": {
                "colors": ["black", "brown"],
                "style": "comfortable"
            }
        },
        "general": {
            "budget_max": 300,
            "brands_liked": ["NorthPeak", "AlpineCo"]
        }
    }


# ============================================================================
# AGENT FIXTURES
# ============================================================================

@pytest.fixture
def memory(temp_memory_file):
    """Fresh UserMemory instance with temporary storage."""
    from src.agents.memory import UserMemory
    return UserMemory(storage_path=temp_memory_file)


@pytest.fixture
def memory_with_data(temp_memory_file_with_data):
    """UserMemory instance with pre-existing data."""
    from src.agents.memory import UserMemory
    return UserMemory(storage_path=temp_memory_file_with_data)


@pytest.fixture
def personalization_agent(temp_memory_file):
    """PersonalizationAgent with LLM disabled and temp storage."""
    from src.agents.personalization_agent import PersonalizationAgent
    from src.agents import memory as mem_module

    # Reset global memory instance and use temp file
    mem_module._memory_instance = None
    original_path = "user_preferences.json"

    # Patch the default storage path
    with patch.object(mem_module.UserMemory, '__init__',
                     lambda self, storage_path=temp_memory_file: (
                         setattr(self, 'storage_path', Path(temp_memory_file)),
                         setattr(self, 'data', {}),
                         setattr(self, 'session_overrides', {})
                     )[-1] if setattr(self, 'storage_path', Path(temp_memory_file)) is None else None):
        pass

    # Create agent with LLM disabled
    agent = PersonalizationAgent(use_llm=False)
    # Ensure memory uses temp file
    agent.memory = mem_module.UserMemory(storage_path=temp_memory_file)
    return agent


@pytest.fixture
def visual_agent():
    """VisualAgent instance."""
    from src.agents.visual_agent import VisualAgent
    return VisualAgent()


@pytest.fixture
def orchestrator_no_llm():
    """Orchestrator with LLM disabled."""
    from src.agents.orchestrator import Orchestrator
    return Orchestrator(use_llm=False)


# ============================================================================
# MOCK FIXTURES
# ============================================================================

@pytest.fixture
def mock_chromadb_collection():
    """Mock ChromaDB collection for testing without database."""
    mock_collection = MagicMock()
    mock_collection.count.return_value = 300
    mock_collection.query.return_value = {
        "ids": [["PROD001", "PROD002", "PROD003"]],
        "documents": [["Product 1", "Product 2", "Product 3"]],
        "metadatas": [[
            {"product_name": "Summit Pro Parka", "brand": "NorthPeak", "price_usd": 275.0},
            {"product_name": "Alpine Shell", "brand": "AlpineCo", "price_usd": 320.0},
            {"product_name": "Peak Insulator", "brand": "TrailForge", "price_usd": 245.0},
        ]],
        "distances": [[0.1, 0.2, 0.3]]
    }
    return mock_collection


@pytest.fixture
def mock_product_search(mock_chromadb_collection, sample_products):
    """Mock ProductSearch for testing without actual database."""
    mock_search = MagicMock()
    mock_search.collection = mock_chromadb_collection
    mock_search.search_semantic.return_value = sample_products[:5]
    mock_search.filter_by_attributes.return_value = sample_products[:3]
    return mock_search


# ============================================================================
# HELPER FIXTURES
# ============================================================================

@pytest.fixture
def long_string():
    """Very long string for edge case testing."""
    return "a" * 10000


@pytest.fixture
def special_characters():
    """String with special characters for injection testing."""
    return '<script>alert("xss")</script>'


@pytest.fixture
def unicode_string():
    """String with unicode characters."""
    return "测试用户名 🎿 émojis ñ"


@pytest.fixture
def path_traversal_strings():
    """Strings attempting path traversal."""
    return [
        "../../../etc/passwd",
        "..\\..\\..\\windows\\system32",
        "....//....//etc/passwd",
        "/etc/passwd",
        "user/../../../etc/passwd"
    ]


@pytest.fixture
def sql_injection_strings():
    """Strings attempting SQL injection."""
    return [
        "'; DROP TABLE users; --",
        "' OR '1'='1",
        "1; SELECT * FROM users",
        "admin'--",
        "' UNION SELECT * FROM passwords --"
    ]


@pytest.fixture
def json_injection_strings():
    """Strings attempting JSON injection."""
    return [
        '"; "malicious": true; "',
        '{"__proto__": {"admin": true}}',
        '\\"; \\"hack\\": true',
        '{"constructor": {"prototype": {"admin": true}}}'
    ]


# ============================================================================
# CLEANUP FIXTURES
# ============================================================================

@pytest.fixture(autouse=True)
def reset_memory_instance():
    """Reset global memory instance before each test."""
    from src.agents import memory as mem_module
    mem_module._memory_instance = None
    yield
    mem_module._memory_instance = None


@pytest.fixture(autouse=True)
def clean_env():
    """Clean up environment variables that might affect tests."""
    env_vars = ["GITHUB_TOKEN", "OPENAI_API_KEY", "AZURE_OPENAI_API_KEY"]
    original_values = {k: os.environ.get(k) for k in env_vars}
    yield
    # Restore original values
    for k, v in original_values.items():
        if v is not None:
            os.environ[k] = v
        elif k in os.environ:
            del os.environ[k]
