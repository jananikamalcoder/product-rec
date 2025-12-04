# Product Advisor - Multi-Agent Recommendation System

AI-powered product recommendation system for outdoor apparel using a hierarchical 3-agent architecture with semantic search, personalization, and visual formatting.

## Features

- **Multi-Agent Architecture**: 3-agent system with orchestrator, personalization, and search agents
- **Semantic Search**: Natural language queries using AI embeddings (all-MiniLM-L6-v2)
- **User Personalization**: Persistent preferences, location-aware climate inference
- **Visual Formatting**: Markdown-based product cards, comparison tables, feature matrices
- **Hybrid Search**: Combines semantic understanding with attribute filters
- **300 Products**: Outdoor apparel catalog (NorthPeak, AlpineCo, TrailForge)
- **Comprehensive Testing**: 62 unit tests + 9 integration tests (Pylint 9.96/10)

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Load products into ChromaDB (first time only)
python load_products.py

# Launch web interface
python app.py
```

Open http://localhost:7860 in your browser.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│              PRODUCT ADVISOR ORCHESTRATOR                       │
│  - Classifies user intent (STYLING, SEARCH, COMPARISON, INFO)  │
│  - Routes tasks to specialized agents                           │
│  - Propagates user preferences to search queries                │
└──────┬───────────────────┬──────────────────────┬───────────────┘
       │                   │                      │
       ▼                   ▼                      ▼
┌──────────────────┐ ┌─────────────────┐ ┌────────────────────────┐
│ PERSONALIZATION  │ │ PRODUCT SEARCH  │ │ VISUAL FORMATTING      │
│ AGENT            │ │ AGENT           │ │ TOOL                   │
│                  │ │                 │ │                        │
│ - User memory    │ │ - Semantic      │ │ - Product cards        │
│ - Preferences    │ │   search        │ │ - Comparison tables    │
│ - Location →     │ │ - Hybrid        │ │ - Feature matrices     │
│   Climate        │ │   filtering     │ │ - Price analysis       │
└──────────────────┘ └────────┬────────┘ └────────────────────────┘
                              │
                              ▼
               ┌──────────────────────────────┐
               │    ChromaDB Vector Store     │
               │  300 Products | 384-dim      │
               └──────────────────────────────┘
```

## Project Structure

```
product-rec/
├── src/
│   ├── agents/
│   │   ├── product_advisor_agent.py    # Orchestrator (MS Agent Framework)
│   │   ├── personalization_agent.py    # User preferences & memory
│   │   ├── product_search_agent.py     # Semantic search agent
│   │   ├── visual_formatting_tool.py   # Markdown visualizations
│   │   └── memory.py                   # JSON-based user memory
│   ├── tools/
│   │   ├── agent_tools.py              # 21 tool functions
│   │   └── visualization_tools.py      # Visualization wrappers
│   └── product_search.py               # ChromaDB search engine
├── data/
│   └── outdoor_products_300.csv        # Product catalog
├── tests/
│   ├── unit/                           # 62 unit tests
│   └── integration/                    # 9 integration tests
├── docs/
│   └── MULTI_AGENT_ARCHITECTURE.md     # Architecture documentation
├── app.py                              # Gradio web interface
├── load_products.py                    # Load data into ChromaDB
└── user_preferences.json               # User memory storage
```

## Web Interface

The Gradio interface provides two modes:

### AI Chat (Tab 1)
Conversational multi-agent system with personalization:
- "Hi, I'm Sarah from Minnesota" - Identifies user, infers cold climate
- "I need a jacket for winter hiking" - Searches with preferences applied
- "Compare the top 3 for me" - Creates comparison table
- "These are too expensive" - Records feedback for future searches

### Simple Search (Tab 2)
Fast semantic search without LLM calls:
- Instant results using local embeddings
- No API costs
- Great for quick product lookups

## Usage Examples

### Programmatic Search

```python
from src.tools import agent_tools

# Semantic search
result = agent_tools.search_products("warm winter jacket", max_results=5)

# Filter search
result = agent_tools.filter_products_by_attributes(
    brand="NorthPeak",
    gender="Women",
    max_price=300
)

# Hybrid search (semantic + filters)
result = agent_tools.search_with_filters(
    query="waterproof hiking boots",
    brand="TrailForge",
    max_results=5
)
```

### User Personalization

```python
from src.tools import agent_tools

# Identify user (new or returning)
result = agent_tools.identify_user("sarah")

# Save preferences with location
result = agent_tools.save_user_preferences(
    user_id="sarah",
    fit="relaxed",
    location="Minnesota"  # Infers cold climate
)

# Get personalized recommendations
result = agent_tools.get_outfit_recommendation(
    query="hiking outfit",
    user_id="sarah"
)
```

## Technology Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.12 |
| Vector DB | ChromaDB |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| Agent Framework | Microsoft Agent Framework (autogen-agentchat) |
| LLM | GPT-4o-mini (OpenAI or GitHub Models) |
| Web UI | Gradio |
| Testing | pytest |

## Testing

```bash
# Run all unit tests
python -m pytest tests/unit/ -v

# Run integration tests
python -m pytest tests/integration/ -v

# Check code quality
pylint src/ --rcfile=pyproject.toml
```

**Test Results**: 62 unit tests + 9 integration tests passing | Pylint: 9.96/10

## Configuration

Create a `.env` file with your API key:

```bash
# Option 1: OpenAI (preferred - higher rate limits)
OPENAI_API_KEY=sk-...

# Option 2: GitHub Models (150 requests/day limit)
GITHUB_TOKEN=ghp_...
```

## Product Catalog

- **Total Products**: 300
- **Brands**: NorthPeak, AlpineCo, TrailForge
- **Categories**: Outerwear, Footwear, Apparel
- **Price Range**: $26 - $775

### Categories

| Category | Subcategories |
|----------|---------------|
| Outerwear | Parkas, Down Jackets, Lightweight Jackets, Vests, Raincoats, Fleece |
| Apparel | Shirts, Pants, Shorts, Base Layers, Knitwear |
| Footwear | Hiking boots, Winter boots, Trail running shoes |

## Documentation

- [MULTI_AGENT_ARCHITECTURE.md](docs/MULTI_AGENT_ARCHITECTURE.md) - Detailed architecture documentation
- [EMBEDDINGS_EXPLAINED.md](docs/EMBEDDINGS_EXPLAINED.md) - How semantic search works

## License

MIT
