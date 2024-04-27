"""
Common CLI Arguments and Options
"""

from typing import Annotated
from pathlib import Path
from enum import Enum
import typer


# ++++++++++++++++++++++++++++++++++++++++ --silent Option ++++++++++++++++++++++++++++++++++++++++


SilentOption = Annotated[
    bool, typer.Option(help="Disable all output from the scraper.")
]
DEFAULT_SCRAPER_SILENT = True


# ++++++++++++++++++++++++++++++++++++++++ --log-level Option ++++++++++++++++++++++++++++++++++++++++


LogLevelOption = Annotated[str, typer.Option(help="Set the log level for the crawler.")]
DEFAULT_SCRAPER_LOG_LEVEL = "ERROR"


# ++++++++++++++++++++++++++++++++++++++++ output_file_name Argument ++++++++++++++++++++++++++++++++++++++++


OutputFileNameArgument = Annotated[
    Path, typer.Argument(help="File to which the data is written")
]


# ++++++++++++++++++++++++++++++++++++++++ --output-file-format Option ++++++++++++++++++++++++++++++++++++++++


class FileFormat(str, Enum):
    JSONL = "jsonl"
    JSON = "json"
    CSV = "csv"


def file_format_to_scrapy(file_format: FileFormat) -> str:
    """Convert the FileFormat enum to the corresponding scrapy output format string."""
    match file_format:
        case FileFormat.JSONL:
            return "jsonlines"  # scrapy's internal name for jsonl
        case FileFormat.JSON:
            return "json"
        case FileFormat.CSV:
            return "csv"
        case _:
            raise NotImplementedError(f"File format {file_format} not supported.")


OutputFileFormatOption = Annotated[
    FileFormat,
    typer.Option(
        "--file-format",
        "-e",
        help="Format of the output file. (Do NOT use JSON for large amounts of scraped data. Use JSON Lines or CSV instead.)",
        case_sensitive=False,
    ),
]
DEFAULT_OUTPUT_FILE_FORMAT = FileFormat.JSONL


# ++++++++++++++++++++++++++++++++++++++++ --append Option ++++++++++++++++++++++++++++++++++++++++


AppendOption = Annotated[
    bool,
    typer.Option(
        help="Append to the output file if it already exists.",
    ),
]
DEFAUL_APPEND = True
