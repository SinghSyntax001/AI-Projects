from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.database.models import Dataset
from app.pipeline.transform import to_response
from app.services.search_service import SearchService


class DatasetService:
    def __init__(self, db: Session, settings: Settings):
        self.db = db
        self.settings = settings

    def get_all_datasets(self, limit: int = 100) -> list[dict]:
        datasets = list(self.db.scalars(select(Dataset).limit(limit)).all())
        return [to_response(dataset).__dict__ for dataset in datasets]

    def get_dataset_by_id(self, dataset_id: int) -> dict | None:
        dataset = self.db.scalar(select(Dataset).where(Dataset.id == dataset_id))
        if dataset is None:
            return None
        return to_response(dataset).__dict__

    def search_datasets(self, query: str, limit: int | None = None) -> list[dict]:
        search_service = SearchService(self.db, self.settings)
        return search_service.search(query, limit)
