# Multi-Agent System Architecture

## Overview

A 3-agent system for AI-powered product recommendations with personalization and visual data representations.

**Key Design Principle**: Visual representations use **markdown tables and formatting** - no product images required. All visual content is generated from structured product data.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Input                               │
│      "Show me warm jackets for skiing, personalized for me"    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   ORCHESTRATOR                                  │
│  - Classifies user intent (STYLING, SEARCH, COMPARISON, INFO)  │
│  - Routes tasks to specialized agents                           │
│  - Combines results into coherent response                      │
└──────┬──────────────────────────────────┬───────────────────────┘
       │                                  │
       ▼                                  ▼
┌──────────────────────┐    ┌─────────────────────────────────────┐
│  PERSONALIZATION     │    │         VISUAL AGENT                │
│  AGENT               │    │                                     │
│                      │    │  - Product cards (markdown)         │
│  - User memory       │    │  - Comparison tables                │
│  - Preferences       │    │  - Feature matrices                 │
│  - Sizing/Fit        │    │  - Price analysis                   │
│  - Feedback signals  │    │                                     │
└──────────┬───────────┘    └─────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────┐
│                   ChromaDB Vector Store                         │
│                     (300 Products)                              │
└─────────────────────────────────────────────────────────────────┘
```

## Agent Specifications

### 1. Orchestrator

**File**: `src/agents/orchestrator.py`

**Status**: ✅ Implemented

**Role**: Coordinates between Personalization Agent and Product Search.

**Capabilities**:
- Classifies user intent (STYLING, SEARCH, COMPARISON, INFO)
- Routes to appropriate agent(s)
- Combines results into coherent response

**Classes**:
- `QueryIntent` (Enum): STYLING, PRODUCT_SEARCH, COMPARISON, INFO, UNKNOWN
- `OrchestratorResult`: Dataclass with intent, context, products, message
- `Orchestrator`: Main coordinator class

**Key Methods**:
```python
classify_intent(query: str) -> QueryIntent
process_query(query: str, user_id: str = None) -> OrchestratorResult
```

---

### 2. PersonalizationAgent

**File**: `src/agents/personalization_agent.py`

**Status**: ✅ Implemented

**Role**: User-aware styling and preference management with persistent memory.

**Components**:
- **Styling**: Outfit recommendations based on activity, weather, style
- **Fit & Sizing**: Size, fit preference (slim/classic/relaxed/oversized)
- **Feedback**: Converts "too flashy", "too tight" into preference signals

**Memory Features** (stored in `user_preferences.json`):
- Category-specific preferences (outerwear colors ≠ footwear colors)
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
```

**User Flow**:
1. New user: "What's your name?" → Gather preferences → Save
2. Returning user: "Welcome back! Your preferences were X. Same or different?"
3. Preference change: "Is relaxed fit your new default, or just for today?"

---

### 3. VisualFormattingTool

**File**: `src/agents/visual_formatting_tool.py`

**Status**: ✅ Implemented

**Role**: Transform product data into markdown visualizations for Gradio display.

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
2. `get_user_preferences(user_id)` - Get saved preferences
3. `save_user_preferences(user_id, fit, shirt_size, ...)` - Save preferences
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
│   │   ├── __init__.py              # Exports all agents
│   │   ├── orchestrator.py          # ✅ Query routing
│   │   ├── personalization_agent.py # ✅ User preferences & styling
│   │   ├── visual_agent.py          # ✅ Markdown visualizations
│   │   └── memory.py                # ✅ JSON-based user memory
│   ├── product_search.py            # ✅ ChromaDB search engine
│   └── product_search_agent.py      # ✅ MS Agent Framework wrapper
├── tools/
│   └── agent_tools.py               # ✅ All tool functions (21 tools)
├── data/
│   └── outdoor_products_300.csv     # ✅ Product catalog
├── chroma_db/                       # ✅ Vector database
├── user_preferences.json            # ✅ User memory storage
├── gradio_app.py                    # ✅ Web interface
└── docs/
    └── MULTI_AGENT_ARCHITECTURE.md  # This document
```

---

## Example Flows

### Flow 1: New User Styling Request
```
User: "Hi, I'm Sarah"
→ identify_user("sarah") → is_new: true
Agent: "Nice to meet you Sarah! What's your preferred fit?"

User: "I like relaxed fit"
→ save_user_preferences(user_id="sarah", fit="relaxed", permanent=True)
Agent: "Got it! What can I help you find today?"

User: "I need an outfit for hiking"
→ get_outfit_recommendation("outfit for hiking", user_id="sarah")
→ format_search_results(products)
Agent: [Shows markdown table with products]
```

### Flow 2: Returning User
```
User: "Hi, I'm Sarah"
→ identify_user("sarah") → is_new: false
→ get_returning_user_prompt("sarah")
Agent: "Welcome back Sarah! Last time you preferred relaxed fit. Same today?"

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

---

**Built with**:
- Microsoft Agent Framework
- ChromaDB (vector database)
- Python 3.12 + uv
- 300 outdoor products (NorthPeak, AlpineCo, TrailForge)
- Markdown-based visualizations (Gradio compatible)

**Last Updated**: December 2025
