"""
Database configuration and session management.

Configures SQLAlchemy for both SQLite (development) and PostgreSQL (production).
Provides session factory and dependency injection for database access.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.config import get_settings


settings = get_settings()

# SQLite doesn't support multiple threads, so we disable that check
connect_args = (
    {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
)

# Create database engine with appropriate connection args
engine = create_engine(settings.database_url, connect_args=connect_args)

# Session factory for creating database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base for ORM models
Base = declarative_base()


def get_db_session() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a database session for a request.

    Yields a session and ensures it's closed after the request completes.
    Used by @Depends(get_database_session) in route handlers.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
