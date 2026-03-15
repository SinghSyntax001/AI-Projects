"""
Dataset ingestion from multiple sources with circuit breaker protection.

Integrates with 8 different data platforms:
- Kaggle: Community dataset repository
- OpenML: OpenML.org platform
- HuggingFace: ML models and datasets hub
- UCI ML: University of California ML datasets
- GitHub: Search for datasets in public repos
- Mendeley Data: Open research datasets
- Zenodo: CERN open-access repository
- Papers with Code: Datasets linked to academic papers

Uses circuit breaker pattern to gracefully handle API failures.
"""

from __future__ import annotations

import importlib
import logging
from typing import Any

import requests

from app.circuit_breaker import circuit_breaker_manager
from app.config import Settings
from app.metrics import track_external_api

# Optional data source libraries - gracefully handle if not installed
try:
    from huggingface_hub import list_datasets
except ImportError:  # pragma: no cover
    list_datasets = None

try:
    from ucimlrepo import list_available_datasets
except ImportError:  # pragma: no cover
    list_available_datasets = None

try:
    from github import Github
except ImportError:  # pragma: no cover
    Github = None

try:
    import openml
except ImportError:  # pragma: no cover
    openml = None


logger = logging.getLogger("datafinder.pipeline.ingest")


class DatasetIngestor:
    """
    Fetches datasets from multiple sources and standardizes them.

    Handles API authentication, pagination, and error handling
    for each source independently.
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self.session = requests.Session()
        # Set user agent to identify our requests (required by some APIs)
        self.session.headers.update({"User-Agent": self.settings.user_agent})

    def ingest(self, query: str, limit: int | None = None) -> list[dict[str, Any]]:
        """
        Run ingestion pipeline across all data sources with circuit breaker protection.

        Fetches datasets matching the query from all available sources,
        aggregates them, and returns combined list. Gracefully handles
        failing sources via circuit breaker pattern.

        Args:
            query: Search query to use across all sources
            limit: Max results per source

        Returns:
            List of standardized dataset dictionaries
        """
        max_results = limit or self.settings.default_search_limit
        logger.info(
            "starting ingestion",
            extra={"event_data": {"query": query, "limit": max_results}},
        )
        items: list[dict[str, Any]] = []

        # Use circuit breakers to prevent cascading failures
        try:
            items.extend(
                circuit_breaker_manager.call(
                    "kaggle", self.fetch_kaggle_metadata, query, max_results
                )
            )
        except Exception as e:
            logger.warning(f"Kaggle source unavailable: {e}")

        try:
            items.extend(
                circuit_breaker_manager.call(
                    "openml", self.fetch_openml_metadata, query, max_results
                )
            )
        except Exception as e:
            logger.warning(f"OpenML source unavailable: {e}")

        try:
            items.extend(
                circuit_breaker_manager.call(
                    "huggingface", self.fetch_huggingface_metadata, query, max_results
                )
            )
        except Exception as e:
            logger.warning(f"HuggingFace source unavailable: {e}")

        try:
            items.extend(self.fetch_uci_metadata(query, max_results))
        except Exception as e:
            logger.warning(f"UCI ML source unavailable: {e}")

        try:
            items.extend(
                circuit_breaker_manager.call(
                    "github", self.fetch_github_datasets, query, max_results
                )
            )
        except Exception as e:
            logger.warning(f"GitHub source unavailable: {e}")

        try:
            items.extend(
                circuit_breaker_manager.call(
                    "zenodo", self.fetch_zenodo_datasets, query, max_results
                )
            )
        except Exception as e:
            logger.warning(f"Zenodo source unavailable: {e}")

        try:
            items.extend(self.fetch_papers_with_code_datasets(query, max_results))
        except Exception as e:
            logger.warning(f"Papers with Code source unavailable: {e}")

        logger.info(
            "completed ingestion",
            extra={"event_data": {"query": query, "count": len(items)}},
        )
        return items

    def fetch_huggingface_metadata(
        self, query: str, limit: int
    ) -> list[dict[str, Any]]:
        if list_datasets is None:
            logger.warning(
                "huggingface dependency missing",
                extra={"event_data": {"source": "huggingface"}},
            )
            return []

        try:
            datasets = list(list_datasets(search=query, limit=limit))
        except Exception:
            logger.exception(
                "huggingface ingestion failed",
                extra={"event_data": {"query": query, "source": "huggingface"}},
            )
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
            logger.exception(
                "kaggle ingestion failed",
                extra={"event_data": {"query": query, "source": "kaggle"}},
            )
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
            logger.warning(
                "uci dependency missing", extra={"event_data": {"source": "uci"}}
            )
            return []

        try:
            datasets = list_available_datasets(search=query)
        except Exception:
            logger.exception(
                "uci ingestion failed",
                extra={"event_data": {"query": query, "source": "uci"}},
            )
            return []

        if not datasets:
            logger.info(
                "uci returned no datasets",
                extra={"event_data": {"query": query, "source": "uci"}},
            )
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

    def fetch_openml_metadata(self, query: str, limit: int) -> list[dict[str, Any]]:
        """Fetch datasets from OpenML (open machine learning platform)."""
        try:
            import openml

            # Set API key if available
            if self.settings.openml_api_key:
                openml.config.apikey = self.settings.openml_api_key

            # Search for datasets
            datasets_list = openml.datasets.list_datasets(output_format="dataframe")

            # Filter by query in name or description
            query_lower = query.lower()
            filtered = datasets_list[
                datasets_list["name"].str.lower().str.contains(query_lower, na=False)
                | datasets_list["description"]
                .str.lower()
                .str.contains(query_lower, na=False)
            ]

            results: list[dict[str, Any]] = []
            for _, row in filtered.head(limit).iterrows():
                results.append(
                    {
                        "name": str(row.get("name", "Unknown")),
                        "description": str(row.get("description", ""))
                        or "OpenML dataset",
                        "source": "openml",
                        "tags": [query, "openml", str(row.get("quality", ""))],
                        "url": f"https://www.openml.org/d/{row.get('did', '')}",
                        "size": str(row.get("NumberOfInstances", "unknown")),
                    }
                )

            logger.info(
                "openml ingestion completed",
                extra={
                    "event_data": {
                        "query": query,
                        "source": "openml",
                        "count": len(results),
                    }
                },
            )
            return results
        except Exception:
            logger.exception(
                "openml ingestion failed",
                extra={"event_data": {"query": query, "source": "openml"}},
            )
            return []

    def fetch_github_datasets(self, query: str, limit: int) -> list[dict[str, Any]]:
        """Fetch datasets from GitHub repositories."""
        try:
            from github import Github

            results: list[dict[str, Any]] = []

            # Search for repositories with dataset files
            search_queries = [
                f"{query} filename:dataset.csv",
                f"{query} filename:data.csv",
                f"{query} filename:datasets.json",
                f"{query} topic:dataset",
            ]

            github = None
            if self.settings.github_token:
                github = Github(self.settings.github_token)
            else:
                github = Github()  # Use unauthenticated access (rate-limited)

            for search_query in search_queries:
                if len(results) >= limit:
                    break

                try:
                    repos = github.search_repositories(
                        query=search_query, sort="stars", order="desc"
                    )

                    for repo in repos[: max(1, limit - len(results))]:
                        results.append(
                            {
                                "name": f"{repo.full_name} - {repo.name}",
                                "description": repo.description
                                or f"GitHub repository with {query} datasets",
                                "source": "github",
                                "tags": [query, "github", repo.language or "code"],
                                "url": repo.html_url,
                                "size": f"{repo.size}KB" if repo.size else "unknown",
                            }
                        )
                except Exception:
                    continue

            logger.info(
                "github ingestion completed",
                extra={
                    "event_data": {
                        "query": query,
                        "source": "github",
                        "count": len(results),
                    }
                },
            )
            return results
        except Exception:
            logger.exception(
                "github ingestion failed",
                extra={"event_data": {"query": query, "source": "github"}},
            )
            return []

    def fetch_zenodo_datasets(self, query: str, limit: int) -> list[dict[str, Any]]:
        """Fetch datasets from Zenodo (open research repository)."""
        try:
            results: list[dict[str, Any]] = []

            # Zenodo API endpoint
            zenodo_url = "https://zenodo.org/api/records"
            params = {
                "q": f"({query}) AND resourcetype:dataset",
                "sort": "-mostrecent",
                "size": limit,
                "all_versions": False,
            }

            response = self.session.get(
                zenodo_url, params=params, timeout=self.settings.request_timeout_seconds
            )
            response.raise_for_status()
            data = response.json()

            for record in data.get("hits", {}).get("hits", [])[:limit]:
                creators = record.get("metadata", {}).get("creators", [])
                creator_names = [
                    c.get("name", "") for c in creators if isinstance(c, dict)
                ]

                results.append(
                    {
                        "name": record.get("metadata", {}).get("title", "Unknown"),
                        "description": record.get("metadata", {}).get(
                            "description", "Zenodo research dataset"
                        ),
                        "source": "zenodo",
                        "tags": [query, "zenodo", "open-science"]
                        + record.get("metadata", {}).get("keywords", [])[:3],
                        "url": record.get("links", {}).get("html", ""),
                        "size": f"{record.get('metadata', {}).get('imprint_place', 'N/A')}",
                    }
                )

            logger.info(
                "zenodo ingestion completed",
                extra={
                    "event_data": {
                        "query": query,
                        "source": "zenodo",
                        "count": len(results),
                    }
                },
            )
            return results
        except Exception:
            logger.exception(
                "zenodo ingestion failed",
                extra={"event_data": {"query": query, "source": "zenodo"}},
            )
            return []

    def fetch_papers_with_code_datasets(
        self, query: str, limit: int
    ) -> list[dict[str, Any]]:
        """Fetch datasets from Papers with Code."""
        try:
            results: list[dict[str, Any]] = []

            # Papers with Code API endpoint
            pwc_url = "https://api.paperswithcode.com/v1/datasets"
            params = {
                "search": query,
                "sort": "trending",
            }

            response = self.session.get(
                pwc_url, params=params, timeout=self.settings.request_timeout_seconds
            )
            response.raise_for_status()
            data = response.json()

            for dataset in data.get("results", [])[:limit]:
                results.append(
                    {
                        "name": dataset.get("name", "Unknown"),
                        "description": dataset.get(
                            "description",
                            "ML/AI research dataset from Papers with Code",
                        ),
                        "source": "paperswithcode",
                        "tags": [query, "paperswithcode", "research"],
                        "url": dataset.get("url", ""),
                        "size": str(dataset.get("size", "unknown")),
                    }
                )

            logger.info(
                "paperswithcode ingestion completed",
                extra={
                    "event_data": {
                        "query": query,
                        "source": "paperswithcode",
                        "count": len(results),
                    }
                },
            )
            return results
        except Exception:
            logger.exception(
                "paperswithcode ingestion failed",
                extra={"event_data": {"query": query, "source": "paperswithcode"}},
            )
            return []

    def fetch_mendeley_datasets(self, query: str, limit: int) -> list[dict[str, Any]]:
        """Fetch datasets from Mendeley Data (research repository)."""
        try:
            results: list[dict[str, Any]] = []

            # Mendeley Data API endpoint
            mendeley_url = "https://api.mendeley.com/datasets"
            headers = {
                "Authorization": f"Bearer {self._get_mendeley_token()}",
                "Accept": "application/vnd.mendeley.api+json; charset=UTF-8",
            }

            params = {
                "q": query,
                "sort": "recent",
                "limit": limit,
            }

            response = self.session.get(
                mendeley_url,
                params=params,
                headers=headers,
                timeout=self.settings.request_timeout_seconds,
            )

            if response.status_code == 401:
                logger.warning(
                    "mendeley authentication failed - invalid token",
                    extra={"event_data": {"source": "mendeley"}},
                )
                return []

            response.raise_for_status()
            data = response.json()

            for dataset in data.get("items", [])[:limit]:
                results.append(
                    {
                        "name": dataset.get("title", "Unknown"),
                        "description": dataset.get(
                            "abstract", "Mendeley research dataset"
                        )
                        or dataset.get("description", ""),
                        "source": "mendeley",
                        "tags": [query, "mendeley", "research"],
                        "url": dataset.get("url", dataset.get("doi", "")),
                        "size": str(dataset.get("version", "unknown")),
                    }
                )

            logger.info(
                "mendeley ingestion completed",
                extra={
                    "event_data": {
                        "query": query,
                        "source": "mendeley",
                        "count": len(results),
                    }
                },
            )
            return results
        except Exception:
            logger.exception(
                "mendeley ingestion failed",
                extra={"event_data": {"query": query, "source": "mendeley"}},
            )
            return []

    def _get_mendeley_token(self) -> str:
        """Get Mendeley API authentication token."""
        if not self.settings.mendeley_api_key or not self.settings.mendeley_api_secret:
            return ""

        try:
            auth_url = "https://api.mendeley.com/oauth/authorize"
            token_url = "https://api.mendeley.com/oauth/token"

            # For production, use proper OAuth flow
            # This is a simplified version - in production use proper OAuth2 library
            return self.settings.mendeley_api_key
        except Exception:
            return ""

    def _infer_size(self, item: dict[str, Any]) -> str:
        for key in ("dataset_size", "size_categories", "downloads", "likes"):
            value = item.get(key)
            if value:
                if isinstance(value, list):
                    return ",".join(str(entry) for entry in value)
                return str(value)
        return "unknown"
