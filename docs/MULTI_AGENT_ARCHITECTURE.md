# Multi-Agent System Architecture

## Overview

A 3-agent system for AI-powered product recommendations with personalization, semantic search, and visual data representations.

**Key Design Principles**:
- Visual representations use **markdown tables and formatting** - no product images required
- **Location-aware preferences** with automatic climate inference
- **Preference propagation** from personalization to search queries
- **Persistent user memory** with JSON storage

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Input                               │
│      "Show me warm jackets for skiing, personalized for me"    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              PRODUCT ADVISOR ORCHESTRATOR                       │
│  - Classifies user intent (STYLING, SEARCH, COMPARISON, INFO)  │
│  - Routes tasks to specialized agents                           │
│  - Propagates user preferences to search queries                │
│  - Combines results into coherent response                      │
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
│ - Sizing/Fit     │ │ - Similar       │ │ - Auto-visualization   │
│ - Feedback       │ │   products      │ │                        │
└────────┬─────────┘ └────────┬────────┘ └────────────────────────┘
         │                    │
         ▼                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                   ChromaDB Vector Store                         │
│           300 Products | 384-dim Embeddings                     │
│              (all-MiniLM-L6-v2 Model)                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Agent Specifications

### 1. Product Advisor Orchestrator

**File**: `src/agents/product_advisor_agent.py`

**Status**: ✅ Implemented

**Role**: Central coordinator that routes queries, manages agent communication, and propagates user preferences.

**Capabilities**:
- Classifies user intent (STYLING, SEARCH, COMPARISON, INFO)
- Routes to appropriate agent(s)
- **Propagates user preferences** (location, climate, sizing) to search queries
- Combines results into coherent response

**Classes**:
- `QueryIntent` (Enum): STYLING, PRODUCT_SEARCH, COMPARISON, INFO, UNKNOWN
- `OrchestratorResult`: Dataclass with intent, context, products, message
- `ProductAdvisorAgent`: Main coordinator class (MS Agent Framework)

**Key Methods**:
```python
classify_intent(query: str) -> QueryIntent
process_query(query: str, user_id: str = None) -> OrchestratorResult
_propagate_preferences_to_query(query: str, preferences: Dict) -> str
```

**Preference Propagation Example**:
```python
# User query: "show me jackets"
# User preferences: location="Minnesota", climate="cold"
# Propagated query: "show me jackets warm insulated winter cold weather"
```

---

### 2. PersonalizationAgent

**File**: `src/agents/personalization_agent.py`

**Status**: ✅ Implemented

**Role**: User-aware styling and preference management with persistent memory and location-based climate inference.

**Components**:
- **Styling**: Outfit recommendations based on activity, weather, style
- **Location Tracking**: Stores user location and infers climate
- **Climate Inference**: Maps locations to climate conditions (cold/mild/warm)
- **Fit & Sizing**: Size, fit preference (slim/classic/relaxed/oversized)
- **Feedback**: Converts "too flashy", "too tight" into preference signals

**Location → Climate Mapping**:
```python
COLD_CLIMATE_LOCATIONS = {
    "minnesota", "alaska", "montana", "wisconsin", "michigan",
    "north dakota", "south dakota", "maine", "vermont", "new hampshire",
    "colorado", "wyoming", "idaho", "canada", "norway", "sweden", "finland"
}
# Location "Minnesota" → climate: "cold" → search for warm/insulated products
```

**Memory Features** (stored in `user_preferences.json`):
- Category-specific preferences (outerwear colors ≠ footwear colors)
- Location and inferred climate
- Permanent vs session-only preference updates
- Returning user detection and confirmation flow

