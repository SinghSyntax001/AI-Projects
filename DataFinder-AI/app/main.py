"""
DataFinder-AI FastAPI Application
Entry point for the AI-powered dataset discovery platform.

This module initializes the FastAPI server with all routes, middleware,
and background services including semantic search, LLM chat, and scheduled data ingestion.
"""

from contextlib import asynccontextmanager
from datetime import datetime, timezone
import logging
from pathlib import Path
from threading import Thread
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.circuit_breaker import circuit_breaker_manager
from app.config import get_settings
from app.database.db import Base, SessionLocal, engine
from app.health import HealthChecker, HealthStatus
from app.logging_config import configure_logging
from app.metrics import app_uptime_seconds, get_metrics_text, http_requests_total
from app.routes.chat import router as chat_router
from app.routes.datasets import router as datasets_router
from app.routes.search import router as search_router
from app.services.search_service import SearchService

# APScheduler is optional - allows background scheduled dataset ingestion
try:
    from apscheduler.schedulers.background import BackgroundScheduler
except ImportError:  # pragma: no cover
    BackgroundScheduler = None


# Initialize app configuration and logging
settings = get_settings()
configure_logging(settings)
logger = logging.getLogger("datafinder.api")

# Initialize rate limiter for API endpoints
limiter = Limiter(key_func=get_remote_address)

# Initialize health checker for Kubernetes/orchestration
health_checker = HealthChecker(startup_time=datetime.now(timezone.utc))

# Initialize background scheduler for periodic dataset ingestion (if available)
scheduler = (
    BackgroundScheduler(timezone="UTC") if BackgroundScheduler is not None else None
)

# Setup UI templates and static files directory
UI_DIR = Path(__file__).resolve().parent.parent / "ui"
templates = Jinja2Templates(directory=str(UI_DIR / "templates"))


def run_ingestion_job() -> None:
    """
    Background task that periodically ingests new datasets from configured sources.

    This runs every N hours (configured via INGESTION_INTERVAL_HOURS) to keep
    the FAISS vector index fresh with new datasets from Kaggle, OpenML, GitHub, etc.
    """
    db = SessionLocal()
    try:
        service = SearchService(db, settings)
        service.ensure_data(
            settings.bootstrap_query, settings.default_search_limit, force_refresh=True
        )
        logger.info(
            "background ingestion completed",
            extra={
                "event_data": {
                    "query": settings.bootstrap_query,
                    "interval_hours": settings.ingestion_interval_hours,
                }
            },
        )
    except Exception:
        logger.exception(
            "background ingestion failed",
            extra={"event_data": {"query": settings.bootstrap_query}},
        )
    finally:
        db.close()


def start_background_ingestion() -> None:
    """
    Start the initial background ingestion task in a daemon thread.

    Runs immediately on app startup (if enabled) to populate the initial
    dataset index before any user searches come in.
    """
    Thread(target=run_ingestion_job, name="initial-ingestion", daemon=True).start()


@asynccontextmanager
async def lifespan(_: FastAPI):
    """
    FastAPI lifespan context manager for startup and shutdown events.

    Startup:
    - Creates all database tables
    - Registers health check handlers
    - Starts background dataset ingestion (if enabled)
    - Initializes scheduler for periodic ingestion (if enabled)

    Shutdown:
    - Gracefully stops the scheduler if running
    - Flushes remaining logs
    """
    # Reset startup time for accurate uptime tracking
    health_checker.startup_time = datetime.now(timezone.utc)

    # Register health check functions
    health_checker.register_check("database", lambda: check_database_health())
    health_checker.register_check("faiss_index", lambda: check_faiss_health())

    Base.metadata.create_all(bind=engine)

    if settings.enable_startup_ingestion:
        start_background_ingestion()

    if settings.enable_scheduler and scheduler is not None:
        scheduler.add_job(
            run_ingestion_job,
            "interval",
            hours=settings.ingestion_interval_hours,
            id="dataset-ingestion",
            replace_existing=True,
        )
        scheduler.start()
        logger.info(
            "scheduler started",
            extra={"event_data": {"interval_hours": settings.ingestion_interval_hours}},
        )
    elif settings.enable_scheduler:
        logger.warning("scheduler requested but APScheduler is unavailable")

    logger.info(
        "Application startup complete",
        extra={"event_data": {"environment": settings.app_env}},
    )

    yield

    logger.info("Application shutdown initiated")

    if scheduler is not None and scheduler.running:
        scheduler.shutdown(wait=False)


def check_database_health() -> bool:
    """Check if database is accessible."""
    try:
        db = SessionLocal()
        db.execute(__import__("sqlalchemy").text("SELECT 1"))
        db.close()
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


def check_faiss_health() -> bool:
    """Check if FAISS index is available."""
    try:
        from pathlib import Path
        import json

        index_path = Path(settings.faiss_index_path)
        return index_path.exists() or not settings.enable_startup_ingestion
    except Exception as e:
        logger.error(f"FAISS health check failed: {e}")
        return False


