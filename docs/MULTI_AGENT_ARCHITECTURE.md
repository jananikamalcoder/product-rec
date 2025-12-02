# Multi-Agent System Architecture

## Overview

A 4-agent system for AI-powered product recommendations with visual data representations and personalized recommendations.

**Key Design Principle**: Visual representations use **data visualizations only** - no product images required. All visual content is generated from structured product data using rich text, tables, and ASCII-based charts.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Input                               │
│      "Show me warm jackets for skiing, personalized for me"    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   ORCHESTRATOR AGENT                            │
│  - Analyzes user intent                                         │
│  - Routes tasks to specialized agents                           │
│  - Combines results into coherent response                      │
│  - Manages conversation flow and context                        │
│  - Coordinates multi-agent workflows                            │
└──────┬────────────┬────────────────┬─────────────────────────┬──┘
       │            │                │                         │
       ▼            ▼                ▼                         ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────────┐ ┌────────────────┐
│  PRODUCT     │ │   VISUAL     │ │ RECOMMENDATION   │ │   USER         │
│  SEARCH      │ │   CONTENT    │ │    ENGINE        │ │  CONTEXT       │
│  AGENT       │ │   AGENT      │ │    AGENT         │ │  (Profiles,    │
│              │ │              │ │                  │ │   History)     │
│ - Semantic   │ │ - Product    │ │ - Personalized   │ │                │
│   search     │ │   Cards      │ │   ranking        │ └────────────────┘
│ - Filtering  │ │ - Comparison │ │ - User prefs     │
│ - Similar    │ │   Tables     │ │ - Collaborative  │
│   products   │ │ - Feature    │ │   filtering      │
│ - Catalog    │ │   Matrix     │ │ - Trending       │
│   info       │ │ - Price Viz  │ │   products       │
└──────┬───────┘ └──────┬───────┘ └────────┬─────────┘
       │                │                   │
       └────────────────┼───────────────────┘
                        ▼
        ┌───────────────────────────────┐
        │   ChromaDB Vector Store       │
        │      (300 Products)           │
        └───────────────────────────────┘
```

## Agent Specifications

### 1. Orchestrator Agent

**Role**: Main coordinator that understands user intent and orchestrates workflow between specialized agents.

**Status**: 📋 **To Be Implemented**

**Capabilities**:
- Parse user queries and determine intent (search, compare, recommend, visualize)
- Route tasks to appropriate agents
- Combine results from multiple agents into coherent responses
- Handle multi-turn conversations with context management
- Error handling and graceful degradation
- Maintain user session state

**Core Functions**:
- `analyze_intent(user_message)` → Determine what the user wants
- `route_task(intent, parameters)` → Delegate to appropriate agent
- `combine_results(agent_responses)` → Aggregate and format results
- `manage_conversation(history)` → Track conversation context

**Example Workflow**:
```
User: "Show me warm jackets under $300 and compare the top 3"

Orchestrator Decision Tree:
1. Parse query: "warm jackets" + filter "$300" + action "compare top 3"
2. Intent: SEARCH + VISUALIZATION (comparison)
3. Route to Product Search Agent → Get products (filter: max_price=300)
4. Route to Visual Content Agent → Create comparison table (top 3)
5. Combine results → Present formatted response
```

**Communication Pattern**:
```python
# User → Orchestrator
{
    "message": "Show me warm jackets under $300 and compare the top 3",
    "user_id": "user123",
    "conversation_id": "conv456"
}

# Orchestrator → Product Search Agent
{
    "agent": "product_search",
    "task": "search_with_filters",
    "parameters": {
        "query": "warm jackets",
        "max_price": 300,
        "max_results": 10
    }
}

# Orchestrator → Visual Content Agent
{
    "agent": "visual_content",
    "task": "create_comparison_table",
    "parameters": {
        "products": [...],  # Top 3 from search
        "attributes": ["price", "rating", "insulation", "waterproofing"]
    }
}

