"""Logging configuration for the application.

Call `setup_logging` to configure the root logger and create a custom application logger.
Then use `get_logger` to get a logger that inherits from the application logger.

Examples:
>>> from .logging_config import setup_logging, get_logger
>>> setup_logging(LogLevel.DEBUG, LogLevel.WARNING)
>>> logger = get_logger(__name__)
"""

import logging
import sys
from enum import Enum

from rich.console import Console
from rich.logging import RichHandler

APP_NAME = "matricula_online_scraper"

quiet = False

console = Console(
    quiet=quiet,
)


class LogLevel(str, Enum):
    """Log levels for the application."""

    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    DEBUG = "DEBUG"


def setup_logging(
    log_level: LogLevel,
    package_logging: LogLevel,
):
    """Configure the root logger and create a custom application logger.

    Args:
        log_level (LogLevel): Log level of the application logger.
        package_logging (LogLevel): Log level of the 3rd-party package (root) logger.

    Returns:
        Logger: The application logger.
    """
    FORMAT = "%(message)s"
    VERBOSE_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # --- 3rd-party package logging ---
    logging.basicConfig(
        format=VERBOSE_FORMAT if package_logging == LogLevel.DEBUG else FORMAT,
        handlers=[
            RichHandler(level=package_logging.value, console=Console(stderr=True))
        ],
    )

    # --- application logging ---
    console_handler = RichHandler(
        level=log_level.value,
        console=Console(stderr=True),
        show_time=log_level == LogLevel.DEBUG,
        show_path=log_level == LogLevel.DEBUG,
    )
    console_handler.setFormatter(
        logging.Formatter(
            VERBOSE_FORMAT if log_level == LogLevel.DEBUG else FORMAT,
        )
    )
    app_logger = logging.getLogger(APP_NAME)
    app_logger.addHandler(console_handler)

    return app_logger


def get_logger(name=None):
    """Get a logger that inherits from the application logger.

    This is just a convenience function to call `logging.getLogger` with a specific name
    – the applications name to inherit from the application logger.

    Args:
        name (str, optional): The name of the module. If None, returns the application logger.
            If provided, returns a child logger with the name 'matricula_online_scraper.{name}'.

    Returns:
        Logger: A logger that inherits from the application logger.
    """
    if name is None:
        return logging.getLogger(APP_NAME)
    else:
        return logging.getLogger(f"{APP_NAME}.{name}")
