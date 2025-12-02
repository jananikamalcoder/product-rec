"""
DeepEval IR Metrics Evaluation

Evaluates retrieval quality using DeepEval's LLM-as-judge IR metrics:
- Contextual Precision - LLM judges if retrieved items are relevant
- Contextual Recall - LLM judges if all relevant items were retrieved
- Faithfulness - LLM judges if agent response has no hallucinations

This COMPLEMENTS (not replaces) traditional IR metrics:
- Traditional Precision/Recall: Fast, deterministic, keyword-based
- DeepEval Precision/Recall: Slow, semantic, LLM-judged

Usage:
    python deepeval_ir_metrics.py              # All metrics
    python deepeval_ir_metrics.py --metric precision  # Only precision
    python deepeval_ir_metrics.py --metric recall     # Only recall
    python deepeval_ir_metrics.py --metric faithfulness  # Only faithfulness
"""

import asyncio
import argparse
import time
import json
from typing import List, Dict, Any
from deepeval.test_case import LLMTestCase
from deepeval.metrics import (
    ContextualPrecisionMetric,
    ContextualRecallMetric,
    FaithfulnessMetric
)
from deepeval_llm import create_github_llm
from retrieval_ground_truth import get_ground_truth
from product_search_agent import create_product_search_agent
import agent_tools


async def generate_agent_response(agent, query: str) -> str:
    """Generate response from product search agent."""
    thread = agent.get_new_thread()
    result = await agent.run(query, thread=thread)
    return result.text


def create_retrieval_context(products: List[Dict]) -> List[str]:
    """Convert product data to context strings."""
    contexts = []
    for p in products:
        ctx = (
            f"{p['product_name']} by {p['brand']} - "
            f"${p['price_usd']} - "
            f"{p['category']} > {p['subcategory']} - "
            f"{p.get('material', 'N/A')} material - "
            f"{p.get('insulation', 'None')} insulation - "
            f"{p.get('waterproofing', 'None')} waterproofing - "
            f"{p.get('season', 'N/A')} season - "
            f"For {p.get('primary_purpose', 'general use')} - "
            f"{p.get('gender', 'Unisex')}"
        )
        contexts.append(ctx)
    return contexts


def create_expected_output(ground_truth_ids: List[str]) -> str:
    """Create expected output from ground truth product IDs."""
    if not ground_truth_ids:
        return "No specific products expected."

    # Get product details for ground truth
    products = []
    for pid in ground_truth_ids[:5]:  # Top 5 expected
        result = agent_tools.get_product_details(pid)
        if result['success']:
            products.append(result['product'])

    if not products:
        return "Expected relevant products from the catalog."

    # Format as expected output
    expected = "Expected products should include:\n"
    for i, p in enumerate(products, 1):
        expected += f"{i}. {p['product_name']} by {p['brand']} - ${p['price_usd']}\n"

    return expected