# Orchestrator → User
{
    "response": "Here are warm jackets under $300:\n\n[comparison table]\n\nBased on your search...",
    "products_found": 10,
    "visualization_included": true
}
```

---

### 2. Product Search Agent

**Role**: Specialized agent for product discovery and catalog information.

**Status**: ✅ **Already Implemented** ([agent_tools.py](agent_tools.py), [product_search.py](product_search.py))

**Capabilities**:
- Semantic search using natural language queries
- Exact attribute filtering (brand, category, price, etc.)
- Hybrid search (semantic + filters combined)
- Find similar products based on vector similarity
- Get detailed product information
- Provide catalog statistics and metadata

**Tools** (9 functions):
1. `search_products(query, max_results, min_similarity)` - Natural language semantic search
2. `filter_products_by_attributes(brand, category, gender, min_price, max_price, ...)` - Exact filtering
3. `search_with_filters(query, brand, category, gender, ...)` - Hybrid search
4. `search_products_by_category(category, subcategory, ...)` - Category-specific search
5. `find_similar_products(product_id, max_results, ...)` - Similarity search
6. `get_product_details(product_id)` - Single product lookup
7. `get_available_brands()` - List all brands in catalog
8. `get_available_categories()` - List all categories and subcategories
9. `get_catalog_statistics()` - Overall catalog overview (counts, price ranges, ratings)

**Example Queries**:
```python
# Natural language search
"warm winter jacket for skiing"
→ search_products(query="warm winter jacket for skiing", max_results=5)

# Filtered search
"Women's NorthPeak jackets under $200"
→ filter_products_by_attributes(brand="NorthPeak", gender="Women", max_price=200)

# Hybrid search
"waterproof hiking jacket from AlpineCo"
→ search_with_filters(query="waterproof hiking jacket", brand="AlpineCo")

# Category browsing
"Browse women's parkas under $300"
→ search_products_by_category(category="Outerwear", subcategory="Parkas", gender="Women", max_price=300)

# Similar products
"Products like PRD-ABC123"
→ find_similar_products(product_id="PRD-ABC123", max_results=5)
```

**Return Format**:
```python
{
    "success": True,
    "query": "warm winter jacket",
    "total_results": 5,
    "products": [
        {
            "product_id": "PRD-ABC123",
            "product_name": "Summit Pro Parka",
            "brand": "NorthPeak",
            "category": "Outerwear",
            "subcategory": "Parkas",
            "description": "Premium winter parka with 700-fill down...",
            "price_usd": 275.0,
            "rating": 4.8,
            "gender": "Women",
            "season": "Winter",
            "waterproofing": "Waterproof",
            "insulation": "Down 700-fill",
            "material": "Recycled Nylon",
            "color": "Midnight Blue",
            "primary_purpose": "Alpine Mountaineering",
            "weather_profile": "Heavy Snow, Wind",
            "terrain": "High Alpine, Urban",
            "similarity_score": 0.87
        },
        # ... more products
    ],
    "metadata": {
        "search_type": "semantic",
        "execution_time_ms": 120
    }
}
```

---

### 3. Visual Content Agent

**Role**: Transform product data into rich visual representations without requiring product images.

**Status**: 🔨 **To Be Implemented**

**Capabilities**:

#### 3.1 Styled Product Cards
Rich text representation of individual products with visual hierarchy:

```
╔═══════════════════════════════════════════════════════════════╗
║  🏔️  SUMMIT PRO PARKA                         ⭐ 4.8 / 5.0  ║
╠═══════════════════════════════════════════════════════════════╣
║  Brand: NorthPeak              Category: Outerwear → Parkas   ║
║  Gender: Women                 Season: Winter                 ║
║                                                               ║
║  💰 Price: $275.00                                            ║
║                                                               ║
║  ✨ Key Features:                                             ║
║  • Waterproofing: Fully Waterproof                           ║
║  • Insulation: Down 700-fill power                           ║
║  • Material: Recycled Nylon                                  ║
║  • Color: Midnight Blue                                      ║
║                                                               ║
║  🎯 Best For: Alpine Mountaineering, Extreme cold            ║
║  🌦️  Weather: Heavy Snow, Wind (-20°F to 30°F)              ║
║  🥾 Terrain: High Alpine, Urban                              ║
╚═══════════════════════════════════════════════════════════════╝
```

#### 3.2 Comparison Tables
Side-by-side product comparison with key attributes:

```
┌─────────────────┬──────────────────┬──────────────────┬──────────────────┐
│ Attribute       │ Summit Pro Parka │ Alpine Shell     │ Peak Insulator   │
├─────────────────┼──────────────────┼──────────────────┼──────────────────┤
│ Brand           │ NorthPeak        │ AlpineCo         │ TrailForge       │
│ Price           │ $275.00 ⭐       │ $320.00          │ $245.00 💰       │
│ Rating          │ 4.8 ⭐⭐         │ 4.6              │ 4.7 ⭐           │
│ Waterproofing   │ Waterproof ✓     │ Waterproof ✓     │ Water Resistant  │
│ Insulation      │ Down 700 🔥🔥    │ Synthetic 🔥     │ Down 650 🔥      │
│ Weight          │ Medium           │ Light            │ Medium           │
│ Season          │ Winter ❄️        │ All-Season       │ Winter ❄️        │
│ Best For        │ Extreme Cold     │ Versatility      │ Value            │
└─────────────────┴──────────────────┴──────────────────┴──────────────────┘

