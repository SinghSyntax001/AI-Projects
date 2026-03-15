from __future__ import annotations

import json
import logging
from pathlib import Path
from threading import Lock

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.database.models import Dataset
from app.pipeline.clean import clean_datasets
from app.pipeline.ingest import DatasetIngestor
from app.pipeline.transform import build_search_text, get_embedding_model, prepare_database_records, to_response

try:
    import faiss
except ImportError:  # pragma: no cover
    faiss = None


logger = logging.getLogger("datafinder.search")


class SearchService:
    _index_lock = Lock()

    def __init__(self, db: Session, settings: Settings):
        self.db = db
        self.settings = settings
        self.ingestor = DatasetIngestor(settings)
        self.model = get_embedding_model()
        self.index_path = Path(settings.faiss_index_path)
        self.mapping_path = Path(settings.faiss_mapping_path)
        self.metadata_path = Path(settings.faiss_metadata_path)
        self.embedding_dimension = int(self.model.get_sentence_embedding_dimension())

    def search(self, query: str, limit: int | None = None) -> list[dict]:
        if self.db.scalar(select(Dataset.id).limit(1)) is None:
            self.ensure_data(query, limit, force_refresh=True)

        top_limit = min(limit or 10, 10)
        query_embedding = np.asarray(
            self.model.encode(query, convert_to_tensor=False, normalize_embeddings=True),
            dtype="float32",
        ).reshape(1, -1)

        if faiss is None:
            logger.warning("faiss dependency missing, using numpy fallback", extra={"event_data": {"query": query}})
            return self._fallback_search(query_embedding, query, top_limit)

        index, id_mapping = self.load_or_build_index()
        if index.ntotal == 0:
            return []

        scores, positions = index.search(query_embedding, top_limit)
        return self._materialize_results(scores[0], positions[0], id_mapping, query)

    def ensure_data(self, query: str, limit: int | None = None, force_refresh: bool = False) -> None:
        if not force_refresh and self.db.scalar(select(Dataset.id).limit(1)) is not None:
            return

        raw_items = self.ingestor.ingest(query, limit)
        cleaned_items = clean_datasets(raw_items)
        if not cleaned_items:
            return

        records = prepare_database_records(cleaned_items)
        changed = False
        for record in records:
            existing = self.db.scalar(select(Dataset).where(Dataset.url == record.url))
            tags = record.tags or record.keywords
            payload = {
                "name": record.name,
                "description": record.description,
                "source": record.source,
                "tags": ",".join(tags),
                "size": record.size,
                "embedding": json.dumps(record.embedding),
                "keywords": ",".join(record.keywords),
            }
            if existing:
                for key, value in payload.items():
                    setattr(existing, key, value)
            else:
                self.db.add(Dataset(url=record.url, **payload))
            changed = True

        if changed:
            self.db.commit()
            self.build_index()

    def build_index(self) -> None:
        datasets = list(self.db.scalars(select(Dataset).order_by(Dataset.id)).all())
        embeddings: list[list[float]] = []
        id_mapping: list[int] = []

        for dataset in datasets:
            embedding = self._load_embedding(dataset)
            if embedding is None:
                embedding = self.model.encode(
                    build_search_text(self._to_item(dataset)),
                    convert_to_tensor=False,
                    normalize_embeddings=True,
                ).tolist()
                dataset.embedding = json.dumps(embedding)
            embeddings.append(embedding)
            id_mapping.append(dataset.id)

        self.db.commit()

        with self._index_lock:
            self.mapping_path.write_text(json.dumps(id_mapping), encoding="utf-8")
            self.metadata_path.write_text(
                json.dumps({"count": len(id_mapping), "max_id": max(id_mapping) if id_mapping else 0}),
                encoding="utf-8",
            )

            if faiss is None:
                return

            index = faiss.IndexFlatIP(self.embedding_dimension)
            if embeddings:
                index.add(np.asarray(embeddings, dtype="float32"))
            faiss.write_index(index, str(self.index_path))

        logger.info("rebuilt search index", extra={"event_data": {"count": len(id_mapping), "faiss_enabled": faiss is not None}})

    def load_or_build_index(self):
        if faiss is None:
            raise RuntimeError("FAISS is unavailable")

        with self._index_lock:
            if self.index_path.exists() and self.mapping_path.exists() and self.metadata_path.exists():
                index = faiss.read_index(str(self.index_path))
                id_mapping = json.loads(self.mapping_path.read_text(encoding="utf-8"))
                metadata = json.loads(self.metadata_path.read_text(encoding="utf-8"))
                db_count, db_max_id = self._database_index_state()
                if index.ntotal == len(id_mapping) == metadata.get("count") == db_count and metadata.get("max_id") == db_max_id:
                    return index, id_mapping
                logger.warning(
                    "search index metadata mismatch detected",
                    extra={
                        "event_data": {
                            "index_count": int(index.ntotal),
                            "mapping_count": len(id_mapping),
                            "metadata_count": metadata.get("count"),
                            "db_count": db_count,
                            "db_max_id": db_max_id,
                        }
                    },
                )

        self.build_index()
        with self._index_lock:
            return faiss.read_index(str(self.index_path)), json.loads(self.mapping_path.read_text(encoding="utf-8"))

    def _database_index_state(self) -> tuple[int, int]:
        ids = list(self.db.scalars(select(Dataset.id).order_by(Dataset.id)).all())
        return len(ids), max(ids) if ids else 0

    def _fallback_search(self, query_embedding: np.ndarray, query: str, limit: int) -> list[dict]:
        datasets = list(self.db.scalars(select(Dataset).order_by(Dataset.id)).all())
        if not datasets:
            return []

        embeddings: list[list[float]] = []
        ids: list[int] = []
        for dataset in datasets:
            embedding = self._load_embedding(dataset)
            if embedding is None:
                continue
            embeddings.append(embedding)
            ids.append(dataset.id)

        if not embeddings:
            return []

        scores = cosine_similarity(query_embedding, np.asarray(embeddings, dtype="float32"))[0]
        order = np.argsort(scores)[::-1][:limit]
        return self._materialize_results(scores, order, ids, query)

    def _materialize_results(self, scores, positions, id_mapping, query: str) -> list[dict]:
        results: list[dict] = []
        for score, position in zip(scores, positions):
            position_int = int(position)
            if position_int < 0 or position_int >= len(id_mapping):
                continue
            dataset = self.db.get(Dataset, int(id_mapping[position_int]))
            if dataset is None:
                continue
            logger.info(
                "search query executed",
                extra={"event_data": {"query": query, "dataset_id": dataset.id, "score": float(score)}},
            )
            results.append(to_response(dataset, float(score)).model_dump())
        return results

    def _load_embedding(self, dataset: Dataset) -> list[float] | None:
        if not dataset.embedding:
            return None
        try:
            values = json.loads(dataset.embedding)
        except json.JSONDecodeError:
            return None
        if not isinstance(values, list):
            return None
        return [float(value) for value in values]

    def _to_item(self, dataset: Dataset) -> dict:
        return {
            "name": dataset.name,
            "description": dataset.description,
            "source": dataset.source,
            "tags": dataset.tags.split(",") if dataset.tags else [],
            "url": dataset.url,
            "size": dataset.size,
        }
