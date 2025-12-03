"""
Shared fixtures for PyTest tests.

This module contains fixtures used across unit and integration tests
for the non-LLM components of the multi-agent system.
"""

import pytest
import tempfile
import os
import json


@pytest.fixture
def temp_storage_path():
    """Temporary JSON file for memory tests."""
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
        yield f.name
    # Cleanup
    if os.path.exists(f.name):
        os.unlink(f.name)


@pytest.fixture
def memory_instance(temp_storage_path):
    """UserMemory with temporary storage."""
    from src.agents.memory import UserMemory
    return UserMemory(storage_path=temp_storage_path)


@pytest.fixture
def search_engine():
    """ProductSearch with real ChromaDB."""
    from src.product_search import ProductSearch
    return ProductSearch(db_path="./chroma_db")


@pytest.fixture
def visual_agent():
    """VisualAgent instance."""
    from src.agents.visual_agent import VisualAgent
    return VisualAgent()


@pytest.fixture
def sample_product():
    """Single product for testing."""
    return {
        "product_id": "PRD-TEST-001",
        "product_name": "Test Winter Jacket",
        "brand": "TestBrand",
        "category": "Outerwear",
        "subcategory": "Down Jackets",
        "gender": "Unisex",
        "price_usd": 199.99,
        "rating": 4.5,
        "waterproofing": "Waterproof",
        "insulation": "Down",
        "season": "Winter",
        "material": "Recycled Nylon",
        "color": "Blue",
        "primary_purpose": "Trail Hiking"
    }


@pytest.fixture
def sample_products_list(sample_product):
    """List of 5 products for testing."""
    products = []
    for i in range(5):
        p = sample_product.copy()
        p["product_id"] = f"PRD-TEST-{i:03d}"
        p["product_name"] = f"Test Product {i}"
        p["price_usd"] = 100 + (i * 50)
        p["rating"] = 4.0 + (i * 0.1)
        products.append(p)
    return products


@pytest.fixture
def sample_products_varied():
    """List of products with varied attributes for visualization tests."""
    return [
        {
            "product_id": "PRD-VAR-001",
            "product_name": "Budget Rain Jacket",
            "brand": "NorthPeak",
            "category": "Outerwear",
            "price_usd": 89.99,
            "rating": 4.2,
            "waterproofing": "Water-Resistant",
            "insulation": "None",
            "season": "All-season",
            "gender": "Unisex"
        },
        {
            "product_id": "PRD-VAR-002",
            "product_name": "Premium Down Parka",
            "brand": "AlpineCo",
            "category": "Outerwear",
            "price_usd": 450.00,
            "rating": 4.8,
            "waterproofing": "Waterproof",
            "insulation": "Down",
            "season": "Winter",
            "gender": "Women"
        },
        {
            "product_id": "PRD-VAR-003",
            "product_name": "Midrange Fleece Jacket",
            "brand": "TrailForge",
            "category": "Outerwear",
            "price_usd": 159.00,
            "rating": 4.5,
            "waterproofing": "None",
            "insulation": "Synthetic",
            "season": "Fall",
            "gender": "Men"
        },
        {
            "product_id": "PRD-VAR-004",
            "product_name": "Technical Shell with Very Long Product Name for Testing",
            "brand": "NorthPeak",
            "category": "Outerwear",
            "price_usd": 299.00,
            "rating": 4.6,
            "waterproofing": "Waterproof",
            "insulation": "None",
            "season": "Winter",
            "gender": "Unisex",
            "material": "Recycled Polyester"
        },
        {
            "product_id": "PRD-VAR-005",
            "product_name": "Entry Level Softshell",
            "brand": "TrailForge",
            "category": "Outerwear",
            "price_usd": 119.00,
            "rating": 4.0,
            "waterproofing": "Water-Resistant",
            "insulation": "None",
            "season": "All-season",
            "gender": "Men"
        }
    ]


@pytest.fixture
def test_user_id():
    """Test user identifier."""
    return "test_user_pytest"


@pytest.fixture
def memory_with_user(memory_instance, test_user_id):
    """Memory pre-populated with test user."""
    memory_instance.save_preferences_bulk(
        user_id=test_user_id,
        sizing={"fit": "relaxed", "shirt": "L"},
        preferences={"outerwear": {"colors": ["blue", "black"]}},
        general={"budget_max": 300}
    )
    return memory_instance


@pytest.fixture
def corrupted_json_file():
    """Create a corrupted JSON file for testing recovery."""
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False, mode='w') as f:
        f.write("{invalid json content")
        path = f.name
    yield path
    if os.path.exists(path):
        os.unlink(path)
