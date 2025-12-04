"""
Visualization tool functions for the Product Advisor Agent.

These functions handle product visualization, comparison tables,
and price analysis.
"""

from typing import List, Dict, Any, Optional
from src.tools.search_tools import get_product_details, search_products


# Initialize visual formatting tool (singleton pattern)
_visual_formatting_tool = None


def _get_visual_formatting_tool():
    """Get or create the VisualFormattingTool instance."""
    global _visual_formatting_tool
    if _visual_formatting_tool is None:
        from src.agents.visual_formatting_tool import VisualFormattingTool
        _visual_formatting_tool = VisualFormattingTool()
    return _visual_formatting_tool


def create_product_card(product_id: str) -> Dict[str, Any]:
    """
    Create a styled markdown product card for a single product.

    Use this to display detailed information about a product in a
    visually appealing format.

    Args:
        product_id: The product ID (e.g., "PRD-6A6DD909")

    Returns:
        Dictionary containing:
        - success (bool): Whether the card was created
        - content (str): Markdown formatted product card
        - metadata (dict): Product metadata

    Example:
        result = create_product_card("PRD-6A6DD909")
        print(result['content'])  # Displays formatted card
    """
    try:
        # First get the product details
        product_result = get_product_details(product_id)
        if not product_result['success']:
            return {
                "success": False,
                "content": "",
                "error": product_result.get('error', 'Product not found')
            }

        agent = _get_visual_formatting_tool()
        return agent.create_product_card(product_result['product'])
    except Exception as e:
        return {
            "success": False,
            "content": "",
            "error": str(e)
        }


