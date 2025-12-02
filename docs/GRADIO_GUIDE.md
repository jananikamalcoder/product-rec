# Gradio Web Interface Guide

## 🎉 Your Product Search Agent Now Has a Web UI!

A beautiful web interface for searching and chatting with the product search agent.

---

## Quick Start

### Launch the Web Interface

```bash
uv run python gradio_app.py
```

The interface will automatically open at: **http://localhost:7860**

In GitHub Codespaces, you'll see a pop-up to open the forwarded port.

---

## Features

### 1. 🔍 Simple Search (Tab 1) - **FREE**

**Fast semantic search without LLM**
- No AI agent, just vector similarity
- Instant results
- No API costs

**How to use:**
1. Enter your search query (e.g., "warm jacket for skiing")
2. Select number of results (1-20)
3. Click "Search"

**Example queries:**
- "warm jacket for skiing"
- "waterproof hiking boots"
- "lightweight travel jacket"
- "down insulated parka"

**What you get:**
- Product name, brand, price
- Rating, category, features
- Season, gender
- Relevance score

---

### 2. 💬 AI Chat (Tab 2) - **Uses GitHub Models**

**Conversational AI agent with 9 tools**
- Natural language conversations
- Can filter, compare, recommend
- Uses all 9 search tools automatically

**How to use:**
1. Type your question/request
2. Click "Send" or press Enter
3. Agent responds with formatted results

**Example conversations:**
- "I need a warm jacket for skiing"
- "Show me women's jackets under $300"
- "What brands do you carry?"
- "Compare AlpineCo and NorthPeak parkas"
- "Find boots suitable for winter hiking"

**Cost:** ~$0.0002 per message (GitHub Models gpt-4o-mini)

---

### 3. 📊 Catalog Info (Tab 3) - **FREE**

**Browse catalog information**
- View catalog statistics
- See all available brands
- Check product distribution

**Buttons:**
- **Get Statistics**: Shows counts, price ranges, ratings
- **Show Brands**: Lists all 3 brands (AlpineCo, NorthPeak, TrailForge)

---

## Interface Layout

```
┌────────────────────────────────────────────────────┐
│  🛍️  Product Search Agent                         │
├────────────────────────────────────────────────────┤
│  Tabs: [🔍 Simple Search] [💬 AI Chat] [📊 Info] │
├────────────────────────────────────────────────────┤
│                                                    │
│  🔍 Simple Search (FREE):                         │
│  ┌──────────────────────┐  ┌──────────────────┐  │
│  │ Search Query         │  │ Results          │  │
│  │                      │  │                  │  │
│  │ [warm jacket...]     │  │ 1. Summit Pro... │  │
│  │                      │  │    $275          │  │
│  │ Results: [5    ▼]    │  │    ⭐ 4.8/5      │  │
│  │                      │  │                  │  │
│  │ [🔍 Search]          │  │ 2. Alpine...     │  │
│  └──────────────────────┘  └──────────────────┘  │
│                                                    │
│  Examples:                                         │
│  • warm jacket for skiing                         │
│  • waterproof hiking jacket                       │
│  • lightweight travel jacket                      │
└────────────────────────────────────────────────────┘
```

---

## Comparison: Simple Search vs AI Chat

| Feature | Simple Search | AI Chat |
|---------|--------------|---------|
| **Speed** | ⚡ Instant | 🕐 2-5 seconds |
| **Cost** | 🆓 Free | 💰 ~$0.0002/message |
| **Capabilities** | Semantic search only | All 9 tools + conversation |
| **Best For** | Quick searches | Complex queries, comparisons |
| **Internet Required** | No (after loading) | Yes (GitHub API) |

---

## Example Usage Scenarios

### Scenario 1: Quick Product Search
**Use Simple Search**

1. Go to "Simple Search" tab
2. Type: "waterproof jacket"
3. Set results: 5
4. Click "Search"
5. Get instant results ✅

**Cost**: $0
**Time**: <1 second

---

### Scenario 2: Complex Shopping Query
**Use AI Chat**

1. Go to "AI Chat" tab
2. Type: "I need a jacket for winter skiing, preferably under $300 and waterproof. What do you recommend?"
3. Agent searches, filters, and recommends
4. You can ask follow-ups:
   - "Show me NorthPeak options"
   - "Compare the top 2 by rating"

**Cost**: ~$0.0006 (3 messages)
**Time**: 5-10 seconds total

---

### Scenario 3: Browse Catalog
**Use Catalog Info**

1. Go to "Catalog Info" tab
2. Click "Get Statistics"
3. See all catalog data:
   - 300 products total
   - 3 brands
   - Price range: $26-$775
   - Categories breakdown

**Cost**: $0
**Time**: Instant

---

## Configuration

