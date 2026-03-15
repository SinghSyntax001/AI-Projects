from __future__ import annotations

from datetime import datetime, timezone
from functools import lru_cache
import logging

from pydantic import BaseModel, ConfigDict, Field
from sklearn.feature_extraction.text import TfidfVectorizer

from app.config import get_settings

try:
    from sentence_transformers import SentenceTransformer
except ImportError:  # pragma: no cover
    SentenceTransformer = None


logger = logging.getLogger("datafinder.pipeline.transform")


class DatasetRecord(BaseModel):
    name: str
    description: str = ""
    source: str
    tags: list[str] = Field(default_factory=list)
    url: str
    size: str = "unknown"
    created_at: datetime | None = None
    embedding: list[float] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)


class DatasetResponse(BaseModel):
    id: int
    name: str
    description: str
    source: str
    tags: list[str]
    url: str
    size: str
    created_at: datetime
    score: float | None = None

    model_config = ConfigDict(from_attributes=True)


class DatasetListResponse(BaseModel):
    items: list[DatasetResponse]
    total: int


class SearchResponse(BaseModel):
    query: str
    count: int
    results: list[DatasetResponse]


@lru_cache
def get_embedding_model():
    """
    Load the sentence embedding model with caching.

    Uses all-MiniLM-L6-v2 by default (small, fast, good for semantic search).
    Model is cached so it's only loaded once per application lifetime.

    Returns:
        SentenceTransformer model instance

    Raises:
        RuntimeError if sentence-transformers package is not installed
    """
    if SentenceTransformer is None:
        raise RuntimeError("sentence-transformers is required for embedding generation")
    settings = get_settings()
    return SentenceTransformer(settings.embedding_model_name)


def generate_embeddings(items: list[dict]) -> list[list[float]]:
    """
    Generate semantic embeddings for a list of dataset records.

    Converts each dataset record's combined text into a normalized
    embedding vector for similarity search.

    Args:
        items: List of dataset dictionaries

    Returns:
        List of embedding vectors (normalized to unit length)
    """
    texts = [build_search_text(item) for item in items]
    if not texts:
        return []
    model = get_embedding_model()
    embeddings = model.encode(
        texts, convert_to_tensor=False, normalize_embeddings=True
    ).tolist()
    logger.info(
        "generated embeddings", extra={"event_data": {"count": len(embeddings)}}
    )
    return embeddings


def extract_keywords(items: list[dict], top_k: int = 5) -> list[list[str]]:
    texts = [build_search_text(item) for item in items]
    if not texts:
        return []

    vectorizer = TfidfVectorizer(stop_words="english", max_features=200)
    matrix = vectorizer.fit_transform(texts)
    feature_names = vectorizer.get_feature_names_out()

    keyword_sets: list[list[str]] = []
    for row_index in range(matrix.shape[0]):
        row = matrix.getrow(row_index).toarray().ravel()
        if row.size == 0:
            keyword_sets.append([])
            continue
        top_indices = row.argsort()[-top_k:][::-1]
        keywords = [feature_names[index] for index in top_indices if row[index] > 0]
        keyword_sets.append(keywords)
    return keyword_sets


def prepare_database_records(items: list[dict]) -> list[DatasetRecord]:
    embeddings = generate_embeddings(items)
    keyword_sets = extract_keywords(items)

    records: list[DatasetRecord] = []
    for index, item in enumerate(items):
        records.append(
            DatasetRecord(
                name=item.get("name", ""),
                description=item.get("description", ""),
                source=item.get("source", ""),
                tags=item.get("tags", []),
                url=item.get("url", ""),
                size=item.get("size", "unknown"),
                created_at=datetime.now(timezone.utc),
                embedding=embeddings[index] if index < len(embeddings) else [],
                keywords=keyword_sets[index] if index < len(keyword_sets) else [],
            )
        )
    logger.info(
        "prepared database records", extra={"event_data": {"count": len(records)}}
    )
    return records


def build_search_text(item: dict) -> str:
    tags = item.get("tags", [])
    if isinstance(tags, str):
        tag_text = tags
    else:
        tag_text = " ".join(tags)
    return " ".join(
        part
        for part in [
            item.get("name", ""),
            item.get("description", ""),
            tag_text,
            item.get("source", ""),
        ]
        if part
    )


def to_response(dataset, score: float | None = None) -> DatasetResponse:
    tag_list = (
        dataset.tags.split(",")
        if isinstance(dataset.tags, str) and dataset.tags
        else dataset.tags or []
    )
    return DatasetResponse(
        id=dataset.id,
        name=dataset.name,
        description=dataset.description,
        source=dataset.source,
        tags=tag_list,
        url=dataset.url,
        size=dataset.size,
        created_at=dataset.created_at,
        score=score,
    )
