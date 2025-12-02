# Evaluation Metrics Comparison
**Traditional IR Metrics vs DeepEval LLM-as-Judge Metrics**

---

## Overview

This project has **TWO complementary evaluation approaches**:

1. **Traditional IR Metrics** - Fast, deterministic, keyword-based
2. **DeepEval LLM-as-Judge Metrics** - Slow, semantic, LLM-judged

**Both are valuable** and serve different purposes. We keep both!

---

## Complete Metrics Table

| Metric Type | Traditional IR | DeepEval LLM-as-Judge | Purpose |
|-------------|---------------|----------------------|---------|
| **Precision** | ✅ `precision_at_k()` | ✅ `ContextualPrecisionMetric` | Fraction of retrieved items that are relevant |
| **Recall** | ✅ `recall_at_k()` | ✅ `ContextualRecallMetric` | Fraction of relevant items that were retrieved |
| **NDCG** | ✅ `ndcg_at_k()` | ❌ Not available in DeepEval | Ranking quality (position matters) |
| **MRR** | ✅ `mean_reciprocal_rank()` | ❌ Not available in DeepEval | Quality of first result |
| **Hit Rate** | ✅ `hit_rate_at_k()` | ❌ Not available in DeepEval | % queries with ≥1 relevant result |
| **Faithfulness** | ❌ N/A | ✅ `FaithfulnessMetric` | Hallucination detection |
| **Answer Relevancy** | ❌ N/A | ✅ `AnswerRelevancyMetric` | Semantic response quality |
| **Contextual Relevancy** | ❌ N/A | ✅ `ContextualRelevancyMetric` | Semantic retrieval quality |

---

## Detailed Comparison

### Precision

| Aspect | Traditional Precision@K | DeepEval Contextual Precision |
|--------|------------------------|------------------------------|
| **What it measures** | % of top K results in ground truth list | LLM judges if each retrieved item is relevant to query |
| **How it works** | `relevant_retrieved / k` | LLM analyzes each item semantically |
| **Speed** | Instant (~0.1s for 15 tests) | Slow (~30s per test) |
| **Cost** | $0 | ~$0.001 per test |
| **Semantic understanding** | No (exact ID match only) | Yes (understands meaning) |
| **Example** | Query: "warm jacket"<br>Retrieved: [ID1, ID2, ID3]<br>Ground truth: [ID1, ID3, ID5]<br>**Score: 2/3 = 0.67** | Query: "warm jacket"<br>Retrieved: ["Down parka $300", "Rain shell $200"]<br>LLM judges: Down parka=relevant, Rain shell=not warm<br>**Score: 0.5** |
| **File** | `retrieval_eval.py` | `deepeval_ir_metrics.py` |
| **Run command** | `uv run python retrieval_eval.py` | `uv run python deepeval_ir_metrics.py --metric precision` |

### Recall

| Aspect | Traditional Recall@K | DeepEval Contextual Recall |
|--------|---------------------|---------------------------|
| **What it measures** | % of ground truth items found in top K | LLM judges if all relevant aspects of query were covered |
| **How it works** | `relevant_retrieved / total_relevant` | LLM analyzes if response addresses all query aspects |
| **Speed** | Instant (~0.1s for 15 tests) | Slow (~30s per test) |
| **Cost** | $0 | ~$0.001 per test |
| **Semantic understanding** | No (exact ID match only) | Yes (understands coverage) |
| **Example** | Query: "warm jacket"<br>Retrieved 3/5 relevant items<br>**Score: 3/5 = 0.6** | Query: "warm waterproof jacket for skiing"<br>Retrieved items cover: warmth ✓, waterproof ✗, skiing ✓<br>**Score: ~0.67** |
| **File** | `retrieval_eval.py` | `deepeval_ir_metrics.py` |
| **Run command** | `uv run python retrieval_eval.py` | `uv run python deepeval_ir_metrics.py --metric recall` |

### NDCG (Normalized Discounted Cumulative Gain)

