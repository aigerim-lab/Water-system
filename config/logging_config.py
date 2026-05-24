"""Structured logging configuration."""

from __future__ import annotations

import logging
import sys


def get_logger(name: str) -> logging.Logger:
    """Return a module-level logger with a consistent format."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s")
        )
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
