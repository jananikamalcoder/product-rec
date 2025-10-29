"""
DeepEval Evaluation Runner for Product Search Agent

Runs LLM-as-judge evaluation using DeepEval metrics:
1. Answer Relevancy - Does response match user intent?
2. Faithfulness - Does agent hallucinate?
3. Contextual Relevancy - Are retrieved products appropriate?

Uses GitHub Models (gpt-4o-mini) as the LLM judge.
"""

import asyncio
import time
from typing import List, Dict, Any
from deepeval.test_case import LLMTestCase
from deepeval.metrics import (
    AnswerRelevancyMetric,
    FaithfulnessMetric,
    ContextualRelevancyMetric
)
from deepeval_llm import create_github_llm
from deepeval_test_cases import create_deepeval_test_cases, search_and_create_context
from product_search_agent import create_product_search_agent


async def generate_agent_response(agent, query: str, filter_params: Dict = None) -> str:
    """
    Generate response from product search agent.

    Args:
        agent: Product search agent instance
        query: User query
        filter_params: Optional filter parameters

    Returns:
        Agent's response text
    """
    # Create thread for this query
    thread = agent.get_new_thread()

    # Run agent with query
    result = await agent.run(query, thread=thread)

    return result.text


def create_llm_test_case(
    test_case_def: Dict[str, Any],
    actual_output: str,
    retrieval_context: List[str]
) -> LLMTestCase:
    """
    Create DeepEval LLMTestCase from test case definition.

    Args:
        test_case_def: Test case dictionary from deepeval_test_cases.py
        actual_output: Agent's actual response
        retrieval_context: Retrieved product descriptions

    Returns:
        LLMTestCase instance for DeepEval
    """
    return LLMTestCase(
        input=test_case_def['input'],
        actual_output=actual_output,
        retrieval_context=retrieval_context,
        expected_output=test_case_def.get('expected_output')
    )


