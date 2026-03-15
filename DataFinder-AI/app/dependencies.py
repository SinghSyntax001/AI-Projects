from fastapi import Depends
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database.db import get_db_session
from app.security.auth import verify_api_key
from app.services.dataset_service import DatasetService
from app.services.search_service import SearchService


def get_settings_dependency() -> Settings:
    return get_settings()


def get_database_session(db: Session = Depends(get_db_session)) -> Session:
    return db


def get_search_service(
    db: Session = Depends(get_database_session),
    settings: Settings = Depends(get_settings_dependency),
) -> SearchService:
    return SearchService(db, settings)


def get_dataset_service(
    db: Session = Depends(get_database_session),
    settings: Settings = Depends(get_settings_dependency),
) -> DatasetService:
    return DatasetService(db, settings)


def require_api_key(_: str = Depends(verify_api_key)) -> None:
    return None
