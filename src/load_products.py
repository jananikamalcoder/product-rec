"""
Load outdoor products into ChromaDB for vector search and recommendations.
"""
from pathlib import Path

import chromadb
import pandas as pd


def load_products_to_chromadb():
    """Load products from CSV into ChromaDB collection."""

    # Initialize ChromaDB client (persistent storage)
    client = chromadb.PersistentClient(path="./chroma_db")

    # Create or get collection
    # ChromaDB will use default embedding function (all-MiniLM-L6-v2)
    collection = client.get_or_create_collection(
        name="outdoor_products",
        metadata={"description": "Outdoor apparel and gear products"}
    )

    # Load products from CSV
    csv_path = Path("data/outdoor_products_300_with_lines.csv")
    df = pd.read_csv(csv_path)

    print(f"Loading {len(df)} products into ChromaDB...")

    # Prepare data for ChromaDB
    documents = []
    metadatas = []
    ids = []

    for _, row in df.iterrows():
        # Create rich text for embedding (semantic search)
        document = f"""
        {row['ProductName']}
        Brand: {row['Brand']}
        Category: {row['Category']} - {row['Subcategory']}
        Description: {row['Description']}
        Gender: {row['Gender']}
        Material: {row['Material']}
        Season: {row['Season']}
        Purpose: {row['PrimaryPurpose']}
        Weather: {row['WeatherProfile']}
        Terrain: {row['Terrain']}
        Features: Waterproofing={row['Waterproofing']}, Insulation={row['Insulation']}
        Price: ${row['PriceUSD']}
        Color: {row['Color']}
        """.strip()

        # Metadata for filtering (keyword search)
        metadata = {
            "product_id": str(row['ProductID']),
            "brand": str(row['Brand']),
            "category": str(row['Category']),
            "subcategory": str(row['Subcategory']),
            "product_line": str(row['ProductLine']),
            "product_name": str(row['ProductName']),
            "gender": str(row['Gender']),
            "material": str(row['Material']),
            "season": str(row['Season']),
            "color": str(row['Color']),
            "primary_purpose": str(row['PrimaryPurpose']),
            "weather_profile": str(row['WeatherProfile']),
            "terrain": str(row['Terrain']),
            "waterproofing": str(row['Waterproofing']),
            "insulation": str(row['Insulation']),
            "price_usd": float(row['PriceUSD']),
            "rating": float(row['Rating']),
        }

        documents.append(document)
        metadatas.append(metadata)
        ids.append(str(row['ProductID']))

    # Add to ChromaDB collection
    # ChromaDB automatically generates embeddings
    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )

    print(f"✓ Successfully loaded {len(df)} products")
    print(f"✓ Collection size: {collection.count()}")

    return collection


if __name__ == "__main__":
    collection = load_products_to_chromadb()

    # Test query
    print("\n--- Testing search ---")
    results = collection.query(
        query_texts=["waterproof jacket for hiking"],
        n_results=3
    )

    print("\nTop 3 results for 'waterproof jacket for hiking':")
    for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0]), 1):
        print(f"\n{i}. {metadata['product_name']}")
        print(f"   Brand: {metadata['brand']}")
        print(f"   Category: {metadata['subcategory']}")
        print(f"   Price: ${metadata['price_usd']}")
        print(f"   Rating: {metadata['rating']}")
