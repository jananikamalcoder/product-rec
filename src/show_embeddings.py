"""
Demonstrate how embeddings work in ChromaDB.
"""
import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


def main():
    print("=" * 70)
    print("HOW EMBEDDINGS WORK IN CHROMADB")
    print("=" * 70)

    # 1. The Embedding Model
    print("\n1. EMBEDDING MODEL USED")
    print("-" * 70)
    print("Model: sentence-transformers/all-MiniLM-L6-v2")
    print("Vector Dimensions: 384")
    print("Model Size: ~80MB")
    print("Location: ~/.cache/chroma/onnx_models/all-MiniLM-L6-v2/")
    print("\nThis model was automatically downloaded when you first loaded products.")

    # 2. Get the embedding function (same one ChromaDB uses)
    print("\n\n2. WHO TRANSFORMS TEXT TO EMBEDDINGS?")
    print("-" * 70)
    print("ChromaDB does it automatically using DefaultEmbeddingFunction!")
    print("\nLet's manually use the same function ChromaDB uses internally:")

    embedding_fn = DefaultEmbeddingFunction()

    # 3. Example texts
    test_texts = [
        "warm winter jacket",
        "insulated coat for cold weather",
        "lightweight summer shirt",
        "waterproof rain jacket"
    ]

    print("\n\n3. CONVERTING TEXT TO VECTORS")
    print("-" * 70)
    print("Input texts:")
    for i, text in enumerate(test_texts, 1):
        print(f"  {i}. '{text}'")

    # Generate embeddings
    embeddings = embedding_fn(test_texts)

    print(f"\nOutput: {len(embeddings)} vectors, each with {len(embeddings[0])} dimensions")
    print(f"\nExample vector for '{test_texts[0]}':")
    print(f"First 20 values: {embeddings[0][:20]}")
    print(f"... (364 more values) ...")

    # 4. Similarity
    print("\n\n4. MEASURING SEMANTIC SIMILARITY")
    print("-" * 70)
    print("Using cosine similarity (1.0 = identical, 0.0 = unrelated):\n")

    similarity_matrix = cosine_similarity(embeddings)

    for i, text1 in enumerate(test_texts):
        print(f"'{text1}':")
        for j, text2 in enumerate(test_texts):
            if i != j:
                print(f"  vs '{text2}': {similarity_matrix[i][j]:.4f}")
        print()

    print("Notice: 'warm winter jacket' is more similar to 'insulated coat'")
    print("        than to 'lightweight summer shirt' - even without shared words!")

    # 5. How ChromaDB uses this
    print("\n\n5. HOW CHROMADB USES EMBEDDINGS")
    print("-" * 70)

    client = chromadb.PersistentClient(path="./chroma_db")
    collection = client.get_collection(name="outdoor_products")

    query = "warm jacket for skiing"
    print(f"\nWhen you query: collection.query(query_texts=['{query}'])")
    print("\nChromaDB internally does:")
    print("  1. query_vector = embedding_fn('{query}')  ← Same model!")
    print("  2. Compare query_vector to ALL 300 product vectors")
    print("  3. Calculate cosine distance for each")
    print("  4. Sort by distance (smaller = more similar)")
    print("  5. Return top N results")

    # Actual query
    results = collection.query(
        query_texts=[query],
        n_results=3
    )

    print(f"\nResults for '{query}':\n")
    for i, (metadata, distance) in enumerate(zip(results['metadatas'][0], results['distances'][0]), 1):
        similarity = 1 - distance
        print(f"{i}. {metadata['product_name']}")
        print(f"   Distance: {distance:.4f} | Similarity: {similarity:.4f}")
        print(f"   Category: {metadata['subcategory']}")
        print()

    # 6. The workflow
    print("\n6. COMPLETE WORKFLOW")
    print("-" * 70)
    print("\n📥 AT INDEX TIME (load_products.py):")
    print("   Product Description → all-MiniLM-L6-v2 → 384-dim Vector → Stored")
    print("   Example: 'Whirlibird GlacierPro Jacket...' → [0.23, -0.45, ...] → DB")

    print("\n🔍 AT QUERY TIME (every search):")
    print("   User Query → all-MiniLM-L6-v2 → 384-dim Vector → Compare → Results")
    print("   Example: 'warm jacket' → [0.25, -0.43, ...] → Compare with all → Top 5")

    print("\n✨ KEY INSIGHT:")
    print("   The SAME model is used for both indexing and querying.")
    print("   This ensures queries and products are in the same 'semantic space'.")

    print("\n\n7. MODEL DETAILS")
    print("-" * 70)
    print("Model: all-MiniLM-L6-v2")
    print("  • Type: Sentence Transformer")
    print("  • Training: Trained on 1+ billion sentence pairs")
    print("  • Purpose: General-purpose semantic similarity")
    print("  • Speed: ~1000 sentences/second on CPU")
    print("  • Quality: Good balance of speed and accuracy")
    print("  • Perfect for: Product search with ~300-10K items")

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("• Embedding Model: all-MiniLM-L6-v2 (automatic)")
    print("• Vector Size: 384 dimensions")
    print("• Who transforms: ChromaDB (you never see the vectors)")
    print("• When: At load time AND at query time")
    print("• Magic: Understands semantic meaning, not just keywords!")
    print("=" * 70)


if __name__ == "__main__":
    main()
