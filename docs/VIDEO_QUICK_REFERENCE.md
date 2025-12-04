# Quick Reference Card for 10-Minute Video

## TIMELINE AT A GLANCE
| Time | What to Show | What to Say |
|------|--------------|-------------|
| 0:00-1:00 | Title + Architecture diagram | Problem: Shopping is overwhelming. Solution: 3-agent AI system |
| 1:00-2:30 | Code files + user_preferences.json | Explain 3 agents: Orchestrator, Personalization, Search |
| 2:30-3:30 | Tab 2: Simple Search | Demo "warm jacket" - show semantic search, no LLM needed |
| 3:30-5:00 | Tab 1: AI Chat | "Hi I'm Maya from Fargo" → preferences saved → search with filters |
| 5:00-6:30 | Feature matrix + Feedback | "Compare top 3" → "too expensive" → feedback recorded |
| 6:30-7:30 | memory.py error handling | Show try/except, mkdir, defensive coding |
| 7:30-8:30 | Modularity code | Swappable backends, backward compat alias |
| 8:30-10:00 | Bullet points | 5 lessons learned + conclusion |

---

## EXACT DEMO COMMANDS

### Before Recording
```bash
source .venv/bin/activate
python -c "from src.agents.memory import reset_memory; reset_memory()"
python app.py
```

### Demo Script (Copy-Paste)
```
Tab 2 - Simple Search:
1. warm jacket for skiing
2. waterproof hiking boots

Tab 1 - AI Chat:
1. Hi, I'm Maya from Fargo
2. I need a jacket for winter hiking and I like blue colors
3. Compare the top 3 for me
4. Which one has the best features?
5. These are too expensive
6. Show me options under $200
```

---

## KEY CODE SNIPPETS TO SHOW

### 1. Defensive Error Handling (memory.py:49-56)
```python
try:
    return json.loads(self.storage_path.read_text(encoding="utf-8"))
except (json.JSONDecodeError, IOError, PermissionError) as e:
    print(f"Warning: Could not load: {e}")
    return {}  # Don't crash, start fresh
```

### 2. Auto-Fetch Preferences (product_advisor_agent.py:166-196)
```python
if user_context is None and current_user_id:
    try:
        user_prefs = get_user_preferences(current_user_id)
        # Build context from preferences
    except Exception:
        pass  # Proceed without preferences
```

### 3. Climate Inference (personalization_agent.py:25-37)
```python
COLD_CLIMATE_LOCATIONS = {
    "fargo": "cold", "minneapolis": "cold",
    "denver": "cold", "anchorage": "very_cold"
}
```

---

## 5 LESSONS LEARNED (Memorize These)

1. **Agent Separation Matters** - Specialized agents = faster + more reliable
2. **Defensive Coding Saves Hours** - mkdir, try/except, graceful fallbacks
3. **Test Non-LLM Components First** - 62 unit tests catch bugs fast
4. **Auto-Propagate User Context** - Don't rely on LLM to remember
5. **Markdown is Powerful** - Tables with 💰⭐ render beautifully, no images needed

---

## NUMBERS TO MENTION

- **3** agents in hierarchy
- **300** products in catalog
- **7** search tools available
- **62** unit tests passing
- **9** integration tests passing
- **9.96**/10 Pylint score
- **384**-dimensional embeddings (all-MiniLM-L6-v2)

---

## IF SOMETHING GOES WRONG

| Problem | Solution |
|---------|----------|
| API rate limited | Use Tab 2 (no API needed) |
| App won't start | Run tests: `pytest tests/unit/ -v` |
| Preferences not saving | Show code, explain JSON persistence |
| Search slow | Explain: First run loads embeddings into memory |

---

## SCREEN RECORDING CHECKLIST

- [ ] Terminal visible showing app startup
- [ ] Browser at localhost:7860
- [ ] VS Code open to src/agents/
- [ ] user_preferences.json visible
- [ ] Console showing agent tracking (📍 Tracking user)
