"""
Retrieval Evaluation Script

Evaluates the quality of Product Search Agent's retrieval using standard metrics:
- Precision@K: Proportion of relevant items in top K results
- Recall@K: Proportion of relevant items found in top K results
- MRR (Mean Reciprocal Rank): Average of 1/rank of first relevant item
- NDCG@K (Normalized Discounted Cumulative Gain): Ranking quality metric
- Hit Rate: Percentage of queries with at least 1 relevant result in top K

Usage:
    python retrieval_eval.py              # Run all evaluations
    python retrieval_eval.py --k 5        # Evaluate at K=5
    python retrieval_eval.py --category semantic  # Only semantic tests
"""

import argparse
import math
from typing import List, Dict, Any, Set
from collections import defaultdict
import agent_tools
from retrieval_ground_truth import get_ground_truth


def precision_at_k(retrieved: List[str], relevant: List[str], k: int) -> float:
    """
    Precision@K: What fraction of retrieved items (top K) are relevant?

    Args:
        retrieved: List of retrieved product IDs (in rank order)
        relevant: List of relevant product IDs
        k: Cutoff position

    Returns:
        Precision@K score (0.0 to 1.0)
    """
    if k == 0 or len(retrieved) == 0:
        return 0.0

    retrieved_at_k = retrieved[:k]
    relevant_set = set(relevant)
    relevant_retrieved = sum(1 for item in retrieved_at_k if item in relevant_set)

    return relevant_retrieved / k


def recall_at_k(retrieved: List[str], relevant: List[str], k: int) -> float:
    """
    Recall@K: What fraction of relevant items are in top K retrieved?

    Args:
        retrieved: List of retrieved product IDs (in rank order)
        relevant: List of relevant product IDs
        k: Cutoff position

    Returns:
        Recall@K score (0.0 to 1.0)
    """
    if len(relevant) == 0:
        return 0.0

    retrieved_at_k = retrieved[:k]
    relevant_set = set(relevant)
    relevant_retrieved = sum(1 for item in retrieved_at_k if item in relevant_set)

    return relevant_retrieved / len(relevant)


def mean_reciprocal_rank(retrieved: List[str], relevant: List[str]) -> float:
    """
    MRR: 1 / rank of first relevant item (0 if no relevant items found)

    Args:
        retrieved: List of retrieved product IDs (in rank order)
        relevant: List of relevant product IDs

    Returns:
        Reciprocal rank score (0.0 to 1.0)
    """
    relevant_set = set(relevant)

    for rank, item in enumerate(retrieved, start=1):
        if item in relevant_set:
            return 1.0 / rank

    return 0.0


def dcg_at_k(retrieved: List[str], relevant: List[str], k: int) -> float:
    """
    DCG@K: Discounted Cumulative Gain at position K

    DCG = sum(rel_i / log2(i + 1)) for i in 1..k
    rel_i = 1 if item is relevant, 0 otherwise

    Args:
        retrieved: List of retrieved product IDs (in rank order)
        relevant: List of relevant product IDs
        k: Cutoff position

    Returns:
        DCG@K score
    """
    relevant_set = set(relevant)
    dcg = 0.0

    for i, item in enumerate(retrieved[:k], start=1):
        if item in relevant_set:
            # Gain is 1 for relevant, 0 for non-relevant
            # Discounted by log2(position + 1)
            dcg += 1.0 / math.log2(i + 1)

    return dcg

# Normalized Discounted Cumulative Gain: evaluates ranking quality
def ndcg_at_k(retrieved: List[str], relevant: List[str], k: int) -> float:
    """
    NDCG@K: Normalized Discounted Cumulative Gain at position K

    NDCG = DCG@K / IDCG@K
    where IDCG@K is the ideal DCG (best possible ranking)

    Args:
        retrieved: List of retrieved product IDs (in rank order)
        relevant: List of relevant product IDs
        k: Cutoff position

    Returns:
        NDCG@K score (0.0 to 1.0)
    """
    dcg = dcg_at_k(retrieved, relevant, k)

    # Ideal DCG: assume perfect ranking (all relevant items first)
    ideal_retrieved = relevant[:k]  # Best case: all relevant items ranked first
    idcg = dcg_at_k(ideal_retrieved, relevant, k)

    if idcg == 0.0:
        return 0.0

    return dcg / idcg


