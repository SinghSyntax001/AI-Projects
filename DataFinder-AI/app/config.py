import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Settings:
    def __init__(self) -> None:
        self.app_name = os.getenv("APP_NAME", "DataFinder-AI")
        self.app_env = os.getenv("APP_ENV", "development")
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        self.api_key = os.getenv("API_KEY", "change-me")
        self.database_url = os.getenv(
            "DATABASE_URL",
            f"sqlite:///{(BASE_DIR / 'data' / 'datafinder.db').as_posix()}",
        )
        self.cors_origins = os.getenv("CORS_ORIGINS", "*")
        self.embedding_model_name = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
        self.default_search_limit = int(os.getenv("DEFAULT_SEARCH_LIMIT", "10"))
        self.request_timeout_seconds = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "15"))
        self.user_agent = os.getenv("USER_AGENT", "datafinder-ai/1.0")
        self.faiss_index_path = os.getenv("FAISS_INDEX_PATH", str(BASE_DIR / "data" / "datasets.faiss"))
        self.faiss_mapping_path = os.getenv("FAISS_MAPPING_PATH", str(BASE_DIR / "data" / "datasets_mapping.json"))
        self.faiss_metadata_path = os.getenv("FAISS_METADATA_PATH", str(BASE_DIR / "data" / "datasets_index_meta.json"))
        self.ingestion_interval_hours = int(os.getenv("INGESTION_INTERVAL_HOURS", "6"))
        self.bootstrap_query = os.getenv("BOOTSTRAP_QUERY", "machine learning")
        self.log_dir = os.getenv("LOG_DIR", str(BASE_DIR / "logs"))
        self.log_file = os.getenv("LOG_FILE", str(Path(self.log_dir) / "app.log"))
        self.enable_scheduler = os.getenv("ENABLE_SCHEDULER", "false").lower() == "true"
        self.enable_startup_ingestion = os.getenv("ENABLE_STARTUP_INGESTION", "true").lower() == "true"


@lru_cache
def get_settings() -> Settings:
    (BASE_DIR / "data").mkdir(parents=True, exist_ok=True)
    (BASE_DIR / "logs").mkdir(parents=True, exist_ok=True)
    return Settings()
