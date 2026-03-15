import json

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import get_settings
from app.dependencies import get_dataset_service, get_search_service
from app.database.db import Base
from app.database.models import Dataset
from app.main import app
from app.services.dataset_service import DatasetService
import app.services.search_service as search_service_module
from app.services.search_service import SearchService


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)


class FakeModel:
    def get_sentence_embedding_dimension(self):
        return 2

    def encode(self, text, convert_to_tensor=False, normalize_embeddings=True):
        if isinstance(text, list):
            return [[1.0, 0.0] if "vision" in item.lower() else [0.0, 1.0] for item in text]
        return [1.0, 0.0] if "vision" in text.lower() else [0.0, 1.0]


class FakeIngestor:
    def ingest(self, query, limit=None):
        return [
            {
                "name": "Vision Dataset",
                "description": "Images for detection",
                "source": "huggingface",
                "tags": ["vision"],
                "url": "https://example.com/datasets/vision",
                "size": "1000",
            },
            {
                "name": "Text Dataset",
                "description": "Text classification corpus",
                "source": "uci",
                "tags": ["nlp"],
                "url": "https://example.com/datasets/text",
                "size": "500",
            },
        ]


def seed_db():
    db = TestingSessionLocal()
    try:
        db.query(Dataset).delete()
        db.add(
            Dataset(
                name="Vision Dataset",
                description="Images for detection",
                source="huggingface",
                tags="vision",
                url="https://example.com/datasets/vision",
                size="1000",
                embedding=json.dumps([1.0, 0.0]),
                keywords="vision",
            )
        )
        db.add(
            Dataset(
                name="Text Dataset",
                description="Text classification corpus",
                source="uci",
                tags="nlp",
                url="https://example.com/datasets/text",
                size="500",
                embedding=json.dumps([0.0, 1.0]),
                keywords="nlp",
            )
        )
        db.commit()
    finally:
        db.close()


def get_test_search_service():
    db = TestingSessionLocal()
    search_service_module.get_embedding_model = lambda: FakeModel()
    service = SearchService(db, get_settings())
    service.model = FakeModel()
    service.ingestor = FakeIngestor()
    service.build_index()
    return service


def get_test_dataset_service():
    db = TestingSessionLocal()
    return DatasetService(db, get_settings())


seed_db()
app.dependency_overrides[get_search_service] = get_test_search_service
app.dependency_overrides[get_dataset_service] = get_test_dataset_service
client = TestClient(app)
headers = {"Authorization": "Bearer change-me"}


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_search_endpoint_requires_api_key():
    response = client.get("/search", params={"q": "vision"})
    assert response.status_code == 401


def test_search_endpoint_with_api_key():
    response = client.get("/search", params={"q": "vision"}, headers=headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] >= 1
    assert payload["results"][0]["name"] == "Vision Dataset"
    assert payload["results"][0]["score"] >= payload["results"][-1]["score"]


def test_datasets_endpoint_requires_api_key():
    response = client.get("/datasets")
    assert response.status_code == 401


def test_datasets_endpoint_with_api_key():
    response = client.get("/datasets", headers=headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 2
    assert len(payload["items"]) == 2


def test_dataset_by_id_endpoint_with_api_key():
    response = client.get("/datasets/1", headers=headers)
    assert response.status_code == 200
    assert response.json()["name"] == "Vision Dataset"
