"""
Structured logging for ClausePilot backend.
Never logs secrets or API keys.
"""
from __future__ import annotations

import logging
import sys
from functools import lru_cache


class _SensitiveFilter(logging.Filter):
    """Strip any record that appears to contain an API key pattern."""

    _SENSITIVE_KEYWORDS = ("api_key", "groq_api_key", "authorization", "bearer")

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: A003
        msg = record.getMessage().lower()
        for keyword in self._SENSITIVE_KEYWORDS:
            if keyword in msg:
                record.msg = "[REDACTED — sensitive field]"
                record.args = ()
        return True


@lru_cache
def get_logger(name: str = "clausepilot") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    handler.setFormatter(formatter)
    handler.addFilter(_SensitiveFilter())
    logger.addHandler(handler)
    logger.propagate = False
    return logger


def configure_logging(level: str = "INFO") -> None:
    """Call once at application startup."""
    numeric = getattr(logging, level.upper(), logging.INFO)
    root = get_logger()
    root.setLevel(numeric)
    logging.getLogger("uvicorn").setLevel(numeric)
    logging.getLogger("uvicorn.access").setLevel(numeric)