**Classes**:
- `Activity` (Enum): HIKING, SKIING, CAMPING, RUNNING, CLIMBING, CASUAL, TRAVEL, EVERYDAY
- `Weather` (Enum): COLD, COOL, MILD, WARM, RAINY, SNOWY, WINDY
- `StylePreference` (Enum): TECHNICAL, CASUAL, STYLISH, MINIMALIST, COLORFUL, NEUTRAL
- `FitPreference` (Enum): SLIM, CLASSIC, RELAXED, OVERSIZED
- `PersonalizationContext`: Dataclass combining styling intent and user preferences
- `PersonalizationAgent`: Main agent class

**Key Methods**:
```python
identify_user(user_name: str) -> Dict  # Check new vs returning user
get_user_preferences(user_id: str) -> Dict  # Get saved preferences
save_user_preferences(user_id, sizing, preferences, general, permanent) -> Dict
process_feedback(user_id, feedback, context) -> Dict  # "too flashy" → avoid bright
get_returning_user_prompt(user_id: str) -> str  # "Same preferences or change?"
get_personalized_recommendation(query, user_id) -> Dict  # Get outfit with preferences
infer_climate_from_location(location: str) -> str  # "Minnesota" → "cold"
```

**User Flow**:
1. New user: "What's your name?" → Gather preferences (including location) → Save
2. Returning user: "Welcome back! Your preferences were X. Same or different?"
3. Preference change: "Is relaxed fit your new default, or just for today?"
4. Location-aware: User in Minnesota → automatically search for warm products

---

### 3. ProductSearchAgent

**File**: `src/agents/product_search_agent.py`

**Status**: ✅ Implemented

**Role**: Semantic search over product catalog using ChromaDB and sentence-transformers.

**Capabilities**:
- **Semantic Search**: Natural language queries → relevant products
- **Hybrid Filtering**: Combine semantic search with attribute filters
- **Similar Products**: Find products similar to a given product ID
- **Category Search**: Browse by category/subcategory

**Embedding Model**: `all-MiniLM-L6-v2` (384 dimensions)

**Key Methods**:
```python
search_products(query: str, max_results: int = 10) -> List[Dict]
filter_by_attributes(brand: str = None, category: str = None, ...) -> List[Dict]
search_with_filters(query: str, brand: str = None, ...) -> List[Dict]
find_similar_products(product_id: str, max_results: int = 5) -> List[Dict]
```

---

### 4. VisualFormattingTool

**File**: `src/agents/visual_formatting_tool.py`

**Status**: ✅ Implemented

**Role**: Transform product data into markdown visualizations for Gradio display.

> **Note**: Previously named `VisualAgent`. A backward compatibility alias is provided:
> ```python
> VisualAgent = VisualFormattingTool  # For backward compatibility
> ```

**Visualization Types**:

#### Product Card
```markdown
### Summit Pro Parka
**NorthPeak** | Outerwear > Parkas

**Rating:** 4.8/5.0 ⭐⭐⭐⭐½
**Price:** $275.00

**Gender:** Women | **Season:** Winter

**Features:**
- Waterproofing: Waterproof
- Insulation: Down 700-fill
```

#### Comparison Table
```markdown
| Attribute | Summit Pro Parka | Alpine Shell | Peak Insulator |
|-----------|------------------|--------------|----------------|
| **Brand** | NorthPeak | AlpineCo | TrailForge |
| **Price** | $275.00 | $320.00 | $245.00 💰 |
| **Rating** | 4.8 ⭐ | 4.6 | 4.7 |

*💰 = Best price | ⭐ = Best rating*
```

#### Feature Matrix
```markdown
### Feature Comparison

| Feature | Product 1 | Product 2 | Product 3 |
|---------|-----------|-----------|-----------|
| Waterproof | ✅ | ✅ | ❌ |
| Down Insulation | ✅ | ❌ | ✅ |
| High Rating (4.5+) | ✅ | ✅ | ✅ |
| **Score** | **3/3** | **2/3** | **2/3** |

**Best Match:** Product 1 (3/3 features)
```

