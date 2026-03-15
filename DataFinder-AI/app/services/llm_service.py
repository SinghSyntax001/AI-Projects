"""
LLM Service using Groq API for intelligent dataset discovery.

This module provides the LLMService class that handles all interactions with
the Groq LLM (mixtral-8x7b-32768). It powers conversational search, intent extraction,
query refinement, and dataset explanations.
"""

import json
import logging
from typing import Any, Optional

from groq import Groq

logger = logging.getLogger("datafinder.llm")


class LLMService:
    """Groq-powered LLM service for understanding queries and reasoning about datasets."""

    def __init__(
        self, api_key: str, model: str = "mixtral-8x7b-32768", temperature: float = 0.7
    ):
        """Initialize Groq client and LLM configuration.

        Args:
            api_key: Groq API key
            model: Model identifier (default: mixtral-8x7b-32768 for best reasoning)
            temperature: Sampling temperature for creativity (0.0-1.0)
        """
        self.client = Groq(api_key=api_key)
        self.model = model
        self.temperature = temperature
        self.conversation_history = []

    def query(self, message: str) -> str:
        """Send a query to Groq and get response.

        Args:
            message: User message

        Returns:
            LLM response text
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": message}],
                temperature=self.temperature,
                max_tokens=1024,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM query failed: {e}")
            raise

    def chat(self, message: str) -> str:
        """Multi-turn conversation with conversation history.

        Args:
            message: User message

        Returns:
            LLM response text
        """
        self.conversation_history.append({"role": "user", "content": message})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.conversation_history,
                temperature=self.temperature,
                max_tokens=1024,
            )
            assistant_message = response.choices[0].message.content
            self.conversation_history.append(
                {"role": "assistant", "content": assistant_message}
            )
            return assistant_message
        except Exception as e:
            logger.error(f"LLM chat failed: {e}")
            raise

    def extract_intent(self, query: str) -> dict[str, Any]:
        """Extract user intent and parameters from natural language query.

        Args:
            query: User query text

        Returns:
            Dict with intent, keywords, filters, and refined_query
        """
        prompt = f"""Analyze this dataset search query and extract structured information.

Query: "{query}"

Respond ONLY with valid JSON (no markdown, no code blocks):
{{
    "intent": "search|filter|compare|recommend|explore",
    "keywords": ["keyword1", "keyword2"],
    "filters": {{"domain": "ml|nlp|images|timeseries|tabular", "size": "small|medium|large"}},
    "refined_query": "improved query for semantic search"
}}"""

        try:
            response = self.query(prompt)
            # Remove markdown code blocks if present
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
                response = response.strip()
            return json.loads(response)
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"Failed to extract intent from query: {e}")
            return {
                "intent": "search",
                "keywords": query.split(),
                "filters": {},
                "refined_query": query,
            }

    def explain_datasets(self, query: str, datasets: list[dict]) -> str:
        """Generate natural language explanation of why datasets match the query.

        Args:
            query: Original user query
            datasets: List of recommended datasets

        Returns:
            Natural language explanation
        """
        dataset_info = "\n".join(
            [
                f"- {d.get('name', 'Unknown')}: {d.get('description', 'No description')[:100]}"
                for d in datasets[:5]
            ]
        )

        prompt = f"""User searched for: "{query}"

Found these relevant datasets:
{dataset_info}

Explain in 2-3 sentences why these datasets match the user's search intent. Be specific about relevance."""

        try:
            return self.query(prompt)
        except Exception as e:
            logger.error(f"Failed to explain datasets: {e}")
            return "Datasets matching your search criteria have been found."

    def refine_search(self, initial_query: str, user_feedback: str) -> str:
        """Refine search based on user feedback using multi-turn reasoning.

        Args:
            initial_query: Original search query
            user_feedback: User's feedback on results

        Returns:
            Refined search query
        """
        prompt = f"""Original search: "{initial_query}"
User feedback: "{user_feedback}"

Based on this feedback, suggest a refined search query that better matches what the user actually wants.
Return ONLY the refined query, nothing else."""

        try:
            return self.query(prompt)
        except Exception as e:
            logger.error(f"Failed to refine search: {e}")
            return initial_query

    def extract_dataset_references(self, text: str) -> list[str]:
        """Extract dataset names or references from text.

        Args:
            text: Text to analyze

        Returns:
            List of likely dataset names/references
        """
        prompt = f"""From this text, extract any dataset names or references mentioned.

Text: "{text}"

Respond with ONLY a JSON array of strings: ["dataset1", "dataset2"]"""

        try:
            response = self.query(prompt)
            if response.startswith("["):
                return json.loads(response)
            return []
        except Exception as e:
            logger.warning(f"Failed to extract dataset references: {e}")
            return []

    def clear_history(self) -> None:
        """Clear conversation history for new session."""
        self.conversation_history = []

    def get_conversation_context(self) -> list[dict]:
        """Get current conversation history."""
        return self.conversation_history.copy()
