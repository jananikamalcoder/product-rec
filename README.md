# Product Recommendation System

AI-powered product search and recommendation system for outdoor apparel using ChromaDB hybrid search.

## Quick Start

```bash
# Activate virtual environment
source .venv/bin/activate

# Load products into ChromaDB (first time only)
uv run python load_products.py

# Test product search
uv run python product_search.py

# Test MS Agent Framework tools
uv run python agent_tools.py

# Run example agent (requires Azure OpenAI or OpenAI credentials)
uv run python example_agent.py

# Interactive chat mode
uv run python example_agent.py --interactive
```

## Features

- **Semantic Search**: Natural language queries using AI embeddings
- **Filter Search**: Exact attribute filtering (brand, price, gender, etc.)
- **Hybrid Search**: Combines semantic understanding with filters
- **Similar Products**: Find related items based on vector similarity
- **300 Products**: Outdoor apparel catalog with 20+ attributes
- **Microsoft Agent Framework Ready**: 9 native tool functions for the new MS Agent Framework (Oct 2025)

## Technology Stack

- **Python 3.12**
- **ChromaDB**: Vector database with hybrid search
- **sentence-transformers**: all-MiniLM-L6-v2 embedding model
- **uv**: Fast Python package manager

## Project Structure

```
product-rec/
├── data/
│   └── outdoor_products_300_with_lines.csv    # Product catalog
├── chroma_db/                                  # Vector database (gitignored)
├── notebooks/
│   ├── chromadb_query_examples.ipynb          # Query examples
│   └── understanding_embeddings.ipynb          # How embeddings work
├── load_products.py                            # Load data into ChromaDB
├── product_search.py                           # ProductSearch class
├── agent_tools.py                              # MS Agent Framework tools
├── show_embeddings.py                          # Embedding demo
├── CLAUDE.md                                   # Development guide
├── MS_AGENT_INTEGRATION.md                     # Agent integration guide
└── EMBEDDINGS_EXPLAINED.md                     # Embedding reference
```

## Usage Examples

### Basic Search

```python
from product_search import ProductSearch

search = ProductSearch()

# Semantic search
results = search.search_semantic("warm jacket for skiing", n_results=5)

# Filter search
results = search.search_by_filters(
    filters={"brand": "NorthPeak", "gender": "Women"},
    n_results=10
)

# Hybrid search
results = search.hybrid_search(
    query="waterproof jacket",
    filters={"primary_purpose": "Trail Hiking"},
    n_results=5
)
```

### MS Agent Framework Integration

```python
import agent_tools

# Use as native tools in your agent
result = agent_tools.search_products("warm winter jacket", max_results=5)
result = agent_tools.filter_products_by_attributes(
    brand="NorthPeak",
    gender="Women",
    max_price=300
)
result = agent_tools.get_catalog_statistics()
```

See [MS_AGENT_INTEGRATION.md](MS_AGENT_INTEGRATION.md) for complete integration guide.

## Product Catalog

- **Total Products**: 300
- **Brands**: NorthPeak, AlpineCo, TrailForge
- **Categories**: Outerwear, Footwear, Apparel
- **Price Range**: $26 - $775
- **Attributes**: 20 fields per product

### Product Ontology

**Outerwear**:
- Parkas, Down Jackets, Lightweight Jackets, Bombers, Vests, Raincoats/Shell Jackets, Fleece

**Apparel/Sportswear**:
- Shirts, Pants, Shorts, Base Layers, Knitwear

**Footwear**:
- Hiking boots, Winter boots, Trail running shoes, Water sports shoes

## Documentation

- **[CLAUDE.md](CLAUDE.md)** - Complete development guide
- **[MS_AGENT_INTEGRATION.md](MS_AGENT_INTEGRATION.md)** - Agent framework integration
- **[EMBEDDINGS_EXPLAINED.md](EMBEDDINGS_EXPLAINED.md)** - How embeddings work
- **[notebooks/](notebooks/)** - Interactive Jupyter notebooks

## Microsoft Agent Framework Tools (Oct 2025)

9 ready-to-use tool functions for the **new Microsoft Agent Framework** (replaces AutoGen):

1. `search_products()` - Semantic search
2. `filter_products_by_attributes()` - Exact filtering
3. `search_with_filters()` - Hybrid search
4. `find_similar_products()` - Similar item search
5. `get_product_details()` - Get specific product
6. `get_available_brands()` - List all brands
7. `get_available_categories()` - List all categories
8. `get_catalog_statistics()` - Catalog overview

All tools return structured JSON-friendly dictionaries.

**Install**: `pip install agent-framework --pre`

## How It Works

### Embeddings

- **Model**: all-MiniLM-L6-v2 (384 dimensions)
- **Automatic**: ChromaDB handles all embedding creation
- **Semantic**: Understands meaning, not just keywords
- **Example**: "warm jacket" matches "insulated coat" (no shared words!)

### Search Flow

```
User Query: "warm jacket for skiing"
     ↓
ChromaDB embeds query → [384-dim vector]
     ↓
Compare with all product vectors
     ↓
Return top N most similar products
```

## Performance

- Semantic search: ~100-200ms
- Filter search: ~50-100ms
- Hybrid search: ~100-200ms
- Works efficiently with 300 products
- Scales well to 10K+ products

## Development

```bash
# Add dependency
uv add <package-name>

# Run tests
uv run python product_search.py
uv run python agent_tools.py

# Explore in notebook
jupyter notebook notebooks/chromadb_query_examples.ipynb
```

## License

MIT

## Contributing

See [CLAUDE.md](CLAUDE.md) for development guidelines.