#### Price Analysis
```markdown
### Price Analysis

**Products Analyzed:** 10

| Metric | Value |
|--------|-------|
| Lowest Price | $145.00 |
| Highest Price | $425.00 |
| Average Price | $267.00 |

**Best Value:** Summit Pro Parka ($275, 4.8⭐)
```

**Key Methods**:
```python
create_product_card(product_data) -> Dict  # Single product card
create_comparison_table(products, attributes) -> Dict  # Side-by-side
create_feature_matrix(products, features) -> Dict  # Checkmark grid
create_price_visualization(products, show_distribution) -> Dict  # Price stats
format_product_list(products, show_details) -> Dict  # Search results table
auto_visualize(products, intent) -> str  # Auto-pick best visualization
```

---

### Supporting: UserMemory

**File**: `src/agents/memory.py`

**Status**: ✅ Implemented

**Role**: Persistent JSON-based storage for user preferences.

**Storage**: `user_preferences.json`

**Features**:
- Per-user preferences (sizing, colors, brands)
- **Location and climate tracking**
- Category-specific preferences (outerwear vs footwear)
- Session overrides (temporary, not persisted)
- Feedback signal extraction

**Key Methods**:
```python
user_exists(user_id) -> bool
get_preferences(user_id) -> Dict
update_preference(user_id, section, key, value, permanent) -> None
save_preferences_bulk(user_id, sizing, preferences, general, permanent) -> None
record_feedback(user_id, feedback, context) -> Dict  # Extract signals
reset_memory() -> None  # Clear all user data
```

**Example Preferences Structure**:
```json
{
  "sarah": {
    "sizing": {"fit": "relaxed", "shirt_size": "M"},
    "preferences": {"style": "casual", "colors": ["blue", "green"]},
    "general": {"location": "Minnesota", "climate": "cold"}
  }
}
```

---

## Tool Functions (agent_tools.py)

All tools available to the MS Agent Framework:

### Search Tools (9 functions)
1. `search_products(query, max_results, min_similarity)` - Semantic search
2. `filter_products_by_attributes(brand, category, gender, ...)` - Exact filtering
3. `search_with_filters(query, brand, category, ...)` - Hybrid search
4. `search_products_by_category(category, subcategory, ...)` - Category search
5. `find_similar_products(product_id, max_results)` - Similarity search
6. `get_product_details(product_id)` - Single product lookup
7. `get_available_brands()` - List all brands
8. `get_available_categories()` - List all categories
9. `get_catalog_statistics()` - Catalog overview

### Personalization Tools (5 functions)
1. `identify_user(user_name)` - Check new/returning user
2. `get_user_preferences(user_id)` - Get saved preferences (includes location/climate)
3. `save_user_preferences(user_id, fit, shirt_size, location, ...)` - Save preferences
4. `record_user_feedback(user_id, feedback, context)` - Process feedback
5. `get_returning_user_prompt(user_id)` - Get confirmation prompt

### Visualization Tools (6 functions)
1. `create_product_card(product_id)` - Styled product card
2. `create_comparison_table(product_ids, attributes)` - Side-by-side comparison
3. `create_feature_matrix(product_ids, features)` - Feature grid
4. `create_price_analysis(product_ids, search_query, category)` - Price stats
5. `format_search_results(products, show_details)` - Format as table
6. `visualize_products(products, intent)` - Auto-pick best format

### Outfit Tool (1 function)
1. `get_outfit_recommendation(query, user_id)` - Personalized outfit

---

## File Structure