def hit_rate_at_k(retrieved: List[str], relevant: List[str], k: int) -> float:
    """
    Hit Rate@K: 1 if at least one relevant item in top K, 0 otherwise

    Args:
        retrieved: List of retrieved product IDs (in rank order)
        relevant: List of relevant product IDs
        k: Cutoff position

    Returns:
        1.0 if hit, 0.0 if miss
    """
    retrieved_at_k = set(retrieved[:k])
    relevant_set = set(relevant)

    return 1.0 if retrieved_at_k & relevant_set else 0.0


def evaluate_query(
    test_case: Dict[str, Any],
    k: int = 10
) -> Dict[str, float]:
    """
    Evaluate a single query and return all metrics.

    Args:
        test_case: Test case from ground truth dataset
        k: Cutoff position for metrics

    Returns:
        Dictionary of metric scores
    """
    # Execute the search based on test case type
    if test_case['category'] in ['semantic', 'hybrid']:
        # Semantic or hybrid search
        result = agent_tools.search_with_filters(
            query=test_case['query'],
            brand=test_case.get('filters', {}).get('brand'),
            category=test_case.get('filters', {}).get('category'),
            gender=test_case.get('filters', {}).get('gender'),
            min_price=test_case.get('filters', {}).get('min_price'),
            max_price=test_case.get('filters', {}).get('max_price'),
            max_results=k * 2  # Get more than K to have enough for eval
        )
    elif test_case['category'] == 'filter':
        # Pure filter search
        filters = test_case['filters']
        result = agent_tools.filter_products_by_attributes(
            brand=filters.get('brand'),
            category=filters.get('category'),
            subcategory=filters.get('subcategory'),
            gender=filters.get('gender'),
            season=filters.get('season'),
            min_price=filters.get('min_price'),
            max_price=filters.get('max_price'),
            max_results=k * 2
        )
    elif test_case['category'] == 'category_browse':
        # Category browsing
        filters = test_case['filters']
        result = agent_tools.search_products_by_category(
            category=filters.get('category'),
            subcategory=filters.get('subcategory'),
            gender=filters.get('gender'),
            min_price=filters.get('min_price'),
            max_price=filters.get('max_price'),
            max_results=k * 2
        )
    else:
        return {"error": f"Unknown category: {test_case['category']}"}

    # Extract retrieved product IDs
    if not result['success']:
        # If search failed, return zero scores
        return {
            "precision@k": 0.0,
            "recall@k": 0.0,
            "mrr": 0.0,
            "ndcg@k": 0.0,
            "hit_rate@k": 0.0,
            "num_retrieved": 0,
            "error": result.get('error', 'Unknown error')
        }

    retrieved_ids = [p['product_id'] for p in result['products']]
    relevant_ids = test_case['relevant_products']

    # Calculate metrics
    metrics = {
        "precision@k": precision_at_k(retrieved_ids, relevant_ids, k),
        "recall@k": recall_at_k(retrieved_ids, relevant_ids, k),
        "mrr": mean_reciprocal_rank(retrieved_ids, relevant_ids),
        "ndcg@k": ndcg_at_k(retrieved_ids, relevant_ids, k),
        "hit_rate@k": hit_rate_at_k(retrieved_ids, relevant_ids, k),
        "num_retrieved": len(retrieved_ids),
        "num_relevant": len(relevant_ids)
    }

    return metrics