Legend: ⭐ = Best in category | 💰 = Best value | 🔥 = Warmth level
```

#### 3.3 Feature Matrix
Grid view showing feature availability across products:

```
Feature Availability Matrix (10 Products)
────────────────────────────────────────────────────────────────────

                      Product ID
Feature         PRD-001  PRD-002  PRD-003  PRD-004  PRD-005  ...
────────────────────────────────────────────────────────────────────
Waterproof        ✓        ✓        ✗        ✓        ✗
Down Insulation   ✓        ✗        ✓        ✓        ✓
Hood              ✓        ✓        ✓        ✗        ✓
Pockets (4+)      ✓        ✗        ✓        ✓        ✓
Recycled Material ✗        ✓        ✓        ✗        ✓
4.5+ Rating       ✓        ✓        ✗        ✓        ✓
Under $300        ✓        ✗        ✓        ✓        ✓
────────────────────────────────────────────────────────────────────
Feature Score     6/7      4/7      5/7      5/7      6/7

Best Match: PRD-001, PRD-005 (6/7 features)
```

#### 3.4 Price Visualization
ASCII-based charts and price distribution:

```
Price Distribution (10 Products)

$0-$100    ║                                    (0 products)
$100-$200  ║████████                            (2 products)
$200-$300  ║████████████████████████            (6 products) ⭐ Most Popular
$300-$400  ║████████                            (2 products)
$400-$500  ║                                    (0 products)
           └─────────────────────────────────────────────────
            0        2        4        6        8       10

Price Range:  $175 - $385
Average:      $267
Median:       $255
Best Value:   Summit Pro Parka ($275, 4.8★)

Rating vs Price Scatter:
 5.0│                      ★
    │            ★    ★        ★
 4.5│       ★         ★
    │  ★         ★
 4.0│    ★    ★
    │
 3.5│
    └─────────────────────────────────────
    $150  $200  $250  $300  $350  $400
```

**Tools** (4 functions to be implemented):
1. `create_product_card(product_data)` → Styled ASCII card for single product
2. `create_comparison_table(products, attributes)` → Side-by-side comparison table
3. `create_feature_matrix(products, features)` → Feature availability grid
4. `create_price_visualization(products, chart_type)` → Price distribution and charts

**Return Format**:
```python
{
    "success": True,
    "visualization_type": "comparison_table",
    "content": "┌─────────────┬──────────┐\n│ ... │",  # ASCII art string
    "metadata": {
        "products_count": 3,
        "attributes_compared": 8,
        "best_value": "PRD-ABC123",
        "generation_time_ms": 45
    }
}
```

**Input Requirements**:
- All functions accept product data in standardized JSON format
- Products must include: product_id, product_name, brand, price_usd, rating
- Optional attributes used when available: waterproofing, insulation, etc.
- No external dependencies (images, files) - pure data transformation

---

### 4. Recommendation Engine Agent

**Role**: Provide personalized product recommendations based on user preferences, behavior, and context.

**Status**: 📋 **To Be Implemented**

**Capabilities**:

#### 4.1 Personalized Ranking
Re-rank search results based on user preferences and history:
- Previous purchase patterns
- Browsing history
- Saved/favorited items
- Explicit preferences (brands, price range, features)

#### 4.2 Collaborative Filtering
"Users who liked X also liked Y":
- Find similar users based on preferences
- Recommend products popular with similar users
- Handle cold-start with content-based fallback

#### 4.3 Contextual Recommendations
Recommendations based on current context:
- Season-appropriate products
- Weather-based suggestions
- Activity-specific recommendations
- Trending products in user's segment

#### 4.4 Complementary Products
"Complete the outfit" / "Frequently bought together":
- Find complementary items (jacket + pants + boots)
- Bundle suggestions
- Accessory recommendations

#### 4.5 Preference Learning
Learn from user interactions:
- Implicit signals (clicks, time spent, comparisons)
- Explicit feedback (ratings, saves, purchases)
- Update user profile over time

**Tools** (6 functions to be implemented):
1. `get_personalized_recommendations(user_id, max_results, context)` → Top recommendations for user
2. `rerank_by_preferences(user_id, products)` → Re-rank product list based on user preferences
3. `find_similar_users(user_id, max_users)` → Find users with similar tastes
4. `get_trending_products(category, timeframe, user_segment)` → Popular products
5. `get_complementary_products(product_id, max_results)` → Items that go well together
6. `update_user_profile(user_id, interaction_type, product_id, metadata)` → Record user interaction

**Example Scenarios**:

**Scenario 1: New User (Cold Start)**
```python
# No user history available
→ get_personalized_recommendations(user_id="new_user_789")