```
product-rec/
├── src/
│   ├── agents/
│   │   ├── __init__.py                 # Exports all agents
│   │   ├── product_advisor_agent.py    # ✅ MS Agent orchestrator
│   │   ├── personalization_agent.py    # ✅ User preferences & styling
│   │   ├── visual_formatting_tool.py   # ✅ Markdown visualizations
│   │   └── memory.py                   # ✅ JSON-based user memory
│   ├── tools/
│   │   ├── agent_tools.py              # ✅ All tool functions (21 tools)
│   │   └── visualization_tools.py      # ✅ Visualization wrappers
│   ├── product_search.py               # ✅ ChromaDB search engine
│   └── product_search_agent.py         # ✅ MS Agent Framework wrapper
├── data/
│   └── outdoor_products_300.csv        # ✅ Product catalog
├── chroma_db/                          # ✅ Vector database
├── user_preferences.json               # ✅ User memory storage
├── app.py                              # ✅ Gradio web interface
├── tests/
│   ├── unit/                           # ✅ 62 unit tests
│   └── integration/                    # ✅ 9 integration tests
└── docs/
    ├── MULTI_AGENT_ARCHITECTURE.md     # This document
    ├── FINAL_REPORT.md                 # Final project report
    ├── VIDEO_DEMO_SCRIPT.md            # Video demo script
    └── VIDEO_QUICK_REFERENCE.md        # Quick reference for recording
```

---

## Example Flows

### Flow 1: New User with Location
```
User: "Hi, I'm Sarah from Minnesota"
→ identify_user("sarah") → is_new: true
→ infer_climate_from_location("Minnesota") → "cold"
Agent: "Nice to meet you Sarah! I see you're in Minnesota - I'll keep that
        in mind for weather-appropriate recommendations. What's your preferred fit?"

User: "I like relaxed fit"
→ save_user_preferences(user_id="sarah", fit="relaxed",
                        location="Minnesota", climate="cold", permanent=True)
Agent: "Got it! What can I help you find today?"

User: "I need an outfit for hiking"
→ get_user_preferences("sarah") → {location: "Minnesota", climate: "cold"}
→ propagate_preferences → "outfit for hiking warm insulated"
→ search_products(enhanced_query)
→ format_search_results(products)
Agent: [Shows markdown table with warm hiking gear]
```

### Flow 2: Returning User
```
User: "Hi, I'm Sarah"
→ identify_user("sarah") → is_new: false
→ get_returning_user_prompt("sarah")
Agent: "Welcome back Sarah! Last time you preferred relaxed fit and were
        in Minnesota. Same preferences today?"

User: "Yes, same"
Agent: "Great! What are you looking for?"
```

### Flow 3: Comparison Request
```
User: "Compare these 3 jackets"
→ search_products("jackets", max_results=3)
→ create_comparison_table(product_ids)
Agent: [Shows markdown comparison table with 💰⭐ indicators]
```

### Flow 4: Climate-Aware Search
```
User: "Show me jackets" (user location: Minnesota)
→ get_user_preferences("sarah") → climate: "cold"
→ propagate_preferences → "jackets warm insulated winter cold weather"
→ search_products(enhanced_query)
Agent: [Shows warm winter jackets, not lightweight shells]
```

---

## Bug-Safety & Error Handling

The system implements defensive coding patterns:

1. **Graceful Degradation**: If ChromaDB fails, returns empty results with error message
2. **Exception Chaining**: Uses `raise ... from e` to preserve stack traces
3. **Input Validation**: Validates user inputs before processing
4. **Null Safety**: Handles missing preferences and product attributes
5. **Singleton Pattern**: Lazy initialization of expensive resources (agents, DB connections)

---

## Testing

- **62 Unit Tests**: Cover all agents, tools, and edge cases
- **9 Integration Tests**: End-to-end workflow validation
- **Pylint Score**: 9.96/10

Run tests:
```bash
pytest tests/unit/ -v
pytest tests/integration/ -v
pylint src/ --rcfile=pyproject.toml
```

---

**Built with**:
- Microsoft Agent Framework (autogen-agentchat, autogen-ext)
- ChromaDB (vector database)
- Sentence-Transformers (all-MiniLM-L6-v2)
- Python 3.12 + uv
- 300 outdoor products (NorthPeak, AlpineCo, TrailForge)
- Markdown-based visualizations (Gradio compatible)

**Last Updated**: December 2025