def evaluate_all(
    k: int = 10,
    category_filter: str = None
) -> Dict[str, Any]:
    """
    Run evaluation on all test cases and aggregate results.

    Args:
        k: Cutoff position for metrics
        category_filter: Only evaluate this category (semantic, filter, hybrid, category_browse)

    Returns:
        Dictionary with aggregated results and per-query details
    """
    print("=" * 70)
    print(f"RETRIEVAL EVALUATION (K={k})")
    print("=" * 70)

    ground_truth = get_ground_truth()

    # Filter by category if specified
    if category_filter:
        ground_truth = [tc for tc in ground_truth if tc['category'] == category_filter]
        print(f"\nFiltering to category: {category_filter}")

    print(f"\nEvaluating {len(ground_truth)} test cases...")
    print()

    # Store results
    all_results = []
    category_results = defaultdict(list)

    # Evaluate each test case
    for i, test_case in enumerate(ground_truth, 1):
        print(f"[{i}/{len(ground_truth)}] {test_case['description']}")

        metrics = evaluate_query(test_case, k=k)

        result = {
            "test_case": test_case,
            "metrics": metrics
        }
        all_results.append(result)
        category_results[test_case['category']].append(metrics)

        # Print quick summary
        print(f"  Precision@{k}: {metrics['precision@k']:.3f} | "
              f"Recall@{k}: {metrics['recall@k']:.3f} | "
              f"MRR: {metrics['mrr']:.3f} | "
              f"NDCG@{k}: {metrics['ndcg@k']:.3f}")

    # Aggregate results
    print("\n" + "=" * 70)
    print("OVERALL RESULTS")
    print("=" * 70)

    all_metrics = [r['metrics'] for r in all_results]

    overall = {
        f"precision@{k}": sum(m['precision@k'] for m in all_metrics) / len(all_metrics),
        f"recall@{k}": sum(m['recall@k'] for m in all_metrics) / len(all_metrics),
        "mrr": sum(m['mrr'] for m in all_metrics) / len(all_metrics),
        f"ndcg@{k}": sum(m['ndcg@k'] for m in all_metrics) / len(all_metrics),
        f"hit_rate@{k}": sum(m['hit_rate@k'] for m in all_metrics) / len(all_metrics),
    }

    print(f"\nOverall Metrics (averaged across {len(all_metrics)} queries):")
    for metric_name, value in overall.items():
        print(f"  {metric_name}: {value:.3f}")

    # Per-category breakdown
    print("\n" + "=" * 70)
    print("RESULTS BY CATEGORY")
    print("=" * 70)

    for category, metrics_list in category_results.items():
        print(f"\n{category.upper()} ({len(metrics_list)} queries):")
        cat_metrics = {
            f"precision@{k}": sum(m['precision@k'] for m in metrics_list) / len(metrics_list),
            f"recall@{k}": sum(m['recall@k'] for m in metrics_list) / len(metrics_list),
            "mrr": sum(m['mrr'] for m in metrics_list) / len(metrics_list),
            f"ndcg@{k}": sum(m['ndcg@k'] for m in metrics_list) / len(metrics_list),
            f"hit_rate@{k}": sum(m['hit_rate@k'] for m in metrics_list) / len(metrics_list),
        }
        for metric_name, value in cat_metrics.items():
            print(f"  {metric_name}: {value:.3f}")

    return {
        "overall": overall,
        "by_category": {
            cat: {
                f"precision@{k}": sum(m['precision@k'] for m in metrics_list) / len(metrics_list),
                f"recall@{k}": sum(m['recall@k'] for m in metrics_list) / len(metrics_list),
                "mrr": sum(m['mrr'] for m in metrics_list) / len(metrics_list),
                f"ndcg@{k}": sum(m['ndcg@k'] for m in metrics_list) / len(metrics_list),
                f"hit_rate@{k}": sum(m['hit_rate@k'] for m in metrics_list) / len(metrics_list),
            }
            for cat, metrics_list in category_results.items()
        },
        "detailed_results": all_results
    }


def main():
    parser = argparse.ArgumentParser(description="Run retrieval evaluation")
    parser.add_argument('--k', type=int, default=10, help='Cutoff position for metrics (default: 10)')
    parser.add_argument('--category', type=str, default=None,
                       choices=['semantic', 'filter', 'hybrid', 'category_browse'],
                       help='Filter to specific category')

    args = parser.parse_args()

    results = evaluate_all(k=args.k, category_filter=args.category)

    print("\n" + "=" * 70)
    print("EVALUATION COMPLETE")
    print("=" * 70)
    print(f"\nResults saved to evaluation object")
    print(f"Evaluated at K={args.k}")

    # Return results for programmatic access
    return results


if __name__ == "__main__":
    results = main()
