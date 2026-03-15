# DataFinder-AI

DataFinder-AI is a FastAPI backend for discovering, normalizing, storing, and semantically searching machine learning datasets from public sources such as Kaggle, UCI, and Hugging Face.

## Project Overview

The service combines a lightweight data engineering pipeline with an API-first backend. Dataset metadata is ingested from external providers, cleaned into a consistent schema, transformed into searchable records, and exposed through secured REST endpoints.

## Architecture

```text
Client
  |
  v
FastAPI Routes
  |
  v
Services
  |-- Search Service
  |-- Dataset Service
  |
  v
Pipeline
  |-- Ingest
  |-- Clean
  |-- Transform
  |
  v
SQLAlchemy
  |
  v
SQLite / PostgreSQL
```

## Features

- FastAPI server with CORS enabled
- API key authentication using `Authorization: Bearer <API_KEY>`
- Dataset ingestion from Kaggle, UCI, and Hugging Face
- Cleaning pipeline for duplicate removal, tag normalization, and null-field pruning
- Semantic search with `sentence-transformers` and a persisted FAISS vector index
- SQLAlchemy database layer with SQLite by default and PostgreSQL support in Docker Compose
- Background ingestion every 6 hours with APScheduler
- Structured JSON logging for API requests and pipeline runs
- Health check and OpenAPI docs

## Tech Stack

- FastAPI
- SQLAlchemy
- Sentence Transformers
- FAISS
- scikit-learn
- SQLite
- PostgreSQL
- Docker
- Pytest

## API Endpoints

- `GET /health`
- `GET /search?q=<query>`
- `GET /datasets`
- `GET /datasets/{id}`

All endpoints except `/health` require a bearer token.

## Local Development

1. Install dependencies.

```bash
pip install -r requirements.txt
```

2. Create a `.env` file in the project root.

```env
API_KEY=change-me
DATABASE_URL=sqlite:///data/datafinder.db
APP_ENV=development
```

3. Run the API.

```bash
uvicorn app.main:app --reload
```

4. Open the docs.

```text
http://localhost:8000/docs
```

The search endpoint returns semantically ranked datasets with similarity scores, source, and dataset links.

## Docker

Build and run with Docker:

```bash
docker build -t datafinder-ai .
docker run -p 8000:8000 -e API_KEY=change-me datafinder-ai
```

Run the app with PostgreSQL using Docker Compose:

```bash
docker compose up --build
```

## Observability

- Request logs are written as JSON to `logs/app.log`
- Ingestion runs and search queries are logged for troubleshooting
- The FAISS index is persisted under `data/` and reloaded on restart

## Deployment

### Render

- Create a new Web Service from the repository
- Set the start command to `uvicorn app.main:app --host 0.0.0.0 --port 8000`
- Add environment variables such as `API_KEY` and `DATABASE_URL`

### Railway

- Create a new project from the repository
- Provision a PostgreSQL service
- Set `DATABASE_URL` and deploy the FastAPI app

### Fly.io

- Install the Fly CLI and run `fly launch`
- Set secrets for `API_KEY` and `DATABASE_URL`
- Deploy with `fly deploy`

## Testing

```bash
pytest
```

## Suggested Commits

- `feat: add FastAPI API layer`
- `feat: add dataset ingestion pipeline`
- `feat: implement semantic search`
- `feat: dockerize application`
