"""
DeepEval vs Custom Metrics Comparison

Compares LLM-as-judge evaluation (DeepEval) with traditional IR metrics
(Precision, Recall, NDCG, MRR, Hit Rate) to identify discrepancies and insights.
"""

import json
import asyncio
from typing import Dict, Any, List
from retrieval_eval import (
    precision_at_k,
    recall_at_k,
    mean_reciprocal_rank,
    ndcg_at_k,
    hit_rate_at_k
)
from retrieval_ground_truth import get_ground_truth
import agent_tools


def run_custom_metrics_evaluation(k: int = 10) -> Dict[str, Any]:
    """
    Run custom IR metrics evaluation.

    Args:
        k: Number of top results to evaluate

    Returns:
        Dictionary with custom metrics results
    """
    ground_truth = get_ground_truth()
    results = []

    print(f"Running custom IR metrics evaluation (K={k})...")
    print(f"Test cases: {len(ground_truth)}\n")

    for i, test_case in enumerate(ground_truth, 1):
        print(f"[{i}/{len(ground_truth)}] {test_case['description']}")

        query = test_case['query']
        relevant_ids = test_case['relevant_products']

        # Execute search
        search_result = agent_tools.search_products(query, max_results=k)

        if search_result['success']:
            retrieved_ids = [p['product_id'] for p in search_result['products']]
        else:
            retrieved_ids = []

        # Calculate metrics
        precision = precision_at_k(retrieved_ids, relevant_ids, k)
        recall = recall_at_k(retrieved_ids, relevant_ids, k)
        mrr = mean_reciprocal_rank(retrieved_ids, relevant_ids)
        ndcg = ndcg_at_k(retrieved_ids, relevant_ids, k)
        hit_rate = hit_rate_at_k(retrieved_ids, relevant_ids, k)

        results.append({
            'query': query,
            'category': test_case['category'],
            'description': test_case['description'],
            'precision': precision,
            'recall': recall,
            'mrr': mrr,
            'ndcg': ndcg,
            'hit_rate': hit_rate,
            'retrieved_count': len(retrieved_ids),
            'relevant_count': len(relevant_ids)
        })

    # Calculate summary
    summary = {
        'avg_precision': sum(r['precision'] for r in results) / len(results),
        'avg_recall': sum(r['recall'] for r in results) / len(results),
        'avg_mrr': sum(r['mrr'] for r in results) / len(results),
        'avg_ndcg': sum(r['ndcg'] for r in results) / len(results),
        'avg_hit_rate': sum(r['hit_rate'] for r in results) / len(results)
    }

    return {
        'summary': summary,
        'results': results,
        'k': k
    }


def load_deepeval_results(filepath: str = "deepeval_results.json") -> Dict[str, Any]:
    """Load DeepEval results from JSON file."""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"ERROR: {filepath} not found. Run deepeval_eval.py first.")
        return None


def compare_results(custom_results: Dict, deepeval_results: Dict) -> List[Dict[str, Any]]:
    """
    Compare custom metrics with DeepEval metrics.

    Args:
        custom_results: Custom IR metrics results
        deepeval_results: DeepEval LLM-as-judge results

    Returns:
        List of comparison insights
    """
    comparisons = []

    # Match test cases by query or description
    for custom_tc in custom_results['results']:
        # Find matching DeepEval test case
        deepeval_tc = None
        for de_tc in deepeval_results['results']:
            # Match by similar query (case-insensitive substring match)
            if (custom_tc['query'].lower() in de_tc.get('input', '').lower() or
                de_tc.get('input', '').lower() in custom_tc['query'].lower()):
                deepeval_tc = de_tc
                break

        if deepeval_tc:
            comparison = {
                'query': custom_tc['query'],
                'description': custom_tc['description'],
                'custom_metrics': {
                    'precision': custom_tc['precision'],
                    'recall': custom_tc['recall'],
                    'mrr': custom_tc['mrr'],
                    'ndcg': custom_tc['ndcg'],
                    'hit_rate': custom_tc['hit_rate']
                },
                'deepeval_metrics': {}
            }

            # Extract DeepEval scores
            for metric_name, metric_data in deepeval_tc.get('metrics', {}).items():
                if 'error' not in metric_data:
                    comparison['deepeval_metrics'][metric_name] = {
                        'score': metric_data.get('score', 0),
                        'success': metric_data.get('success', False)
                    }

            # Identify discrepancies
            comparison['insights'] = analyze_discrepancy(comparison)

            comparisons.append(comparison)

    return comparisons


