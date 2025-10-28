# AgentThread Implementation Guide

## What is AgentThread?

**AgentThread** is a conversation thread manager in Microsoft Agent Framework that maintains conversation context across multiple interactions. It stores chat history, tool calls, and agent responses.

## Why Use AgentThread?

### Without AgentThread (Stateless)
```python
result = await agent.run("warm jacket for skiing")
# Next query has NO memory of previous conversation
result = await agent.run("show me cheaper options")  # ❌ Agent doesn't know what to compare
```

### With AgentThread (Stateful)
```python
thread = agent.get_new_thread()
result = await agent.run("warm jacket for skiing", thread=thread)
# Next query remembers the context
result = await agent.run("show me cheaper options", thread=thread)  # ✅ Agent knows which jackets to filter
```

---

## How AgentThread Works

### 1. Creating a Thread

```python
# Create agent
agent = await create_product_search_agent()

# Create a new conversation thread
thread = agent.get_new_thread()
```

### 2. Using the Thread

```python
# First message
result = await agent.run("I need a warm jacket", thread=thread)

# Second message - remembers context
result = await agent.run("Show me women's options under $300", thread=thread)

# Third message - still remembers everything
result = await agent.run("What brands did you show me?", thread=thread)
```

### 3. Multiple Users/Sessions

```python
# Store threads per user session
user_threads = {}

def get_thread(user_id: str):
    if user_id not in user_threads:
        user_threads[user_id] = agent.get_new_thread()
    return user_threads[user_id]

# User 1
thread_user1 = get_thread("user_123")
await agent.run("Show me jackets", thread=thread_user1)

# User 2 (separate conversation)
thread_user2 = get_thread("user_456")
await agent.run("Show me boots", thread=thread_user2)
```

---

## Implementation in Product Search Agent

### Demo Mode ([product_search_agent.py](product_search_agent.py):152-190)

```python
async def demo_conversation():
    """Run a demo conversation with the agent using AgentThread."""

    # Create agent
    agent = await create_product_search_agent()

    # Create a conversation thread
    thread = agent.get_new_thread()

    # Run multiple queries on same thread
    queries = [
        "I need a warm jacket for skiing",
        "Show me women's jackets under $300",
        "What brands do you carry?",
    ]

    for query in queries:
        result = await agent.run(query, thread=thread)
        print(result.text)
```

### Interactive Mode ([product_search_agent.py](product_search_agent.py):193-230)

```python
async def interactive_mode():
    """Run interactive chat with the agent using AgentThread."""

    agent = await create_product_search_agent()

    # Create a persistent thread for the conversation
    thread = agent.get_new_thread()

    while True:
        user_input = input("\nYou: ").strip()

        if user_input.lower() in ['quit', 'exit']:
            break

        # Use same thread to maintain context
        result = await agent.run(user_input, thread=thread)
        print(f"Agent: {result.text}")
```

### Gradio Web Interface ([gradio_app.py](gradio_app.py):17-108)

```python
# Global agent and thread storage
agent = None
user_threads = {}  # Store threads per user session

def get_or_create_thread(session_id: str = "default"):
    """Get or create a conversation thread for a user session."""
    global agent, user_threads

    if session_id not in user_threads:
        user_threads[session_id] = agent.get_new_thread()

    return user_threads[session_id]

async def chat_with_agent(message: str, history: list, session_id: str = "default"):
    """Chat with the AI agent using AgentThread for conversation context."""

    # Initialize agent if needed
    await initialize_agent()

    # Get or create thread for this session
    thread = get_or_create_thread(session_id)

    # Run agent with message using thread (maintains context)
    result = await agent.run(message, thread=thread)

    return result.text
```

---

## AgentThread API Reference

### `agent.get_new_thread(**kwargs)`

Creates a new conversation thread for the agent.

**Parameters:**
- `service_thread_id` (str, optional): Service-managed thread ID
- `**kwargs`: Additional thread configuration

**Returns:**
- `AgentThread` object

**Example:**
```python
thread = agent.get_new_thread()
```

### `agent.run(messages, thread=None, **kwargs)`

Runs the agent with a message, optionally using a thread for context.

**Parameters:**
- `messages` (str | ChatMessage | list): The user message(s)
- `thread` (AgentThread, optional): Thread to maintain conversation context
- `**kwargs`: Additional chat options (temperature, max_tokens, etc.)

**Returns:**
- `AgentRunResponse` with `.text` property

**Example:**
```python
result = await agent.run("Hello", thread=thread)
print(result.text)
```

---

## Benefits of AgentThread

### 1. Conversation Context
- Agent remembers previous messages
- Can reference prior search results
- Understands follow-up questions

