"""Provides a user console for printing any user-facing messages.

If you want to print an information message to the user, that is not a log message,
use this console instead of the logger.

Example:
>>> from .user_console import UserConsole
>>> usrcon = UserConsole()
>>> usrcon.info("This is an info message to the user!")
"""

import enum
from typing import Optional

from rich.console import Console

from matricula_online_scraper.utils.singleton import Singleton


class Level(enum.Enum):
    """Levels of user console messages."""

    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


_iconMap: dict[Level, str] = {
    Level.INFO: "ℹ",
    Level.SUCCESS: "✔︎",
    Level.WARNING: "⚠",
    Level.ERROR: "✖",
}

_colorMap: dict[Level, str] = {
    Level.INFO: "blue",
    Level.SUCCESS: "green",
    Level.WARNING: "yellow",
    Level.ERROR: "red",
}


class UserConsole(metaclass=Singleton):
    """A user console for printing user-facing messages."""

    def __init__(self, *, stderr: bool = True):  # noqa: D107
        self.console = Console(stderr=stderr)
        self._quiet = False

    @property
    def quiet(self) -> bool:
        """Return whether the console is in quiet mode."""
        return self._quiet

    @quiet.setter
    def quiet(self, value: bool):
        """Set the quiet mode of the console."""
        self._quiet = value
        self.console = Console(stderr=False, quiet=value)

    @staticmethod
    def get_prefix(level: Level) -> str:
        """Return the prefix symbol for the given level."""
        c = _colorMap[level]
        i = _iconMap[level]
        return f"[{c}]{i}[/{c}]"

    def info(self, *args, **kwargs):
        """Print an info message to the user console."""
        prefix = self.get_prefix(Level.INFO)
        self.console.print(prefix, *args, **kwargs)

    def success(self, *args, **kwargs):
        """Print a success message to the user console."""
        prefix = self.get_prefix(Level.SUCCESS)
        self.console.print(prefix, *args, **kwargs)

    def warning(self, *args, **kwargs):
        """Print a warning message to the user console."""
        prefix = self.get_prefix(Level.WARNING)
        self.console.print(prefix, *args, **kwargs)

    def error(self, *args, **kwargs):
        """Print an error message to the user console."""
        prefix = self.get_prefix(Level.ERROR)
        self.console.print(prefix, *args, **kwargs)

    def print(self, *args, **kwargs):
        """Print a message to the user console without any prefix."""
        self.console.print(*args, **kwargs)

    def print_with_prefix(self, *args, prefix: str = "", **kwargs):
        """Print a message to the user console with a custom prefix.

        Leave the `prefix` empty to print with a leading space.
        """
        self.console.print(prefix, *args, **kwargs)
