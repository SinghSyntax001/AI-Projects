"""
Chat and LLM-powered discovery API endpoints.

Provides conversational interfaces for dataset discovery using the Groq LLM
(mixtral-8x7b-32768). Includes multi-turn chat, intent extraction, query refinement,
intelligent search with explanations, and full ReAct agentic loop.

All endpoints are protected by API key authentication.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.agents.orchestrator import DatasetAgent
from app.config import get_settings, Settings
from app.dependencies import get_database_session, require_api_key
from app.metrics import track_llm_request
from app.security.auth import verify_api_key
from app.services.llm_service import LLMService
from app.services.search_service import SearchService

logger = logging.getLogger("datafinder.chat")
router = APIRouter(prefix="/api/v1/chat", tags=["chat"])

limiter = Limiter(key_func=get_remote_address)

# Global LLM service instance (lazy-initialized on first request)
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """
    Lazy-load or retrieve the global LLM service instance.

    Ensures only one LLM service is created across all requests.
    Raises RuntimeError if GROQ_API_KEY is not configured.
    """
    global _llm_service
    if _llm_service is None:
        settings = get_settings()
        if not settings.groq_api_key:
            raise RuntimeError("GROQ_API_KEY not configured")
        _llm_service = LLMService(
            api_key=settings.groq_api_key,
            model=settings.llm_model,
            temperature=settings.llm_temperature,
        )
    return _llm_service


class ChatMessage(BaseModel):
    """Single message in a conversation (either user or assistant)."""

    role: str  # "user" or "assistant"
    content: str  # Message text


class ChatRequest(BaseModel):
    """Request body for chat endpoint."""

    message: str  # User's question or statement
    session_id: Optional[str] = None  # Optional session ID for tracking


class ChatResponse(BaseModel):
    """Response body for chat endpoint."""

    message: str  # LLM's response
    reasoning: Optional[str] = None  # Optional: LLM's reasoning process
    tools_used: list[str] = []  # List of tools invoked (e.g., search, filter)
    follow_up_suggestions: list[str] = []  # Suggested follow-up questions


class SearchWithIntentRequest(BaseModel):
    """Request for intent-based search."""

    query: str  # User's natural language search query
    limit: Optional[int] = 10  # Max results to return


class SearchWithIntentResponse(BaseModel):
    """Response with intent extraction and explanation."""

    query: str  # Original user query
    refined_query: str  # LLM's improved query for better search
    intent: str  # Extracted intent (search, filter, compare, etc.)
    datasets: list[dict]  # Matching datasets
    explanation: str  # Natural language explanation of relevance


@router.post("/ask", response_model=ChatResponse)
@limiter.limit("50/hour")  # Rate limit: 50 LLM requests per hour (expensive)
async def chat(
    request: ChatRequest,
    http_request: Request,
    db: Session = Depends(get_database_session),
    _: None = Depends(require_api_key),
) -> ChatResponse:
    """Conversational dataset discovery.

    Understands natural language queries and provides intelligent responses.
    Maintains conversation history for multi-turn interactions.

    Example:
        POST /api/v1/chat/ask
        {
            "message": "I need image datasets for computer vision projects",
            "session_id": "user-123"
        }

    Rate Limit: 50 requests per hour per IP address
    """
    try:
        llm_service = get_llm_service()
        search_service = SearchService(db, get_settings())

        with track_llm_request("mixtral-8x7b-32768", "chat"):
            # Get LLM response
            response = llm_service.chat(request.message)

        logger.info(
            "chat response generated",
            extra={
                "event_data": {
                    "message_length": len(request.message),
                    "response_length": len(response),
                }
            },
        )

        return ChatResponse(message=response, tools_used=[], follow_up_suggestions=[])

    except Exception as e:
        logger.error(f"Chat failed: {e}")
        raise HTTPException(status_code=500, detail="Chat processing failed")


class AgentRequest(BaseModel):
    """Request body for agentic reasoning endpoint."""

    query: str  # User's natural language query
    max_iterations: int = 5  # Max reasoning iterations


class AgentResponse(BaseModel):
    """Response from agentic reasoning."""

    query: str
    answer: str
    iterations: int
    tools_used: list[str]
    reasoning_steps: list[dict]


@router.post("/agent", response_model=AgentResponse)
@limiter.limit("25/hour")  # Rate limit: 25 agent queries per hour (very expensive)
async def agent_reasoning(
    request: AgentRequest,
    http_request: Request,
    db: Session = Depends(get_database_session),
    _: None = Depends(require_api_key),
) -> AgentResponse:
    """
    Advanced dataset discovery using ReAct agentic reasoning loop.

    Uses Groq LLM to reason about queries, decide which tools to use,
    and iteratively refine the search strategy.

    Implements: Reason → Act → Observe → Repeat pattern

    Example:
        POST /api/v1/chat/agent
        {
            "query": "Find me image datasets for medical imaging applications with cross-modal data",
            "max_iterations": 5
        }

    Rate Limit: 25 requests per hour per IP address (expensive LLM calls)

    Returns:
        - query: Original user query
        - answer: Final synthesized answer with best datasets
        - iterations: Number of reasoning steps taken
        - tools_used: List of tools invoked (search, filter, compare, etc.)
        - reasoning_steps: Detailed reasoning trace for transparency
    """
    try:
        llm_service = get_llm_service()
        search_service = SearchService(db, get_settings())

        # Create and run agent
        agent = DatasetAgent(llm_service, search_service)
        agent.max_iterations = request.max_iterations

        with track_llm_request("mixtral-8x7b-32768", "agent_reasoning"):
            result = await agent.run(request.query)

        logger.info(
            "agent reasoning completed",
            extra={
                "event_data": {
                    "query": request.query,
                    "iterations": result["iterations"],
                    "tools_used": result["tools_used"],
                }
            },
        )

        return AgentResponse(
            query=result["query"],
            answer=result["answer"],
            iterations=result["iterations"],
            tools_used=result["tools_used"],
            reasoning_steps=result["steps"],
        )

    except Exception as e:
        logger.error(f"Agent reasoning failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Agent reasoning failed")


@router.post("/search-intent", response_model=SearchWithIntentResponse)
@limiter.limit("100/hour")  # Rate limit: 100 intent searches per hour
async def search_with_intent(
    request: SearchWithIntentRequest,
    http_request: Request,
    db: Session = Depends(get_database_session),
    _: None = Depends(require_api_key),
) -> SearchWithIntentResponse:
    """Intelligent search with intent extraction and explanation.

    1. Extracts user intent from natural language
    2. Refines the search query
    3. Performs semantic search
    4. Explains why results match

    Example:
        POST /api/v1/chat/search-intent
        {
            "query": "I'm building a face recognition system",
            "limit": 10
        }

    Rate Limit: 100 requests per hour per IP address
    """
    try:
        llm_service = get_llm_service()
        search_service = SearchService(db, get_settings())

        with track_llm_request("mixtral-8x7b-32768", "intent_extraction"):
            # Extract intent and refine query
            intent_data = llm_service.extract_intent(request.query)
            refined_query = intent_data.get("refined_query", request.query)

        # Perform semantic search
        datasets = search_service.search(refined_query, limit=request.limit, skip=0)

        # Generate explanation
        explanation = llm_service.explain_datasets(request.query, datasets)

        logger.info(
            "intent-based search completed",
            extra={
                "event_data": {
                    "original_query": request.query,
                    "refined_query": refined_query,
                    "intent": intent_data.get("intent", "unknown"),
                    "results_count": len(datasets),
                }
            },
        )

        return SearchWithIntentResponse(
            query=request.query,
            refined_query=refined_query,
            intent=intent_data.get("intent", "search"),
            datasets=datasets,
            explanation=explanation,
        )

    except Exception as e:
        logger.error(f"Intent-based search failed: {e}")
        raise HTTPException(status_code=500, detail="Search processing failed")


@router.post("/refine")
@limiter.limit("50/hour")  # Rate limit: 50 refinements per hour
async def refine_search(
    request: Request,
    query: str = Query(...),
    feedback: str = Query(...),
    db: Session = Depends(get_database_session),
    _: None = Depends(require_api_key),
) -> dict:
    """Refine search based on user feedback.

    Example:
        POST /api/v1/chat/refine?query=ml+datasets&feedback=too+many+results
    """
    try:
        llm_service = get_llm_service()
        search_service = SearchService(db, get_settings())

        # Refine query based on feedback
        refined_query = llm_service.refine_search(query, feedback)

        # Perform new search
        datasets = search_service.search(refined_query, limit=10, skip=0)

        logger.info(
            "search refinement completed",
            extra={
                "event_data": {
                    "original_query": query,
                    "feedback": feedback,
                    "refined_query": refined_query,
                }
            },
        )

        return {
            "original_query": query,
            "refined_query": refined_query,
            "datasets": datasets,
        }

    except Exception as e:
        logger.error(f"Search refinement failed: {e}")
        raise HTTPException(status_code=500, detail="Refinement failed")


@router.get("/history")
async def get_conversation_history(
    _: None = Depends(require_api_key),
) -> dict:
    """Get current conversation history.

    Example:
        GET /api/v1/chat/history
    """
    try:
        llm_service = get_llm_service()
        history = llm_service.get_conversation_context()

        return {"conversation_history": history}

    except Exception as e:
        logger.error(f"Failed to get history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get history")


@router.post("/reset")
async def reset_conversation(
    _: None = Depends(require_api_key),
) -> dict:
    """Reset conversation history for new session.

    Example:
        POST /api/v1/chat/reset
    """
    try:
        llm_service = get_llm_service()
        llm_service.clear_history()

        logger.info("conversation history cleared")

        return {"status": "conversation reset"}

    except Exception as e:
        logger.error(f"Failed to reset conversation: {e}")
        raise HTTPException(status_code=500, detail="Failed to reset")


@router.get("/health")
async def chat_health(_: None = Depends(require_api_key)) -> dict:
    """Check if LLM service is healthy.

    Example:
        GET /api/v1/chat/health
    """
    try:
        llm_service = get_llm_service()
        # Quick test
        _ = llm_service.query("What is a dataset?")
        return {"status": "healthy", "llm_available": True}
    except Exception as e:
        logger.error(f"LLM health check failed: {e}")
        return {"status": "unhealthy", "llm_available": False, "error": str(e)}