Strategy:
1. Show trending products (most popular overall)
2. Include variety (different brands, price points, categories)
3. Use content-based filtering from any stated preferences
4. Learn quickly from first interactions

Return:
{
    "success": True,
    "user_id": "new_user_789",
    "recommendation_strategy": "cold_start_trending",
    "products": [
        {"product_id": "PRD-001", "score": 0.92, "reason": "Most popular in Outerwear"},
        {"product_id": "PRD-045", "score": 0.89, "reason": "High rating, versatile"},
        ...
    ]
}
```

**Scenario 2: Returning User**
```python
# User has history: previously viewed NorthPeak jackets, likes waterproof gear
→ get_personalized_recommendations(user_id="user_123", context={"season": "winter"})

Strategy:
1. Prioritize preferred brand (NorthPeak)
2. Filter for waterproof products
3. Show winter-appropriate items
4. Include similar products to previously viewed

Return:
{
    "success": True,
    "user_id": "user_123",
    "recommendation_strategy": "personalized_history",
    "products": [
        {
            "product_id": "PRD-078",
            "score": 0.95,
            "reason": "NorthPeak brand (your favorite), Waterproof, Perfect for winter",
            "personalization_factors": ["brand_match", "feature_match", "season_match"]
        },
        ...
    ]
}
```

**Scenario 3: Re-ranking Search Results**
```python
# User searches "hiking jackets" - 50 results found
→ rerank_by_preferences(user_id="user_123", products=[...50 products...])

