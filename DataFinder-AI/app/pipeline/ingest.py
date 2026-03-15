from __future__ import annotations

import importlib
import logging
from typing import Any

import requests

from app.config import Settings

try:
    from huggingface_hub import list_datasets
except ImportError:  # pragma: no cover
    list_datasets = None

try:
    from ucimlrepo import list_available_datasets
except ImportError:  # pragma: no cover
    list_available_datasets = None


logger = logging.getLogger("datafinder.pipeline.ingest")


class DatasetIngestor:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.settings.user_agent})

    def ingest(self, query: str, limit: int | None = None) -> list[dict[str, Any]]:
        max_results = limit or self.settings.default_search_limit
        logger.info("starting ingestion", extra={"event_data": {"query": query, "limit": max_results}})
        items: list[dict[str, Any]] = []
        items.extend(self.fetch_kaggle_metadata(query, max_results))
        items.extend(self.fetch_uci_metadata(query, max_results))
        items.extend(self.fetch_huggingface_metadata(query, max_results))
        logger.info("completed ingestion", extra={"event_data": {"query": query, "count": len(items)}})
        return items

    def fetch_huggingface_metadata(self, query: str, limit: int) -> list[dict[str, Any]]:
        if list_datasets is None:
            logger.warning("huggingface dependency missing", extra={"event_data": {"source": "huggingface"}})
            return []

        try:
            datasets = list(list_datasets(search=query, limit=limit))
        except Exception:
            logger.exception("huggingface ingestion failed", extra={"event_data": {"query": query, "source": "huggingface"}})
            return []

        results: list[dict[str, Any]] = []
        for item in datasets[:limit]:
            card_data = item.cardData or {}
            tags = [tag for tag in getattr(item, "tags", []) if isinstance(tag, str)]
            results.append(
                {
                    "name": item.id,
                    "description": card_data.get("description", "") or "",
                    "source": "huggingface",
                    "tags": tags,
                    "url": f"https://huggingface.co/datasets/{item.id}",
                    "size": self._infer_size(card_data),
                }
            )
        return results

    def fetch_kaggle_metadata(self, query: str, limit: int) -> list[dict[str, Any]]:
        try:
            kaggle_module = importlib.import_module("kaggle.api.kaggle_api_extended")
            KaggleApi = getattr(kaggle_module, "KaggleApi")
            api = KaggleApi()
            api.authenticate()
            datasets = api.dataset_list(search=query)
        except BaseException:
            logger.exception("kaggle ingestion failed", extra={"event_data": {"query": query, "source": "kaggle"}})
            return []

        results: list[dict[str, Any]] = []
        for item in datasets[:limit]:
            results.append(
                {
                    "name": getattr(item, "title", "Unknown dataset"),
                    "description": getattr(item, "subtitle", "") or "",
                    "source": "kaggle",
                    "tags": [query, "kaggle", getattr(item, "creatorName", "kaggle")],
                    "url": f"https://www.kaggle.com/datasets/{item.ref}",
                    "size": "unknown",
                }
            )
        return results

    def fetch_uci_metadata(self, query: str, limit: int) -> list[dict[str, Any]]:
        if list_available_datasets is None:
            logger.warning("uci dependency missing", extra={"event_data": {"source": "uci"}})
            return []

        try:
            datasets = list_available_datasets(search=query)
        except Exception:
            logger.exception("uci ingestion failed", extra={"event_data": {"query": query, "source": "uci"}})
            return []

        if not datasets:
            logger.info("uci returned no datasets", extra={"event_data": {"query": query, "source": "uci"}})
            return []

        results: list[dict[str, Any]] = []
        for item in datasets[:limit]:
            dataset_id = item.get("ID")
            task = item.get("Task", "")
            results.append(
                {
                    "name": item.get("Name", "Unknown dataset"),
                    "description": item.get("Abstract", "") or "",
                    "source": "uci",
                    "tags": [tag for tag in [query, "uci", task] if tag],
                    "url": f"https://archive.ics.uci.edu/dataset/{dataset_id}",
                    "size": str(item.get("Instances", "unknown")),
                }
            )
        return results

    def _infer_size(self, item: dict[str, Any]) -> str:
        for key in ("dataset_size", "size_categories", "downloads", "likes"):
            value = item.get(key)
            if value:
                if isinstance(value, list):
                    return ",".join(str(entry) for entry in value)
                return str(value)
        return "unknown"
