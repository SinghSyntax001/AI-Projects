# 🚀 DataFinder-AI

**Intelligent dataset discovery platform with semantic search, LLM-powered reasoning, and integration with 8 major data sources.**

[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **For beginners**: DataFinder-AI helps you discover datasets by asking questions in natural language. For advanced users: It's a production-ready semantic search engine with AI agents, circuit breakers, and Kubernetes-ready infrastructure.

---

## Table of Contents

- [What is DataFinder-AI?](#what-is-datafinder-ai)
- [Features](#features)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Production Features](#production-features)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [Contact & Support](#contact--support)

---

## What is DataFinder-AI?

DataFinder-AI is a **production-ready FastAPI backend** for discovering machine learning datasets from 8 public sources using semantic search and AI reasoning. It's designed for:

- **Data Scientists**: Find the perfect dataset for your project
- **Researchers**: Discover relevant research datasets easily
- **AI Engineers**: Build your own applications on top of this API
- **Organizations**: Deploy as an internal tool for dataset discovery

### Key Features

- **Semantic Search**: FAISS-powered vector search that understands meaning, not just keywords
- **AI Agents**: Multi-step reasoning to answer complex dataset discovery questions
- **8 Data Sources**: Kaggle, OpenML, Hugging Face, GitHub, Zenodo, UCL ML, Papers with Code, Mendeley
- **Enterprise-Ready**: Rate limiting, circuit breakers, health checks, Prometheus metrics, Kubernetes-compatible
- **Developer-Friendly**: Well-documented APIs, Docker deployment, database migrations

---

## Features

### 🔍 **Semantic Search**

- FAISS-powered vector search with embeddings
- Multi-source dataset discovery across 8 platforms
- Similarity ranking with confidence scores
- Fast (~50ms) and accurate results

### 🤖 **LLM-Powered Intelligence**

- **Conversational Chat** - Ask questions in natural language
- **Intent Detection** - AI understands what you're looking for
- **Query Refinement** - Improves vague queries automatically
- **Agentic Reasoning** - Multi-step thinking with tool invocation
- **Powered by Groq** - Fastest open-source LLM (~500ms responses)

### 📦 **8 Integrated Data Sources**

| Source               | Content                                  | Size                    |
| -------------------- | ---------------------------------------- | ----------------------- |
| **Kaggle**           | Machine learning competitions & datasets | 100,000+ datasets       |
| **OpenML**           | Curated ML datasets & benchmarks         | 50,000+ datasets        |
| **Hugging Face**     | NLP, computer vision, audio datasets     | 5,000+ datasets         |
| **GitHub**           | Dataset repositories worldwide           | 1,000,000+ repositories |
| **UCI ML**           | Classic ML datasets                      | 600+ datasets           |
| **Zenodo**           | Open research data from CERN             | 100,000+ datasets       |
| **Papers with Code** | ML research datasets                     | 10,000+ papers          |
| **Mendeley Data**    | Research data repository                 | 50,000+ datasets        |

### 🛡️ **Production-Ready Infrastructure**

| Component           | Purpose                       | Tech                        |
| ------------------- | ----------------------------- | --------------------------- |
| **Rate Limiting**   | DOS protection & cost control | slowapi (25-100 req/hr)     |
| **Circuit Breaker** | Graceful failure handling     | 8 protected services        |
| **Health Checks**   | Kubernetes orchestration      | liveness & readiness probes |
| **Metrics**         | Monitoring & alerting         | Prometheus (30+ metrics)    |
| **Migrations**      | Database schema versioning    | Alembic                     |
| **Agents**          | Intelligent reasoning         | ReAct pattern with 5 tools  |

---

## Quick Start

### Prerequisites

- Python 3.9+
- pip or conda
- API keys: Groq, Kaggle (optional for specific sources)

### Installation (5 minutes)

```bash
# Clone repository
git clone <your-repo-url>
cd DataFinder-AI

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your Groq API key and other settings

# Apply database migrations
python -c "from app.migrations import apply_migrations; apply_migrations()"

# Start the server
uvicorn app.main:app --reload --port 8000
```

Visit http://localhost:8000/docs for interactive API documentation.

### First API Call

**Simple Search:**

```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "machine learning datasets for image classification"}' \
  -H "X-API-Key: your-api-key"
```

**LLM Chat:**

```bash
curl -X POST "http://localhost:8000/chat/ask" \
  -H "Content-Type: application/json" \
  -d '{"query": "What datasets are good for computer vision?"}' \
  -H "X-API-Key: your-api-key"
```

**Agentic Reasoning (Multi-step):**

```bash
curl -X POST "http://localhost:8000/chat/agent" \
  -H "Content-Type: application/json" \
  -d '{"user_query": "Find free image datasets under 1GB with license for commercial use"}' \
  -H "X-API-Key: your-api-key"
```

### Available Endpoints

| Endpoint              | Method | Purpose                            | Rate Limit |
| --------------------- | ------ | ---------------------------------- | ---------- |
| `/search`             | POST   | Semantic search across all sources | 100/hr     |
| `/chat/ask`           | POST   | LLM-powered chat response          | 50/hr      |
| `/chat/agent`         | POST   | Multi-step agentic reasoning       | 25/hr      |
| `/chat/search-intent` | POST   | Detect intent from query           | 100/hr     |
| `/chat/refine`        | POST   | Refine/improve query               | 50/hr      |
| `/health`             | GET    | Liveness probe (K8s)               | Unlimited  |
| `/ready`              | GET    | Readiness probe (K8s)              | Unlimited  |
| `/metrics`            | GET    | Prometheus metrics                 | Unlimited  |
| `/circuit-breaker`    | GET    | Circuit breaker status             | Unlimited  |

---

## Architecture

### System Overview

```
┌─────────────────────────────────────────┐
│         Client Requests                 │
│  (Web, Mobile, API, etc)                │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│     FastAPI Application Server          │
│  (app/main.py)                          │
├─────────────────────────────────────────┤
│  Middleware:                            │
│  • Request size limiting (10MB)         │
│  • Metrics collection                   │
│  • CORS & security headers              │
│  • Rate limiting                        │
└────────┬──────────────────┬─────────────┘
         │                  │
    ┌────▼─────┐      ┌──────▼──────┐
    │ Search   │      │ LLM Chat &  │
    │ Routes   │      │ Agents      │
    │          │      │             │
    │/search   │      │/chat/ask    │
    │/datasets │      │/chat/agent  │
    └────┬─────┘      └──────┬──────┘
         │                   │
    ┌────▼───────────────────▼─────┐
    │  Core Services               │
    │  • Search Engine (FAISS)     │
    │  • LLM Service (Groq)        │
    │  • Dataset Service (DB)      │
    └────┬────────────────┬────────┘
         │                │
    ┌────▼────────┐  ┌────▼──────────┐
    │ FAISS Index │  │ PostgreSQL DB │
    │ (in-memory) │  │ (dataset meta)│
    └─────────────┘  └───────────────┘

Reliability Layer (per service):
├─ Circuit Breaker (8 protected APIs)
├─ Rate Limiter (25-100 req/hr)
├─ Health Checks (K8s probes)
├─ Metrics (Prometheus export)
└─ Graceful Degradation
```

### How It Works

**Search Request Flow:**

1. Client sends query
2. Rate limiter checks quota
3. Query converted to embeddings
4. FAISS searches vector index
5. Results ranked by similarity
6. Response returned with confidence scores

**Chat Request Flow:**

1. Client sends question
2. Rate limiter checks quota
3. Groq LLM processes question (protected by circuit breaker)
4. LLM may refine or clarify intent
5. Search performed based on refined query
6. Results explained by LLM

**Agent Request Flow:**

1. Client sends complex discovery request
2. Rate limiter checks quota (strictest: 25/hr)
3. ReAct loop begins:
   - **Think**: LLM determines next step
   - **Act**: Tool invocation (search/filter/compare)
   - **Observe**: Capture tool output
   - **Iterate**: Repeat until answer found
4. Final answer + reasoning trace returned
5. Metrics recorded (iterations, tokens, latency)

---

## Production Features

### 🏥 Health Checks

Enable Kubernetes orchestration:

```bash
# Liveness probe - Is the container running?
curl http://localhost:8000/health
# {"status": "healthy", "timestamp": "2024-03-15T10:30:00Z"}

# Readiness probe - Is it ready to serve?
curl http://localhost:8000/ready
# {"ready": true, "services": {"database": "OK", "faiss": "OK"}}
```

### 🛡️ Rate Limiting

Protects against abuse and controls costs:

```
/search              → 100 requests/hour
/chat/ask            → 50  requests/hour  (LLM call)
/chat/agent          → 25  requests/hour  (expensive multi-turn)
/chat/search-intent  → 100 requests/hour
/chat/refine         → 50  requests/hour
```

Returns `429 Too Many Requests` when limit exceeded.

### 🔌 Circuit Breaker

Prevents cascading failures from external APIs:

```bash
# Check status
curl http://localhost:8000/circuit-breaker

# Circuit states:
# CLOSED:     Normal operation
# OPEN:       Service failing, requests blocked
# HALF_OPEN:  Testing if service recovered
```

Protected services:

- Kaggle API
- OpenML API
- Hugging Face API
- GitHub API
- Zenodo API
- Mendeley Data API
- Groq LLM API

### 📊 Prometheus Metrics

30+ metrics for monitoring and alerting:

```bash
# Export metrics
curl http://localhost:8000/metrics

# Key metrics:
# - http_requests_total (by method/endpoint/status)
# - http_request_duration_seconds (latency)
# - groq_requests_total (LLM calls)
# - groq_tokens_used_total (cost tracking)
# - circuit_breaker_state (resilience monitoring)
# - db_query_duration_seconds (performance)
```

### 🗄️ Database Migrations

Manage schema changes safely:

```bash
# Apply migrations
python -c "from app.migrations import apply_migrations; apply_migrations()"

# Rollback if needed
python -c "from app.migrations import rollback_migration; rollback_migration()"

# Check migration status
python -c "from app.migrations import get_migration_history; print(get_migration_history())"
```

---

## Deployment

### Docker (Recommended for most users)

```bash
# Build image
docker build -t datafinder-ai:latest .

# Run container
docker run -p 8000:8000 \
  -e GROQ_API_KEY=your-key \
  -e DATABASE_URL=postgresql://user:pass@db:5432/datafinder \
  -v ./data:/app/data \
  datafinder-ai:latest

# Or use docker-compose for full stack
docker-compose up
```

### Kubernetes

```bash
# Create namespace
kubectl create namespace datafinder

# Apply manifests (create k8s/ directory with configs)
kubectl apply -f k8s/ -n datafinder

# Check pods
kubectl get pods -n datafinder

# View logs
kubectl logs -f deployment/datafinder-ai -n datafinder

# Enable auto-scaling
kubectl autoscale deployment datafinder-ai \
  --min=3 --max=10 --cpu-percent=70 -n datafinder
```

### Cloud Platforms

- **AWS ECS**: Use docker-compose configuration with ECS task definitions
- **GCP Cloud Run**: Push Docker image, configure environment variables
- **Azure ACI**: Deploy container group with managed identity
- **Render.com**: Connect GitHub repo, auto-deploy on push

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed cloud-specific instructions.

### Environment Variables

```env
# API Configuration
APP_ENV=production
DEBUG=false
API_KEY=your-secure-api-key-min-32-chars

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/datafinder
DATABASE_POOL_SIZE=20

# LLM (Groq)
GROQ_API_KEY=your-groq-api-key
GROQ_MODEL=mixtral-8x7b-32768

# External APIs (optional)
KAGGLE_API_KEY=your-kaggle-key
GITHUB_TOKEN=your-github-token

# Rate Limiting
RATE_LIMIT_SEARCH=100/hour
RATE_LIMIT_CHAT=50/hour
RATE_LIMIT_AGENT=25/hour

# Server
HOST=0.0.0.0
PORT=8000
WORKERS=4
```

### Monitoring Stack

Set up monitoring (optional but recommended for production):

```bash
# Prometheus (metrics collection)
docker run -d -p 9090:9090 \
  -v prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus

# Grafana (visualization)
docker run -d -p 3000:3000 grafana/grafana

# Create dashboards for:
# - Request volume and latency
# - LLM token usage and costs
# - Circuit breaker states
# - Data source availability
```

---

## Contributing

We welcome contributions from everyone! Whether you're a beginner or experienced developer:

### For Beginners

1. **Fork** this repository
2. **Create** a feature branch: `git checkout -b feature/your-feature-name`
3. **Make** your changes
4. **Test** locally: `pytest tests/`
5. **Push** to your fork: `git push origin feature/your-feature-name`
6. **Create** a Pull Request with description of what you changed and why

### Code Style

- **Comments**: Write comments as if explaining to a colleague (not over-documented)
- **Code**: Keep code minimal and necessary for the feature (no bloat, no "just in case" code)
- **Functions**: Use clear names, docstrings for purpose, not implementation details
- **Tests**: Write tests for new features

Example of good code with human-like comments:

```python
# Check if user has hit their rate limit
if user_request_count > rate_limit:
    raise RateLimitExceeded(
        f"You've made {user_request_count} requests. "
        f"Limit is {rate_limit} per hour."
    )
```

### Areas We Need Help With

- [ ] Frontend UI for dataset discovery (React/Vue/Svelte)
- [ ] Additional data source integrations
- [ ] Performance optimization and benchmarking
- [ ] Kubernetes manifests and Helm charts
- [ ] Documentation improvements
- [ ] Bug fixes and feature requests from issues

### Making a Pull Request

When creating a PR:

1. **Title**: Brief, clear description (e.g., "Add Hugging Face dataset filtering")
2. **Description**:
   - What problem does this solve?
   - How did you test it?
   - Any breaking changes?
3. **Code**: Follow the style guide above
4. **Tests**: Include tests for new features
5. **Documentation**: Update README if adding new features

### Reporting Issues

- **Bug**: Include steps to reproduce, expected vs actual behavior
- **Feature Request**: Explain the use case and how it helps
- **Question**: Check existing issues/docs first

---

## Technical Stack

| Component            | Technology                    | Purpose             |
| -------------------- | ----------------------------- | ------------------- |
| **Framework**        | FastAPI                       | REST API server     |
| **Search**           | FAISS + sentence-transformers | Semantic similarity |
| **LLM**              | Groq API                      | AI reasoning        |
| **Database**         | PostgreSQL / SQLite           | Dataset metadata    |
| **Monitoring**       | Prometheus                    | Metrics export      |
| **Resilience**       | pybreaker                     | Circuit breakers    |
| **Rate Limiting**    | slowapi                       | DOS protection      |
| **Migrations**       | Alembic                       | Schema versioning   |
| **Containerization** | Docker                        | Deployment          |
| **Orchestration**    | Kubernetes                    | Scaling (optional)  |

---

## Performance Metrics

Typical performance under normal load:

| Operation                 | Latency    | Throughput           |
| ------------------------- | ---------- | -------------------- |
| Semantic search           | ~50ms      | 1000-5000 QPS        |
| LLM chat response         | ~500ms     | 100-500 QPS          |
| Agent reasoning (3 steps) | ~2 seconds | 25-50 QPS            |
| Health check              | <5ms       | 10000 QPS            |
| Data source fallback      | <100ms     | Automatic on failure |

---

## Troubleshooting

### Common Issues

**Q: "Port 8000 already in use"**

```bash
# Find what's using it
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill the process or use different port
uvicorn app.main:app --port 8001
```

**Q: "GROQ_API_KEY not found"**

```bash
# Make sure .env file exists and has your key
cat .env | grep GROQ_API_KEY

# If not, set it:
export GROQ_API_KEY=your-key-here
```

**Q: "Database connection refused"**

```bash
# Check if PostgreSQL is running
psql -h localhost -U postgres -d datafinder

# Or use SQLite for development
DATABASE_URL=sqlite:///./datafinder.db
```

**Q: "Rate limit errors during development"**

```bash
# Disable rate limiting for local testing (in .env)
DEBUG=true  # Automatically disables rate limiting in dev
```

### Getting Help

1. **Check** existing [GitHub Issues](issues)
2. **Search** in documentation (README.md, DEPLOYMENT.md)
3. **Ask** in discussions or open a new issue
4. **Contact** maintainer: see below

---

## Contact & Support

### Questions & Feedback

- **GitHub Issues**: Report bugs or request features
- **Discussions**: Ask questions and connect with community
- **Email**: [your-email@example.com](mailto:your-email@example.com)

### For Your Own Project

If you're building something with DataFinder-AI:

1. **Fork & Customize**: This repo is MIT licensed, freely use and modify
2. **Deploy**: Follow deployment guide for your cloud provider
3. **Integrate**: Use API endpoints in your application
4. **Extend**: Add your own data sources or features
5. **Share**: We'd love to hear what you build! Open an issue to showcase it

### Want to Contribute?

1. Read [CONTRIBUTING.md](CONTRIBUTING.md)
2. Pick an issue or feature to work on
3. Make sure your code is clean and well-commented
4. Submit PR with clear description

---

## License

MIT License - See [LICENSE](LICENSE) file for details. Use freely, modify as needed, just include original copyright notice.

## Quick Reference

### Health & Monitoring

```bash
# Is it running?
curl http://localhost:8000/health

# Is it ready?
curl http://localhost:8000/ready

# Get metrics
curl http://localhost:8000/metrics

# Check circuit breaker
curl http://localhost:8000/circuit-breaker
```

### Search & Chat

```bash
# Search datasets
curl -X POST http://localhost:8000/search \
  -d '{"query": "machine learning"}' \
  -H "X-API-Key: your-key"

# Chat with AI
curl -X POST http://localhost:8000/chat/ask \
  -d '{"query": "What datasets for NLP?"}' \
  -H "X-API-Key: your-key"

# Multi-step reasoning
curl -X POST http://localhost:8000/chat/agent \
  -d '{"user_query": "Free image datasets under 1GB"}' \
  -H "X-API-Key: your-key"
```

### Database

```bash
# Apply migrations
python -c "from app.migrations import apply_migrations; apply_migrations()"

# Rollback
python -c "from app.migrations import rollback_migration; rollback_migration()"
```

### Environment

```bash
# Copy template
cp .env.example .env

# Set your keys
export GROQ_API_KEY=your-key
export DATABASE_URL=postgresql://...
```

---

**Made with ❤️ by the DataFinder-AI community**
└──────────┬──────────┘
│
┌──────────▼──────────┐
│ Data Layer │
│ │
│ • SQLAlchemy ORM │
│ • SQLite/PostgreSQL │
│ • FAISS Indices │
└─────────────────────┘

````

---

## 🚀 Quick Start

### 1. **Clone & Setup**

```bash
git clone https://github.com/yourusername/DataFinder-AI.git
cd DataFinder-AI
pip install -r requirements.txt
````

### 2. **Configure Environment**

```bash
cp .env.example .env
# Edit .env and add your API keys (see Configuration section)
```

### 3. **Start Server**

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. **Test It**

```bash
# In another terminal
python test_llm_features.py
```

### 5. **Access API**

- **API Docs**: http://localhost:8000/docs
- **Traditional Search**: `GET http://localhost:8000/search?q=machine+learning`
- **Chat**: `POST http://localhost:8000/api/v1/chat/ask`

---

## ⚙️ Configuration

### Environment Variables

Create `.env` file with these variables:

```env
# ===== Core Settings =====
API_KEY=your-secret-api-key-here
APP_ENV=development
DEBUG=false

# ===== Database =====
DATABASE_URL=sqlite:///data/datafinder.db
# For production: DATABASE_URL=postgresql://user:password@localhost:5432/datafinder

# ===== Data Source Credentials =====
# Required: Already configured if you have kaggle.json in ~/.kaggle/

# Highly Recommended (Get from https://github.com/settings/tokens)
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx

# Optional (Get from https://www.openml.org/api)
OPENML_API_KEY=

# Optional (From https://dev.mendeley.com/)
MENDELEY_API_KEY=
MENDELEY_API_SECRET=

# ===== LLM Configuration =====
# Get key from: https://console.groq.com/keys
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx

# LLM Model (default is best balance)
# Options: mixtral-8x7b-32768, llama-3-70b-8192, llama-3-8b-8192, gemma-7b-it
LLM_MODEL=mixtral-8x7b-32768

# Temperature for LLM (0.0=deterministic, 1.0=creative)
LLM_TEMPERATURE=0.7

# ===== Search Settings =====
EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2
DEFAULT_SEARCH_LIMIT=10

# ===== Ingestion Settings =====
INGESTION_INTERVAL_HOURS=6
BOOTSTRAP_QUERY=machine learning
ENABLE_SCHEDULER=false
ENABLE_STARTUP_INGESTION=true
```

---

## 📚 API Endpoints

### **Traditional Search Endpoints**

All endpoints require `Authorization: Bearer YOUR_API_KEY` header (except `/health`).

#### Health Check

```bash
GET /health
```

Returns server status.

#### Search Datasets

```bash
GET /search?q=<query>&limit=10
```

Semantic search across all 8 data sources.

**Example:**

```bash
curl -H "Authorization: Bearer your-api-key" \
  "http://localhost:8000/search?q=image+classification&limit=10"
```

#### Browse Datasets

```bash
GET /datasets
GET /datasets/{id}
```

Browse available datasets.

---

### **🤖 LLM-Powered Chat Endpoints (NEW!)**

All chat endpoints require authentication.

#### 1. Conversational Chat

```bash
POST /api/v1/chat/ask
Content-Type: application/json

{
  "message": "I need datasets for building a recommendation system"
}
```

**Response:**

```json
{
  "message": "Based on your need for recommendation systems, I'd suggest looking for datasets with user-item interactions...",
  "reasoning": null,
  "tools_used": [],
  "follow_up_suggestions": [...]
}
```

#### 2. Intent-Based Search

```bash
POST /api/v1/chat/search-intent
Content-Type: application/json

{
  "query": "Building a medical imaging classifier",
  "limit": 10
}
```

**Response:**

```json
{
  "query": "Building a medical imaging classifier",
  "refined_query": "medical imaging classification datasets",
  "intent": "search",
  "datasets": [...],
  "explanation": "These datasets are ideal because they contain labeled medical images..."
}
```

#### 3. Search Refinement

```bash
POST /api/v1/chat/refine?query=ml+datasets&feedback=too+many+results
```

Refine search based on user feedback with LLM assistance.

#### 4. Conversation History

```bash
GET /api/v1/chat/history
```

Get current conversation history.

#### 5. Reset Conversation

```bash
POST /api/v1/chat/reset
```

Clear conversation history and start fresh.

#### 6. LLM Health Status

```bash
GET /api/v1/chat/health
```

Check if LLM service is functional.

---

## 📊 Data Sources

### Overview

| Source           | # Datasets | Auth Required  | Setup Time | API Type |
| ---------------- | ---------- | -------------- | ---------- | -------- |
| Kaggle           | 100,000+   | ✅ Yes         | 5 min      | Library  |
| UCI ML           | 1,000+     | ❌ No          | 0 min      | Library  |
| Hugging Face     | 50,000+    | ❌ No          | 0 min      | Library  |
| OpenML           | 50,000+    | ⭐ Optional    | 2 min      | Library  |
| GitHub           | ∞          | ⭐ Recommended | 2 min      | Library  |
| Zenodo           | 15 million | ❌ No          | 0 min      | REST API |
| Papers with Code | 10,000+    | ❌ No          | 0 min      | REST API |
| Mendeley Data    | 1 million  | ⭐ Optional    | 3 min      | REST API |

### Setup Instructions

**Kaggle (Pre-configured)**

- Download credentials: https://www.kaggle.com/account/api
- Place `kaggle.json` in `~/.kaggle/` directory
- Windows: `C:\Users\<YourUsername>\.kaggle\kaggle.json`

**GitHub (Recommended)**

- Create token: https://github.com/settings/tokens
- Add to `.env`: `GITHUB_TOKEN=ghp_xxxx`
- Benefit: 5,000 requests/hour vs 60 without token

**OpenML (Optional)**

- Create account: https://www.openml.org
- Generate API key
- Add to `.env`: `OPENML_API_KEY=xxxx`

**Mendeley Data (Optional)**

- Register with Mendeley API: https://dev.mendeley.com
- Add credentials to `.env`

**HuggingFace, UCI, Zenodo, Papers with Code**

- No authentication required!

---

## 🧪 Testing

### Quick Test

```bash
python test_llm_features.py
```

This comprehensive test suite validates:

- ✅ LLM health check
- ✅ Chat functionality
- ✅ Intent extraction
- ✅ Search refinement
- ✅ Conversation history
- ✅ All API endpoints

### Manual Testing

#### Test Traditional Search

```bash
curl -H "Authorization: Bearer your-api-key" \
  "http://localhost:8000/search?q=neural+networks"
```

#### Test Chat

```bash
curl -X POST http://localhost:8000/api/v1/chat/ask \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"message": "What datasets are good for NLP?"}'
```

#### Test Intent-Based Search

```bash
curl -X POST http://localhost:8000/api/v1/chat/search-intent \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"query": "Time series forecasting", "limit": 10}'
```

### Unit Tests

```bash
pytest
```

---

## 📦 Tech Stack

### Backend

- **FastAPI** 0.115+ - Modern Python web framework
- **SQLAlchemy** 2.0+ - ORM and database toolkit
- **Pydantic** 2.8+ - Data validation

### Search & ML

- **Sentence Transformers** 3.0+ - Text embeddings
- **FAISS** 1.8+ - Vector similarity search (CPU)
- **scikit-learn** 1.5+ - ML utilities

### LLM (NEW!)

- **Groq** 0.4+ - Fast open-source LLM API
- **Mixtral** - Default model (fast + accurate)

### Data Sources

- **Kaggle** API - Largest dataset platform
- **ucimlrepo** - UCI ML Repository
- **huggingface-hub** - Hugging Face datasets
- **openml** - OpenML platform
- **PyGithub** - GitHub API
- **requests** - HTTP client for REST APIs

### Data & Storage

- **SQLite** - Development database
- **PostgreSQL** - Production database
- **JSON** - Configuration and metadata

### DevOps

- **Docker** & **Docker Compose** - Containerization
- **Uvicorn** - ASGI server
- **APScheduler** - Background task scheduling

### Testing & Logging

- **Pytest** - Unit testing
- **Structured logging** - JSON logs

---

## 🐳 Docker

### Development

```bash
docker build -t datafinder-ai .
docker run -p 8000:8000 \
  -e GROQ_API_KEY=your_key \
  -e API_KEY=your_api_key \
  datafinder-ai
```

### Production with PostgreSQL

```bash
docker compose up --build
```

The `docker-compose.yml` sets up:

- FastAPI backend
- PostgreSQL database
- Adminer for database management

---

## 🚀 Deployment

### Render

1. Create new Web Service from repository
2. Set start command: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
3. Add environment variables: `API_KEY`, `GROQ_API_KEY`, `DATABASE_URL`, `GITHUB_TOKEN`
4. Deploy!

### Railway

1. Create project from repository
2. Provision PostgreSQL service
3. Set `DATABASE_URL` environment variable
4. Deploy FastAPI app

### Fly.io

1. Install Fly CLI
2. Run `fly launch`
3. Set secrets: `fly secrets set GROQ_API_KEY=xxx`
4. Deploy: `fly deploy`

### AWS, Azure, GCP

Deploy as containerized application with environment variables for API keys and database URL.

---

## 🔄 How It Works

### Traditional Search Flow

```
1. User Query
    ↓
2. Convert to Embedding (sentence-transformers)
    ↓
3. Vector Similarity Search (FAISS)
    ↓
4. Rank Results
    ↓
5. Return Top K Datasets
```

### NEW: LLM-Enhanced Search Flow

```
1. User Query
    ↓
2. LLM Intent Extraction (Groq)
    ↓
3. Query Refinement
    ↓
4. Convert to Embedding
    ↓
5. Vector Similarity Search (FAISS)
    ↓
6. LLM Result Explanation
    ↓
7. Return Results + Explanation
```

### Data Ingestion Pipeline

```
1. Fetch from 8 Sources (parallel)
    ↓
2. Clean & Normalize (remove duplicates, standardize fields)
    ↓
3. Transform (extract embeddings, prepare records)
    ↓
4. Store in Database (SQLAlchemy)
    ↓
5. Build FAISS Index
    ↓
6. Persist Index to Disk
```

---

## 📊 Performance

- **Chat Response Time**: ~500ms (Groq is fast!)
- **Intent Extraction**: ~300ms
- **Semantic Search**: ~50ms (FAISS - unchanged)
- **Full LLM Pipeline**: ~850ms average
- **Throughput**: >1,000 requests/hour
- **Ingestion Speed**: All 8 sources simultaneously

---

## 🔐 Security

- ✅ API key authentication on all endpoints
- ✅ CORS protection
- ✅ Input validation with Pydantic
- ✅ No sensitive data in logs
- ✅ Groq API calls server-side (keys never exposed)
- ✅ Environment variable configuration

---

## 🐛 Troubleshooting

### LLM Service Not Responding

```bash
# Check Groq API key
echo $GROQ_API_KEY

# Check LLM health
curl http://localhost:8000/api/v1/chat/health \
  -H "Authorization: Bearer your-api-key"

# View logs
tail -f logs/app.log
```

### Search Returning No Results

- Check if data has been ingested: `GET /datasets`
- FAISS index may need rebuilding after adding new data
- Verify database connectivity

### High Response Times

- Switch to faster LLM model: `LLM_MODEL=gemma-7b-it`
- Check network latency to Groq
- Reduce `DEFAULT_SEARCH_LIMIT`

### Database Errors

- Verify `DATABASE_URL` is correct
- For PostgreSQL: ensure server is running
- Reset SQLite: delete `data/datafinder.db`

### API Key Authentication Failing

```bash
# Must use Bearer token format
curl -H "Authorization: Bearer YOUR_ACTUAL_API_KEY" http://localhost:8000/search?q=test

# API_KEY in .env must match the one you use in Authorization header
```

---

## 📖 Documentation

- **API Docs** (interactive): http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **LLM Features**: See [LLM integration guide](#llm-integration)

---

## 🎓 Usage Examples

### Python

```python
import requests

API_KEY = "your-api-key"
headers = {"Authorization": f"Bearer {API_KEY}"}

# Traditional search
response = requests.get(
    "http://localhost:8000/search",
    params={"q": "neural networks", "limit": 10},
    headers=headers
)
datasets = response.json()["results"]

# Intelligent chat
response = requests.post(
    "http://localhost:8000/api/v1/chat/ask",
    headers=headers,
    json={"message": "I need time series data"}
)
print(response.json()["message"])

# Intent-based search
response = requests.post(
    "http://localhost:8000/api/v1/chat/search-intent",
    headers=headers,
    json={"query": "Medical imaging datasets", "limit": 10}
)
data = response.json()
print(f"Intent: {data['intent']}")
print(f"Explanation: {data['explanation']}")
```

### JavaScript/React

```javascript
const API_KEY = "your-api-key";

// Search datasets
const response = await fetch("http://localhost:8000/search?q=ml", {
  headers: { Authorization: `Bearer ${API_KEY}` },
});
const datasets = await response.json();

// Chat with AI
const chatResponse = await fetch("http://localhost:8000/api/v1/chat/ask", {
  method: "POST",
  headers: {
    Authorization: `Bearer ${API_KEY}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({ message: "What datasets for NLP?" }),
});
const chat = await chatResponse.json();
console.log(chat.message);
```

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Areas for Contribution

- Frontend UI (React/Vue component)
- Additional data source connectors
- LLM prompt optimization
- Performance improvements
- Documentation improvements

---

## 📝 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙋 Support & Questions

- **Issues**: Create a GitHub issue for bugs or feature requests
- **Discussions**: Use GitHub Discussions for questions
- **Documentation**: See full docs in this README

---

## 🌟 What Makes This Special

| Feature              | Value                                                                         |
| -------------------- | ----------------------------------------------------------------------------- |
| **Data Sources**     | 8 integrated sources (Kaggle, UCI, HF, OpenML, GitHub, Zenodo, PWC, Mendeley) |
| **LLM Intelligence** | Natural language understanding with Groq (not just keyword matching)          |
| **Speed**            | Groq API: ~500ms response, FAISS: ~50ms search                                |
| **Ease of Use**      | Chat API makes dataset discovery conversational                               |
| **Production Ready** | Docker, logging, error handling, monitoring                                   |
| **Extensible**       | Add new sources and tools easily                                              |
| **Open Source**      | MIT licensed, fully self-hostable                                             |

---

## 📈 Roadmap

- [ ] Frontend UI (React + beautiful design)
- [ ] Dataset comparison tool
- [ ] Custom tool development for specific workflows
- [ ] Fine-tuning LLM on domain-specific data
- [ ] RAG implementation for better explanations
- [ ] Mobile app
- [ ] Analytics dashboard
- [ ] Advanced filtering and faceted search

---

## 🚀 Get Started Now!

```bash
# Clone
git clone https://github.com/yourusername/DataFinder-AI.git
cd DataFinder-AI

# Setup
cp .env.example .env
# Edit .env with your API keys

# Run
python -m uvicorn app.main:app --reload

# Test
python test_llm_features.py

# Visit
http://localhost:8000/docs
```

---

**Built with ❤️ using FastAPI, FAISS, and Groq LLM**

_Making dataset discovery intelligent, conversational, and effortless._
