import logging
import os
import sys


def configure_logging(level: str = None):
    """
    Configures structured logging for the Hermes Memory Engine.

    Call once at application startup. The log level can be set via the
    HERMES_LOG_LEVEL environment variable (default: INFO).
    """
    if level is None:
        level = os.environ.get("HERMES_LOG_LEVEL", "INFO").upper()

    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    datefmt = "%Y-%m-%dT%H:%M:%S%z"

    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format=fmt,
        datefmt=datefmt,
        stream=sys.stderr,
    )

    # Quiet noisy third-party loggers
    logging.getLogger("chromadb").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
