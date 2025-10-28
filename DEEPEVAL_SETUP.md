# DeepEval with Open-Source LLM Setup

## Option 1: DeepEval + Ollama (Local Llama3)

### Step 1: Install Ollama

```bash
# Download and install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull Llama3 model (~4.7GB)
ollama pull llama3

# Verify it's working
ollama run llama3 "Hello, how are you?"
```

### Step 2: Install DeepEval

```bash
uv add deepeval
```

### Step 3: Create Custom LLM Wrapper

```python
# File: deepeval_custom_llm.py

from deepeval.models import DeepEvalBaseLLM
import requests
import json

class OllamaLlama(DeepEvalBaseLLM):
    """Custom DeepEval model using local Ollama."""

    def __init__(self, model_name="llama3"):
        self.model_name = model_name
        self.ollama_url = "http://localhost:11434/api/generate"

    def load_model(self):
        """Model is loaded by Ollama server."""
        return self

    def generate(self, prompt: str) -> str:
        """Generate response from Ollama."""
        response = requests.post(
            self.ollama_url,
            json={
                "model": self.model_name,
                "prompt": prompt,
                "stream": False
            }
        )
        return response.json()["response"]

    async def a_generate(self, prompt: str) -> str:
        """Async version (calls sync for simplicity)."""
        return self.generate(prompt)

    def get_model_name(self):
        return f"Ollama-{self.model_name}"
```

### Step 4: Use with DeepEval

```python
from deepeval.metrics import AnswerRelevancyMetric
from deepeval.test_case import LLMTestCase
from deepeval_custom_llm import OllamaLlama

# Create custom LLM instance
custom_llm = OllamaLlama(model_name="llama3")

# Use in metric
metric = AnswerRelevancyMetric(
    threshold=0.7,
    model=custom_llm  # Use local Llama instead of OpenAI
)

# Create test case
test_case = LLMTestCase(
    input="warm jacket for skiing",
    actual_output="Summit Pro Parka - $275, insulated, waterproof"
)

# Evaluate (FREE - no API calls!)
metric.measure(test_case)
print(f"Score: {test_case.score}")
print(f"Reason: {test_case.reason}")
```

### Step 5: Run Evaluation

```python
from deepeval import evaluate
from deepeval_custom_llm import OllamaLlama

# Setup
custom_llm = OllamaLlama()
test_cases = [...]  # Your test cases
metrics = [
    AnswerRelevancyMetric(model=custom_llm),
    FaithfulnessMetric(model=custom_llm)
]

# Evaluate (all local, no API costs)
evaluate(test_cases=test_cases, metrics=metrics)
```

---

## Option 2: DeepEval + HuggingFace API (Free Tier)

### Step 1: Get HuggingFace Token

1. Sign up at https://huggingface.co
2. Go to Settings → Access Tokens
3. Create token (free tier: 1,000 requests/day)

### Step 2: Create HF Wrapper

```python
from deepeval.models import DeepEvalBaseLLM
from huggingface_hub import InferenceClient

class HuggingFaceLLM(DeepEvalBaseLLM):
    def __init__(self, model="meta-llama/Llama-2-7b-chat-hf", token=None):
        self.client = InferenceClient(model=model, token=token)
        self.model_name = model

    def load_model(self):
        return self

    def generate(self, prompt: str) -> str:
        response = self.client.text_generation(
            prompt,
            max_new_tokens=500
        )
        return response

    async def a_generate(self, prompt: str) -> str:
        return self.generate(prompt)

    def get_model_name(self):
        return self.model_name
```

### Step 3: Use with DeepEval

```python
import os
from deepeval_custom_llm import HuggingFaceLLM

# Set token
os.environ["HF_TOKEN"] = "hf_..."

# Create model
hf_llm = HuggingFaceLLM(
    model="meta-llama/Llama-2-7b-chat-hf",
    token=os.environ["HF_TOKEN"]
)

# Use in metrics
metric = AnswerRelevancyMetric(model=hf_llm)
```

**Free tier limits**:
- 1,000 requests/day
- Rate limited
- Good for development

---

## Comparison: Paid vs Free LLMs

### Quality Comparison (Answer Relevancy Metric)

| LLM | Accuracy | Agreement with Human | Speed |
|-----|----------|---------------------|-------|
| **GPT-4o** | 95% | Very High | 500ms |
| **GPT-4o-mini** | 90% | High | 300ms |
| **Llama3-8B (local)** | 75-80% | Medium | 2-5s |
| **Llama2-7B (HF API)** | 70-75% | Medium | 1-3s |

### Cost Comparison (1,000 evals)

| Option | Setup Time | Runtime | Cost |
|--------|-----------|---------|------|
| **GPT-4o-mini** | 5 min | 5 min | $0.15 |
| **Ollama Llama3** | 30 min | 30 min | $0 |
| **HF API** | 15 min | 15 min | $0 (free tier) |

---

## Recommendation

### For Learning: Use Ollama + Llama3
- Cost: $0
- Setup: 30 minutes
- Good enough for experimentation

### For Production: Use GPT-4o-mini
- Cost: Negligible ($0.15 per 1,000 evals)
- Setup: 5 minutes
- Best quality

### For Development: Our Custom Metrics
- Cost: $0
- Setup: Already done ✅
- Fast and reliable for retrieval evaluation

---

## When to Choose What

```
Question: Do I need LLM-based semantic evaluation?
    │
    ├─ NO → Use our custom metrics (precision, recall, NDCG) ✅ FREE
    │
    └─ YES → Do I need it frequently?
        │
        ├─ YES → Use GPT-4o-mini ($0.15/1K) ✅ BEST QUALITY
        │
        └─ NO → Want to experiment?
            │
            ├─ YES → Use Ollama Llama3 ✅ FREE, SLOW
            │
            └─ NO → Use our metrics ✅ DONE
```

---

## Files to Create (If Using Ollama)

1. `deepeval_custom_llm.py` - Ollama wrapper for DeepEval
2. `test_deepeval_local.py` - Tests using local LLM
3. `requirements.txt` - Add deepeval, ollama dependencies

---

**Bottom Line**:
- DeepEval is open-source (FREE)
- But needs an LLM (FREE if local, CHEAP if OpenAI)
- For production: $0.15/1000 evals with GPT-4o-mini is negligible
- For learning: Local Llama3 is free but slower/lower quality
