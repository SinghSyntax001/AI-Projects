"""
Structured JSON logging configuration.

Configures Python logging to output JSON for easier parsing by
log aggregation systems and monitoring tools.
"""

import json
import logging
import logging.config
from datetime import datetime, timezone

from app.config import Settings


class JsonFormatter(logging.Formatter):
    """
    Custom logging formatter that outputs structured JSON.

    Each log entry includes timestamp, level, logger name, message,
    and any additional event_data attached to the LogRecord.
    """

    def format(self, record: logging.LogRecord) -> str:
        # Build base payload with standard fields
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Include any additional event metadata
        event_data = getattr(record, "event_data", None)
        if isinstance(event_data, dict):
            payload.update(event_data)

        # Include exception traceback if present
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=True)


def configure_logging(settings: Settings) -> None:
    """
    Configure Python logging with JSON output.

    Sets up both console (stdout) and file logging with JSON formatter.
    All logs go to both handlers at INFO level.

    Args:
        settings: Application settings with log file path
    """
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {"json": {"()": "app.logging_config.JsonFormatter"}},
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "json",
                    "level": "INFO",
                },
                "file": {
                    "class": "logging.FileHandler",
                    "formatter": "json",
                    "level": "INFO",
                    "filename": settings.log_file,
                    "encoding": "utf-8",
                },
            },
            "root": {"handlers": ["console", "file"], "level": "INFO"},
        }
    )
