# How Embeddings Work in ChromaDB

## Quick Answer to Your Questions

### 1. Which embedding model is used?
**`all-MiniLM-L6-v2`** - A sentence-transformer model
- 384-dimensional vectors
- ~80MB size
- Automatically used by ChromaDB (default)

### 2. Who transforms queries to embeddings?
**ChromaDB does it automatically!**
- You never manually create embeddings
- ChromaDB handles both indexing and querying
- Uses the same model for consistency

---

## The Complete Flow

### 📥 Loading Products (One-time Setup)

```
CSV File
    ↓
load_products.py reads products
    ↓
For each product:
    Product Description Text
    "Whirlibird GlacierPro Raincoat for alpine climbing..."
         ↓
    all-MiniLM-L6-v2 Model (ChromaDB calls it)
         ↓
    384-dimensional Vector
    [-0.096, 0.119, 0.008, ..., 0.054]  ← 384 numbers
         ↓
    Stored in ChromaDB
    {
        id: "PRD-123",
        text: "Whirlibird...",
        vector: [-0.096, 0.119, ...],
        metadata: {brand: "NorthPeak", ...}
    }
```

### 🔍 Searching Products (Every Query)

```
User types: "warm jacket for skiing"
         ↓
collection.query(query_texts=["warm jacket for skiing"])
         ↓
ChromaDB calls all-MiniLM-L6-v2 Model
         ↓
Query Vector: [0.025, -0.043, 0.078, ..., -0.011]
         ↓
Compare with ALL 300 product vectors:

    Product 1 vector: [-0.096, 0.119, ...]
    Product 2 vector: [0.034, -0.087, ...]
    Product 3 vector: [0.012, 0.045, ...]
    ...
    Product 300 vector: [-0.051, 0.098, ...]
         ↓
Calculate Cosine Distance for each:

    Product 1: distance = 0.6015  (closer = more similar)
    Product 2: distance = 0.7367
    Product 3: distance = 0.7604
    ...
         ↓
Sort by distance (ascending)
         ↓
Return top N results:

    1. Product 1 (distance: 0.6015)
    2. Product 2 (distance: 0.7367)
    3. Product 3 (distance: 0.7604)
```

---

## Key Concepts

### What is an Embedding?

An **embedding** is a numerical representation of text that captures semantic meaning.

```python
Text: "warm winter jacket"
  ↓
Embedding Model
  ↓
Vector: [-0.096, 0.119, 0.008, 0.096, ..., 0.054]
         └─────────── 384 numbers ──────────┘
```

### Why Vectors?

Vectors allow mathematical comparison:

```
"warm winter jacket"     → [0.23, -0.45, 0.67, ...]
"insulated cold coat"    → [0.25, -0.43, 0.65, ...]  ← Similar!
"lightweight summer tee" → [-0.12, 0.78, -0.34, ...] ← Different!
```

**Cosine Similarity** measures how "close" vectors are:
- Similar meaning = Close vectors = High similarity
- Different meaning = Far apart = Low similarity

### The Magic of Semantic Search

The model understands meaning, not just keywords:

```
Query: "warm jacket"

Traditional keyword search finds:
  ✓ "warm jacket" (exact match)
  ✗ "insulated coat" (no shared words!)
  ✗ "heated parka" (no shared words!)

Semantic search (embeddings) finds:
  ✓ "warm jacket" (high similarity: 0.95)
  ✓ "insulated coat" (high similarity: 0.87)
  ✓ "heated parka" (high similarity: 0.82)
```

---

## Model Details: all-MiniLM-L6-v2

### Specifications
- **Full Name**: sentence-transformers/all-MiniLM-L6-v2
- **Type**: Sentence Transformer (BERT-based)
- **Vector Dimensions**: 384
- **Model Size**: ~80MB
- **Speed**: ~1000 sentences/second (CPU)
- **Training**: 1+ billion sentence pairs

### Where It Lives
```bash
~/.cache/chroma/onnx_models/all-MiniLM-L6-v2/
├── onnx/                    # ONNX format (optimized)
│   └── model.onnx
└── onnx.tar.gz             # 80MB download
```