Strategy:
1. Boost products matching user preferences (price range, brands, features)
2. De-prioritize products user has already viewed/rejected
3. Consider implicit signals (user prefers highly-rated items)
4. Maintain some diversity (don't show only one brand)

Return:
{
    "success": True,
    "original_count": 50,
    "reranked_products": [
        {
            "product_id": "PRD-034",
            "original_rank": 12,
            "new_rank": 1,
            "boost_score": 0.25,
            "boost_reasons": ["price_range_match", "preferred_brand", "high_rating"]
        },
        ...
    ]
}
```

**Scenario 4: Complementary Products**
```python
# User viewing a winter jacket
→ get_complementary_products(product_id="PRD-123", max_results=5)

Strategy:
1. Find products in complementary categories (pants, boots, gloves)
2. Match features (if jacket is waterproof, show waterproof pants)
3. Match style/brand (coordinate the outfit)
4. Consider price point (similar range)

Return:
{
    "success": True,
    "base_product_id": "PRD-123",
    "complementary_products": [
        {
            "product_id": "PRD-234",
            "category": "Pants",
            "reason": "Matches waterproof feature and NorthPeak brand",
            "confidence": 0.88
        },
        {
            "product_id": "PRD-567",
            "category": "Footwear",
            "reason": "Same terrain compatibility (Alpine)",
            "confidence": 0.82
        },
        ...
    ]
}
```

**User Profile Structure**:
```python
{
    "user_id": "user_123",
    "preferences": {
        "favorite_brands": ["NorthPeak", "AlpineCo"],
        "price_range": {"min": 150, "max": 350},
        "preferred_features": ["Waterproof", "Down Insulation"],
        "gender": "Women",
        "size": "Medium"
    },
    "interaction_history": [
        {
            "timestamp": "2025-10-15T14:30:00Z",
            "action": "view",
            "product_id": "PRD-045",
            "duration_seconds": 45
        },
        {
            "timestamp": "2025-10-16T09:15:00Z",
            "action": "save",
            "product_id": "PRD-078"
        },
        ...
    ],
    "derived_insights": {
        "preferred_categories": ["Outerwear", "Footwear"],
        "average_rating_threshold": 4.5,
        "style_preference": "Technical/Outdoor",
        "season_activity": "Winter sports"
    }
}
```

**Recommendation Algorithms**:

1. **Content-Based Filtering**
   - Use product embeddings from ChromaDB
   - Find products similar to user's liked items
   - Weight by user's stated preferences

2. **Collaborative Filtering**
   - User-user similarity (cosine similarity on preference vectors)
   - Item-item similarity (products frequently liked together)
   - Matrix factorization for large-scale patterns

3. **Hybrid Approach**
   - Combine content-based + collaborative scores
   - Weight by confidence (more history = more collaborative weight)
   - Apply business rules (inventory, promotions, seasonality)

4. **Contextual Bandits** (Optional Advanced)
   - Multi-armed bandit for exploration vs. exploitation
   - Learn which recommendations work best
   - Adapt in real-time to user responses

---

## Communication Flow

### Example 1: Simple Search
```
User → "Show me warm jackets for skiing"

Orchestrator:
  ├─→ Product Search Agent:
  │   search_products("warm jackets skiing", max_results=10)
  │   └─→ Returns 10 products
  │
  └─→ Returns formatted results to user

Agents involved: 2 (Orchestrator + Product Search)
Response time: ~200ms
```

### Example 2: Search + Visualization
```
User → "Compare the top 3 waterproof jackets under $300"

Orchestrator:
  ├─→ Product Search Agent:
  │   search_with_filters(
  │     query="waterproof jackets",
  │     max_price=300,
  │     max_results=3
  │   )
  │   └─→ Returns [Product1, Product2, Product3]
  │
  └─→ Visual Content Agent:
      create_comparison_table(
        products=[Product1, Product2, Product3],
        attributes=["price", "rating", "waterproofing", "insulation"]
      )
      └─→ Returns formatted comparison table

Orchestrator combines both outputs and presents to user

Agents involved: 3 (Orchestrator + Product Search + Visual Content)
Response time: ~300-500ms
```

### Example 3: Personalized Recommendations
```
User → "What jackets would you recommend for me?"

Orchestrator:
  ├─→ Recommendation Engine Agent:
  │   get_personalized_recommendations(
  │     user_id="user_123",
  │     max_results=10,
  │     context={"current_season": "winter"}
  │   )
  │   └─→ Returns 10 recommended products with scores
  │
  ├─→ Visual Content Agent:
  │   create_product_card(product_data) for top 3
  │   └─→ Returns 3 styled cards
  │
  └─→ Combines recommendations + visualizations

Agents involved: 3 (Orchestrator + Recommendation Engine + Visual Content)
Response time: ~400-600ms
```

### Example 4: Complex Multi-Agent Workflow
```
User → "I need a jacket for winter hiking, show me options and complete the outfit"

Orchestrator (analyzes intent: search + recommendations + visualization):

  Step 1: Product Search
  ├─→ Product Search Agent:
  │   search_with_filters(
  │     query="jacket winter hiking",
  │     season="Winter",
  │     primary_purpose="Trail Hiking"
  │   )
  │   └─→ Returns 10 jackets

  Step 2: Personalized Ranking
  ├─→ Recommendation Engine Agent:
  │   rerank_by_preferences(
  │     user_id="user_123",
  │     products=[...10 jackets...]
  │   )
  │   └─→ Returns re-ranked list (top jacket: PRD-078)

  Step 3: Find Complementary Items
  ├─→ Recommendation Engine Agent:
  │   get_complementary_products(
  │     product_id="PRD-078",
  │     max_results=4
  │   )
  │   └─→ Returns [pants, boots, gloves, hat]

  Step 4: Visualize
  └─→ Visual Content Agent:
      - create_product_card(jacket PRD-078)
      - create_comparison_table([pants, boots, gloves, hat])
      └─→ Returns formatted visualizations

Orchestrator combines all outputs:
"Based on your preferences, I recommend the Summit Pro Parka:
[styled card for jacket]

To complete your winter hiking outfit:
[comparison table for complementary items]"

Agents involved: 4 (All agents)
Response time: ~800-1200ms
```

### Example 5: Multi-Turn Conversation
```
Turn 1:
User → "I need a jacket for winter hiking"
Orchestrator → Product Search Agent → Returns 5 jackets
Orchestrator → Visual Content Agent → Creates cards
Response: [5 styled product cards]

Turn 2:
User → "Show me more details about the NorthPeak options"
Orchestrator (remembers context: previous search results)
  → Product Search Agent → filter previous results by brand
  → Visual Content Agent → Create detailed cards for 2 NorthPeak jackets
Response: [Detailed cards with full specs]

Turn 3:
User → "Which one is more popular?"
Orchestrator (remembers context: 2 NorthPeak jackets)
  → Recommendation Engine Agent → get_trending_products(compare 2 IDs)
  → Visual Content Agent → create_comparison_table(with popularity data)
Response: [Comparison table showing ratings, purchases, trends]

Turn 4:
User → "I'll take the Summit Pro. What else do I need?"
Orchestrator (remembers context: user selected PRD-078)
  → Recommendation Engine Agent → get_complementary_products(PRD-078)
  → Visual Content Agent → create_product_card for each item
Response: [4 cards for pants, boots, gloves, hat]

Agents involved: All 4
Total conversation: 4 turns
Context maintained by: Orchestrator
```

---

## Implementation Roadmap

### Phase 1: Foundation ✅ (Complete)
- ✅ ChromaDB setup with 300 products
- ✅ Product Search Agent (9 tools)
- ✅ MS Agent Framework integration
- ✅ Example agent implementation

### Phase 2: Visual Content Agent 🔨 (Next)
- [ ] Implement `create_product_card()`
- [ ] Implement `create_comparison_table()`
- [ ] Implement `create_feature_matrix()`
- [ ] Implement `create_price_visualization()`
- [ ] Create [visual_content_agent.py](visual_content_agent.py)
- [ ] Unit tests for each visualization type

### Phase 3: Recommendation Engine Agent 📋 (Planned)
- [ ] User profile data structure
- [ ] Implement `get_personalized_recommendations()`
- [ ] Implement `rerank_by_preferences()`
- [ ] Implement `get_trending_products()`
- [ ] Implement `get_complementary_products()`
- [ ] Implement `update_user_profile()`
- [ ] Create [recommendation_agent.py](recommendation_agent.py)
- [ ] Mock user data for testing

### Phase 4: Orchestrator Agent 📋 (Planned)
- [ ] Intent classification logic
- [ ] Task routing to specialized agents
- [ ] Result aggregation
- [ ] Conversation context management
- [ ] Create [orchestrator_agent.py](orchestrator_agent.py)

### Phase 5: Integration & Testing 📋 (Planned)
- [ ] Multi-agent conversation flow
- [ ] Create [example_multi_agent.py](example_multi_agent.py)
- [ ] End-to-end testing with all 4 agents
- [ ] Performance optimization
- [ ] Error handling and edge cases

---

## Technical Decisions

### Why No Product Images?
1. **Simplicity**: No image hosting/storage needed
2. **Speed**: Faster response times (no image generation/retrieval)
3. **Data-Driven**: Focus on factual product information
4. **Accessibility**: Text-based visualizations work everywhere (terminal, API, chat)
5. **Extensibility**: Can add images later without architecture changes

### Why These 4 Agents?
1. **Orchestrator**: Essential for coordinating multi-agent workflows
2. **Product Search**: Core functionality - finding products
3. **Visual Content**: Enhanced UX - making data readable and comparable
4. **Recommendation Engine**: Personalization - making it relevant to each user

This covers the complete user journey: search → personalize → visualize

### Why ChromaDB for Recommendations?
- Product embeddings already in ChromaDB (semantic similarity)
- Can leverage vector similarity for content-based recommendations
- No additional infrastructure needed
- User preference vectors can be stored in same database

### Technology Choices
- **Microsoft Agent Framework**: Native tool support, production-ready, A2A protocol
- **ChromaDB**: Embedded vector DB, hybrid search, perfect for 300 products
- **ASCII Art**: Universal, no dependencies, fast to generate
- **Structured JSON**: All agents communicate via JSON-serializable messages

---

## Agent Communication Protocol

All agents use structured JSON messages for inter-agent communication:

```python
# Standard Request Format
{
    "agent": "product_search" | "visual_content" | "recommendation_engine",
    "task": "function_name",
    "parameters": {
        "param1": "value1",
        "param2": "value2"
        # ... task-specific parameters
    },
    "context": {
        "conversation_id": "conv_uuid",
        "turn_number": 1,
        "user_id": "user_123",
        "user_intent": "search" | "compare" | "recommend" | "visualize"
    }
}

# Standard Response Format
{
    "success": True | False,
    "agent": "product_search" | "visual_content" | "recommendation_engine",
    "task": "function_name",
    "result": {
        # Task-specific results
        # e.g., products array, visualization string, recommendation scores
    },
    "metadata": {
        "execution_time_ms": 150,
        "items_processed": 5,
        "algorithm_used": "hybrid_search",
        # ... other metadata
    },
    "error": None | "error message"
}
```

---

## Data Flow Example

```
User Message: "Show me jackets similar to what I bought last time, under $300"

┌─────────────────────────────────────────────────────────────┐
│ 1. ORCHESTRATOR receives message                           │
│    - Extracts: similar items + price filter + personalized │
│    - Intent: RECOMMEND + SEARCH + VISUALIZE                │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. ORCHESTRATOR → RECOMMENDATION ENGINE                    │
│    "Get user's purchase history and find similar items"    │
│                                                             │
│    Request: get_personalized_recommendations(              │
│      user_id="user_123",                                   │
│      context={"based_on": "purchase_history"},             │
│      max_results=20                                        │
│    )                                                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. RECOMMENDATION ENGINE processes                         │
│    - Fetches user purchase history: [PRD-045, PRD-128]    │
│    - Finds similar products using embeddings               │
│    - Returns 20 products with similarity scores            │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. ORCHESTRATOR → PRODUCT SEARCH                           │
│    "Filter these 20 products by price < $300"              │
│                                                             │
│    Request: filter_products_by_attributes(                 │
│      products=[...20 products...],                         │
│      max_price=300                                         │
│    )                                                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. PRODUCT SEARCH filters                                  │
│    - Applies price filter                                  │
│    - Returns 8 products under $300                         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. ORCHESTRATOR → VISUAL CONTENT                           │
│    "Create cards for top 5 products"                       │
│                                                             │
│    Request: create_product_card() × 5                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 7. VISUAL CONTENT generates                                │
│    - Creates 5 styled product cards                        │
│    - Returns formatted ASCII art                           │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 8. ORCHESTRATOR combines results                           │
│    - Aggregates: 8 products found, showing top 5           │
│    - Formats response with visualizations                  │
│    - Adds context: "Based on your previous purchases..."   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 9. Response to User                                        │
│                                                             │
│    "Based on your previous purchases, here are similar     │
│     jackets under $300:                                    │
│                                                             │
│     [5 styled product cards displayed]                     │
│                                                             │
│     Found 8 matches total. Would you like to see more?"    │
└─────────────────────────────────────────────────────────────┘

Total agents involved: 4
Total agent calls: 3 (Recommendation → Search → Visual)
Response time: ~800ms
```

---

## Performance Targets

| Operation | Target Time | Agents Involved | Notes |
|-----------|-------------|-----------------|-------|
| Simple search | < 300ms | Orchestrator + Product Search | Direct ChromaDB query |
| Search + visualization | < 600ms | Orchestrator + Product Search + Visual | One visualization |
| Personalized recommendations | < 500ms | Orchestrator + Recommendation Engine | User profile lookup + ranking |
| Complex workflow (search + personalize + visualize) | < 1000ms | All 4 agents | Multiple agent hops |
| Orchestrator routing | < 50ms | Orchestrator only | Intent analysis + task delegation |
| Visual generation | < 200ms | Visual Content only | ASCII art creation |
| Re-ranking | < 150ms | Recommendation Engine | Sort + score calculation |

---

## Error Handling

Each agent implements graceful degradation:

```python
# Example: If Recommendation Engine fails
Orchestrator fallback strategy:
1. Try personalized recommendations
   └─→ If fails: Fall back to Product Search (popular items)
       └─→ If fails: Return cached/static results

# Example: If Visual Content fails
Orchestrator fallback strategy:
1. Try styled product cards
   └─→ If fails: Return plain text product list
       └─→ Still provides value to user
```

---

## File Structure (After Full Implementation)

```
product-rec/
├── agents/
│   ├── __init__.py
│   ├── orchestrator_agent.py           # 📋 Main coordinator
│   ├── product_search_agent.py         # ✅ Search functionality (renamed from agent_tools.py)
│   ├── visual_content_agent.py         # 🔨 Visualizations
│   └── recommendation_agent.py         # 📋 Personalization
├── core/
│   ├── product_search.py               # ✅ Core search engine
│   ├── load_products.py                # ✅ Data loader
│   └── user_profile.py                 # 📋 User data management
├── examples/
│   ├── product_search_agent.py         # ✅ Product Search Agent implementation
│   └── example_multi_agent.py          # 📋 Multi-agent orchestration example
├── data/
│   └── outdoor_products_300_with_lines.csv  # ✅ Product catalog
├── chroma_db/                          # ✅ Vector database (gitignored)
├── notebooks/
│   ├── understanding_embeddings.ipynb  # ✅ Embeddings education
│   └── chromadb_query_examples.ipynb   # ✅ Query examples
├── docs/
│   ├── MULTI_AGENT_ARCHITECTURE.md     # 📄 This document
│   ├── MS_AGENT_INTEGRATION.md         # ✅ Framework integration guide
│   ├── INTEGRATION_SUMMARY.md          # ✅ Migration guide
│   └── EMBEDDINGS_EXPLAINED.md         # ✅ Embeddings reference
├── CLAUDE.md                            # ✅ Development guide
├── README.md                            # ✅ Project overview
├── pyproject.toml                       # ✅ Dependencies
└── .gitignore                           # ✅ Git exclusions
```

Legend: ✅ Complete | 🔨 In Progress | 📋 Planned | 📄 Documentation

---

## Next Steps

### Immediate (Phase 2)
1. **Implement Visual Content Agent**
   - Create [visual_content_agent.py](visual_content_agent.py)
   - Implement 4 visualization functions
   - Test with sample product data from ChromaDB
   - Add unit tests

### Short-term (Phase 3)
2. **Implement Recommendation Engine Agent**
   - Design user profile schema
   - Create [recommendation_agent.py](recommendation_agent.py)
   - Implement 6 recommendation functions
   - Create mock user data for testing
   - Test personalization algorithms

### Medium-term (Phase 4)
3. **Implement Orchestrator Agent**
   - Intent classification (NLP or rule-based)
   - Task routing logic
   - Create [orchestrator_agent.py](orchestrator_agent.py)
   - Conversation context management
   - Multi-agent coordination

### Long-term (Phase 5)
4. **Integration & Polish**
   - Create [example_multi_agent.py](example_multi_agent.py)
   - End-to-end testing with all 4 agents
   - Performance optimization
   - Documentation updates
   - Interactive demo (CLI or notebook)

---

## Use Case Examples

### Use Case 1: First-Time User
**User**: "I need a winter jacket"

**Flow**:
1. Orchestrator → Product Search: search_products("winter jacket")
2. Orchestrator → Recommendation Engine: get_trending_products(category="Outerwear", season="Winter")
3. Orchestrator → Visual Content: create_product_card() for top 3
4. **Result**: Shows 3 popular winter jackets with styled cards

### Use Case 2: Returning User with Preferences
**User**: "Show me new arrivals"

**Flow**:
1. Orchestrator → Recommendation Engine: get_personalized_recommendations(user_id, context="new_arrivals")
2. Orchestrator → Visual Content: create_comparison_table for top 5
3. **Result**: Personalized new arrivals with comparison table

### Use Case 3: Product Comparison
**User**: "Compare NorthPeak parkas under $300"

**Flow**:
1. Orchestrator → Product Search: filter_products_by_attributes(brand="NorthPeak", category="Parkas", max_price=300)
2. Orchestrator → Visual Content: create_comparison_table + create_price_visualization
3. **Result**: Side-by-side comparison with price chart

### Use Case 4: Complete Outfit
**User**: "I'm buying this jacket (PRD-123), what else do I need for winter hiking?"

**Flow**:
1. Orchestrator → Product Search: get_product_details("PRD-123")
2. Orchestrator → Recommendation Engine: get_complementary_products("PRD-123")
3. Orchestrator → Visual Content: create_product_card for jacket + create_comparison_table for accessories
4. **Result**: Jacket details + recommended pants, boots, gloves, hat

### Use Case 5: Similar Products
**User**: "Show me products similar to what I bought last month"

**Flow**:
1. Orchestrator → Recommendation Engine: get_user_history(user_id) → [PRD-045]
2. Orchestrator → Product Search: find_similar_products("PRD-045", max_results=10)
3. Orchestrator → Recommendation Engine: rerank_by_preferences(user_id, products)
4. Orchestrator → Visual Content: create_feature_matrix (compare features)
5. **Result**: Similar products ranked by relevance with feature comparison

---

**Built with**:
- Microsoft Agent Framework (Oct 2025, v1.0.0b251016)
- ChromaDB (persistent vector database)
- Python 3.12 + uv package manager
- 300 outdoor products (NorthPeak, AlpineCo, TrailForge)
- ASCII-based data visualizations (no images required)

**Last Updated**: October 28, 2025