def create_comparison_table(
    product_ids: List[str],
    attributes: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Create a markdown comparison table for multiple products.

    Use this to help users compare 2-5 products side by side.
    The table highlights the best price and best rating.

    Args:
        product_ids: List of product IDs to compare (2-5 recommended)
        attributes: Optional list of attributes to compare
                   Default: brand, price_usd, rating, waterproofing, insulation, season, gender

    Returns:
        Dictionary containing:
        - success (bool): Whether the table was created
        - content (str): Markdown formatted comparison table
        - metadata (dict): Comparison metadata (best price, best rating products)

    Example:
        result = create_comparison_table(["PRD-001", "PRD-002", "PRD-003"])
        print(result['content'])  # Displays formatted table
    """
    try:
        # Get product details for each ID
        products = []
        for pid in product_ids[:5]:  # Limit to 5
            product_result = get_product_details(pid)
            if product_result['success']:
                product = product_result['product']
                product['product_id'] = pid
                products.append(product)

        if not products:
            return {
                "success": False,
                "content": "",
                "error": "No valid products found"
            }

        agent = _get_visual_formatting_tool()
        return agent.create_comparison_table(products, attributes)
    except Exception as e:
        return {
            "success": False,
            "content": "",
            "error": str(e)
        }


def create_feature_matrix(
    product_ids: List[str],
    features: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Create a feature availability matrix showing which products have which features.

    Use this to help users see at a glance which products meet specific criteria
    like waterproof, high rating, under budget, etc.

    Args:
        product_ids: List of product IDs to include (up to 8)
        features: Optional list of features to check
                 Default: Waterproof, Down Insulation, High Rating (4.5+),
                         Under $300, Winter Ready, Recycled Material

    Returns:
        Dictionary containing:
        - success (bool): Whether the matrix was created
        - content (str): Markdown formatted feature matrix
        - metadata (dict): Matrix metadata (best products, scores)

    Example:
        result = create_feature_matrix(["PRD-001", "PRD-002", "PRD-003"])
        print(result['content'])  # Shows feature grid with checkmarks
    """
    try:
        # Get product details for each ID
        products = []
        for pid in product_ids[:8]:  # Limit to 8
            product_result = get_product_details(pid)
            if product_result['success']:
                product = product_result['product']
                product['product_id'] = pid
                products.append(product)

        if not products:
            return {
                "success": False,
                "content": "",
                "error": "No valid products found"
            }

        agent = _get_visual_formatting_tool()
        return agent.create_feature_matrix(products, features)
    except Exception as e:
        return {
            "success": False,
            "content": "",
            "error": str(e)
        }


def create_price_analysis(
    product_ids: Optional[List[str]] = None,
    search_query: Optional[str] = None,
    category: Optional[str] = None,
    show_distribution: bool = True
) -> Dict[str, Any]:
    """
    Create a price analysis visualization showing statistics and distribution.

    Use this to help users understand the price range and find best value products.
    You can either provide specific product IDs or search criteria.

    Args:
        product_ids: Optional list of specific product IDs to analyze
        search_query: Optional search query to find products to analyze
        category: Optional category to filter products
        show_distribution: Whether to show price distribution chart (default: True)

    Returns:
        Dictionary containing:
        - success (bool): Whether the analysis was created
        - content (str): Markdown formatted price analysis
        - metadata (dict): Price statistics (min, max, avg, best value)

    Example:
        # Analyze specific products
        result = create_price_analysis(product_ids=["PRD-001", "PRD-002"])

        # Analyze category
        result = create_price_analysis(category="Outerwear")

        # Analyze search results
        result = create_price_analysis(search_query="waterproof hiking jacket")
    """
    try:
        products = []

        # Get products from IDs
        if product_ids:
            for pid in product_ids:
                product_result = get_product_details(pid)
                if product_result['success']:
                    products.append(product_result['product'])

        # Or search for products
        elif search_query:
            search_result = search_products(search_query, max_results=50)
            if search_result['success']:
                products = search_result['products']

        # Or filter by category (use search to avoid filter format issues)
        elif category:
            search_result = search_products(f"{category} products", max_results=50)
            if search_result['success']:
                # Filter to only include products in the specified category
                products = [p for p in search_result['products'] if p.get('category') == category]

        if not products:
            return {
                "success": False,
                "content": "",
                "error": "No products found for analysis"
            }

        agent = _get_visual_formatting_tool()
        return agent.create_price_visualization(products, show_distribution)
    except Exception as e:
        return {
            "success": False,
            "content": "",
            "error": str(e)
        }


def format_search_results(
    products: List[Dict[str, Any]],
    show_details: bool = True
) -> Dict[str, Any]:
    """
    Format a list of products as a markdown table or list.

    Use this to display search results in a clean, readable format.

    Args:
        products: List of product dictionaries (from search results)
        show_details: If True, show as detailed table; if False, simple numbered list

    Returns:
        Dictionary containing:
        - success (bool): Whether formatting succeeded
        - content (str): Markdown formatted product list
        - metadata (dict): List metadata (products shown, total)

    Example:
        search_result = search_products("hiking boots", max_results=5)
        formatted = format_search_results(search_result['products'])
        print(formatted['content'])
    """
    try:
        agent = _get_visual_formatting_tool()
        return agent.format_product_list(products, show_details)
    except Exception as e:
        return {
            "success": False,
            "content": "",
            "error": str(e)
        }


def visualize_products(
    products: List[Dict[str, Any]],
    intent: str = "search"
) -> str:
    """
    Automatically choose and create the best visualization based on context.

    This is a convenience function that picks the right visualization:
    - 1 product -> Product card
    - 2-5 products -> Comparison table
    - 6+ products -> Product list with price analysis

    Args:
        products: List of product dictionaries
        intent: The query intent (search, comparison, styling, info)

    Returns:
        Markdown string with appropriate visualization

    Example:
        search_result = search_products("winter jacket", max_results=10)
        visualization = visualize_products(search_result['products'], intent="search")
        print(visualization)
    """
    try:
        agent = _get_visual_formatting_tool()
        return agent.auto_visualize(products, intent)
    except Exception as e:
        return f"Error creating visualization: {str(e)}"