### When It Was Downloaded
Automatically downloaded the first time you ran:
```python
collection.add(documents=[...])  # First time triggers download
```

---

## Code Examples

### What You Write (Simple)
```python
# Query - you just provide text
results = collection.query(
    query_texts=["warm jacket for skiing"],
    n_results=5
)
```

### What ChromaDB Does (Behind the Scenes)
```python
# 1. Load the embedding model
embedding_model = DefaultEmbeddingFunction()  # all-MiniLM-L6-v2

# 2. Transform query to vector
query_vector = embedding_model(["warm jacket for skiing"])
# Result: [0.025, -0.043, 0.078, ..., -0.011]  (384 numbers)

# 3. Compare with all stored product vectors
for product in database:
    distance = cosine_distance(query_vector, product.vector)
    product.score = distance

# 4. Sort and return top 5
sorted_products = sorted(products, key=lambda p: p.score)
return sorted_products[:5]
```

---

## Comparison with Other Models

| Model | Dimensions | Size | Speed | Quality | Use Case |
|-------|-----------|------|-------|---------|----------|
| **all-MiniLM-L6-v2** ⭐ | 384 | 80MB | ⚡⚡⚡ Fast | Good | Default (your setup) |
| all-mpnet-base-v2 | 768 | 420MB | ⚡⚡ Medium | Better | Higher accuracy needed |
| multi-qa-MiniLM-L6 | 384 | 80MB | ⚡⚡⚡ Fast | Good | Q&A optimized |
| text-embedding-3-small | 1536 | Cloud | ⚡ Slow | Best | OpenAI API (costs money) |

**For 300 products**: The default `all-MiniLM-L6-v2` is perfect!

---

## Visualizing the Process

### 1. Vector Space (Simplified to 2D)

```
         ^
         |
    "warm jacket" •
         |           • "insulated coat"
         |
    "hiking boot" •
         |
         |                     • "rain jacket"
    -----+------------------------->
         |
    "summer shirt" •
         |
         |
```

Products with similar embeddings cluster together in vector space.

### 2. Similarity Example

```python
# These get similar embeddings:
"warm winter jacket"        → [0.23, -0.45, 0.67, ...]
"insulated cold weather coat" → [0.25, -0.43, 0.65, ...]
Similarity: 0.70 ✅ High!

# These get different embeddings:
"warm winter jacket"        → [0.23, -0.45, 0.67, ...]
"lightweight summer shirt"  → [-0.12, 0.78, -0.34, ...]
Similarity: 0.26 ❌ Low!
```

---

## FAQ

### Q: Do I need to manually create embeddings?
**A: No!** ChromaDB does it automatically. You only provide text.

### Q: Can I see the embedding vectors?
**A: Yes!** Run the `show_embeddings.py` script to see them.

### Q: Can I use a different model?
**A: Yes!** But for 300 products, the default is perfect.

### Q: How accurate is it?
**A: Very good!** The model was trained on 1+ billion sentence pairs.

### Q: Does it work with typos?
**A: Partially.** Similar typos may work, but exact spelling is better.

### Q: What about synonyms?
**A: Yes!** "jacket" vs "coat" are understood as similar.

### Q: Multiple languages?
**A: No.** The default model is English-only. Use `paraphrase-multilingual` for other languages.

---

## Summary

### The Essentials
1. **Model**: `all-MiniLM-L6-v2` (automatic)
2. **Vector Size**: 384 dimensions
3. **Who creates embeddings**: ChromaDB (transparent to you)
4. **When**: Both at index time and query time
5. **Same model always**: Ensures consistency

### The Magic
- Understands **meaning**, not just keywords
- "warm jacket" matches "insulated coat" (no shared words!)
- Trained on 1+ billion examples
- Works instantly on 300 products

### Files to Explore
- **[show_embeddings.py](show_embeddings.py)** - See embeddings in action
- **[notebooks/understanding_embeddings.ipynb](notebooks/understanding_embeddings.ipynb)** - Interactive exploration
- **[product_search.py](product_search.py)** - Uses embeddings for search

---

**Bottom Line**: You just provide text, ChromaDB handles all the embedding magic! 🎩✨
