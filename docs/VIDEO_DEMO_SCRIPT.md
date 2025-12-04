# Video Demo Script: Product Advisor Multi-Agent System
## 10-Minute Video Presentation

---

## REQUIREMENTS CHECKLIST
- [x] Full demo of working system
- [x] Evidence of bug-safety (error handling, defensive coding)
- [x] Clarity (clear architecture, clean code)
- [x] Adaptability (modular design, configurable)
- [x] Reflection on lessons learned

---

## VIDEO TIMELINE (10 Minutes)

| Time | Section | Content |
|------|---------|---------|
| 0:00-1:00 | Introduction | Problem, solution, architecture overview |
| 1:00-2:30 | Architecture Deep Dive | 3-agent system explanation |
| 2:30-5:00 | Live Demo Part 1 | Simple search + AI chat with personalization |
| 5:00-6:30 | Live Demo Part 2 | Comparison tables, feature matrix, feedback |
| 6:30-7:30 | Code Quality | Bug-safety, error handling, tests |
| 7:30-8:30 | Adaptability | Modular design, extensibility |
| 8:30-10:00 | Lessons Learned | Reflection + conclusion |

---

## DETAILED SCRIPT

### SECTION 1: INTRODUCTION (0:00 - 1:00)
**[SCREEN: Title slide with project name]**

> "Hello! Today I'm presenting my Product Advisor system—a multi-agent AI application for personalized outdoor apparel recommendations.

> The problem I'm solving is this: Shopping for outdoor gear is overwhelming. There are hundreds of products with technical specifications like waterproofing levels, insulation types, and seasonal ratings. Users need personalized guidance, not just a search box.

> My solution uses a hierarchical 3-agent architecture powered by GPT-4o-mini. The system remembers your preferences, searches intelligently using semantic understanding, and formats results beautifully—all through a web interface."

**[SCREEN: Show architecture diagram]**

```
┌─────────────────────────────────────────────────┐
│         PRODUCT ADVISOR (Orchestrator)          │
│     Routes tasks, applies context, formats      │
├─────────────────┬───────────────────────────────┤
│                 │                               │
│  PERSONALIZATION│      PRODUCT SEARCH          │
│     AGENT       │         AGENT                │
│  (User Memory)  │   (Semantic + Filters)       │
│                 │                               │
└─────────────────┴───────────────────────────────┘
         ↓                      ↓
    user_preferences.json    ChromaDB (300 products)
```

---

### SECTION 2: ARCHITECTURE DEEP DIVE (1:00 - 2:30)
**[SCREEN: Show src/agents/ folder structure]**

> "Let me explain the architecture. I have three specialized agents:

> **First, the Product Advisor Agent**—this is the orchestrator. When you ask 'I need a warm jacket,' it decides: Should I identify this user first? Should I search for products? How do I format the results? It coordinates everything."

**[SCREEN: Show product_advisor_agent.py, lines 99-120]**

> "**Second, the PersonalizationAgent** handles user memory. It remembers your name, your preferred fit—whether you like slim or relaxed—your favorite colors, brands, even your location for weather-based recommendations. All persisted to a JSON file."

