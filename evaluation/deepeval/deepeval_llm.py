"""
GitHub Models LLM Wrapper for DeepEval

Custom DeepEval LLM implementation that uses GitHub Models API
with the gpt-4o-mini model for LLM-as-judge evaluation.

Uses the same GitHub token and endpoint as product_search_agent.py.
"""

import os
from typing import Optional
from dotenv import load_dotenv
from deepeval.models.base_model import DeepEvalBaseLLM

# Load environment variables
load_dotenv()


class GitHubModelsLLM(DeepEvalBaseLLM):
    """
    Custom DeepEval LLM using GitHub Models API.

    GitHub Models provides OpenAI-compatible API with free tier for
    GitHub users. This wrapper allows DeepEval to use GitHub Models
    as the LLM judge instead of OpenAI directly.

    Usage:
        >>> llm = GitHubModelsLLM(model="gpt-4o-mini")
        >>> from deepeval.metrics import AnswerRelevancyMetric
        >>> metric = AnswerRelevancyMetric(model=llm, threshold=0.7)
    """

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        temperature: float = 0.0,
        max_tokens: Optional[int] = None
    ):
        """
        Initialize GitHub Models LLM.

        Args:
            model: Model ID (default: gpt-4o-mini)
            temperature: Sampling temperature (0.0 = deterministic)
            max_tokens: Maximum tokens in response
        """
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        # Get GitHub token from environment
        self.api_key = os.getenv("GITHUB_TOKEN")
        if not self.api_key:
            raise ValueError(
                "GITHUB_TOKEN not found in environment. "
                "Please set it in your .env file."
            )

        # GitHub Models endpoint (OpenAI-compatible)
        self.base_url = "https://models.inference.ai.azure.com"

        # OpenAI client (lazy loaded)
        self._client = None

    def load_model(self):
        """Load the OpenAI client (lazy initialization)."""
        if self._client is None:
            try:
                from openai import OpenAI
            except ImportError:
                raise ImportError(
                    "OpenAI package required for GitHub Models. "
                    "Install with: uv add openai"
                )

            self._client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )

            print(f"✓ Loaded GitHub Models LLM: {self.model}")

        return self._client

    def generate(self, prompt: str, schema: Optional[type] = None):
        """
        Generate completion using GitHub Models.

        Args:
            prompt: The prompt to send to the LLM
            schema: Optional Pydantic model for structured output

        Returns:
            Generated text response or Pydantic model instance
        """
        client = self.load_model()

        # Prepare request parameters
        params = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.temperature,
        }

        if self.max_tokens:
            params["max_tokens"] = self.max_tokens

        # If schema is provided, use JSON mode
        if schema is not None:
            try:
                # Try to use structured output with beta.chat.completions.parse
                response = client.beta.chat.completions.parse(
                    **params,
                    response_format=schema
                )
                return response.choices[0].message.parsed
            except Exception as e:
                # Fall back to JSON mode if parse not available
                params["response_format"] = {"type": "json_object"}
                response = client.chat.completions.create(**params)
                import json
                json_response = json.loads(response.choices[0].message.content)
                # Try to instantiate the schema with the JSON response
                try:
                    return schema(**json_response)
                except:
                    # If that fails, return the raw content
                    return response.choices[0].message.content

        # Call GitHub Models API (no schema)
        try:
            response = client.chat.completions.create(**params)
            return response.choices[0].message.content

        except Exception as e:
            raise RuntimeError(
                f"GitHub Models API error: {e}\n"
                f"Model: {self.model}\n"
                f"Base URL: {self.base_url}"
            )

    async def a_generate(self, prompt: str, schema: Optional[type] = None):
        """
        Async generate (uses sync for now).

        Args:
            prompt: The prompt to send to the LLM
            schema: Optional Pydantic model for structured output

        Returns:
            Generated text response or Pydantic model instance
        """
        # DeepEval supports async, but GitHub Models OpenAI client
        # is synchronous, so we just call the sync version
        return self.generate(prompt, schema)

    def get_model_name(self) -> str:
        """Get the model name for logging."""
        return f"GitHubModels-{self.model}"


def create_github_llm(
    model: str = "gpt-4o-mini",
    temperature: float = 0.0
) -> GitHubModelsLLM:
    """
    Convenience function to create GitHub Models LLM for DeepEval.

    Args:
        model: Model ID (default: gpt-4o-mini)
        temperature: Sampling temperature (0.0 = deterministic)

    Returns:
        GitHubModelsLLM instance ready for DeepEval metrics

    Example:
        >>> llm = create_github_llm()
        >>> from deepeval.metrics import FaithfulnessMetric
        >>> metric = FaithfulnessMetric(model=llm, threshold=0.9)
    """
    return GitHubModelsLLM(model=model, temperature=temperature)


# Test the LLM wrapper
if __name__ == "__main__":
    print("=" * 70)
    print("Testing GitHub Models LLM for DeepEval")
    print("=" * 70)

    # Create LLM instance
    print("\n1. Creating GitHub Models LLM...")
    llm = create_github_llm(model="gpt-4o-mini")
    print(f"   Model: {llm.get_model_name()}")
    print(f"   Base URL: {llm.base_url}")

    # Test generation
    print("\n2. Testing generation...")
    test_prompt = "What is 2 + 2? Answer with just the number."
    response = llm.generate(test_prompt)
    print(f"   Prompt: {test_prompt}")
    print(f"   Response: {response}")

    # Test with DeepEval metric
    print("\n3. Testing with DeepEval metric...")
    try:
        from deepeval.metrics import AnswerRelevancyMetric
        from deepeval.test_case import LLMTestCase

        # Create test case
        test_case = LLMTestCase(
            input="What is a warm jacket for skiing?",
            actual_output="I recommend the Summit Pro Parka. It has 700-fill down insulation and is waterproof.",
            retrieval_context=["Summit Pro Parka - 700-fill down - waterproof - $275"]
        )

        # Create metric with GitHub Models
        metric = AnswerRelevancyMetric(model=llm, threshold=0.7)

        # Measure
        print("   Running Answer Relevancy metric...")
        metric.measure(test_case)

        print(f"   Score: {metric.score:.3f}")
        print(f"   Threshold: {metric.threshold}")
        print(f"   Pass: {metric.is_successful()}")
        print(f"   Reason: {metric.reason}")

    except ImportError as e:
        print(f"   Skipping DeepEval test: {e}")

    print("\n" + "=" * 70)
    print("✓ GitHub Models LLM is ready for DeepEval!")
    print("=" * 70)
