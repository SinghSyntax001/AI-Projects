from fastapi import APIRouter, Depends, Query

from app.dependencies import get_search_service, require_api_key
from app.pipeline.transform import SearchResponse
from app.services.search_service import SearchService


router = APIRouter(prefix="/search", tags=["search"], dependencies=[Depends(require_api_key)])


@router.get("", response_model=SearchResponse)
def search_datasets(
    q: str = Query(..., min_length=2, max_length=500, description="Natural-language dataset search query", examples=["medical imaging datasets"]),
    limit: int | None = Query(default=None, ge=1, le=50),
    service: SearchService = Depends(get_search_service),
) -> SearchResponse:
    """Return the top semantic matches from the persisted FAISS vector index."""
    results = service.search(q, limit)
    return SearchResponse(query=q, count=len(results), results=results)
