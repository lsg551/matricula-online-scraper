"""
'fetch' command group for the CLI, including subcommands for fetching various spiders.
"""

from pathlib import Path
from typing import Annotated, Optional

import typer
from rich import print
from scrapy import crawler

from matricula_online_scraper.spiders.newsfeed_spider import NewsfeedSpider

from .common import (
    DEFAULT_OUTPUT_FILE_FORMAT,
    DEFAULT_SCRAPER_LOG_LEVEL,
    DEFAULT_SCRAPER_SILENT,
    LogLevelOption,
    OutputFileFormatOption,
    OutputFileNameArgument,
    SilentOption,
    file_format_to_scrapy,
)

app = typer.Typer()


@app.command()
def fetch(
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
    """Download Matricula Online's newsfeed.

Matricula has a minimal newsfeed where they announce new parishes, new registers, and\
 other changes: https://data.matricula-online.eu/en/nachrichten/.\
 This command will download the entire newsfeed or a limited number of news articles.
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