async def evaluate_test_case_with_deepeval(
    test_case: Dict[str, Any],
    agent,
    llm,
    metrics_to_run: List[str] = None,
    verbose: bool = True
) -> Dict[str, Any]:
    """
    Evaluate a single test case with DeepEval IR metrics.

    Args:
        test_case: Ground truth test case
        agent: Product search agent
        llm: GitHub Models LLM
        metrics_to_run: List of metrics to run (precision, recall, faithfulness)
        verbose: Print progress

    Returns:
        Evaluation results
    """
    if metrics_to_run is None:
        metrics_to_run = ['precision', 'recall', 'faithfulness']

    if verbose:
        print(f"\n{'='*70}")
        print(f"Test: {test_case['description']}")
        print(f"Query: {test_case['query']}")
        print(f"Category: {test_case['category']}")

    # Step 1: Search products
    if verbose:
        print("\n1. Searching products...")

    query = test_case['query']
    search_result = agent_tools.search_products(query, max_results=10)

    if not search_result['success']:
        return {
            'query': query,
            'error': 'Search failed',
            'success': False
        }

    retrieved_products = search_result['products']
    retrieval_context = create_retrieval_context(retrieved_products)

    if verbose:
        print(f"   Retrieved: {len(retrieved_products)} products")
        print(f"   Relevant: {len(test_case['relevant_products'])} expected")

    # Step 2: Generate agent response
    if verbose:
        print("\n2. Generating agent response...")

    actual_output = await generate_agent_response(agent, query)

    if verbose:
        print(f"   Response length: {len(actual_output)} characters")

    # Step 3: Create expected output
    expected_output = create_expected_output(test_case['relevant_products'])

    # Step 4: Create LLMTestCase
    llm_test_case = LLMTestCase(
        input=query,
        actual_output=actual_output,
        expected_output=expected_output,
        retrieval_context=retrieval_context
    )

    # Step 5: Run DeepEval metrics
    results = {
        'query': query,
        'description': test_case['description'],
        'category': test_case['category'],
        'retrieved_count': len(retrieved_products),
        'relevant_count': len(test_case['relevant_products']),
        'metrics': {}
    }

    if verbose:
        print(f"\n3. Running DeepEval IR metrics: {metrics_to_run}")

    # Contextual Precision
    if 'precision' in metrics_to_run:
        if verbose:
            print("\n   Contextual Precision (LLM-as-judge):")

        try:
            metric = ContextualPrecisionMetric(
                model=llm,
                threshold=0.5,
                include_reason=True
            )

            start_time = time.time()
            metric.measure(llm_test_case)
            duration = time.time() - start_time

            results['metrics']['contextual_precision'] = {
                'score': metric.score,
                'threshold': metric.threshold,
                'success': metric.is_successful(),
                'reason': metric.reason,
                'duration_seconds': duration
            }

            if verbose:
                print(f"     Score: {metric.score:.3f}")
                print(f"     Threshold: {metric.threshold}")
                print(f"     Pass: {metric.is_successful()}")
                print(f"     Time: {duration:.2f}s")

        except Exception as e:
            if verbose:
                print(f"     ERROR: {e}")
            results['metrics']['contextual_precision'] = {'error': str(e)}

    # Contextual Recall
    if 'recall' in metrics_to_run:
        if verbose:
            print("\n   Contextual Recall (LLM-as-judge):")

        try:
            metric = ContextualRecallMetric(
                model=llm,
                threshold=0.5,
                include_reason=True
            )

            start_time = time.time()
            metric.measure(llm_test_case)
            duration = time.time() - start_time

            results['metrics']['contextual_recall'] = {
                'score': metric.score,
                'threshold': metric.threshold,
                'success': metric.is_successful(),
                'reason': metric.reason,
                'duration_seconds': duration
            }

            if verbose:
                print(f"     Score: {metric.score:.3f}")
                print(f"     Threshold: {metric.threshold}")
                print(f"     Pass: {metric.is_successful()}")
                print(f"     Time: {duration:.2f}s")

        except Exception as e:
            if verbose:
                print(f"     ERROR: {e}")
            results['metrics']['contextual_recall'] = {'error': str(e)}

    # Faithfulness
    if 'faithfulness' in metrics_to_run:
        if verbose:
            print("\n   Faithfulness (Hallucination Detection):")

        try:
            metric = FaithfulnessMetric(
                model=llm,
                threshold=0.7,
                include_reason=True
            )

            start_time = time.time()
            metric.measure(llm_test_case)
            duration = time.time() - start_time

            results['metrics']['faithfulness'] = {
                'score': metric.score,
                'threshold': metric.threshold,
                'success': metric.is_successful(),
                'reason': metric.reason,
                'duration_seconds': duration
            }

            if verbose:
                print(f"     Score: {metric.score:.3f}")
                print(f"     Threshold: {metric.threshold}")
                print(f"     Pass: {metric.is_successful()}")
                print(f"     Time: {duration:.2f}s")

        except Exception as e:
            if verbose:
                print(f"     ERROR: {e}")
            results['metrics']['faithfulness'] = {'error': str(e)}

    return results


