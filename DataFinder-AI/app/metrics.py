"""
Prometheus metrics and monitoring integration.

Exports metrics for monitoring API performance, LLM usage, and external API health.
"""

import time
from contextlib import contextmanager
from functools import wraps
from typing import Any, Callable

from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    Summary,
    CollectorRegistry,
    generate_latest,
)

# Create dedicated registry for our metrics
registry = CollectorRegistry()

# =======================
# Request Metrics
# =======================

http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
    registry=registry,
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
    registry=registry,
)

http_request_size_bytes = Summary(
    "http_request_size_bytes",
    "HTTP request size in bytes",
    ["method", "endpoint"],
    registry=registry,
)

http_response_size_bytes = Summary(
    "http_response_size_bytes",
    "HTTP response size in bytes",
    ["method", "endpoint"],
    registry=registry,
)

# =======================
# Search Service Metrics
# =======================

search_queries_total = Counter(
    "search_queries_total",
    "Total search queries",
    ["status", "source"],
    registry=registry,
)

search_query_duration_seconds = Histogram(
    "search_query_duration_seconds",
    "Search query duration in seconds",
    ["source"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0],
    registry=registry,
)

faiss_index_size = Gauge(
    "faiss_index_size",
    "Number of vectors in FAISS index",
    registry=registry,
)

faiss_search_latency_ms = Summary(
    "faiss_search_latency_ms",
    "FAISS search latency in milliseconds",
    registry=registry,
)

datasets_indexed = Gauge(
    "datasets_indexed",
    "Total datasets in index",
    ["source"],
    registry=registry,
)

# =======================
# LLM Service Metrics
# =======================

llm_requests_total = Counter(
    "llm_requests_total",
    "Total LLM API requests",
    ["model", "operation", "status"],
    registry=registry,
)

llm_request_duration_seconds = Histogram(
    "llm_request_duration_seconds",
    "LLM API request duration in seconds",
    ["model", "operation"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
    registry=registry,
)

llm_tokens_used = Counter(
    "llm_tokens_used",
    "Total tokens used by LLM",
    ["model", "token_type"],
    registry=registry,
)

llm_errors_total = Counter(
    "llm_errors_total",
    "Total LLM API errors",
    ["model", "error_type"],
    registry=registry,
)

# =======================
# Database Metrics
# =======================

database_query_duration_seconds = Histogram(
    "database_query_duration_seconds",
    "Database query duration in seconds",
    ["operation"],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5],
    registry=registry,
)

database_errors_total = Counter(
    "database_errors_total",
    "Total database errors",
    ["operation"],
    registry=registry,
)

database_connection_pool_size = Gauge(
    "database_connection_pool_size",
    "Current database connection pool size",
    registry=registry,
)

# =======================
# External API Metrics
# =======================

external_api_calls_total = Counter(
    "external_api_calls_total",
    "Total external API calls",
    ["api", "status"],
    registry=registry,
)

external_api_errors_total = Counter(
    "external_api_errors_total",
    "Total external API errors",
    ["api", "error_type"],
    registry=registry,
)

external_api_latency_seconds = Histogram(
    "external_api_latency_seconds",
    "External API call latency in seconds",
    ["api"],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
    registry=registry,
)

circuit_breaker_state = Gauge(
    "circuit_breaker_state",
    "Circuit breaker state (0=closed, 1=open, 2=half_open)",
    ["service"],
    registry=registry,
)

# =======================
# System Metrics
# =======================

app_uptime_seconds = Gauge(
    "app_uptime_seconds",
    "Application uptime in seconds",
    registry=registry,
)

active_requests = Gauge(
    "active_requests",
    "Number of currently active requests",
    registry=registry,
)

# =======================
# Helper Functions
# =======================


@contextmanager
def track_request(method: str, endpoint: str):
    """Context manager to track HTTP request metrics."""
    start = time.perf_counter()
    active_requests.inc()

    try:
        yield
    finally:
        duration = time.perf_counter() - start
        http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(
            duration
        )
        active_requests.dec()


@contextmanager
def track_search(source: str = "default"):
    """Context manager to track search metrics."""
    start = time.perf_counter()

    try:
        yield
        search_queries_total.labels(status="success", source=source).inc()
    except Exception:
        search_queries_total.labels(status="error", source=source).inc()
        raise
    finally:
        duration = time.perf_counter() - start
        search_query_duration_seconds.labels(source=source).observe(duration)


@contextmanager
def track_llm_request(model: str, operation: str):
    """Context manager to track LLM request metrics."""
    start = time.perf_counter()

    try:
        yield
        llm_requests_total.labels(
            model=model, operation=operation, status="success"
        ).inc()
    except Exception as e:
        llm_requests_total.labels(
            model=model, operation=operation, status="error"
        ).inc()
        llm_errors_total.labels(model=model, error_type=type(e).__name__).inc()
        raise
    finally:
        duration = time.perf_counter() - start
        llm_request_duration_seconds.labels(model=model, operation=operation).observe(
            duration
        )


@contextmanager
def track_db_query(operation: str):
    """Context manager to track database query metrics."""
    start = time.perf_counter()

    try:
        yield
    except Exception:
        database_errors_total.labels(operation=operation).inc()
        raise
    finally:
        duration = time.perf_counter() - start
        database_query_duration_seconds.labels(operation=operation).observe(duration)


@contextmanager
def track_external_api(api_name: str):
    """Context manager to track external API calls."""
    start = time.perf_counter()

    try:
        yield
        external_api_calls_total.labels(api=api_name, status="success").inc()
    except Exception as e:
        external_api_calls_total.labels(api=api_name, status="error").inc()
        external_api_errors_total.labels(
            api=api_name, error_type=type(e).__name__
        ).inc()
        raise
    finally:
        duration = time.perf_counter() - start
        external_api_latency_seconds.labels(api=api_name).observe(duration)


def track_function_calls(metric_histogram: Histogram):
    """Decorator to track function execution time."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                duration = time.perf_counter() - start
                metric_histogram.observe(duration)

        return wrapper

    return decorator


def get_metrics_text() -> bytes:
    """Get Prometheus-format metrics text."""
    return generate_latest(registry)
