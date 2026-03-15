"""
Database models for storing dataset metadata.

Uses SQLAlchemy ORM to map Python classes to database tables.
The Dataset model stores information about all discovered datasets.
"""

from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.db import Base


class Dataset(Base):
    """
    Dataset metadata record.

    Stores information about each discovered dataset including name,
    description, source, embedding vector, and semantic keywords.
    """

    __tablename__ = "datasets"

    # Unique database identifier for each dataset
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Dataset name (indexed for quick lookups)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # Long-form description of the dataset
    description: Mapped[str] = mapped_column(Text, default="")

    # Source platform (Kaggle, OpenML, GitHub, etc. - indexed for filtering)
    source: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Comma-separated tags/categories for categorization
    tags: Mapped[str] = mapped_column(Text, default="")

    # Original URL where dataset can be accessed (unique constraint for deduplication)
    url: Mapped[str] = mapped_column(
        String(1000), unique=True, nullable=False, index=True
    )

    # Dataset size estimate (e.g., "5 GB", "500 MB")
    size: Mapped[str] = mapped_column(String(100), default="unknown")

    # JSON-serialized embedding vector for semantic search
    embedding: Mapped[str] = mapped_column(Text, default="")

    # Comma-separated keywords extracted via TF-IDF
    keywords: Mapped[str] = mapped_column(Text, default="")

    # Timestamp when record was created
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
