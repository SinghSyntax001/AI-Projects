"""
Dataset metadata service.

Provides methods to query and retrieve dataset records from the database.
Bridges between database models and API responses.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.database.models import Dataset
from app.pipeline.transform import to_response
from app.services.search_service import SearchService


class DatasetService:
    """
    Service layer for dataset CRUD operations.

    Wraps database access with business logic and response formatting.
    """

    def __init__(self, db: Session, settings: Settings):
        self.db = db
        self.settings = settings

    def get_all_datasets(self, limit: int = 100) -> list[dict]:
        """
        Fetch all datasets with a limit.

        Args:
            limit: Maximum number of datasets to return

        Returns:
            List of dataset dictionaries
        """
        datasets = list(self.db.scalars(select(Dataset).limit(limit)).all())
        return [to_response(dataset).__dict__ for dataset in datasets]

    def get_dataset_by_id(self, dataset_id: int) -> dict | None:
        """
        Fetch a single dataset by its database ID.

        Args:
            dataset_id: Database primary key

        Returns:
            Dataset dictionary or None if not found
        """
        dataset = self.db.scalar(select(Dataset).where(Dataset.id == dataset_id))
        if dataset is None:
            return None
        return to_response(dataset).__dict__

    def search_datasets(self, query: str, limit: int | None = None) -> list[dict]:
        """
        Search datasets using semantic similarity.

        Args:
            query: Natural language search query
            limit: Max results to return

        Returns:
            List of matching datasets ranked by relevance
        """
        search_service = SearchService(self.db, self.settings)
        return search_service.search(query, limit)