| Aspect | Traditional NDCG@K | DeepEval Equivalent |
|--------|-------------------|---------------------|
| **What it measures** | Ranking quality (position matters) | ❌ **Not available** |
| **How it works** | Penalizes relevant items in lower positions | N/A |
| **Speed** | Instant | N/A |
| **Cost** | $0 | N/A |
| **Why it's important** | Measures if BEST results are at top | N/A |
| **File** | `retrieval_eval.py` | N/A |
| **Run command** | `uv run python retrieval_eval.py` | N/A |

**Note**: DeepEval doesn't have NDCG. Keep using traditional NDCG for ranking quality.

### MRR (Mean Reciprocal Rank)

| Aspect | Traditional MRR | DeepEval Equivalent |
|--------|----------------|---------------------|
| **What it measures** | 1 / rank of first relevant result | ❌ **Not available** |
| **How it works** | Rewards having relevant result at position 1 | N/A |
| **Speed** | Instant | N/A |
| **Cost** | $0 | N/A |
| **Why it's important** | Users often only look at first result | N/A |
| **File** | `retrieval_eval.py` | N/A |
| **Run command** | `uv run python retrieval_eval.py` | N/A |

**Note**: DeepEval doesn't have MRR. Keep using traditional MRR for first-result quality.

### Faithfulness (Hallucination Detection)

| Aspect | Traditional Equivalent | DeepEval Faithfulness |
|--------|----------------------|----------------------|
| **What it measures** | ❌ **Not available** | Does agent response contain only info from retrieved products? |
| **How it works** | N/A | LLM checks if each statement is supported by context |
| **Speed** | N/A | Slow (~20-30s per test) |
| **Cost** | N/A | ~$0.001 per test |
| **Why it's important** | N/A | Prevents false product claims (price, features, availability) |
| **Example** | N/A | Context: "Jacket costs $300"<br>Response: "Jacket costs $250" ❌<br>**Score: Low (hallucination detected)** |
| **File** | N/A | `deepeval_ir_metrics.py` |
| **Run command** | N/A | `uv run python deepeval_ir_metrics.py --metric faithfulness` |

**Note**: Faithfulness is **ONLY available in DeepEval**. Critical for e-commerce accuracy!

---

## When to Use Which

### Use Traditional IR Metrics (Fast, Free, Deterministic)

✅ **Daily testing / CI/CD**
- Run on every code change
- Fast feedback (30 seconds for 15 tests)
- No API costs

✅ **Performance tracking**
- Track Precision, Recall, NDCG, MRR over time
- Compare different retrieval algorithms
- A/B testing

✅ **Ranking quality (NDCG, MRR)**
- Ensure best results are at top
- Optimize for first-result quality
- **No DeepEval alternative**

**Run:**
```bash
uv run python retrieval_eval.py
```

### Use DeepEval LLM-as-Judge Metrics (Slow, Semantic, Insightful)

✅ **Weekly hallucination audits** (Faithfulness)
- Detect wrong prices, features, brands
- Critical for e-commerce trust
- **No traditional IR alternative**

✅ **Debugging low-performing queries**
- Why did semantic search fail?
- Are products semantically relevant?
- Understand LLM's perspective

✅ **Semantic quality assessment**
- Beyond keyword matching
- Understand if response "feels right"
- User-perceived relevance

**Run:**
```bash
# All DeepEval IR metrics
uv run python deepeval_ir_metrics.py

# Specific metric
uv run python deepeval_ir_metrics.py --metric faithfulness
uv run python deepeval_ir_metrics.py --metric precision
uv run python deepeval_ir_metrics.py --metric recall
```

---

## Recommended Evaluation Strategy

### Daily (Automated, CI/CD)
```bash
# Traditional IR metrics (30 seconds, $0)
uv run python retrieval_eval.py
```

**Track**: Precision, Recall, NDCG, MRR, Hit Rate

### Weekly (Manual, Quality Audit)
```bash
# DeepEval Faithfulness (5-10 minutes, ~$0.01)
uv run python deepeval_ir_metrics.py --metric faithfulness
```

**Purpose**: Detect hallucinations, ensure product accuracy

### Monthly (Deep Analysis)
```bash
# All DeepEval IR metrics (10-15 minutes, ~$0.03)
uv run python deepeval_ir_metrics.py
```

