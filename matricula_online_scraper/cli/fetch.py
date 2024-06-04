"""
'fetch' command group for the CLI, including subcommands for fetching various spiders.
"""

from typing import Annotated, List, Optional, Tuple
from pathlib import Path
import typer
from scrapy import crawler  # pylint: disable=import-error # type: ignore
from rich import print  # pylint: disable=redefined-builtin
from matricula_online_scraper.spiders.locations_spider import LocationsSpider
from matricula_online_scraper.spiders.newsfeed_spider import NewsfeedSpider
from matricula_online_scraper.spiders.parish_registers_spider import (
    ParishRegistersSpider,
)
from .utils import URL
from .common import (
    DEFAULT_SCRAPER_LOG_LEVEL,
    DEFAULT_SCRAPER_SILENT,
    DEFAULT_OUTPUT_FILE_FORMAT,
    DEFAUL_APPEND,
    LogLevelOption,
    OutputFileNameArgument,
    OutputFileFormatOption,
    SilentOption,
    AppendOption,
    file_format_to_scrapy,
)


app = typer.Typer()


@app.command()
def location(
    output_file_name: OutputFileNameArgument = Path("matricula_locations"),
    output_file_format: OutputFileFormatOption = DEFAULT_OUTPUT_FILE_FORMAT,
    append: AppendOption = DEFAUL_APPEND,
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
    exclude_coordinates: Annotated[
        bool,
        typer.Option(
            "--exclude-coordinates/",
            help="Coordinates of a parish will be included by default. Using this option will exclude coordinates from the output and speed up the scraping process.",
        ),
    ] = False,
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

    output_path_str = str(output_file_name.absolute()) + "." + output_file_format
    output_path = Path(output_path_str)

    # check if output file already exists
    if output_path.exists() and not append:
        print(
            f"[red]Output file already exists: {output_path.absolute()}."
            " Use the option '--append' if you want to append to the file.[/red]"
        )
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
                "FEEDS": {
                    str(output_path.absolute()): {
                        "format": file_format_to_scrapy(output_file_format)
                    }
                },
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
            include_coordinates=not exclude_coordinates,
        )
        process.start()

        print(
            "[green]Scraping completed successfully. "
            f"Output saved to: {output_path.absolute()}[/green]"
        )

    except Exception as exception:
        print("[red]An unknown error occurred while scraping.[/red]")
        raise typer.Exit(code=1) from exception


@app.command()
def parish(
    urls: Annotated[
        List[URL],
        typer.Option("--url", "-u", parser=URL, help="One ore more URLs to scrape."),
    ],
    output_file_name: OutputFileNameArgument = Path("matricula-newsfeed"),
    output_file_format: OutputFileFormatOption = DEFAULT_OUTPUT_FILE_FORMAT,
    append: AppendOption = DEFAUL_APPEND,
    log_level: LogLevelOption = DEFAULT_SCRAPER_LOG_LEVEL,
    silent: SilentOption = DEFAULT_SCRAPER_SILENT,
):
    """
    Scrape a parish register
    """

    output_path_str = str(output_file_name.absolute()) + "." + output_file_format
    output_path = Path(output_path_str)

    # check if output file already exists
    if output_path.exists() and not append:
        print(
            f"[red]Output file already exists: {output_path.absolute()}."
            " Use the option '--append' if you want to append to the file.[/red]"
        )
        raise typer.Exit()

    if len(urls) <= 0:
        print("[red]No URLs provided to scrape.[/red]")
        raise typer.Exit()

    try:
        process = crawler.CrawlerProcess(
            settings={
                "FEEDS": {
                    str(output_path.absolute()): {
                        "format": file_format_to_scrapy(output_file_format)
                    }
                },
                "LOG_LEVEL": log_level,
                "LOG_ENABLED": not silent,
            }
        )

        process.crawl(ParishRegistersSpider, start_urls=[str(url) for url in urls])  # type: ignore
        process.start()

        print(
            "[green]Scraping completed successfully. "
            f"Output saved to: {output_path.absolute()}[/green]"
        )

    except Exception as exception:
        print("[red]An unknown error occurred while scraping.[/red]")
        raise typer.Exit(code=1) from exception


@app.command()
def newsfeed(
    output_file_name: OutputFileNameArgument = Path("matricula_parishes"),
    output_file_format: OutputFileFormatOption = DEFAULT_OUTPUT_FILE_FORMAT,
    log_level: LogLevelOption = DEFAULT_SCRAPER_LOG_LEVEL,
    silent: SilentOption = DEFAULT_SCRAPER_SILENT,
    # options
    last_n_days: Annotated[
        Optional[int],
        typer.Option(
            "--last-n-days",
            "-n",
            help="Scrape news from the last n days (including today).",
        ),
    ] = None,
    limit: Annotated[
        Optional[int],
        typer.Option(
            help=(
                "Limit the number of max. news articles to scrape"
                "(note that this is a upper bound, it might be less depending on other parameters)."
            )
        ),
    ] = 100,
):
    """
    Scrape Matricula Online's Newsfeed.
    """

    output_path_str = str(output_file_name.absolute()) + "." + output_file_format
    output_path = Path(output_path_str)

    # check if output file already exists
    if output_path.exists():
        print(
            f"[red]Output file already exists: {output_path.absolute()}."
            " Use the option '--append' if you want to append to the file.[/red]"
        )
        raise typer.Exit()

    try:
        process = crawler.CrawlerProcess(
            settings={
                "FEEDS": {
                    str(output_path.absolute()): {
                        "format": file_format_to_scrapy(output_file_format),
                    }
                },
                "LOG_LEVEL": log_level,
                "LOG_ENABLED": not silent,
            }
        )

        process.crawl(NewsfeedSpider, limit=limit, last_n_days=last_n_days)
        process.start()

        print(
            "[green]Scraping completed successfully. "
            f"Output saved to: {output_path.absolute()}[/green]"
        )

    except Exception as exception:
        print("[red]An unknown error occurred while scraping.[/red]")
        raise typer.Exit(code=1) from exception
