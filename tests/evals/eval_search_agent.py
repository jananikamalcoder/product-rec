"""
DeepEval evaluations for ProductSearchAgent.

Tests LLM behavior:
- Returns raw JSON output (not formatted markdown)
- No conversational commentary
- Semantic relevance of search results
- Correct application of price filters
"""

import pytest
import json
from deepeval import assert_test
from deepeval.metrics import GEval, AnswerRelevancyMetric
from deepeval.test_case import LLMTestCase, LLMTestCaseParams


@pytest.mark.eval
@pytest.mark.asyncio
async def test_eval_returns_raw_json(search_agent):
    """Eval: ProductSearchAgent returns raw JSON only."""
    thread = search_agent.get_new_thread()
    result = await search_agent.run("Search: warm winter jackets", thread=thread)

    test_case = LLMTestCase(
        input="Search: warm winter jackets",
        actual_output=result.text
    )

    metric = GEval(
        name="Raw JSON Output",
        criteria="""The response must be raw JSON output only.
        It should NOT contain:
        - Markdown formatting (**, ##, *italics*, etc.)
        - Bullet points or numbered lists with descriptions
        - Commentary like "I found..." or "Here are..." or "Based on your search..."
        - Product descriptions written in prose
        - Conversational language
        It SHOULD be:
        - A JSON object or JSON-like structure
        - Contains fields like success, total_results, products
        - Machine-parseable data format
        - Minimal or no surrounding text""",
        evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT],
        threshold=0.7
    )

    assert_test(test_case, [metric])


@pytest.mark.eval
@pytest.mark.asyncio
async def test_eval_no_formatting(search_agent):
    """Eval: Agent should not format results as markdown."""
    thread = search_agent.get_new_thread()
    result = await search_agent.run("Search: hiking boots", thread=thread)

    test_case = LLMTestCase(
        input="Search: hiking boots",
        actual_output=result.text
    )

    metric = GEval(
        name="No Markdown Formatting",
        criteria="""The response should NOT use markdown formatting.
        REJECT responses that contain:
        - Bold text (**text**)
        - Headers (### or ##)
        - Bullet points (- item or * item)
        - Numbered lists with formatted descriptions (1. **Product Name** - description)
        - Tables with | separators
        - Code blocks
        ACCEPT responses that:
        - Are plain JSON
        - Have minimal formatting
        - Are data-focused output""",
        evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT],
        threshold=0.7
    )

    assert_test(test_case, [metric])


@pytest.mark.eval
@pytest.mark.asyncio
async def test_eval_semantic_relevance(search_agent):
    """Eval: Search results are semantically relevant."""
    thread = search_agent.get_new_thread()
    result = await search_agent.run("Search: waterproof rain jacket for hiking", thread=thread)

    test_case = LLMTestCase(
        input="waterproof rain jacket for hiking",
        actual_output=result.text,
        expected_output="Products that are waterproof jackets suitable for outdoor hiking activities, including rain jackets, shell jackets, or similar waterproof outerwear"
    )

    metric = AnswerRelevancyMetric(threshold=0.5)

    assert_test(test_case, [metric])


@pytest.mark.eval
@pytest.mark.asyncio
async def test_eval_price_filter_accuracy(search_agent):
    """Eval: Price filters are applied correctly."""
    thread = search_agent.get_new_thread()
    result = await search_agent.run(
        "Search: jackets under $200",
        thread=thread
    )

    test_case = LLMTestCase(
        input="Search: jackets under $200",
        actual_output=result.text
    )

    metric = GEval(
        name="Price Filter Applied",
        criteria="""The response should show products that respect the price constraint.
        The query asks for products "under $200".
        ACCEPT if:
        - The products listed have prices below or around $200
        - The response indicates price filtering was applied
        - Products shown are budget-appropriate
        REJECT if:
        - Products significantly over $200 are prominently featured
        - The price constraint was clearly ignored
        - Expensive items ($300+) appear without explanation""",
        evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT],
        threshold=0.6
    )

    assert_test(test_case, [metric])


@pytest.mark.eval
@pytest.mark.asyncio
async def test_eval_applies_context_filters(search_agent):
    """Eval: User context filters are applied to search."""
    thread = search_agent.get_new_thread()
    result = await search_agent.run(
        """Search: warm jacket

Apply these user preferences when filtering:
{
  "budget_max": 250,
  "gender": "Women"
}""",
        thread=thread
    )

    test_case = LLMTestCase(
        input="Search for warm jacket with budget $250 and gender Women",
        actual_output=result.text
    )

    metric = GEval(
        name="Context Filters Applied",
        criteria="""The response should apply the user context filters.
        The context specifies:
        - budget_max: 250 (products should be $250 or less)
        - gender: Women (products should be for Women or Unisex)
        ACCEPT if:
        - Products shown respect these constraints
        - The search appears filtered appropriately
        - Response indicates filters were considered
        REJECT if:
        - Men's-only products are prominently shown
        - Prices significantly exceed $250
        - Context appears ignored""",
        evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT],
        threshold=0.6
    )

    assert_test(test_case, [metric])