def analyze_discrepancy(comparison: Dict[str, Any]) -> List[str]:
    """
    Analyze discrepancies between custom and DeepEval metrics.

    Args:
        comparison: Comparison dictionary

    Returns:
        List of insight strings
    """
    insights = []

    custom = comparison['custom_metrics']
    deepeval = comparison['deepeval_metrics']

    # High precision but low answer relevancy
    if (custom['precision'] > 0.7 and
        'answer_relevancy' in deepeval and
        deepeval['answer_relevancy']['score'] < 0.5):
        insights.append(
            "⚠️ High Precision but Low Answer Relevancy - "
            "Products match keywords but not semantic intent"
        )

    # Low precision but high answer relevancy
    if (custom['precision'] < 0.5 and
        'answer_relevancy' in deepeval and
        deepeval['answer_relevancy']['score'] > 0.7):
        insights.append(
            "✓ Low Precision but High Answer Relevancy - "
            "Agent provides good response despite poor retrieval"
        )

    # High precision and high answer relevancy
    if (custom['precision'] > 0.7 and
        'answer_relevancy' in deepeval and
        deepeval['answer_relevancy']['score'] > 0.7):
        insights.append(
            "✓✓ High Precision AND High Answer Relevancy - "
            "Excellent retrieval and response quality"
        )

    # Low contextual relevancy despite high MRR
    if (custom['mrr'] > 0.8 and
        'contextual_relevancy' in deepeval and
        deepeval['contextual_relevancy']['score'] < 0.5):
        insights.append(
            "⚠️ High MRR but Low Contextual Relevancy - "
            "First result is technically relevant but semantically mismatched"
        )

    # Faithfulness issues
    if ('faithfulness' in deepeval and
        not deepeval['faithfulness']['success']):
        insights.append(
            "🚨 Low Faithfulness - Agent may be hallucinating product features"
        )

    return insights


def print_comparison_report(comparisons: List[Dict], custom_results: Dict, deepeval_results: Dict):
    """Print detailed comparison report."""

    print("\n" + "=" * 80)
    print("CUSTOM METRICS vs DEEPEVAL COMPARISON REPORT")
    print("=" * 80)

    # Overall summary
    print("\nOVERALL SUMMARY:")
    print(f"\nCustom IR Metrics (K={custom_results['k']}):")
    for metric, value in custom_results['summary'].items():
        print(f"  {metric}: {value:.3f}")

    print(f"\nDeepEval LLM-as-Judge Metrics:")
    if 'by_metric' in deepeval_results['summary']:
        for metric, stats in deepeval_results['summary']['by_metric'].items():
            print(f"  {metric}:")
            print(f"    Avg Score: {stats['avg_score']:.3f}")
            print(f"    Pass Rate: {stats['pass_rate']:.1%}")

    # Detailed comparisons
    print("\n" + "=" * 80)
    print("DETAILED COMPARISONS")
    print("=" * 80)

    for i, comp in enumerate(comparisons, 1):
        print(f"\n[{i}] {comp['description']}")
        print(f"Query: \"{comp['query']}\"")

        print("\n  Custom Metrics:")
        for metric, value in comp['custom_metrics'].items():
            print(f"    {metric}: {value:.3f}")

        print("\n  DeepEval Metrics:")
        if comp['deepeval_metrics']:
            for metric, data in comp['deepeval_metrics'].items():
                status = "✓" if data['success'] else "✗"
                print(f"    {metric}: {data['score']:.3f} {status}")
        else:
            print("    (No DeepEval results)")

        if comp['insights']:
            print("\n  Insights:")
            for insight in comp['insights']:
                print(f"    {insight}")

    # Summary insights
    print("\n" + "=" * 80)
    print("KEY INSIGHTS")
    print("=" * 80)

    all_insights = [insight for comp in comparisons for insight in comp['insights']]

    # Count insight types
    high_prec_low_relevancy = sum(1 for i in all_insights if "High Precision but Low Answer Relevancy" in i)
    low_prec_high_relevancy = sum(1 for i in all_insights if "Low Precision but High Answer Relevancy" in i)
    both_high = sum(1 for i in all_insights if "High Precision AND High Answer Relevancy" in i)
    faithfulness_issues = sum(1 for i in all_insights if "Low Faithfulness" in i)

    print(f"\n✓✓ Excellent (High Precision + High Answer Relevancy): {both_high}")
    print(f"⚠️  Keyword Match Only (High Precision, Low Relevancy): {high_prec_low_relevancy}")
    print(f"⚠️  Good Response, Poor Retrieval (Low Precision, High Relevancy): {low_prec_high_relevancy}")
    print(f"🚨 Hallucination Detected (Low Faithfulness): {faithfulness_issues}")

    print("\n" + "=" * 80)


# Main execution
if __name__ == "__main__":
    print("=" * 80)
    print("DeepEval vs Custom Metrics Comparison")
    print("=" * 80)

    # Step 1: Run custom metrics evaluation
    print("\nStep 1: Running custom IR metrics evaluation...")
    custom_results = run_custom_metrics_evaluation(k=10)

    # Step 2: Load DeepEval results
    print("\nStep 2: Loading DeepEval results...")
    deepeval_results = load_deepeval_results("deepeval_results.json")

    if deepeval_results is None:
        print("\nERROR: Cannot compare without DeepEval results.")
        print("Run: uv run python deepeval_eval.py")
        exit(1)

    # Step 3: Compare results
    print("\nStep 3: Comparing results...")
    comparisons = compare_results(custom_results, deepeval_results)

    # Step 4: Print comparison report
    print_comparison_report(comparisons, custom_results, deepeval_results)

    # Step 5: Save comparison to file
    output = {
        'custom_results': custom_results,
        'deepeval_results_summary': deepeval_results['summary'],
        'comparisons': comparisons
    }

    output_file = "deepeval_comparison.json"
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n✓ Comparison saved to {output_file}")