# Create FastAPI app instance with configuration
app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
    description="Production-grade dataset discovery API with semantic vector search, LLM-powered agents, and API key authentication.",
    openapi_tags=[
        {"name": "search", "description": "Semantic vector search endpoints."},
        {"name": "datasets", "description": "Dataset catalog endpoints."},
        {"name": "chat", "description": "LLM-powered chat and agent endpoints."},
        {"name": "health", "description": "Operational health and metrics endpoints."},
    ],
)

# Attach rate limiter to app
app.state.limiter = limiter


# Add exception handler for rate limit errors
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Handle rate limit exceeded errors."""
    return Response(
        content='{"detail": "Rate limit exceeded. Too many requests."}',
        status_code=429,
        media_type="application/json",
    )


# Add middleware for request size limits and metrics
@app.middleware("http")
async def max_request_size_middleware(request: Request, call_next):
    """
    Enforce maximum request body size (prevent DOS).

    Default: 10 MB max request size
    """
    MAX_REQUEST_SIZE = int(
        __import__("os").getenv("MAX_REQUEST_SIZE_MB", "10")
        ** 20  # Convert MB to bytes
    )

    if request.method in ["POST", "PUT", "PATCH"]:
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_REQUEST_SIZE:
            return Response(
                content='{"detail": "Request body too large"}',
                status_code=413,
                media_type="application/json",
            )

    return await call_next(request)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Track HTTP request metrics."""
    start = time.perf_counter()

    try:
        response = await call_next(request)
        duration = time.perf_counter() - start

        # Record metrics
        http_requests_total.labels(
            method=request.method,
            endpoint=request.url.path,
            status_code=response.status_code,
        ).inc()

        return response
    except Exception:
        duration = time.perf_counter() - start
        http_requests_total.labels(
            method=request.method, endpoint=request.url.path, status_code=500
        ).inc()
        raise


# Add exception handler for rate limit errors
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Handle rate limit exceeded errors."""
    return Response(
        content='{"detail": "Rate limit exceeded. Too many requests."}',
        status_code=429,
        media_type="application/json",
    )


# Add CORS middleware to allow requests from frontend applications
app.add_middleware(
    CORSMiddleware,
    allow_origins=(
        ["*"]
        if settings.cors_origins == "*"
        else [origin.strip() for origin in settings.cors_origins.split(",")]
    ),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (CSS, JavaScript) for the web UI
app.mount("/static", StaticFiles(directory=str(UI_DIR / "static")), name="static")

# Register API route handlers
app.include_router(search_router)  # Semantic search endpoints
app.include_router(datasets_router)  # Dataset catalog endpoints
app.include_router(chat_router)  # LLM chat and agentic discovery endpoints


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    HTTP middleware that logs all incoming requests and responses.

    Captures: request path, method, response status code, and duration (ms)
    Logs are written in JSON format for easy parsing by monitoring tools.
    """
    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.exception(
            "request failed",
            extra={
                "event_data": {
                    "path": request.url.path,
                    "method": request.method,
                    "duration_ms": duration_ms,
                }
            },
        )
        raise

    duration_ms = round((time.perf_counter() - start) * 1000, 2)
    logger.info(
        "request completed",
        extra={
            "event_data": {
                "path": request.url.path,
                "method": request.method,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            }
        },
    )
    return response


@app.get("/health", tags=["health"])
async def liveness_check():
    """
    Liveness probe for Kubernetes and monitoring systems.

    Returns health status of all system components.
    Used by orchestrators to determine if pod should be restarted.
    """
    health_report = await health_checker.check_all()

    status_code = 200 if health_report.status == HealthStatus.HEALTHY else 503

    # Update uptime metric
    uptime = (datetime.now(timezone.utc) - health_checker.startup_time).total_seconds()
    app_uptime_seconds.set(uptime)

    return Response(
        content=health_report.model_dump_json(),
        status_code=status_code,
        media_type="application/json",
    )


@app.get("/ready", tags=["health"])
async def readiness_check():
    """
    Readiness probe for Kubernetes.

    Returns True only if system is fully initialized and ready to serve requests.
    Used by load balancers to determine if pod should receive traffic.
    """
    readiness = await health_checker.check_ready()

    status_code = 200 if readiness.ready else 503

    return Response(
        content=readiness.model_dump_json(),
        status_code=status_code,
        media_type="application/json",
    )


@app.get("/metrics", tags=["health"], include_in_schema=False)
def metrics_endpoint():
    """
    Prometheus metrics endpoint.

    Exports metrics for monitoring and alerting.
    Endpoint: /metrics, Format: Prometheus text format
    """
    return Response(content=get_metrics_text(), media_type="text/plain; charset=utf-8")


@app.get("/circuit-breaker", tags=["health"])
def circuit_breaker_status():
    """
    Get status of all circuit breakers.

    Shows which external services are currently failing and their recovery status.
    """
    return {
        "circuit_breakers": circuit_breaker_manager.get_states(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/", tags=["health"], response_class=HTMLResponse, include_in_schema=False)
def home(request: Request):
    """
    Serve the main web UI homepage.

    Returns the Jinja2-compiled index.html template with app metadata.
    This is the main landing page users see when visiting the API.
    """
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "app_name": settings.app_name,
            "api_key": settings.api_key,
        },
    )
