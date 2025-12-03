"""
Visual Content Agent - Transforms product data into markdown visualizations.

Handles:
- Product cards (markdown formatted)
- Comparison tables (markdown tables)
- Feature matrices (availability grids)
- Price visualizations (statistics and distributions)

All output is markdown-compatible for Gradio display.
"""

from typing import Any, Dict, List, Optional


# ============================================================================
# VISUALIZATION TOOLS
# ============================================================================

def create_product_card(product_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a styled markdown product card for a single product.

    Args:
        product_data: Product dictionary with attributes

    Returns:
        Dictionary with markdown card string and metadata
    """
    try:
        # Extract product details
        name = product_data.get('product_name', 'Unknown Product')
        brand = product_data.get('brand', 'Unknown')
        price = product_data.get('price_usd', 0.0)
        rating = product_data.get('rating', 0.0)
        category = product_data.get('category', 'Unknown')
        subcategory = product_data.get('subcategory', '')
        gender = product_data.get('gender', '')
        season = product_data.get('season', '')
        waterproofing = product_data.get('waterproofing', '')
        insulation = product_data.get('insulation', '')
        material = product_data.get('material', '')
        color = product_data.get('color', '')
        primary_purpose = product_data.get('primary_purpose', '')

        # Build markdown card
        lines = []
        lines.append(f"### {name}")
        lines.append(f"**{brand}** | {category}" + (f" > {subcategory}" if subcategory else ""))
        lines.append("")

        # Rating and price
        stars = "⭐" * int(rating) + ("½" if rating % 1 >= 0.5 else "")
        lines.append(f"**Rating:** {rating}/5.0 {stars}")
        lines.append(f"**Price:** ${price:.2f}")
        lines.append("")

        # Basic info
        info_parts = []
        if gender:
            info_parts.append(f"**Gender:** {gender}")
        if season:
            info_parts.append(f"**Season:** {season}")
        if info_parts:
            lines.append(" | ".join(info_parts))
            lines.append("")

        # Features
        features = []
        if waterproofing:
            features.append(f"- Waterproofing: {waterproofing}")
        if insulation:
            features.append(f"- Insulation: {insulation}")
        if material:
            features.append(f"- Material: {material}")
        if color:
            features.append(f"- Color: {color}")

        if features:
            lines.append("**Features:**")
            lines.extend(features)
            lines.append("")

        # Purpose
        if primary_purpose:
            lines.append(f"**Best For:** {primary_purpose}")

        lines.append("---")

        card_str = "\n".join(lines)

        return {
            "success": True,
            "visualization_type": "product_card",
            "content": card_str,
            "metadata": {
                "product_id": product_data.get('product_id'),
                "product_name": name,
                "price": price,
                "rating": rating
            }
        }

    except Exception as e:
        return {
            "success": False,
            "visualization_type": "product_card",
            "content": "",
            "error": str(e)
        }


def create_comparison_table(
    products: List[Dict[str, Any]],
    attributes: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Create a markdown comparison table for multiple products.

    Args:
        products: List of product dictionaries (2-5 products recommended)
        attributes: List of attributes to compare (default: key attributes)

    Returns:
        Dictionary with markdown table string and metadata
    """
    try:
        if not products:
            return {
                "success": False,
                "visualization_type": "comparison_table",
                "content": "",
                "error": "No products provided"
            }

        # Default attributes if not specified
        if not attributes:
            attributes = ["brand", "price_usd", "rating", "waterproofing",
                         "insulation", "season", "gender"]

        # Limit to first 5 products for readability
        products = products[:5]
        num_products = len(products)

        # Find best values for highlighting
        prices = [p.get('price_usd', float('inf')) for p in products]
        ratings = [p.get('rating', 0) for p in products]
        best_price_idx = prices.index(min(prices)) if prices else -1
        best_rating_idx = ratings.index(max(ratings)) if ratings else -1

        # Build markdown table
        lines = []

        # Header row
        header = "| Attribute |"
        for prod in products:
            name = prod.get('product_name', 'Unknown')
            # Truncate long names
            if len(name) > 20:
                name = name[:17] + "..."
            header += f" {name} |"
        lines.append(header)

        # Separator row
        separator = "|-----------|"
        for _ in range(num_products):
            separator += "------------|"
        lines.append(separator)

        # Data rows
        for attr in attributes:
            row = f"| **{attr.replace('_', ' ').title()}** |"

            for idx, prod in enumerate(products):
                value = prod.get(attr, '')

                # Format value
                if value == '' or value is None:
                    formatted = "-"
                elif attr == 'price_usd':
                    formatted = f"${value:.2f}" if isinstance(value, (int, float)) else "-"
                    if idx == best_price_idx and formatted != "-":
                        formatted += " 💰"
                elif attr == 'rating':
                    formatted = f"{value:.1f}" if isinstance(value, (int, float)) else "-"
                    if idx == best_rating_idx and formatted != "-":
                        formatted += " ⭐"
                elif isinstance(value, float):
                    formatted = f"{value:.2f}"
                elif isinstance(value, bool):
                    formatted = "✓" if value else "✗"
                else:
                    formatted = str(value)
                    # Truncate long values
                    if len(formatted) > 15:
                        formatted = formatted[:12] + "..."

                row += f" {formatted} |"

            lines.append(row)

        # Legend
        lines.append("")
        lines.append("*💰 = Best price | ⭐ = Best rating*")

        table_str = "\n".join(lines)

        return {
            "success": True,
            "visualization_type": "comparison_table",
            "content": table_str,
            "metadata": {
                "products_count": num_products,
                "attributes_compared": len(attributes),
                "best_price_product": products[best_price_idx].get('product_name') if best_price_idx >= 0 else None,
                "best_rating_product": products[best_rating_idx].get('product_name') if best_rating_idx >= 0 else None
            }
        }

    except Exception as e:
        return {
            "success": False,
            "visualization_type": "comparison_table",
            "content": "",
            "error": str(e)
        }


def create_feature_matrix(
    products: List[Dict[str, Any]],
    features: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Create a feature availability matrix (markdown table with checkmarks).

    Args:
        products: List of product dictionaries
        features: List of features to check (default: common features)

    Returns:
        Dictionary with feature matrix string and metadata
    """
    try:
        if not products:
            return {
                "success": False,
                "visualization_type": "feature_matrix",
                "content": "",
                "error": "No products provided"
            }

        # Limit to first 8 products
        products = products[:8]
        num_products = len(products)

        # Define feature checks
        if not features:
            feature_checks = {
                "Waterproof": lambda p: "waterproof" in str(p.get('waterproofing', '')).lower(),
                "Down Insulation": lambda p: "down" in str(p.get('insulation', '')).lower(),
                "High Rating (4.5+)": lambda p: p.get('rating', 0) >= 4.5,
                "Under $300": lambda p: p.get('price_usd', float('inf')) < 300,
                "Winter Ready": lambda p: p.get('season', '') == 'Winter',
                "Recycled Material": lambda p: "recycled" in str(p.get('material', '')).lower(),
            }
        else:
            # Custom features - check if attribute exists and is truthy
            feature_checks = {feat: lambda p, f=feat: bool(p.get(f)) for feat in features}

        # Build markdown table
        lines = []
        lines.append("### Feature Comparison")
        lines.append("")

        # Header row with product names
        header = "| Feature |"
        for prod in products:
            name = prod.get('product_name', 'Unknown')
            # Use short name
            short_name = name[:12] + "..." if len(name) > 15 else name
            header += f" {short_name} |"
        lines.append(header)

        # Separator
        separator = "|---------|"
        for _ in range(num_products):
            separator += "------------|"
        lines.append(separator)

        # Feature rows
        feature_scores = [0] * num_products
        for feature_name, check_func in feature_checks.items():
            row = f"| {feature_name} |"
            for idx, prod in enumerate(products):
                has_feature = check_func(prod)
                row += " ✅ |" if has_feature else " ❌ |"
                if has_feature:
                    feature_scores[idx] += 1
            lines.append(row)

        # Score row
        max_features = len(feature_checks)
        score_row = "| **Score** |"
        for score in feature_scores:
            score_row += f" **{score}/{max_features}** |"
        lines.append(score_row)

        # Best matches summary
        lines.append("")
        max_score = max(feature_scores) if feature_scores else 0
        best_indices = [i for i, s in enumerate(feature_scores) if s == max_score]
        best_products = [products[i].get('product_name', 'Unknown') for i in best_indices]

        lines.append(f"**Best Match:** {', '.join(best_products)} ({max_score}/{max_features} features)")

        matrix_str = "\n".join(lines)

        return {
            "success": True,
            "visualization_type": "feature_matrix",
            "content": matrix_str,
            "metadata": {
                "products_count": num_products,
                "features_checked": len(feature_checks),
                "best_products": best_products,
                "max_score": max_score
            }
        }

    except Exception as e:
        return {
            "success": False,
            "visualization_type": "feature_matrix",
            "content": "",
            "error": str(e)
        }


def create_price_visualization(
    products: List[Dict[str, Any]],
    show_distribution: bool = True
) -> Dict[str, Any]:
    """
    Create price statistics and optional distribution visualization.

    Args:
        products: List of product dictionaries
        show_distribution: Whether to show price distribution buckets

    Returns:
        Dictionary with price visualization string and metadata
    """
    try:
        if not products:
            return {
                "success": False,
                "visualization_type": "price_visualization",
                "content": "",
                "error": "No products provided"
            }

        # Extract prices and ratings
        prices = [p.get('price_usd', 0) for p in products if p.get('price_usd', 0) > 0]
        ratings = [p.get('rating', 0) for p in products]

        if not prices:
            return {
                "success": False,
                "visualization_type": "price_visualization",
                "content": "",
                "error": "No valid prices found"
            }

        # Calculate statistics
        min_price = min(prices)
        max_price = max(prices)
        avg_price = sum(prices) / len(prices)
        sorted_prices = sorted(prices)
        median_price = sorted_prices[len(sorted_prices) // 2]

        # Find best value (highest rating / price ratio)
        best_value_idx = 0
        best_value_score = 0
        for idx, prod in enumerate(products):
            price = prod.get('price_usd', 0)
            rating = prod.get('rating', 0)
            if price > 0:
                value_score = rating / price * 100
                if value_score > best_value_score:
                    best_value_score = value_score
                    best_value_idx = idx

        best_value_product = products[best_value_idx]

        # Build markdown output
        lines = []
        lines.append("### Price Analysis")
        lines.append("")
        lines.append(f"**Products Analyzed:** {len(products)}")
        lines.append("")

        # Statistics table
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| Lowest Price | ${min_price:.2f} |")
        lines.append(f"| Highest Price | ${max_price:.2f} |")
        lines.append(f"| Average Price | ${avg_price:.2f} |")
        lines.append(f"| Median Price | ${median_price:.2f} |")
        lines.append("")

        # Best value
        lines.append(f"**Best Value:** {best_value_product.get('product_name', 'Unknown')} " +
                    f"(${best_value_product.get('price_usd', 0):.2f}, " +
                    f"{best_value_product.get('rating', 0):.1f}⭐)")
        lines.append("")

        # Price distribution
        if show_distribution:
            lines.append("**Price Distribution:**")
            lines.append("")

            # Create buckets
            bucket_size = 100
            max_bucket = int((max_price // bucket_size + 1) * bucket_size)
            buckets = {}

            for price in prices:
                bucket = int(price // bucket_size) * bucket_size
                buckets[bucket] = buckets.get(bucket, 0) + 1

            # Find max count for bar scaling
            max_count = max(buckets.values()) if buckets else 1

            # Display distribution
            lines.append("| Price Range | Count | |")
            lines.append("|-------------|-------|---|")

            for bucket_start in sorted(buckets.keys()):
                count = buckets[bucket_start]
                bar_length = int((count / max_count) * 10)
                bar = "█" * bar_length
                lines.append(f"| ${bucket_start}-${bucket_start + bucket_size} | {count} | {bar} |")

        viz_str = "\n".join(lines)

        return {
            "success": True,
            "visualization_type": "price_visualization",
            "content": viz_str,
            "metadata": {
                "products_count": len(products),
                "price_range": {"min": min_price, "max": max_price},
                "average_price": avg_price,
                "median_price": median_price,
                "best_value_product": best_value_product.get('product_name')
            }
        }

    except Exception as e:
        return {
            "success": False,
            "visualization_type": "price_visualization",
            "content": "",
            "error": str(e)
        }


def format_product_list(
    products: List[Dict[str, Any]],
    show_details: bool = True
) -> Dict[str, Any]:
    """
    Format a list of products as a markdown list or table.

    Args:
        products: List of product dictionaries
        show_details: Whether to show detailed info or just names

    Returns:
        Dictionary with formatted product list
    """
    try:
        if not products:
            return {
                "success": False,
                "visualization_type": "product_list",
                "content": "No products found.",
                "error": None
            }

        lines = []

        if show_details:
            # Detailed table format
            lines.append("| Product | Brand | Price | Rating |")
            lines.append("|---------|-------|-------|--------|")

            for prod in products[:10]:  # Limit to 10
                name = prod.get('product_name', 'Unknown')
                if len(name) > 25:
                    name = name[:22] + "..."
                brand = prod.get('brand', '-')
                price = prod.get('price_usd', 0)
                rating = prod.get('rating', 0)

                lines.append(f"| {name} | {brand} | ${price:.2f} | {rating:.1f}⭐ |")
        else:
            # Simple list format
            for idx, prod in enumerate(products[:10], 1):
                name = prod.get('product_name', 'Unknown')
                price = prod.get('price_usd', 0)
                lines.append(f"{idx}. **{name}** - ${price:.2f}")

        if len(products) > 10:
            lines.append("")
            lines.append(f"*...and {len(products) - 10} more products*")

        list_str = "\n".join(lines)

        return {
            "success": True,
            "visualization_type": "product_list",
            "content": list_str,
            "metadata": {
                "products_shown": min(len(products), 10),
                "total_products": len(products)
            }
        }

    except Exception as e:
        return {
            "success": False,
            "visualization_type": "product_list",
            "content": "",
            "error": str(e)
        }


class VisualAgent:
    """
    Visual Content Agent for transforming product data into markdown representations.

    Specializes in:
    - Styled product cards
    - Comparison tables
    - Feature matrices
    - Price visualizations
    """

    def __init__(self):
        self.name = "VisualAgent"
        self.role = "Product data visualization and formatting"

    def create_product_card(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Create a markdown product card."""
        return create_product_card(product)

    def create_comparison_table(
        self,
        products: List[Dict[str, Any]],
        attributes: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a comparison table."""
        return create_comparison_table(products, attributes)

    def create_feature_matrix(
        self,
        products: List[Dict[str, Any]],
        features: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a feature matrix."""
        return create_feature_matrix(products, features)

    def create_price_visualization(
        self,
        products: List[Dict[str, Any]],
        show_distribution: bool = True
    ) -> Dict[str, Any]:
        """Create price statistics and visualization."""
        return create_price_visualization(products, show_distribution)

    def format_product_list(
        self,
        products: List[Dict[str, Any]],
        show_details: bool = True
    ) -> Dict[str, Any]:
        """Format a list of products."""
        return format_product_list(products, show_details)

    def auto_visualize(
        self,
        products: List[Dict[str, Any]],
        intent: str = "search"
    ) -> str:
        """
        Automatically choose and create the best visualization based on context.

        Args:
            products: List of products to visualize
            intent: The query intent (search, comparison, styling, info)

        Returns:
            Markdown string with appropriate visualization
        """
        if not products:
            return "No products found."

        num_products = len(products)

        # Single product - show detailed card
        if num_products == 1:
            result = self.create_product_card(products[0])
            return result.get('content', '')

        # 2-5 products - comparison table
        if 2 <= num_products <= 5 or intent == "comparison":
            result = self.create_comparison_table(products[:5])
            return result.get('content', '')

        # Many products - show list with price analysis
        if num_products > 5:
            list_result = self.format_product_list(products)
            price_result = self.create_price_visualization(products, show_distribution=False)

            return f"{list_result.get('content', '')}\n\n{price_result.get('content', '')}"

        # Default - simple list
        result = self.format_product_list(products)
        return result.get('content', '')


# Convenience functions for direct use
def visualize_products(products: List[Dict[str, Any]], intent: str = "search") -> str:
    """Convenience function to auto-visualize products."""
    agent = VisualAgent()
    return agent.auto_visualize(products, intent)
