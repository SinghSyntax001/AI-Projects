"""
Health check and readiness probe implementation.

Provides liveness and readiness probes for Kubernetes orchestration.
Monitors critical system components and reports their status.
"""

import asyncio
import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable

from pydantic import BaseModel

logger = logging.getLogger("datafinder.health")


class HealthStatus(str, Enum):
    """System health status."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ServiceHealth(BaseModel):
    """Health status of an individual service."""

    name: str
    healthy: bool
    latency_ms: float = 0.0
    message: str = ""


class HealthCheckResponse(BaseModel):
    """Complete health check response."""

    status: HealthStatus
    timestamp: str
    version: str
    uptime_seconds: float
    services: dict[str, bool]
    service_details: list[ServiceHealth]


class ReadinessResponse(BaseModel):
    """Readiness probe response."""

    ready: bool
    database: bool
    faiss_index: bool
    message: str = ""


class HealthChecker:
    """Orchestrates health checks for all system components."""

    def __init__(self, startup_time: datetime):
        self.startup_time = startup_time
        self.checks: dict[str, Callable] = {}

    def register_check(self, name: str, check_fn: Callable) -> None:
        """Register a health check function."""
        self.checks[name] = check_fn

    async def check_all(self) -> HealthCheckResponse:
        """Run all health checks in parallel."""
        service_details: list[ServiceHealth] = []

        # Run all checks concurrently
        results = await asyncio.gather(
            *[self._run_check(name, fn) for name, fn in self.checks.items()],
            return_exceptions=True,
        )

        for (name, _), result in zip(self.checks.items(), results):
            if isinstance(result, Exception):
                logger.warning(f"Health check failed for {name}: {result}")
                service_details.append(
                    ServiceHealth(name=name, healthy=False, message=str(result))
                )
            else:
                service_details.append(result)

        # Determine overall status
        all_healthy = all(detail.healthy for detail in service_details)
        status = HealthStatus.HEALTHY if all_healthy else HealthStatus.DEGRADED

        # Calculate uptime
        uptime = (datetime.now(timezone.utc) - self.startup_time).total_seconds()

        return HealthCheckResponse(
            status=status,
            timestamp=datetime.now(timezone.utc).isoformat(),
            version="1.0.0",
            uptime_seconds=uptime,
            services={detail.name: detail.healthy for detail in service_details},
            service_details=service_details,
        )

    async def check_ready(self) -> ReadinessResponse:
        """Check if system is ready to serve requests."""
        try:
            db_check = self.checks.get("database")
            index_check = self.checks.get("faiss_index")

            db_ready = await self._run_check("database", db_check) if db_check else True
            index_ready = (
                await self._run_check("faiss_index", index_check)
                if index_check
                else True
            )

            db_ok = db_ready.healthy if isinstance(db_ready, ServiceHealth) else False
            index_ok = (
                index_ready.healthy if isinstance(index_ready, ServiceHealth) else False
            )

            ready = db_ok and index_ok

            return ReadinessResponse(
                ready=ready,
                database=db_ok,
                faiss_index=index_ok,
                message="Ready to serve requests" if ready else "Not ready",
            )
        except Exception as e:
            logger.error(f"Readiness check failed: {e}")
            return ReadinessResponse(
                ready=False,
                database=False,
                faiss_index=False,
                message=str(e),
            )

    @staticmethod
    async def _run_check(name: str, check_fn: Callable) -> ServiceHealth:
        """Run a single health check with timeout."""
        import time

        try:
            start = time.perf_counter()
            result = check_fn()

            # Handle async checks
            if asyncio.iscoroutine(result):
                result = await asyncio.wait_for(result, timeout=5.0)

            latency = (time.perf_counter() - start) * 1000

            return ServiceHealth(
                name=name,
                healthy=result if isinstance(result, bool) else True,
                latency_ms=latency,
                message="OK" if result else "Failed",
            )
        except asyncio.TimeoutError:
            logger.error(f"Health check {name} timed out")
            return ServiceHealth(
                name=name, healthy=False, message="Check timed out (>5s)"
            )
        except Exception as e:
            logger.error(f"Health check {name} failed: {e}")
            return ServiceHealth(name=name, healthy=False, message=str(e))
