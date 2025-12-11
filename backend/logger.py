"""
Configurable logging module for the backend.

Supports different log levels:
- CRITICAL: Only failures and critical errors
- ERROR: Errors and above
- WARNING: Warnings, errors, and above
- INFO: Informational messages and above (default)
- DEBUG: All messages including debug info

Configuration:
- Set LOG_LEVEL environment variable to one of: CRITICAL, ERROR, WARNING, INFO, DEBUG
- Default: INFO
- Can be changed at runtime via the /config/log-level endpoint
"""

import logging
import os
from enum import Enum
from typing import Optional

# Define log levels as an Enum for type safety
class LogLevel(str, Enum):
    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    DEBUG = "DEBUG"

# Current global log level
_current_log_level = LogLevel(os.getenv("LOG_LEVEL", "INFO").upper())

# Create logger instance
logger = logging.getLogger("wardrobe-api")

# Remove any existing handlers
logger.handlers = []

# Set up handler with formatter
handler = logging.StreamHandler()
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
handler.setFormatter(formatter)
logger.addHandler(handler)

# Set initial log level
logger.setLevel(_current_log_level.value)


def get_log_level() -> LogLevel:
    """Get the current log level."""
    return _current_log_level


def set_log_level(level: LogLevel) -> None:
    """
    Set the log level at runtime.

    Args:
        level: One of CRITICAL, ERROR, WARNING, INFO, DEBUG
    """
    global _current_log_level
    _current_log_level = level
    logger.setLevel(level.value)
    logger.info(f"Log level changed to {level.value}")


def log_debug(message: str, **kwargs) -> None:
    """Log a debug message."""
    logger.debug(message, **kwargs)


def log_info(message: str, **kwargs) -> None:
    """Log an info message."""
    logger.info(message, **kwargs)


def log_warning(message: str, **kwargs) -> None:
    """Log a warning message."""
    logger.warning(message, **kwargs)


def log_error(message: str, exception: Optional[Exception] = None, **kwargs) -> None:
    """Log an error message, optionally with exception details."""
    if exception:
        logger.error(f"{message} | Exception: {str(exception)}", **kwargs)
    else:
        logger.error(message, **kwargs)


def log_critical(message: str, exception: Optional[Exception] = None, **kwargs) -> None:
    """Log a critical message, optionally with exception details."""
    if exception:
        logger.critical(f"{message} | Exception: {str(exception)}", **kwargs)
    else:
        logger.critical(message, **kwargs)
