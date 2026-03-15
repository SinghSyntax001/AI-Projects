"""
Dataset catalog API endpoints.

Provides endpoints to list and retrieve individual dataset records
from the persistent metadata database.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies import get_dataset_service, require_api_key
from app.pipeline.transform import DatasetListResponse, DatasetResponse
from app.services.dataset_service import DatasetService


router = APIRouter(
    prefix="/datasets", tags=["datasets"], dependencies=[Depends(require_api_key)]
)


@router.get("", response_model=DatasetListResponse)
def get_all_datasets(
    limit: int = Query(default=100, ge=1, le=500),
    service: DatasetService = Depends(get_dataset_service),
) -> DatasetListResponse:
    """
    List all datasets in the metadata catalog with pagination.

    Args:
        limit: Max number of datasets to return (default: 100, max: 500)

    Returns:
        DatasetListResponse with list of datasets and total count
    """
    items = service.get_all_datasets(limit)
    return DatasetListResponse(items=items, total=len(items))


@router.get("/{dataset_id}", response_model=DatasetResponse)
def get_dataset_by_id(
    dataset_id: int,
    service: DatasetService = Depends(get_dataset_service),
) -> DatasetResponse:
    """
    Fetch a single dataset record by its database ID.

    Args:
        dataset_id: Database ID of the dataset

    Returns:
        DatasetResponse with complete dataset metadata

    Raises:
        HTTPException 404 if dataset_id not found
    """
    dataset = service.get_dataset_by_id(dataset_id)
    if dataset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset with id {dataset_id} was not found",
        )
    return DatasetResponse(**dataset)
