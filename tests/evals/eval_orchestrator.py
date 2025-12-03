"""
DeepEval evaluations for ProductAdvisorAgent (Orchestrator).

Tests LLM behavior:
- Delegates to correct sub-agents
- Formats results (doesn't echo raw JSON)
- Friendly, non-interrogative conversation style
- Factual product information (no hallucination)
"""

import pytest
from deepeval import assert_test
from deepeval.metrics import GEval, HallucinationMetric
from deepeval.test_case import LLMTestCase, LLMTestCaseParams


@pytest.mark.eval
@pytest.mark.asyncio
async def test_eval_delegates_to_personalization(advisor_agent):
    """Eval: User introduction should delegate to PersonalizationAgent."""
    thread = advisor_agent.get_new_thread()
    result = await advisor_agent.run("Hi, I'm Sarah", thread=thread)

    test_case = LLMTestCase(
        input="Hi, I'm Sarah",
        actual_output=result.text
    )

    metric = GEval(
        name="Delegates to Personalization",
        criteria="""The response should indicate the user was identified/welcomed.
        For a user introduction like "Hi, I'm Sarah":
        ACCEPT responses that:
        - Welcome the user by name (Sarah)
        - Acknowledge them as new or returning
        - Ask what they're looking for or how to help
        - Are friendly and conversational
        REJECT responses that:
        - Ignore the introduction entirely
        - Jump straight to product search without acknowledgment
        - Don't recognize the user introduction""",
        evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT],
        threshold=0.7
    )

    assert_test(test_case, [metric])


@pytest.mark.eval
@pytest.mark.asyncio
async def test_eval_delegates_to_search(advisor_agent):
    """Eval: Product search request should delegate to SearchAgent."""
    thread = advisor_agent.get_new_thread()
    result = await advisor_agent.run("Find me warm jackets for winter", thread=thread)

    test_case = LLMTestCase(
        input="Find me warm jackets for winter",
        actual_output=result.text
    )

    metric = GEval(
        name="Returns Search Results",
        criteria="""The response should show product search results.
        For a search request like "Find me warm jackets":
        ACCEPT responses that:
        - Show product names and prices
        - Present multiple options
        - Include product information (brand, rating, features)
        - Format results readably
        REJECT responses that:
        - Only ask clarifying questions without showing products
        - Don't search for products at all
        - Return empty or error responses""",
        evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT],
        threshold=0.6
    )

    assert_test(test_case, [metric])


@pytest.mark.eval
@pytest.mark.asyncio
async def test_eval_formats_results(advisor_agent):
    """Eval: Advisor formats results, doesn't echo raw JSON."""
    thread = advisor_agent.get_new_thread()
    result = await advisor_agent.run("Show me hiking boots", thread=thread)

    test_case = LLMTestCase(
        input="Show me hiking boots",
        actual_output=result.text
    )

    metric = GEval(
        name="Formatted Output",
        criteria="""The response should be user-friendly formatted output.
        It should NOT:
        - Echo raw JSON like {"success": true, "products": [...]}
        - Show unformatted data structures with curly braces and array brackets
        - Dump machine-readable output directly
        It SHOULD:
        - Present products in a readable format (table, list, cards)
        - Use formatting appropriate for humans (markdown is fine)
        - Be visually organized and scannable""",
        evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT],
        threshold=0.7
    )

    assert_test(test_case, [metric])


@pytest.mark.eval
@pytest.mark.asyncio
async def test_eval_one_question_max(advisor_agent):
    """Eval: Response should have max 1 question."""
    thread = advisor_agent.get_new_thread()
    result = await advisor_agent.run("Hi, I'm looking for outdoor gear", thread=thread)

    test_case = LLMTestCase(
        input="Hi, I'm looking for outdoor gear",
        actual_output=result.text
    )

    metric = GEval(
        name="Concise Questions",
        criteria="""The response should ask at most ONE question.
        REJECT responses that:
        - Ask multiple questions (more than 1 question mark)
        - Present a list of preference questions
        - Feel like an interrogation (What's your fit? Size? Budget? Colors?)
        - Bombard the user with questions
        ACCEPT responses that:
        - Ask 0 or 1 clarifying question
        - Focus on helping with the request
        - Are conversational and natural
        - Move forward with available information""",
        evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT],
        threshold=0.7
    )

    assert_test(test_case, [metric])


@pytest.mark.eval
@pytest.mark.asyncio
async def test_eval_friendly_welcome(advisor_agent):
    """Eval: New users get friendly welcome, not interrogation."""
    thread = advisor_agent.get_new_thread()
    result = await advisor_agent.run("Hi, I'm Alex", thread=thread)

    test_case = LLMTestCase(
        input="Hi, I'm Alex",
        actual_output=result.text
    )

    metric = GEval(
        name="Friendly Welcome",
        criteria="""The response should be a warm, friendly welcome.
        REJECT responses that:
        - Ask more than 1 question
        - Present a numbered list of preference questions
        - Feel like form-filling or data collection
        - Immediately demand sizing, budget, color preferences
        - Start with "Let me gather your preferences" or similar
        ACCEPT responses that:
        - Welcome the user warmly by name
        - Ask what brings them in OR what they're looking for
        - Are conversational and natural
        - Make the user feel welcome, not interrogated""",
        evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT],
        threshold=0.7
    )

    assert_test(test_case, [metric])


@pytest.mark.eval
@pytest.mark.asyncio
async def test_eval_no_hallucination(advisor_agent, search_engine):
    """Eval: Product details are factual, not hallucinated."""
    # Get a real product from the database
    products = search_engine.search_semantic("jacket", n_results=1)
    if not products:
        pytest.skip("No products found in search engine")

    product = products[0]
    product_name = product.get("product_name", "")

    thread = advisor_agent.get_new_thread()
    result = await advisor_agent.run(f"Tell me about {product_name}", thread=thread)

    # Create context from ground truth
    context = [
        f"Product: {product.get('product_name', 'Unknown')}",
        f"Brand: {product.get('brand', 'Unknown')}",
        f"Price: ${product.get('price_usd', 0)}",
        f"Rating: {product.get('rating', 0)}",
        f"Category: {product.get('category', 'Unknown')}",
    ]

    test_case = LLMTestCase(
        input=f"Tell me about {product_name}",
        actual_output=result.text,
        context=context
    )

    metric = HallucinationMetric(threshold=0.5)

    assert_test(test_case, [metric])


@pytest.mark.eval
@pytest.mark.asyncio
async def test_eval_handles_feedback(advisor_agent):
    """Eval: Feedback is acknowledged and acted upon."""
    thread = advisor_agent.get_new_thread()

    # First get some products
    await advisor_agent.run("Show me jackets", thread=thread)

    # Then give feedback
    result = await advisor_agent.run("These are too flashy, show me something more neutral", thread=thread)

    test_case = LLMTestCase(
        input="These are too flashy, show me something more neutral",
        actual_output=result.text
    )

    metric = GEval(
        name="Handles Feedback",
        criteria="""The response should acknowledge feedback and adjust recommendations.
        ACCEPT responses that:
        - Acknowledge the feedback (too flashy)
        - Show different/adjusted products
        - Indicate understanding of the preference (neutral colors)
        - Try to help based on the feedback
        REJECT responses that:
        - Ignore the feedback entirely
        - Show the same products again
        - Don't acknowledge the user's concern""",
        evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT],
        threshold=0.6
    )

    assert_test(test_case, [metric])
