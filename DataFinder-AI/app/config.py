"""
Configuration management for DataFinder-AI.

Loads environment variables from .env file and provides a Settings class
that holds all configuration needed for the application to run.
"""

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Settings:
    """
    Application settings loaded from environment variables.

    Covers database config, API keys, LLM settings, embedding models,
    and operational parameters for ingestion, logging, and CORS.
    """

    def __init__(self) -> None:
        # === Core Application Settings ===
        self.app_name = os.getenv("APP_NAME", "DataFinder-AI")
        self.app_env = os.getenv("APP_ENV", "development")
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        self.api_key = os.getenv("API_KEY", "change-me")

        # === Database Configuration ===
        # Supports SQLite (development) or PostgreSQL (production)
        self.database_url = os.getenv(
            "DATABASE_URL",
            f"sqlite:///{(BASE_DIR / 'data' / 'datafinder.db').as_posix()}",
        )

        # === CORS and Web Configuration ===
        self.cors_origins = os.getenv("CORS_ORIGINS", "*")

        # === Embedding Model Configuration ===
        # all-MiniLM-L6-v2: Fast, lightweight model for semantic search
        self.embedding_model_name = os.getenv(
            "EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2"
        )
        self.default_search_limit = int(os.getenv("DEFAULT_SEARCH_LIMIT", "10"))

        # === Request Handling ===
        self.request_timeout_seconds = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "15"))
        self.user_agent = os.getenv("USER_AGENT", "datafinder-ai/1.0")

        # === FAISS Vector Index Paths ===
        # These store the semantic search index and metadata
        self.faiss_index_path = os.getenv(
            "FAISS_INDEX_PATH", str(BASE_DIR / "data" / "datasets.faiss")
        )
        self.faiss_mapping_path = os.getenv(
            "FAISS_MAPPING_PATH", str(BASE_DIR / "data" / "datasets_mapping.json")
        )
        self.faiss_metadata_path = os.getenv(
            "FAISS_METADATA_PATH", str(BASE_DIR / "data" / "datasets_index_meta.json")
        )

        # === Background Ingestion Configuration ===
        # Periodically refresh the dataset catalogue from configured sources
        self.ingestion_interval_hours = int(os.getenv("INGESTION_INTERVAL_HOURS", "6"))
        self.bootstrap_query = os.getenv("BOOTSTRAP_QUERY", "machine learning")

        # === Logging Configuration ===
        self.log_dir = os.getenv("LOG_DIR", str(BASE_DIR / "logs"))
        self.log_file = os.getenv("LOG_FILE", str(Path(self.log_dir) / "app.log"))

        # === Scheduler Configuration ===
        # Enable background scheduler for periodic dataset ingestion
        self.enable_scheduler = os.getenv("ENABLE_SCHEDULER", "false").lower() == "true"
        self.enable_startup_ingestion = (
            os.getenv("ENABLE_STARTUP_INGESTION", "true").lower() == "true"
        )

        # === External API Keys (Optional) ===
        # These allow integration with additional data sources for richer datasets
        self.github_token = os.getenv("GITHUB_TOKEN", "")
        self.mendeley_api_key = os.getenv("MENDELEY_API_KEY", "")
        self.mendeley_api_secret = os.getenv("MENDELEY_API_SECRET", "")
        self.openml_api_key = os.getenv("OPENML_API_KEY", "")

        # === LLM Configuration (Groq API) ===
        # Powers conversational search and intelligent agent reasoning
        self.groq_api_key = os.getenv("GROQ_API_KEY", "")
        self.llm_model = os.getenv("LLM_MODEL", "mixtral-8x7b-32768")
        self.llm_temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))


@lru_cache
def get_settings() -> Settings:
    """
    Get or create the Settings instance with caching.

    This is called via dependency injection in FastAPI to ensure
    we only create the Settings object once per application lifetime.

    Also creates required data directories (logs/, data/) if they don't exist.
    """
    (BASE_DIR / "data").mkdir(parents=True, exist_ok=True)
    (BASE_DIR / "logs").mkdir(parents=True, exist_ok=True)
    return Settings()
