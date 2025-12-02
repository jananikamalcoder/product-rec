"""
Product search system using ChromaDB hybrid search.
"""
import chromadb
from typing import List, Dict, Any, Optional


class ProductSearch:
    """Hybrid search product search engine using ChromaDB."""

    def __init__(self, db_path: str = "./chroma_db"):
        """Initialize the product search with ChromaDB client."""
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_collection(name="outdoor_products")

    def search_semantic(
        self,
        query: str,
        n_results: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict]:
        """
        Semantic search using vector embeddings.

        Args:
            query: Natural language search query
            n_results: Number of results to return
            filters: Optional metadata filters (e.g., {"category": "Outerwear"})

        Returns:
            List of product dictionaries
        """
        where = filters if filters else None

        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where
        )

        return self._format_results(results)

    def search_by_filters(
        self,
        filters: Dict[str, Any],
        n_results: int = 10
    ) -> List[Dict]:
        """
        Filter-based search (keyword search).

        Args:
            filters: Metadata filters. Can be either:
                     - Simple dict (e.g., {"brand": "NorthPeak", "gender": "Women"})
                     - ChromaDB-formatted filter (e.g., {"$and": [...]})
            n_results: Number of results to return

        Returns:
            List of product dictionaries
        """
        # Check if filters are already in ChromaDB format (contains $and or $or)
        if "$and" in filters or "$or" in filters:
            where_clause = filters
        # Otherwise, convert simple dict to ChromaDB format
        elif len(filters) > 1:
            where_clause = {
                "$and": [{key: {"$eq": value}} for key, value in filters.items()]
            }
        elif len(filters) == 1:
            key, value = list(filters.items())[0]
            where_clause = {key: {"$eq": value}}
        else:
            where_clause = None

        # Get all items matching filters
        results = self.collection.get(
            where=where_clause,
            limit=n_results
        )

        return self._format_get_results(results)

    def hybrid_search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        n_results: int = 10
    ) -> List[Dict]:
        """
        Hybrid search: Semantic search with metadata filtering.

        Args:
            query: Natural language search query
            filters: Optional metadata filters
            n_results: Number of results to return

        Returns:
            List of product dictionaries
        """
        return self.search_semantic(query, n_results, filters)

    def get_similar_products(
        self,
        product_id: str,
        n_results: int = 5
    ) -> List[Dict]:
        """
        Find similar products based on a given product ID.

        Args:
            product_id: ID of the reference product
            n_results: Number of similar products to return

        Returns:
            List of similar product dictionaries
        """
        # Get the product document
        product = self.collection.get(
            ids=[product_id],
            include=["documents"]
        )

        if not product['documents']:
            return []

        # Use the product's document to find similar items
        results = self.collection.query(
            query_texts=product['documents'],
            n_results=n_results + 1,  # +1 because it includes itself
        )

        # Remove the original product from results
        formatted = self._format_results(results)
        return [p for p in formatted if p['product_id'] != product_id][:n_results]

    def _format_results(self, results: Dict) -> List[Dict]:
        """Format query results into list of product dictionaries."""
        products = []
        for metadata, distance in zip(
            results['metadatas'][0],
            results['distances'][0]
        ):
            product = {**metadata, 'similarity_score': 1 - distance}
            products.append(product)
        return products

    def _format_get_results(self, results: Dict) -> List[Dict]:
        """Format get results into list of product dictionaries."""
        if not results['metadatas']:
            return []
        return list(results['metadatas'])


def main():
    """Demo the product search system."""
    search = ProductSearch()

    print("=== Semantic Search ===")
    results = search.search_semantic("warm winter jacket for skiing", n_results=5)
    for i, product in enumerate(results, 1):
        print(f"\n{i}. {product['product_name']}")
        print(f"   Brand: {product['brand']} | Price: ${product['price_usd']}")
        print(f"   {product['subcategory']} - {product['weather_profile']}")
        print(f"   Similarity: {product['similarity_score']:.3f}")

    print("\n\n=== Filter Search (Women's Outerwear) ===")
    results = search.search_by_filters(
        filters={"gender": "Women", "category": "Outerwear"},
        n_results=5
    )
    for i, product in enumerate(results, 1):
        print(f"\n{i}. {product['product_name']}")
        print(f"   {product['subcategory']} | ${product['price_usd']}")

    print("\n\n=== Hybrid Search (Waterproof + Hiking) ===")
    results = search.hybrid_search(
        query="waterproof jacket",
        filters={"primary_purpose": "Trail Hiking"},
        n_results=5
    )
    for i, product in enumerate(results, 1):
        print(f"\n{i}. {product['product_name']}")
        print(f"   Purpose: {product['primary_purpose']}")
        print(f"   Waterproofing: {product['waterproofing']} | ${product['price_usd']}")


if __name__ == "__main__":
    main()
