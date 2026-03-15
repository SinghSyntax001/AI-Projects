"""
FastAPI dependency injection helpers.

Provides reusable dependency functions for route handlers to access
services, databases, and authentication without direct coupling.
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database.db import get_db_session
from app.security.auth import verify_api_key
from app.services.dataset_service import DatasetService
from app.services.search_service import SearchService


def get_settings_dependency() -> Settings:
    """Get the application settings instance."""
    return get_settings()


def get_database_session(db: Session = Depends(get_db_session)) -> Session:
    """Get a database session for the request."""
    return db


def get_search_service(
    db: Session = Depends(get_database_session),
    settings: Settings = Depends(get_settings_dependency),
) -> SearchService:
    """Get a search service instance with dependencies."""
    return SearchService(db, settings)


def get_dataset_service(
    db: Session = Depends(get_database_session),
    settings: Settings = Depends(get_settings_dependency),
) -> DatasetService:
    """Get a dataset service instance with dependencies."""
    return DatasetService(db, settings)


def require_api_key(_: str = Depends(verify_api_key)) -> None:
    """
    Dependency that enforces API key requirement.

    Used with @Depends(require_api_key) to protect endpoints.
    Raises HTTPException with 401 status if key is invalid.
    """
    return None
