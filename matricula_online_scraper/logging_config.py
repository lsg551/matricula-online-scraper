"""Logging configuration for the application.

This does two important things:
1. Configure the root logger to be used for all 3rd-party packages.
2. Create and isolate a custom application logger that is used solely for the application.

Call `setup_logging` to configure the root logger and create a custom application logger.
Then use `get_logger(__name__)` to get a logger that inherits from the application logger.

Examples:
>>> from .logging_config import setup_logging, get_logger
>>> setup_logging(LogLevel.DEBUG, LogLevel.WARNING)
>>> logger = get_logger(__name__)
"""

# NOTE: when modifying the root logger, scrapy must be used with the `CrawlerRunner` class
# see https://docs.scrapy.org/en/latest/topics/logging.html#module-scrapy.utils.log

import logging
from enum import Enum
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler
from rich.theme import Theme

APP_NAME = "matricula_online_scraper"
"""Name used for the root application logger."""


class LogLevel(str, Enum):
    """Log levels for the application."""

    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    DEBUG = "DEBUG"

    def __str__(self) -> str:
        """Return the string representation of the log level (the enum's value)."""
        return self.value


DEFAULT_LOG_LEVEL = LogLevel.INFO
DEFAULT_PACKAGE_LOG_LEVEL = LogLevel.CRITICAL


LOGGING_THEME = Theme({"logging.level.debug": "blue", "logging.level.info": "green"})
"""Custom theme for the RichHandler."""

FORMAT = "%(message)s"
# NOTE: the levelname and time are not needed when using the RichHandler
# bc it is already added through separate columns
# VERBOSE_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
VERBOSE_FORMAT = "%(name)s: %(message)s"


LOG_TIME_FORMAT = "[%Y-%m-%d %H:%M:%S%z]"
"""ISO 8601 format for time in logs."""


class Logging:
    """Logging configuration for the application.

    Use this class once to configure the root logger and create a custom application logger.
    To get an instance of the application logger, use `get_logger(__name__)`.

    Example:
    >>> from .logging_config import Logging
    >>> logging_config = Logging()
    >>> logging_config.setup_logging()
    """

    def __init__(
        self,
        *,
        log_level: LogLevel = DEFAULT_LOG_LEVEL,
        package_log_level: LogLevel = DEFAULT_PACKAGE_LOG_LEVEL,
        use_stderr: bool = True,
    ) -> None:
        """Initialize the logging configuration.

        Args:
            log_level (LogLevel, optional): Log level for the application logger. Defaults to DEFAULT_LOG_LEVEL.
            package_log_level (LogLevel, optional): Log level for the root logger, affecting all 3rd party packages.
                Defaults to DEFAULT_PACKAGE_LOG_LEVEL.
            use_stderr (bool, optional): Use stderr to print logs. Defaults to True.
        """
        self.log_level = log_level
        self.package_log_level = package_log_level
        self.app_name = APP_NAME
        self.use_stderr = use_stderr

    def setup_logging(self) -> logging.Logger:
        """Configure the root logger and create a custom application logger.

        Returns:
            Logger: The application logger.
        """
        # --- 3rd-party package logging ---
        logging.basicConfig(
            level=self.package_log_level,
            format=VERBOSE_FORMAT
            if self.package_log_level == LogLevel.DEBUG
            else FORMAT,
            datefmt=LOG_TIME_FORMAT,
            handlers=[
                RichHandler(
                    console=Console(stderr=self.use_stderr, theme=LOGGING_THEME),
                    show_time=self.log_level == LogLevel.DEBUG,
                    show_path=self.log_level == LogLevel.DEBUG,
                    # log_time_format=LOG_TIME_FORMAT,
                )
            ],
            # force=True,
        )

        # --- application logging ---
        console_handler = RichHandler(
            console=Console(stderr=self.use_stderr, theme=LOGGING_THEME),
            show_time=self.log_level == LogLevel.DEBUG,
            show_path=self.log_level == LogLevel.DEBUG,
            # log_time_format=LOG_TIME_FORMAT,
        )
        console_handler.setFormatter(
            logging.Formatter(
                fmt=VERBOSE_FORMAT if self.log_level == LogLevel.DEBUG else FORMAT,
                datefmt=LOG_TIME_FORMAT,
            )
        )
        app_logger = logging.getLogger(self.app_name)
        app_logger.addHandler(console_handler)
        app_logger.setLevel(self.log_level.value)

        # Prevent this logger from propagating messages to the root logger
        # Isolate against future changes in the root logger
        app_logger.propagate = False

        app_logger.debug(
            f"Using logging configuration: {self.log_level=},"
            f" {self.package_log_level=}, {self.use_stderr=}, {self.app_name=}"
        )

        return app_logger

    def __call__(self, name: Optional[str] = None):
        """Same as `get_logger`."""
        return self.get_logger(name)

    @staticmethod
    def get_logger(name: Optional[str] = None):
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


# Backwards compatibility and convenience
get_logger = Logging.get_logger