**[SCREEN: Show data/user_preferences.json with Janani's profile]**

```json
{
  "janani": {
    "preferences": {
      "outerwear": { "colors": ["blue"] }
    },
    "location": { "city": "Fargo", "climate": "cold" }
  }
}
```

> "**Third, the ProductSearchAgent** handles the actual searching. It has 7 specialized tools: semantic search using embeddings, filter-based search for exact matches, hybrid search combining both, and more. It returns raw JSON—never markdown—leaving formatting to the orchestrator."

**[SCREEN: Show product_search_agent.py tool list]**

> "This separation of concerns is critical. Each agent does one thing well, making the system easier to test, debug, and extend."

---

### SECTION 3: LIVE DEMO - SIMPLE SEARCH (2:30 - 3:30)
**[SCREEN: Open browser at localhost:7860]**

> "Let me show you the system in action. I'll start with the Simple Search tab—this uses semantic search without any LLM calls, so it's fast and free."

**[TYPE: "warm jacket for skiing"]**

> "Notice the results show similarity scores. The system understands that 'warm jacket' matches 'insulated coat' even though they don't share keywords. That's the power of semantic search with embeddings."

**[TYPE: "waterproof hiking boots"]**

> "Search is instant because embeddings are computed locally using the all-MiniLM-L6-v2 model—no API calls needed."

---

### SECTION 4: LIVE DEMO - AI CHAT WITH PERSONALIZATION (3:30 - 5:00)
**[SCREEN: Switch to AI Chat tab]**

> "Now let's see the full multi-agent system. I'll introduce myself as a new user."

**[TYPE: "Hi, I'm Maya from Fargo"]**

> "Watch what happens... The orchestrator delegates to the PersonalizationAgent which identifies me as a new user and saves my location. Fargo triggers a 'cold climate' inference—the system knows I'll need winter-ready products."

**[SHOW: Console output with "📍 Tracking user: maya"]**

**[TYPE: "I need a jacket for winter hiking and I like blue colors"]**

> "Now the magic happens. The system:
> 1. Saves my color preference permanently
> 2. Searches for 'winter hiking jacket'
> 3. Auto-applies my preferences as filters
> 4. Formats results as a beautiful comparison table"

**[SHOW: Markdown table with products]**

> "Notice the 💰 indicator for best price and ⭐ for best rating. This is all markdown—no images—rendered by Gradio."

**[TYPE: "Compare the top 3 for me"]**

> "The orchestrator creates a detailed comparison table with all the technical specs side by side."

**[SHOW: Comparison table with brand, price, rating, waterproofing, insulation]**

---

### SECTION 5: LIVE DEMO - FEATURE MATRIX & FEEDBACK (5:00 - 6:30)
**[TYPE: "Which one has the best features?"]**

> "Here's the feature matrix—checkmarks show which products have which features. The system even calculates a 'Best Match' based on feature count."

**[SHOW: Feature matrix with ✅ and ❌]**

```
| Feature          | Summit Pro | Alpine Shell | Peak Insulator |
|------------------|------------|--------------|----------------|
| Waterproof       | ✅         | ✅           | ✅             |
| Down Insulation  | ✅         | ❌           | ✅             |
| High Rating      | ✅         | ✅           | ✅             |
| Under $300       | ❌         | ❌           | ❌             |

**Best Match: Summit Pro (4/4 features)**
```

**[TYPE: "These are too expensive"]**

> "This demonstrates the feedback loop. The system records my feedback as a 'budget concern' signal and will prioritize affordable options next time."

**[SHOW: Console output with feedback signal]**

**[TYPE: "Show me options under $200"]**

> "Now it searches with a price filter automatically applied."

**[RETURNING USER DEMO - Optional]**

> "If I were to close this session and come back..."

**[TYPE: "Hi, I'm Maya"]**

> "Watch—it remembers me! 'Welcome back, Maya! Last time you preferred blue colors and were concerned about budget.' That's the persistence working."

---

### SECTION 6: BUG-SAFETY & ERROR HANDLING (6:30 - 7:30)
**[SCREEN: Show code snippets demonstrating defensive coding]**

> "Now let's talk about bug-safety. I implemented several defensive coding practices:"

**[SCREEN: Show memory.py _load() method]**

> "**1. Graceful File Handling**: If the preferences file is corrupted, the system catches the exception and starts fresh instead of crashing."

```python
def _load(self) -> Dict[str, Any]:
    if self.storage_path.exists():
        try:
            return json.loads(self.storage_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, IOError, PermissionError) as e:
            print(f"Warning: Could not load {self.storage_path}: {e}")
            return {}  # Start fresh instead of crashing
    return {}
```

**[SCREEN: Show memory.py _save() method]**

> "**2. Directory Creation**: Before saving, we ensure the parent directory exists."

```python
def _save(self):
    self.storage_path.parent.mkdir(parents=True, exist_ok=True)
    self.storage_path.write_text(json.dumps(self.data, indent=2), encoding="utf-8")
```

**[SCREEN: Show product_advisor_agent.py auto-fetch with try/except]**

> "**3. Safe Preference Fetching**: If preferences can't be loaded, we proceed without them rather than failing."

```python
try:
    user_prefs = get_user_preferences(current_user_id)
except Exception as e:
    print(f"⚠️ Could not auto-fetch preferences: {e}")
    # Proceed without preferences
```

**[SCREEN: Show test results]**

> "**4. Comprehensive Testing**: 62 unit tests, 9 integration tests—all passing. Pylint score: 9.96/10."

**[RUN: pytest tests/unit/ -v --tb=short | Show green checkmarks]**

---

### SECTION 7: ADAPTABILITY & MODULARITY (7:30 - 8:30)
**[SCREEN: Show file structure]**

> "The system is highly adaptable. Here's how:"

> "**1. Modular Agent Design**: Each agent is independent. I could swap out the PersonalizationAgent for a database-backed version without touching the search or orchestration code."

**[SCREEN: Show agents/__init__.py exports]**

> "**2. Configurable LLM Backend**: The system supports both OpenAI and GitHub Models. Just change an environment variable."

```python
# Try OpenAI first (higher rate limits)
openai_key = os.getenv("OPENAI_API_KEY")
if openai_key:
    return OpenAIChatClient()

# Fall back to GitHub Models
github_token = os.getenv("GITHUB_TOKEN")
if github_token:
    os.environ["OPENAI_BASE_URL"] = "https://models.inference.ai.azure.com"
    return OpenAIChatClient()
```

> "**3. Extensible Product Catalog**: Adding new products is as simple as running the load script. The ChromaDB embeddings are regenerated automatically."

> "**4. Backward Compatibility**: When I renamed VisualAgent to VisualFormattingTool, I added an alias to maintain compatibility with existing code."

```python
# Backward compatibility alias
VisualAgent = VisualFormattingTool
```

> "**5. Location-Based Weather Inference**: I added a cold climate mapping that's easily extendable."

```python
COLD_CLIMATE_LOCATIONS = {
    "fargo": "cold", "minneapolis": "cold", "chicago": "cold",
    "denver": "cold", "boston": "cold", "anchorage": "very_cold"
}
```

---

### SECTION 8: LESSONS LEARNED & REFLECTION (8:30 - 10:00)
**[SCREEN: Bullet points appearing as you speak]**

> "Let me reflect on what I learned building this system:

> **Lesson 1: Agent Separation Matters**
> Early on, I had one monolithic agent doing everything. It was slow, hard to debug, and the LLM got confused. Splitting into specialized agents—each with a clear role—made the system faster and more reliable. The PersonalizationAgent just handles data; it never asks questions. The SearchAgent returns raw JSON; it never formats.

> **Lesson 2: Defensive Coding Saves Hours**
> I found a bug where the first user to save preferences crashed the app because the data/ directory didn't exist. Adding `mkdir(parents=True, exist_ok=True)` fixed it. Now I proactively add such guards everywhere.

> **Lesson 3: Test Non-LLM Components First**
> The memory system, search engine, and visualization tools don't need LLM calls. I wrote 62 unit tests for these components. When something breaks, I know immediately if it's the LLM or my code.

> **Lesson 4: User Context Should Flow Automatically**
> Initially, I expected the LLM to always pass user preferences to searches. It often forgot. So I added automatic preference fetching—if a user is identified, their preferences are applied to every search without relying on the LLM to remember.

> **Lesson 5: Markdown is Powerful**
> Instead of generating images or complex HTML, I use pure markdown. It's lightweight, fast, and Gradio renders it beautifully. The comparison tables with 💰 and ⭐ indicators are just markdown—no frontend framework needed.

> **What I'd Do Differently**
> If I were starting over, I'd implement a proper database for user preferences instead of JSON files, and I'd add caching for embeddings to make the first search faster.

> **Conclusion**
> This project taught me that multi-agent systems require clear boundaries, robust error handling, and comprehensive testing. The result is a personalized shopping assistant that remembers you, understands natural language, and presents information clearly. Thank you for watching!"

**[SCREEN: Show Gradio interface one more time with final search results]**

---

## DEMO COMMANDS CHEAT SHEET

### Before Recording
```bash
# 1. Ensure dependencies installed
source .venv/bin/activate
uv sync

# 2. Reset user preferences for clean demo
python -c "from src.agents.memory import reset_memory; reset_memory()"

# 3. Launch app
python app.py
```

### Demo Conversation Flow
1. **Tab 2 - Simple Search**:
   - "warm jacket for skiing"
   - "waterproof hiking boots"

2. **Tab 1 - AI Chat**:
   - "Hi, I'm Maya from Fargo"
   - "I need a jacket for winter hiking and I like blue colors"
   - "Compare the top 3 for me"
   - "Which one has the best features?"
   - "These are too expensive"
   - "Show me options under $200"

3. **Returning User** (optional):
   - "Hi, I'm Maya" (shows remembered preferences)

### Code Files to Show
1. `src/agents/product_advisor_agent.py` - Lines 99-150 (orchestrator)
2. `src/agents/personalization_agent.py` - Lines 25-50 (climate mapping)
3. `src/agents/memory.py` - Lines 49-62 (defensive loading/saving)
4. `data/user_preferences.json` - Show saved user data
5. `tests/unit/` - Show test file list

### Terminal Commands for Demo
```bash
# Show tests passing
pytest tests/unit/ -v --timeout=60 | head -30

# Show pylint score
pylint src/ --disable=R,C0301 2>&1 | tail -5
```

---

## BACKUP PLANS

### If API Rate Limited
- Use Tab 2 (Simple Search) which requires no API calls
- Explain: "The semantic search works offline using local embeddings"

### If App Crashes
- Show test suite passing as evidence of working code
- Walk through code manually explaining the flow

### If Gradio Won't Start
- Use the CLI interactive mode: `python src/agents/product_search_agent.py`
- Demonstrate search tools directly

---

## KEY TALKING POINTS

### For Bug-Safety
- JSON corruption recovery
- Directory auto-creation
- Exception chaining with `from e`
- Try/except around preference fetching
- 62 unit tests + 9 integration tests

### For Clarity
- Clear 3-agent separation
- Each file under 500 lines
- Comprehensive docstrings
- Type hints throughout
- Pylint score 9.96/10

### For Adaptability
- Swappable LLM backends
- Modular agent design
- Backward compatibility aliases
- Extensible climate mapping
- Easy product catalog updates

### For Lessons Learned
- Agent separation importance
- Defensive coding value
- Test non-LLM components first
- Automatic context propagation
- Markdown power over complex rendering
