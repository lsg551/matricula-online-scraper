"""
Utils for the CLI.
"""

from __future__ import annotations
from urllib.parse import urlparse


class URL:
    """Custom typer CLI argument parser for URLs."""

    def __init__(self, value: str):
        if URL.is_valid(value) is False:
            raise ValueError(f"Invalid URL: {value}")
        self.value = value

    def __str__(self):
        return self.value

    def __repr__(self):
        return f"<URL: value={self.value}>"

    @staticmethod
    def is_valid(value: str) -> bool:
        """Check if a string is a valid URL."""
        try:
            result = urlparse(value)
            return all([result.scheme, result.netloc])
        except AttributeError:
            return False