async def run_all_deepeval_ir_metrics(
    metrics_to_run: List[str] = None,
    max_tests: int = None,
    verbose: bool = True
) -> Dict[str, Any]:
    """
    Run DeepEval IR metrics on all ground truth test cases.

    Args:
        metrics_to_run: List of metrics (precision, recall, faithfulness)
        max_tests: Maximum number of tests to run (None = all)
        verbose: Print progress

    Returns:
        Complete evaluation results
    """
    if metrics_to_run is None:
        metrics_to_run = ['precision', 'recall', 'faithfulness']

    # Load ground truth
    ground_truth = get_ground_truth()
    if max_tests:
        ground_truth = ground_truth[:max_tests]

    if verbose:
        print("=" * 70)
        print("DeepEval IR Metrics Evaluation")
        print("=" * 70)
        print(f"\nMetrics: {', '.join(metrics_to_run)}")
        print(f"Test cases: {len(ground_truth)}")
        print(f"LLM Judge: GitHub Models (gpt-4o-mini)")
        print("\nThis will take several minutes...\n")

    # Initialize agent and LLM
    if verbose:
        print("Initializing agent and LLM judge...")

    agent = await create_product_search_agent()
    llm = create_github_llm(model="gpt-4o-mini", temperature=0.0)

    if verbose:
        print("✓ Ready!\n")

    # Run evaluations
    start_time = time.time()
    results = []

    for i, test_case in enumerate(ground_truth, 1):
        if verbose:
            print(f"\nProgress: {i}/{len(ground_truth)}")

        try:
            result = await evaluate_test_case_with_deepeval(
                test_case,
                agent,
                llm,
                metrics_to_run,
                verbose=verbose
            )
            results.append(result)

        except Exception as e:
            if verbose:
                print(f"\nERROR: {e}")
            results.append({
                'query': test_case['query'],
                'error': str(e),
                'success': False
            })

    total_duration = time.time() - start_time

    # Calculate summary
    summary = calculate_summary(results, metrics_to_run)
    summary['total_duration_seconds'] = total_duration
    summary['total_test_cases'] = len(ground_truth)

    if verbose:
        print_summary(summary, metrics_to_run)

    return {
        'summary': summary,
        'results': results,
        'metrics_run': metrics_to_run
    }


def calculate_summary(results: List[Dict], metrics: List[str]) -> Dict[str, Any]:
    """Calculate summary statistics."""
    summary = {'by_metric': {}}

    for metric_name in metrics:
        metric_key = f"contextual_{metric_name}" if metric_name in ['precision', 'recall'] else metric_name
        scores = []

        for result in results:
            if 'error' not in result and metric_key in result.get('metrics', {}):
                metric_data = result['metrics'][metric_key]
                if 'error' not in metric_data:
                    scores.append({
                        'score': metric_data['score'],
                        'success': metric_data['success']
                    })

        if scores:
            summary['by_metric'][metric_key] = {
                'total_tests': len(scores),
                'passed': sum(1 for s in scores if s['success']),
                'failed': sum(1 for s in scores if not s['success']),
                'avg_score': sum(s['score'] for s in scores) / len(scores),
                'min_score': min(s['score'] for s in scores),
                'max_score': max(s['score'] for s in scores),
                'pass_rate': sum(1 for s in scores if s['success']) / len(scores)
            }

    return summary


def print_summary(summary: Dict, metrics: List[str]):
    """Print evaluation summary."""
    print("\n" + "=" * 70)
    print("DEEPEVAL IR METRICS SUMMARY")
    print("=" * 70)

    print(f"\nTotal Duration: {summary['total_duration_seconds']:.1f}s")
    print(f"Total Test Cases: {summary['total_test_cases']}")

    print(f"\nMetrics Evaluated:")
    for metric_name in metrics:
        metric_key = f"contextual_{metric_name}" if metric_name in ['precision', 'recall'] else metric_name

        if metric_key in summary['by_metric']:
            stats = summary['by_metric'][metric_key]
            print(f"\n  {metric_key.upper().replace('_', ' ')}:")
            print(f"    Tests: {stats['total_tests']}")
            print(f"    Passed: {stats['passed']} ({stats['pass_rate']:.1%})")
            print(f"    Failed: {stats['failed']}")
            print(f"    Avg Score: {stats['avg_score']:.3f}")
            print(f"    Score Range: {stats['min_score']:.3f} - {stats['max_score']:.3f}")

    print("\n" + "=" * 70)


# Main execution
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DeepEval IR Metrics Evaluation")
    parser.add_argument(
        '--metric',
        choices=['precision', 'recall', 'faithfulness', 'all'],
        default='all',
        help="Metric to evaluate"
    )
    parser.add_argument(
        '--max-tests',
        type=int,
        default=None,
        help="Maximum number of tests to run (default: all)"
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help="Reduce output verbosity"
    )

    args = parser.parse_args()

    # Determine metrics to run
    if args.metric == 'all':
        metrics_to_run = ['precision', 'recall', 'faithfulness']
    else:
        metrics_to_run = [args.metric]

    # Run evaluation
    results = asyncio.run(run_all_deepeval_ir_metrics(
        metrics_to_run=metrics_to_run,
        max_tests=args.max_tests,
        verbose=not args.quiet
    ))

    # Save results
    output_file = f"deepeval_ir_metrics_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n✓ Results saved to {output_file}")
