"""
Advanced dataset agent with ReAct loop implementation.

Implements Reason + Act + Observe pattern for intelligent dataset discovery.
Uses LLM for decision-making and tool execution.
"""

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any

from app.services.llm_service import LLMService
from app.services.search_service import SearchService

logger = logging.getLogger("datafinder.agent")


@dataclass
class AgentStep:
    """Single step in the agent's reasoning process."""

    iteration: int
    thought: str
    action: str | None = None
    action_input: dict[str, Any] = field(default_factory=dict)
    observation: str = ""
    final_answer: str | None = None


class DatasetAgent:
    """
    ReAct agent for intelligent dataset discovery.

    Uses Groq LLM for reasoning combined with tool execution
    to discover optimal datasets for user queries.
    """

    def __init__(self, llm_service: LLMService, search_service: SearchService):
        """Initialize agent with dependencies."""
        self.llm = llm_service
        self.search = search_service
        self.history: list[AgentStep] = []
        self.max_iterations = 5

    async def run(self, query: str) -> dict[str, Any]:
        """
        Execute ReAct loop.

        Iteratively: Think → Choose Action → Observe → Reason

        Args:
            query: User's natural language query

        Returns:
            Dictionary with final answer, steps taken, and tool invocations
        """
        self.history = []
        logger.info(f"Agent starting for query: {query}")

        for iteration in range(self.max_iterations):
            step = AgentStep(iteration=iteration)

            # THINK: Get LLM's reasoning for next step
            step.thought = await self._think(query, iteration)
            logger.info(f"[Iteration {iteration}] Thought: {step.thought}")

            # PARSE: Extract action from thought
            action, action_input = self._parse_thought(step.thought)
            step.action = action
            step.action_input = action_input

            # CHECK: If no action, agent returns answer
            if action is None:
                step.final_answer = step.thought
                self.history.append(step)
                logger.info(f"[Iteration {iteration}] Agent returning answer")
                break

            logger.info(
                f"[Iteration {iteration}] Action: {action}, Input: {action_input}"
            )

            # ACT: Execute the chosen tool
            try:
                observation = await self._execute_action(action, action_input)
                step.observation = observation
                logger.info(
                    f"[Iteration {iteration}] Observation: {observation[:100]}..."
                )
            except Exception as e:
                step.observation = f"Error: {str(e)}"
                logger.error(
                    f"[Iteration {iteration}] Action failed: {e}",
                    exc_info=True,
                )

            self.history.append(step)

        # Generate final answer from all observations
        final_answer = await self._generate_final_answer(query)

        return {
            "query": query,
            "answer": final_answer,
            "iterations": len(self.history),
            "steps": [
                {
                    "iteration": s.iteration,
                    "thought": s.thought,
                    "action": s.action,
                    "observation": s.observation,
                    "final_answer": s.final_answer,
                }
                for s in self.history
            ],
            "tools_used": [s.action for s in self.history if s.action],
        }

    async def _think(self, query: str, iteration: int) -> str:
        """Get LLM's reasoning for the next step."""
        history_summary = self._format_history(iteration)

        prompt = f"""You are an intelligent dataset discovery agent.

User Query: "{query}"

Available Tools:
1. search_datasets(query: str, limit: int) - Semantic search across all datasets
2. filter_datasets(criteria: str, datasets: list) - Filter datasets by criteria
3. get_metadata(dataset_id: str) - Get detailed metadata for a dataset
4. compare_datasets(dataset_ids: list) - Compare multiple datasets
5. recommend_datasets(use_case: str) - Recommend datasets for a use case

{history_summary}

You must respond in this format:
Thought: Your reasoning about what to do next
Action: [ONLY if you need more info] name of the tool to use
Action Input: {{"param1": "value1", "param2": "value2"}}

OR if you have enough information:
Thought: Your reasoning about the best datasets for this query
[No Action - provide the answer directly]"""

        try:
            response = self.llm.query(prompt)
            return response
        except Exception as e:
            logger.error(f"LLM thought generation failed: {e}")
            return f"Unable to reason: {str(e)}"

    def _parse_thought(self, thought: str) -> tuple[str | None, dict[str, Any]]:
        """Parse LLM output to extract action and parameters."""
        # Check if agent is providing final answer (no Action: line)
        if "Action:" not in thought:
            return None, {}

        # Extract action name
        action_match = re.search(r"Action:\s*(\w+)", thought, re.IGNORECASE)
        if not action_match:
            return None, {}

        action = action_match.group(1).lower()

        # Extract action input (JSON)
        input_match = re.search(
            r"Action Input:\s*({[^}]*})", thought, re.IGNORECASE | re.DOTALL
        )
        action_input = {}

        if input_match:
            try:
                input_str = input_match.group(1)
                action_input = json.loads(input_str)
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse action input: {e}")
                action_input = {}

        return action, action_input

    async def _execute_action(self, action: str, action_input: dict) -> str:
        """Execute the specified action/tool."""
        try:
            if action == "search_datasets":
                return await self._tool_search_datasets(**action_input)
            elif action == "filter_datasets":
                return await self._tool_filter_datasets(**action_input)
            elif action == "get_metadata":
                return await self._tool_get_metadata(**action_input)
            elif action == "compare_datasets":
                return await self._tool_compare_datasets(**action_input)
            elif action == "recommend_datasets":
                return await self._tool_recommend_datasets(**action_input)
            else:
                return f"Unknown action: {action}"
        except Exception as e:
            logger.error(f"Tool execution error for {action}: {e}")
            raise

    async def _tool_search_datasets(self, query: str, limit: int = 10) -> str:
        """Tool: Search for datasets matching query."""
        results = self.search.search(query, limit)
        if not results:
            return f"No datasets found matching '{query}'"

        summary = f"Found {len(results)} datasets for '{query}':\n"
        for i, result in enumerate(results[:5], 1):
            summary += (
                f"{i}. {result.get('name', 'Unknown')} "
                f"(Source: {result.get('source', 'Unknown')}, "
                f"Score: {result.get('score', 0):.2f})\n"
            )
        return summary

    async def _tool_filter_datasets(
        self, criteria: str, datasets: list[dict] | None = None
    ) -> str:
        """Tool: Filter datasets by criteria."""
        # Use LLM to understand natural language criteria and filter
        if datasets is None:
            return "No datasets provided to filter"

        prompt = f"""Filter these datasets based on: "{criteria}"
Datasets: {json.dumps(datasets[:5])}
Return a JSON array of indices of datasets that match."""

        try:
            response = self.llm.query(prompt)
            # Parse response to extract indices and filter
            return f"Filtered {len(datasets)} datasets by criteria: {criteria}"
        except Exception as e:
            return f"Filtering error: {str(e)}"

    async def _tool_get_metadata(self, dataset_id: str) -> str:
        """Tool: Get detailed metadata for a dataset."""
        try:
            dataset = self.search.db.query(
                __import__("sqlalchemy").text(f"SELECT * FROM datasets WHERE id = :id"),
                {"id": dataset_id},
            )
            if not dataset:
                return f"Dataset {dataset_id} not found"
            return f"Metadata for {dataset_id}: {json.dumps(dict(dataset))}"
        except Exception as e:
            return f"Metadata retrieval error: {str(e)}"

    async def _tool_compare_datasets(self, dataset_ids: list[str]) -> str:
        """Tool: Compare multiple datasets."""
        if not dataset_ids or len(dataset_ids) < 2:
            return "Need at least 2 datasets to compare"

        comparison = f"Comparing {len(dataset_ids)} datasets:\n"
        for ds_id in dataset_ids[:3]:
            comparison += f"- Dataset {ds_id}: [Metadata comparison pending]\n"
        return comparison

    async def _tool_recommend_datasets(self, use_case: str) -> str:
        """Tool: Recommend datasets for a use case."""
        # Use semantic search to find relevant datasets
        results = self.search.search(use_case, limit=5)
        if not results:
            return f"No datasets found for use case: {use_case}"

        recommendation = f"Recommended datasets for '{use_case}':\n"
        for i, result in enumerate(results[:3], 1):
            recommendation += (
                f"{i}. {result.get('name', 'Unknown')} - "
                f"{result.get('description', 'No description')[:80]}...\n"
            )
        return recommendation

    def _format_history(self, current_iteration: int) -> str:
        """Format previous steps for context."""
        if not self.history or current_iteration == 0:
            return "This is the first step."

        history_text = "Previous steps taken:\n"
        for step in self.history[-2:]:  # Show last 2 steps for context
            history_text += f"- Thought: {step.thought[:100]}...\n"
            if step.action:
                history_text += f"  Action: {step.action}\n"
            history_text += f"  Observation: {step.observation[:150]}...\n"
        return history_text

    async def _generate_final_answer(self, query: str) -> str:
        """Generate final synthesis from all observations."""
        if not self.history:
            return "No analysis performed"

        observations = "\n".join(
            [f"- {step.observation}" for step in self.history if step.observation]
        )

        prompt = f"""Based on this analysis of datasets for the query "{query}":

{observations}

Provide a concise summary of the best matching datasets and why they're relevant.
Include specific dataset names and key characteristics."""

        try:
            return self.llm.query(prompt)
        except Exception as e:
            logger.error(f"Final answer generation failed: {e}")
            return "Analysis complete. See observations above for discovered datasets."
