"""
Database migration utilities using Alembic.

Provides setup and management for database schema versioning.
Run: alembic upgrade head (to apply migrations)
Run: alembic revision --autogenerate -m "description" (to create new migration)
"""

import logging
from pathlib import Path
from typing import Optional

import alembic
from alembic import command
from alembic.config import Config

logger = logging.getLogger("datafinder.migrations")


def get_migration_config() -> Config:
    """Get Alembic configuration."""
    base_dir = Path(__file__).resolve().parent.parent
    alembic_dir = base_dir / "alembic"

    config = Config(str(alembic_dir / "alembic.ini"))
    config.set_main_option(
        "sqlalchemy.url",
        __import__("os").getenv(
            "DATABASE_URL",
            f"sqlite:///{(base_dir / 'data' / 'datafinder.db').as_posix()}",
        ),
    )

    return config


def init_migrations() -> None:
    """Initialize Alembic for a new project."""
    base_dir = Path(__file__).resolve().parent.parent
    alembic_dir = base_dir / "alembic"

    if not alembic_dir.exists():
        logger.info("Initializing Alembic migrations")
        command.init(get_migration_config(), str(alembic_dir), template="generic")


def create_migration(message: str, autogenerate: bool = True) -> Optional[str]:
    """
    Create a new migration file.

    Args:
        message: Migration description
        autogenerate: Auto-detect schema changes

    Returns:
        Path to created migration file
    """
    try:
        config = get_migration_config()
        if autogenerate:
            logger.info(f"Creating auto-generated migration: {message}")
            command.revision(config, message=message, autogenerate=True)
        else:
            logger.info(f"Creating manual migration: {message}")
            command.revision(config, message=message)
        return "Migration created successfully"
    except Exception as e:
        logger.error(f"Failed to create migration: {e}")
        return None


def apply_migrations(sql_only: bool = False) -> bool:
    """
    Apply pending migrations.

    Args:
        sql_only: Generate SQL without executing

    Returns:
        True if successful
    """
    try:
        config = get_migration_config()
        if sql_only:
            logger.info("Generating migration SQL (not executing)")
            command.upgrade(config, "head", sql=True)
        else:
            logger.info("Applying migrations")
            command.upgrade(config, "head")
        return True
    except Exception as e:
        logger.error(f"Failed to apply migrations: {e}")
        return False


def rollback_migration(steps: int = 1) -> bool:
    """
    Rollback N migrations.

    Args:
        steps: Number of migrations to rollback

    Returns:
        True if successful
    """
    try:
        config = get_migration_config()
        logger.info(f"Rolling back {steps} migration(s)")
        for _ in range(steps):
            command.downgrade(config, "-1")
        return True
    except Exception as e:
        logger.error(f"Failed to rollback migration: {e}")
        return False


def get_migration_history() -> list[tuple]:
    """Get list of applied migrations."""
    try:
        config = get_migration_config()
        # This requires a database connection
        from sqlalchemy import create_engine, text
        from sqlalchemy.pool import StaticPool

        db_url = config.get_main_option("sqlalchemy.url")

        # Handle SQLite in-memory if needed
        connect_args = {}
        if db_url.startswith("sqlite"):
            connect_args = {"check_same_thread": False}

        engine = create_engine(db_url, connect_args=connect_args, poolclass=StaticPool)

        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT version_num, description FROM alembic_version")
            )
            return list(result.fetchall())
    except Exception as e:
        logger.warning(f"Could not retrieve migration history: {e}")
        return []
