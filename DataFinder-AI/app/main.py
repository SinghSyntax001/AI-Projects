from contextlib import asynccontextmanager
import logging
from threading import Thread
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from app.config import get_settings
from app.database.db import Base, SessionLocal, engine
from app.logging_config import configure_logging
from app.routes.datasets import router as datasets_router
from app.routes.search import router as search_router
from app.services.search_service import SearchService

try:
    from apscheduler.schedulers.background import BackgroundScheduler
except ImportError:  # pragma: no cover
    BackgroundScheduler = None


settings = get_settings()
configure_logging(settings)
logger = logging.getLogger("datafinder.api")
scheduler = BackgroundScheduler(timezone="UTC") if BackgroundScheduler is not None else None


def run_ingestion_job() -> None:
    db = SessionLocal()
    try:
        service = SearchService(db, settings)
        service.ensure_data(settings.bootstrap_query, settings.default_search_limit, force_refresh=True)
        logger.info(
            "background ingestion completed",
            extra={"event_data": {"query": settings.bootstrap_query, "interval_hours": settings.ingestion_interval_hours}},
        )
    except Exception:
        logger.exception("background ingestion failed", extra={"event_data": {"query": settings.bootstrap_query}})
    finally:
        db.close()


def start_background_ingestion() -> None:
    Thread(target=run_ingestion_job, name="initial-ingestion", daemon=True).start()


@asynccontextmanager
async def lifespan(_: FastAPI):
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
        logger.info("scheduler started", extra={"event_data": {"interval_hours": settings.ingestion_interval_hours}})
    elif settings.enable_scheduler:
        logger.warning("scheduler requested but APScheduler is unavailable")

    yield

    if scheduler is not None and scheduler.running:
        scheduler.shutdown(wait=False)


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
    description="Production-style dataset discovery API with semantic vector search, scheduled ingestion, and API key protection.",
    openapi_tags=[
        {"name": "search", "description": "Semantic vector search endpoints."},
        {"name": "datasets", "description": "Dataset catalog endpoints."},
        {"name": "health", "description": "Operational health endpoints."},
    ],
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.cors_origins == "*" else [origin.strip() for origin in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(search_router)
app.include_router(datasets_router)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.exception(
            "request failed",
            extra={"event_data": {"path": request.url.path, "method": request.method, "duration_ms": duration_ms}},
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
def health() -> dict[str, str]:
    """Simple readiness endpoint for containers and load balancers."""
    return {"status": "ok", "environment": settings.app_env}


@app.get("/", tags=["health"], response_class=HTMLResponse, include_in_schema=False)
def home() -> str:
    return f"""
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>{settings.app_name}</title>
        <style>
          body {{
            font-family: Georgia, 'Times New Roman', serif;
            margin: 0;
            background: linear-gradient(135deg, #f7f1e8 0%, #dce8f2 100%);
            color: #14213d;
          }}
          .wrap {{
            max-width: 860px;
            margin: 80px auto;
            padding: 32px;
          }}
          .card {{
            background: rgba(255,255,255,0.88);
            border: 1px solid rgba(20,33,61,0.12);
            border-radius: 20px;
            padding: 32px;
            box-shadow: 0 24px 80px rgba(20,33,61,0.12);
          }}
          h1 {{
            margin: 0 0 12px;
            font-size: 3rem;
          }}
          p {{
            font-size: 1.05rem;
            line-height: 1.6;
          }}
          .links {{
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
            margin-top: 24px;
          }}
          a {{
            text-decoration: none;
            padding: 12px 18px;
            border-radius: 999px;
            background: #14213d;
            color: white;
            font-weight: 600;
          }}
          .muted {{
            margin-top: 18px;
            color: #4f5d75;
            font-size: 0.95rem;
          }}
          code {{
            background: rgba(20,33,61,0.08);
            padding: 2px 6px;
            border-radius: 6px;
          }}
        </style>
      </head>
      <body>
        <div class="wrap">
          <div class="card">
            <h1>DataFinder-AI</h1>
            <p>Semantic dataset discovery backend powered by FastAPI, embeddings, and FAISS vector search.</p>
            <div class="links">
              <a href="/docs">Open Swagger Docs</a>
              <a href="/redoc">Open ReDoc</a>
              <a href="/health">Health Check</a>
            </div>
            <p class="muted">
              Main API routes: <code>/search?q=...</code>, <code>/datasets</code>, <code>/datasets/{{id}}</code>.
              Protected routes require <code>Authorization: Bearer &lt;API_KEY&gt;</code>.
            </p>
          </div>
        </div>
      </body>
    </html>
    """
