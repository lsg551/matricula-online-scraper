"""Common CLI Arguments and Options."""

from enum import Enum
from typing import Self


class FileFormat(str, Enum):
    """Supported output file formats."""

    JSONL = "jsonl"
    JSON = "json"
    CSV = "csv"

    def to_scrapy(self) -> str:
        """Convert the FileFormat enum to the corresponding scrapy output format string."""
        match self:
            case FileFormat.JSONL:
                return "jsonlines"  # scrapy's internal name for jsonl
            case _:
                # In most cases the file suffix is the same as scrapy's value for it
                return self.value