**Purpose**: Comprehensive semantic quality assessment

### On-Demand (When Debugging)
```bash
# Traditional + DeepEval comparison
uv run python retrieval_eval.py
uv run python deepeval_ir_metrics.py
uv run python deepeval_comparison.py
```

**Purpose**: Understand discrepancies, identify issues

---

## Performance Comparison

| Metric | Traditional IR | DeepEval |
|--------|---------------|----------|
| **Speed (15 tests)** | 30 seconds | 7-10 minutes |
| **Cost (15 tests)** | $0.00 | ~$0.01-0.02 |
| **Speed (1 test)** | ~2 seconds | ~30-60 seconds |
| **Deterministic** | Yes (same input = same output) | No (LLM variance) |
| **Requires LLM** | No | Yes (GitHub Models) |
| **Requires API key** | No | Yes (GITHUB_TOKEN) |

---

## Current Evaluation Results

### Traditional IR Metrics (K=10)

| Metric | Score | Status |
|--------|-------|--------|
| Precision@10 | 62.0% | ✅ Good |
| Recall@10 | 62.4% | ✅ Good |
| MRR | 88.6% | ✅ Excellent |
| NDCG@10 | 74.0% | ✅ Good |
| Hit Rate@10 | 93.3% | ✅ Excellent |

**Report**: [RETRIEVAL_EVAL_REPORT.md](RETRIEVAL_EVAL_REPORT.md)

### DeepEval IR Metrics (Sample: 2 tests)

| Metric | Avg Score | Pass Rate | Status |
|--------|-----------|-----------|--------|
| Faithfulness | 0.758 | 50% | ⚠️ Needs attention |

**Report**: [DEEPEVAL_INTEGRATION_REPORT.md](DEEPEVAL_INTEGRATION_REPORT.md)

**Note**: Full DeepEval IR metrics evaluation not yet run (only 2 sample tests).

---

## Files Reference

### Traditional IR Metrics
- **Implementation**: [retrieval_eval.py](retrieval_eval.py) (356 lines)
- **Test Cases**: [retrieval_ground_truth.py](retrieval_ground_truth.py) (15 test cases)
- **Results**: [RETRIEVAL_EVAL_REPORT.md](RETRIEVAL_EVAL_REPORT.md)

### DeepEval IR Metrics
- **Implementation**: [deepeval_ir_metrics.py](deepeval_ir_metrics.py) (NEW - 518 lines)
- **LLM Wrapper**: [deepeval_llm.py](deepeval_llm.py) (GitHub Models integration)
- **Test Cases**: Uses same [retrieval_ground_truth.py](retrieval_ground_truth.py)
- **Results**: `deepeval_ir_metrics_results.json` (auto-generated)

### DeepEval Other Metrics
- **Implementation**: [deepeval_eval.py](deepeval_eval.py)
- **Test Cases**: [deepeval_test_cases.py](deepeval_test_cases.py) (15 test cases)
- **Results**: [DEEPEVAL_INTEGRATION_REPORT.md](DEEPEVAL_INTEGRATION_REPORT.md)

### Comparison Tools
- **Compare IR vs DeepEval**: [deepeval_comparison.py](deepeval_comparison.py)

---

## Summary

**We have BOTH evaluation approaches:**

✅ **Traditional IR Metrics** (Precision, Recall, NDCG, MRR, Hit Rate)
- Fast, free, deterministic
- Great for daily testing and CI/CD
- Essential for ranking quality (NDCG, MRR)

✅ **DeepEval IR Metrics** (Contextual Precision, Contextual Recall, Faithfulness)
- Slow, minimal cost, semantic
- Great for hallucination detection
- Provides LLM-perspective insights

**Both are valuable. Use them together strategically!**

---

**Questions?**
- Traditional IR metrics: See [RETRIEVAL_EVAL_REPORT.md](RETRIEVAL_EVAL_REPORT.md)
- DeepEval metrics: See [DEEPEVAL_INTEGRATION_REPORT.md](DEEPEVAL_INTEGRATION_REPORT.md)
- DeepEval setup: See [DEEPEVAL_SETUP.md](DEEPEVAL_SETUP.md)