### Change Port (if 7860 is busy)

Edit `gradio_app.py`:
```python
demo.launch(
    server_port=8080,  # Change this
    # ...
)
```

### Enable Public Sharing

Edit `gradio_app.py`:
```python
demo.launch(
    share=True,  # Creates public Gradio link
    # ...
)
```

This creates a public URL (e.g., `https://abc123.gradio.live`) valid for 72 hours.

### Change LLM Model

The AI Chat uses `gpt-4o-mini` by default. To change:

Edit `product_search_agent.py` line 57:
```python
os.environ["OPENAI_CHAT_MODEL_ID"] = "gpt-4o"  # More capable, more expensive
```

Available models:
- `gpt-4o-mini` (default) - $0.15/$0.60 per 1M tokens
- `gpt-4o` - $5/$15 per 1M tokens
- `gpt-4` - $30/$60 per 1M tokens

---

## Troubleshooting

### "No AI provider configured"

**Problem**: GitHub token not loaded

**Solution**:
```bash
# Check .env file exists
cat .env

# Should contain:
GITHUB_TOKEN=github_pat_...

# Restart app
uv run python gradio_app.py
```

---

### Port 7860 already in use

**Problem**: Another Gradio app is running

**Solution**:
```bash
# Kill existing process
pkill -f gradio_app.py

# Or change port in gradio_app.py
server_port=8080
```

---

### Simple Search works, AI Chat doesn't

**Problem**: GitHub Models API issue

**Check**:
1. Is GITHUB_TOKEN valid?
2. Do you have internet connectivity?
3. Check logs for error messages

**Fallback**: Use Simple Search (works offline, free)

---

## Tech Stack

```
┌─────────────────────────────────────────┐
│           Gradio Web UI                 │
│  - 3 tabs (Search, Chat, Info)         │
│  - Markdown formatting                  │
│  - Examples & buttons                   │
└───────────┬─────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────┐
│      Backend (Python)                   │
│  - gradio_app.py (UI logic)            │
│  - product_search_agent.py (agent)     │
│  - agent_tools.py (9 tools)            │
└───────────┬─────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────┐
│      Data & Models                      │
│  - ChromaDB (300 products)             │
│  - all-MiniLM-L6-v2 (embeddings)       │
│  - GitHub Models (gpt-4o-mini for chat)│
└─────────────────────────────────────────┘
```

---

## Cost Breakdown

### Simple Search
- **Embedding model**: Local (all-MiniLM-L6-v2)
- **Search**: ChromaDB (local)
- **Cost**: $0 ✅

### AI Chat
- **LLM**: GitHub Models (gpt-4o-mini)
- **Cost per message**: ~$0.0002
- **Cost for 100 messages**: ~$0.02 (2 cents)
- **Cost per month (1000 messages)**: ~$0.20 (20 cents)

**Typical usage**: $0.50-2/month

---

## Deployment Options

### Option 1: Local Development (Current)
```bash
uv run python gradio_app.py
# Access: http://localhost:7860
```

### Option 2: GitHub Codespaces (Current)
```bash
uv run python gradio_app.py
# Auto-forwards port, click link
```

### Option 3: Public Gradio Link
```bash
# Edit gradio_app.py: share=True
uv run python gradio_app.py
# Get: https://abc123.gradio.live (72 hours)
```

### Option 4: Deploy to HuggingFace Spaces
1. Create HuggingFace Space
2. Upload code
3. Set GITHUB_TOKEN secret
4. Auto-deployed!

### Option 5: Deploy to Cloud (Production)
- Docker container
- Cloud Run / Azure Container Apps
- AWS Lambda + API Gateway
- Fly.io / Railway

---

## Next Steps

### Add Features:
- [ ] Filter controls (brand, price range, gender)
- [ ] Product images (if available)
- [ ] Comparison table view
- [ ] Export results to CSV
- [ ] Save favorite products
- [ ] Search history

### Improve UI:
- [ ] Custom CSS styling
- [ ] Logo and branding
- [ ] Mobile-responsive design
- [ ] Dark mode toggle

### Add Analytics:
- [ ] Track popular searches
- [ ] Monitor LLM costs
- [ ] User feedback buttons
- [ ] A/B testing

---

## Keyboard Shortcuts

- **Simple Search**:
  - Enter: Submit search
  - Ctrl+K: Focus search box

- **AI Chat**:
  - Enter: Send message
  - Shift+Enter: New line

---

## Resources

- **Gradio Docs**: https://gradio.app/docs
- **GitHub Models**: https://github.com/marketplace/models
- **Microsoft Agent Framework**: https://github.com/microsoft/agent-framework

---

**Enjoy your new web interface!** 🎉

Run `uv run python gradio_app.py` to start exploring.
