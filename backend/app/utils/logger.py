"""Logging utility to configure structured logs."""

import logging


def configure_logging(level: str = "INFO") -> None:
    """Configure root logger with a consistent formatter."""

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

