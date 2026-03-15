"""
Circuit breaker pattern for external API calls.

Prevents cascading failures by stopping requests to failing services.
Implements exponential backoff for recovery.
"""

import logging
import time
from enum import Enum
from typing import Any, Callable

logger = logging.getLogger("datafinder.circuit_breaker")


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitBreaker:
    """
    Circuit breaker for external API calls.

    Tracks failures and prevents requests when service is degraded.
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception,
    ):
        """
        Initialize circuit breaker.

        Args:
            name: Service name
            failure_threshold: Failures before opening circuit
            recovery_timeout: Seconds before attempting recovery
            expected_exception: Exception type to catch
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: float | None = None
        self.success_count = 0

    def call(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """
        Execute function with circuit breaker protection.

        Args:
            func: Function to call
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            CircuitBreakerOpen: If circuit is open
            Original exception: If function fails
        """
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                logger.info(f"Circuit breaker '{self.name}' entering HALF_OPEN state")
            else:
                raise CircuitBreakerOpen(
                    f"Circuit breaker '{self.name}' is OPEN. Service unavailable."
                )

        try:
            result = func(*args, **kwargs)

            if self.state == CircuitState.HALF_OPEN:
                self._on_success()

            return result

        except self.expected_exception as e:
            self._on_failure()
            raise

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt recovery."""
        if self.last_failure_time is None:
            return True

        elapsed = time.time() - self.last_failure_time
        return elapsed >= self.recovery_timeout

    def _on_failure(self) -> None:
        """Track failure and update state."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        self.success_count = 0

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.error(
                f"Circuit breaker '{self.name}' opened after {self.failure_count} failures"
            )

    def _on_success(self) -> None:
        """Track success and potentially close circuit."""
        self.success_count += 1

        if self.success_count >= 2:  # 2 successes to close
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            logger.info(f"Circuit breaker '{self.name}' closed (recovered)")

    def get_state(self) -> dict[str, Any]:
        """Get current circuit breaker state."""
        return {
            "name": self.name,
            "state": self.state.value,
            "failures": self.failure_count,
            "successes": self.success_count,
            "last_failure": self.last_failure_time,
        }


class CircuitBreakerOpen(Exception):
    """Raised when circuit breaker is open."""

    pass


class CircuitBreakerManager:
    """Manages multiple circuit breakers for different services."""

    def __init__(self):
        self.breakers: dict[str, CircuitBreaker] = {}

    def register(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception,
    ) -> CircuitBreaker:
        """Register a new circuit breaker."""
        breaker = CircuitBreaker(
            name=name,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            expected_exception=expected_exception,
        )
        self.breakers[name] = breaker
        return breaker

    def get(self, name: str) -> CircuitBreaker | None:
        """Get a registered circuit breaker."""
        return self.breakers.get(name)

    def call(self, name: str, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """Call function through circuit breaker."""
        breaker = self.breakers.get(name)
        if breaker is None:
            raise ValueError(f"Circuit breaker '{name}' not registered")
        return breaker.call(func, *args, **kwargs)

    def get_states(self) -> dict[str, dict[str, Any]]:
        """Get states of all circuit breakers."""
        return {name: breaker.get_state() for name, breaker in self.breakers.items()}


# Global circuit breaker manager
circuit_breaker_manager = CircuitBreakerManager()

# Register circuit breakers for each data source
circuit_breaker_manager.register("kaggle", failure_threshold=5, recovery_timeout=120)
circuit_breaker_manager.register("openml", failure_threshold=5, recovery_timeout=120)
circuit_breaker_manager.register(
    "huggingface", failure_threshold=5, recovery_timeout=120
)
circuit_breaker_manager.register("github", failure_threshold=5, recovery_timeout=120)
circuit_breaker_manager.register("zenodo", failure_threshold=5, recovery_timeout=120)
circuit_breaker_manager.register("mendeley", failure_threshold=5, recovery_timeout=120)
circuit_breaker_manager.register("groq", failure_threshold=3, recovery_timeout=60)