async def evaluate_test_case(
    test_case_def: Dict[str, Any],
    agent,
    llm,
    verbose: bool = True
) -> Dict[str, Any]:
    """
    Evaluate a single test case with DeepEval metrics.

    Args:
        test_case_def: Test case definition
        agent: Product search agent
        llm: GitHub Models LLM for judging
        verbose: Print progress

    Returns:
        Evaluation results dictionary
    """
    if verbose:
        print(f"\n{'='*70}")
        print(f"Test: {test_case_def['name']}")
        print(f"Input: {test_case_def['input']}")

    # Step 1: Get retrieval context (search products)
    if verbose:
        print("\n1. Retrieving products...")

    retrieval_context = search_and_create_context(test_case_def)

    if verbose:
        print(f"   Retrieved {len(retrieval_context)} products")

    # Step 2: Generate agent response
    if verbose:
        print("\n2. Generating agent response...")

    actual_output = await generate_agent_response(
        agent,
        test_case_def['input'],
        test_case_def.get('filter_params')
    )

    if verbose:
        print(f"   Response length: {len(actual_output)} characters")
        # Show first 200 chars
        preview = actual_output[:200] + "..." if len(actual_output) > 200 else actual_output
        print(f"   Preview: {preview}")

    # Step 3: Create LLMTestCase
    llm_test_case = create_llm_test_case(
        test_case_def,
        actual_output,
        retrieval_context
    )

    # Step 4: Run DeepEval metrics
    results = {
        'name': test_case_def['name'],
        'input': test_case_def['input'],
        'actual_output': actual_output,
        'retrieval_context_count': len(retrieval_context),
        'metrics': {}
    }

    metrics_to_run = test_case_def['metrics']
    threshold = test_case_def.get('threshold', 0.7)

    if verbose:
        print(f"\n3. Running DeepEval metrics: {metrics_to_run}")

    # Run each metric
    for metric_name in metrics_to_run:
        if verbose:
            print(f"\n   {metric_name}:")

        try:
            # Create metric instance
            if metric_name == 'answer_relevancy':
                metric = AnswerRelevancyMetric(
                    model=llm,
                    threshold=threshold,
                    include_reason=True
                )
            elif metric_name == 'faithfulness':
                metric = FaithfulnessMetric(
                    model=llm,
                    threshold=threshold,
                    include_reason=True
                )
            elif metric_name == 'contextual_relevancy':
                metric = ContextualRelevancyMetric(
                    model=llm,
                    threshold=threshold,
                    include_reason=True
                )
            else:
                if verbose:
                    print(f"     Unknown metric: {metric_name}")
                continue

            # Measure
            start_time = time.time()
            metric.measure(llm_test_case)
            duration = time.time() - start_time

            # Store results
            results['metrics'][metric_name] = {
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
                print(f"     Reason: {metric.reason[:150]}..." if len(metric.reason) > 150 else f"     Reason: {metric.reason}")
                print(f"     Time: {duration:.2f}s")

        except Exception as e:
            if verbose:
                print(f"     ERROR: {e}")
            results['metrics'][metric_name] = {
                'error': str(e),
                'success': False
            }

    return results


async def run_all_evaluations(
    test_cases: List[Dict[str, Any]] = None,
    verbose: bool = True
) -> Dict[str, Any]:
    """
    Run DeepEval evaluation on all test cases.

    Args:
        test_cases: List of test case definitions (or None to use all)
        verbose: Print progress

    Returns:
        Complete evaluation results
    """
    # Load test cases
    if test_cases is None:
        test_cases = create_deepeval_test_cases()

    if verbose:
        print("=" * 70)
        print("DeepEval Evaluation - Product Search Agent")
        print("=" * 70)
        print(f"\nRunning {len(test_cases)} test cases with GitHub Models (gpt-4o-mini)")
        print("This will take several minutes...\n")

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

    for i, test_case_def in enumerate(test_cases, 1):
        if verbose:
            print(f"\nProgress: {i}/{len(test_cases)}")

        try:
            result = await evaluate_test_case(
                test_case_def,
                agent,
                llm,
                verbose=verbose
            )
            results.append(result)

        except Exception as e:
            if verbose:
                print(f"\nERROR evaluating {test_case_def['name']}: {e}")
            results.append({
                'name': test_case_def['name'],
                'error': str(e),
                'success': False
            })

    total_duration = time.time() - start_time

    # Calculate summary statistics
    summary = calculate_summary(results)
    summary['total_duration_seconds'] = total_duration
    summary['total_test_cases'] = len(test_cases)

    if verbose:
        print_summary(summary)

    return {
        'summary': summary,
        'results': results,
        'test_cases': test_cases
    }


def calculate_summary(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate summary statistics from results."""
    summary = {
        'by_metric': {},
        'overall': {
            'total_tests': len(results),
            'successful_tests': 0,
            'failed_tests': 0
        }
    }

    # Aggregate by metric
    metric_scores = {}

    for result in results:
        if 'error' in result:
            summary['overall']['failed_tests'] += 1
            continue

        test_success = True
        for metric_name, metric_result in result['metrics'].items():
            if 'error' in metric_result:
                test_success = False
                continue

            if metric_name not in metric_scores:
                metric_scores[metric_name] = []

            metric_scores[metric_name].append({
                'score': metric_result['score'],
                'success': metric_result['success'],
                'threshold': metric_result['threshold']
            })

            if not metric_result['success']:
                test_success = False

        if test_success:
            summary['overall']['successful_tests'] += 1
        else:
            summary['overall']['failed_tests'] += 1

    # Calculate statistics per metric
    for metric_name, scores in metric_scores.items():
        summary['by_metric'][metric_name] = {
            'total_tests': len(scores),
            'passed': sum(1 for s in scores if s['success']),
            'failed': sum(1 for s in scores if not s['success']),
            'avg_score': sum(s['score'] for s in scores) / len(scores) if scores else 0,
            'min_score': min(s['score'] for s in scores) if scores else 0,
            'max_score': max(s['score'] for s in scores) if scores else 0,
            'pass_rate': sum(1 for s in scores if s['success']) / len(scores) if scores else 0
        }

    return summary


def print_summary(summary: Dict[str, Any]):
    """Print evaluation summary."""
    print("\n" + "=" * 70)
    print("EVALUATION SUMMARY")
    print("=" * 70)

    print(f"\nOverall:")
    print(f"  Total tests: {summary['overall']['total_tests']}")
    print(f"  Successful: {summary['overall']['successful_tests']}")
    print(f"  Failed: {summary['overall']['failed_tests']}")
    print(f"  Duration: {summary['total_duration_seconds']:.1f}s")

    print(f"\nBy Metric:")
    for metric_name, stats in summary['by_metric'].items():
        print(f"\n  {metric_name.upper().replace('_', ' ')}:")
        print(f"    Tests: {stats['total_tests']}")
        print(f"    Passed: {stats['passed']} ({stats['pass_rate']:.1%})")
        print(f"    Failed: {stats['failed']}")
        print(f"    Avg Score: {stats['avg_score']:.3f}")
        print(f"    Score Range: {stats['min_score']:.3f} - {stats['max_score']:.3f}")

    print("\n" + "=" * 70)


# Main execution
if __name__ == "__main__":
    import sys

    # Check for selective execution
    if len(sys.argv) > 1:
        # Run specific test cases by name prefix
        prefix = sys.argv[1]
        all_test_cases = create_deepeval_test_cases()
        test_cases = [tc for tc in all_test_cases if tc['name'].startswith(prefix)]

        if not test_cases:
            print(f"No test cases found with prefix: {prefix}")
            print("\nAvailable prefixes:")
            print("  AR - Answer Relevancy (5 tests)")
            print("  F  - Faithfulness (5 tests)")
            print("  CR - Contextual Relevancy (5 tests)")
            sys.exit(1)

        print(f"Running {len(test_cases)} test cases with prefix '{prefix}'")
        results = asyncio.run(run_all_evaluations(test_cases, verbose=True))
    else:
        # Run all test cases
        results = asyncio.run(run_all_evaluations(verbose=True))

    # Save results to file
    import json
    output_file = "deepeval_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n✓ Results saved to {output_file}")