**Example:**
```
User: "Show me winter jackets"
Agent: [Shows 10 winter jackets]

User: "Which of those are waterproof?"  # ✅ Knows "those" = the 10 jackets shown
```

### 2. Tool Call History
- Agent remembers what tools were called
- Can avoid duplicate searches
- Builds on previous results

**Example:**
```
User: "What brands do you have?"
Agent: [Calls get_available_brands()]

User: "Show me products from the first brand"  # ✅ Remembers the brand list
```

### 3. Session Management
- Multiple users can have separate threads
- Each user gets isolated conversation
- No cross-contamination between users

---

## Common Patterns

### Pattern 1: Single-User CLI
```python
# Create one thread for the entire session
thread = agent.get_new_thread()

while True:
    user_input = input("You: ")
    result = await agent.run(user_input, thread=thread)
    print(f"Agent: {result.text}")
```

### Pattern 2: Multi-User Web App
```python
# Store threads by session ID
threads = {}

def get_thread(session_id):
    if session_id not in threads:
        threads[session_id] = agent.get_new_thread()
    return threads[session_id]

# In request handler
@app.post("/chat")
async def chat(session_id: str, message: str):
    thread = get_thread(session_id)
    result = await agent.run(message, thread=thread)
    return {"response": result.text}
```

### Pattern 3: Stateless Single-Shot
```python
# No thread - fresh context each time
result = await agent.run("Show me jackets")  # No memory of previous calls
```

---

## Thread Lifecycle

### Creating
```python
thread = agent.get_new_thread()  # Creates new thread with empty history
```

### Using
```python
await agent.run("message 1", thread=thread)  # Adds to thread history
await agent.run("message 2", thread=thread)  # Builds on previous message
```

### Resetting
```python
# To reset conversation, create new thread
thread = agent.get_new_thread()  # Fresh start
```

### Cleanup
```python
# No explicit cleanup needed - threads are garbage collected
del user_threads[session_id]  # Remove from storage when done
```

---

## Advanced Features

### Service-Managed Threads
```python
# Use external thread ID (e.g., from database)
thread = agent.get_new_thread(service_thread_id="db_thread_123")
```

### Message Stores
```python
# Configure custom message storage
agent = chat_client.create_agent(
    instructions="...",
    tools=[...],
    chat_message_store_factory=my_custom_store_factory
)

thread = agent.get_new_thread()  # Uses custom storage
```

---

## Testing AgentThread

### Run Demo (3 queries with context)
```bash
uv run python product_search_agent.py
```

### Run Interactive Mode
```bash
uv run python product_search_agent.py --interactive
```

### Run Gradio Web UI (session-based threads)
```bash
uv run python gradio_app.py
```

**Test Conversation:**
```
User: Show me winter jackets
Agent: [Shows jackets]

User: Which are waterproof?  # ✅ Remembers previous results
Agent: [Filters to waterproof ones]

User: Show me the cheapest one  # ✅ Remembers filtered results
Agent: [Shows cheapest waterproof jacket]
```

---

## Performance Considerations

### Thread Storage
- Each thread stores full conversation history
- Memory grows with conversation length
- For long conversations, consider:
  - Limiting thread history
  - Periodically creating new threads
  - Implementing message pruning

### Multi-User Scaling
- Threads are in-memory by default
- For production, use service-managed threads with database storage
- Implement thread cleanup for inactive users

---

## Comparison: With vs Without AgentThread

| Feature | Without Thread | With Thread |
|---------|---------------|-------------|
| **Memory** | None | Full conversation |
| **Follow-ups** | ❌ Doesn't understand | ✅ Understands context |
| **Tool Results** | ❌ Forgotten | ✅ Remembered |
| **Multi-turn** | ❌ Each turn is isolated | ✅ Connected conversation |
| **Use Case** | One-off queries | Chat, assistance |
| **Performance** | Faster (no history) | Slightly slower |
| **Cost** | Lower tokens | Higher tokens (history) |

---

## Summary

**AgentThread enables:**
- ✅ Conversational AI with memory
- ✅ Multi-turn dialogues
- ✅ Follow-up questions
- ✅ Session management
- ✅ User-specific conversations

**When to use:**
- Interactive chat applications
- Multi-step workflows
- Customer support bots
- Personal assistants

**When NOT to use:**
- One-off searches (use `agent.run()` without thread)
- Batch processing
- Stateless APIs

---

**Updated Files:**
- [product_search_agent.py](product_search_agent.py) - Uses AgentThread in demo and interactive modes
- [gradio_app.py](gradio_app.py) - Session-based threads for web chat

**Generated:** October 28, 2025
