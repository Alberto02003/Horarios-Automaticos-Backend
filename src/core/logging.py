"""Structured logging configuration for the application."""

import logging
import sys
from src.core.config import settings


def setup_logging() -> logging.Logger:
    """Configure structured logging for the app."""
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    # Format: timestamp | level | module | message
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-7s | %(name)-25s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # Root logger
    root = logging.getLogger()
    root.setLevel(log_level)
    root.addHandler(handler)

    # Quiet noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    logger = logging.getLogger("horarios")
    logger.setLevel(log_level)
    return logger


logger = setup_logging()
