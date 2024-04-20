"""
'fetch' command group for the CLI, including subcommands for fetching various spiders.
"""

from typing import Annotated, List, Optional, Tuple
from pathlib import Path
import typer
from scrapy import crawler  # pylint: disable=import-error # type: ignore
from rich import print  # pylint: disable=redefined-builtin
from matricula_online_scraper.spiders.locations_spider import LocationsSpider
from matricula_online_scraper.spiders.parish_registers_spider import (
    ParishRegistersSpider,
)
from .utils import URL

app = typer.Typer()

SilentOption = Annotated[
    bool, typer.Option(help="Disable all output from the scraper.")
]
DEFAULT_SCRAPER_SILENT = True

LogLevelOption = Annotated[str, typer.Option(help="Set the log level for the crawler.")]
DEFAULT_SCRAPER_LOG_LEVEL = "ERROR"


@app.command()
def location(
    output_file: Annotated[Path, typer.Argument()],
    place: Annotated[
        Optional[str], typer.Option(help="Full text search for a location.")
    ] = None,
    diocese: Annotated[
        Optional[int],
        typer.Option(
            help="Enum value of the diocese. (See their website for the list of dioceses.)"
        ),
    ] = None,
    date_filter: Annotated[
        bool, typer.Option(help="Enable/disable date filter.")
    ] = False,
    date_range: Annotated[
        Optional[Tuple[int, int]],
        typer.Option(help="Filter by date of the parish registers."),
    ] = None,
    log_level: LogLevelOption = DEFAULT_SCRAPER_LOG_LEVEL,
    silent: SilentOption = DEFAULT_SCRAPER_SILENT,
):
    """
    Scrape available locations from https://data.matricula-online.eu/en/suchen/ .
    A location is typically a parish, region, or city where digitzed church records are available.
    Sometimes virtual locations (e.g. private collections) are included
    as well as references to external websites.

    If none of the search parameters are provided, all available locations will be scraped.

    Example:
    >>> matricula-online-scraper fetch location ./output.jsonl
    """

    # user specified only a filename, not a complete path
    if output_file.suffix == "":
        print(f"[yellow]Output file has no type suffix: {output_file}[/yellow]")
        output_file = output_file.with_suffix(".jsonl")
        print(
            f"Adding '.jsonl' suffix to the output file. New path: {output_file.absolute()}"
        )

    # atm only jsonl is supported
    if output_file.suffix != ".jsonl":
        print(f"[red]Output file type must be '.jsonl': {output_file}[/red]")
        raise typer.Exit()

    # check if output file already exists
    if output_file.exists():
        print(f"[red]Output file already exists: {output_file.absolute()}[/red]")
        raise typer.Exit()

    # all search parameters are unused => fetching everything takes some time
    if (
        place is None
        or place == ""
        and diocese is None
        and date_filter is False
        and date_range is None
    ):
        print(
            "[yellow]No search parameters provided. Fetching all available locations."
            "This might take some time.[/yellow]"
        )

    try:
        process = crawler.CrawlerProcess(
            settings={
                "FEEDS": {str(output_file.absolute()): {"format": "jsonlines"}},
                "LOG_LEVEL": log_level,
                "LOG_ENABLED": not silent,
            },
        )

        process.crawl(  # type: ignore
            LocationsSpider,
            place=place or "",
            diocese=diocese,
            date_filter=date_filter,
            date_range=date_range or (0, 9999),
        )
        process.start()

        print(
            "[green]Scraping completed successfully. "
            f"Output saved to: {output_file.absolute()}[/green]"
        )

    except Exception as exception:
        print("[red]An unknown error occurred while scraping.[/red]")
        raise typer.Exit(code=1) from exception


@app.command()
def parish(
    output_file: Annotated[Path, typer.Argument()],
    urls: Annotated[
        List[URL],
        typer.Option(parser=URL, help="One ore more URLs to scrape."),
    ],
    log_level: LogLevelOption = DEFAULT_SCRAPER_LOG_LEVEL,
    silent: SilentOption = DEFAULT_SCRAPER_SILENT,
):
    """
    Scrape a parish register
    """

    # user specified only a filename, not a complete path
    if output_file.suffix == "":
        print(f"[yellow]Output file has no type suffix: {output_file}[/yellow]")
        output_file = output_file.with_suffix(".jsonl")
        print(
            f"Adding '.jsonl' suffix to the output file. New path: {output_file.absolute()}"
        )

    # atm only jsonl is supported
    if output_file.suffix != ".jsonl":
        print(f"[red]Output file type must be '.jsonl': {output_file}[/red]")
        raise typer.Exit()

    # check if output file already exists
    if output_file.exists():
        print(f"[red]Output file already exists: {output_file.absolute()}[/red]")
        raise typer.Exit()

    if len(urls) <= 0:
        print("[red]No URLs provided to scrape.[/red]")
        raise typer.Exit()

    try:
        process = crawler.CrawlerProcess(
            settings={
                "FEEDS": {str(output_file.absolute()): {"format": "jsonlines"}},
                "LOG_LEVEL": log_level,
                "LOG_ENABLED": not silent,
            }
        )

        process.crawl(ParishRegistersSpider, start_urls=[str(url) for url in urls])  # type: ignore
        process.start()

        print(
            "[green]Scraping completed successfully. "
            f"Output saved to: {output_file.absolute()}[/green]"
        )

    except Exception as exception:
        print("[red]An unknown error occurred while scraping.[/red]")
        raise typer.Exit(code=1) from exception
