"""
Semantic search API endpoints.

Provides the /search endpoint for performing semantic similarity search
over the FAISS vector index of datasets using natural language queries.
"""

from fastapi import APIRouter, Depends, Query, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.dependencies import get_search_service, require_api_key
from app.pipeline.transform import SearchResponse
from app.services.search_service import SearchService


router = APIRouter(
    prefix="/search", tags=["search"], dependencies=[Depends(require_api_key)]
)

limiter = Limiter(key_func=get_remote_address)


@router.get("", response_model=SearchResponse)
@limiter.limit("100/hour")  # Rate limit: 100 requests per hour
def search_datasets(
    request: Request,
    q: str = Query(
        ...,
        min_length=2,
        max_length=500,
        description="Natural-language dataset search query",
        examples=["medical imaging datasets"],
    ),
    limit: int | None = Query(default=None, ge=1, le=50),
    service: SearchService = Depends(get_search_service),
) -> SearchResponse:
    """
    Perform semantic search across all datasets in the FAISS vector index.

    Uses embedding-based similarity to find relevant datasets matching
    the natural language query. Results are ranked by semantic similarity score.

    Args:
        q: User's search query (natural language, min 2 chars)
        limit: Max number of results to return (default: 10, max: 50)

    Returns:
        SearchResponse with query, count, and ranked list of matching datasets

    Rate Limit: 100 requests per hour per IP address
    """
    results = service.search(q, limit)
    return SearchResponse(query=q, count=len(results), results=results)
