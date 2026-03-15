"""
Agentic tools for intelligent dataset discovery and workflows.

Defines tools that an LLM agent can invoke to search, filter, compare,
and recommend datasets. Each tool has:
- JSON schema describing its inputs
- Description for LLM understanding
- Callable execute function (optional)

The agent uses these tools to break down complex user requests into
discrete steps for dataset discovery.
"""

import json
from typing import Any, Callable

from pydantic import BaseModel, Field


class Tool(BaseModel):
    """Tool definition for agentic discovery."""

    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="What the tool does")
    input_schema: dict = Field(..., description="JSON schema for input")
    execute: Callable = Field(default=None, exclude=True)


# Tool input schemas
class SearchInput(BaseModel):
    """Input for search_datasets tool."""

    query: str = Field(..., description="Semantic search query")
    limit: int = Field(default=10, description="Number of results to return")
    domain: str = Field(
        default="",
        description="Optional domain filter: ml, nlp, images, timeseries, tabular",
    )


class FilterInput(BaseModel):
    """Input for filter_datasets tool."""

    criteria: str = Field(..., description="Filter criteria in natural language")
    datasets: list[dict] = Field(..., description="List of datasets to filter")


class CompareInput(BaseModel):
    """Input for compare_datasets tool."""

    dataset_ids: list[str] = Field(..., description="IDs of datasets to compare")
    aspects: list[str] = Field(
        default=["size", "domain", "source", "availability"],
        description="Aspects to compare",
    )


class GetMetadataInput(BaseModel):
    """Input for get_metadata tool."""

    dataset_id: str = Field(..., description="Dataset ID or name")


class RecommendInput(BaseModel):
    """Input for recommend_datasets tool."""

    use_case: str = Field(..., description="Target use case for recommendation")
    constraints: str = Field(default="", description="Optional constraints")


def create_tools() -> dict[str, Tool]:
    """Create all available agentic tools.

    Returns:
        Dictionary of tool name -> Tool definition
    """
    tools = {}

    # Search tool
    tools["search_datasets"] = Tool(
        name="search_datasets",
        description="Semantically search for datasets using natural language. Returns ranked list of relevant datasets.",
        input_schema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "What to search for (e.g., 'image classification datasets', 'time series data')",
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of results (default: 10)",
                },
                "domain": {
                    "type": "string",
                    "enum": ["ml", "nlp", "images", "timeseries", "tabular", ""],
                    "description": "Optional domain filter",
                },
            },
            "required": ["query"],
        },
    )

    # Filter tool
    tools["filter_datasets"] = Tool(
        name="filter_datasets",
        description="Filter search results based on specific criteria like size, source, or content type.",
        input_schema={
            "type": "object",
            "properties": {
                "criteria": {
                    "type": "string",
                    "description": "Filter criteria (e.g., 'only large datasets from Kaggle', 'smaller than 5GB')",
                },
                "dataset_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "IDs of datasets to filter (from search results)",
                },
            },
            "required": ["criteria", "dataset_ids"],
        },
    )

    # Compare tool
    tools["compare_datasets"] = Tool(
        name="compare_datasets",
        description="Compare multiple datasets across size, domain, source, and other attributes.",
        input_schema={
            "type": "object",
            "properties": {
                "dataset_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "IDs of datasets to compare",
                },
                "aspects": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "What to compare: size, domain, source, rows, features, etc.",
                },
            },
            "required": ["dataset_ids"],
        },
    )

    # Get metadata tool
    tools["get_metadata"] = Tool(
        name="get_metadata",
        description="Get detailed metadata about a specific dataset including stats, source, and licensing.",
        input_schema={
            "type": "object",
            "properties": {
                "dataset_id": {
                    "type": "string",
                    "description": "Dataset ID or name",
                },
            },
            "required": ["dataset_id"],
        },
    )

    # Recommend tool
    tools["recommend_datasets"] = Tool(
        name="recommend_datasets",
        description="Get dataset recommendations for a specific use case or research goal.",
        input_schema={
            "type": "object",
            "properties": {
                "use_case": {
                    "type": "string",
                    "description": "What do you need the data for? (e.g., 'training image classification model', 'analyzing customer behavior')",
                },
                "constraints": {
                    "type": "string",
                    "description": "Optional constraints (e.g., 'less than 10GB', 'must be free')",
                },
            },
            "required": ["use_case"],
        },
    )

    # Explore tool
    tools["explore_domain"] = Tool(
        name="explore_domain",
        description="Explore what datasets are available in a specific domain or category.",
        input_schema={
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "description": "Domain to explore (ml, nlp, images, timeseries, tabular, research, etc.)",
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of popular datasets to show (default: 10)",
                },
            },
            "required": ["domain"],
        },
    )

    return tools


def format_tool_for_llm(tool: Tool) -> str:
    """Format tool definition for LLM context.

    Args:
        tool: Tool definition

    Returns:
        Formatted tool description
    """
    return f"""Tool: {tool.name}
Description: {tool.description}
Input Schema: {json.dumps(tool.input_schema, indent=2)}
"""


def format_all_tools_for_llm(tools: dict[str, Tool]) -> str:
    """Format all tools for LLM context.

    Args:
        tools: Dictionary of tools

    Returns:
        Formatted tools description
    """
    return "\n\n".join([format_tool_for_llm(tool) for tool in tools.values()])
