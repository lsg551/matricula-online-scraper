import logging
import select
import sys
from pathlib import Path
from typing import Annotated, List, Optional, Tuple

import typer
from rich import (
    console,
    print,  # pylint: disable=redefined-builtin
)
from rich.text import Text
from scrapy import crawler

from matricula_online_scraper.spiders.locations_spider import LocationsSpider
from matricula_online_scraper.spiders.parish_registers_spider import (
    ParishRegistersSpider,
)

from ..spiders.church_register import ChurchRegisterSpider
from .cli_utils.badges import Badge
from .cli_utils.color import Color
from .common import (
    DEFAUL_APPEND,
    DEFAULT_OUTPUT_FILE_FORMAT,
    DEFAULT_SCRAPER_LOG_LEVEL,
    DEFAULT_SCRAPER_SILENT,
    AppendOption,
    LogLevelOption,
    OutputFileFormatOption,
    OutputFileNameArgument,
    SilentOption,
    file_format_to_scrapy,
)

app = typer.Typer()

# from ..utils.pipeline_observer import PipelineObserver


logger = logging.getLogger(__name__)
stderr = console.Console(stderr=True)

app = typer.Typer()


@app.command()
def fetch(
    urls: Annotated[
        Optional[List[str]],
        typer.Argument(
            help=(
                "One or more URLs to church register pages,"
                " for example https://data.matricula-online.eu/de/deutschland/augsburg/aach/1-THS/"
                " '/1-THS' is the identifier of one church register from Aach, a parish in Augsburg, Germany."
                " Note that the parameter '?pg=1' may or may not be included in the URL."
                " It will by ignored anyway, because it does not alter the behavior of the scraper."
                " If no URL is provided, this argument is expected to be read from stdin."
            )
        ),
    ] = None,
    directory: Annotated[
        Path,
        typer.Option(
            "--directory",
            "-d",
            help="Directory to save the image files in.",
        ),
    ] = Path.cwd() / "church_register_images",
    debug: Annotated[
        bool,
        typer.Option(
            help="Enable debug mode for scrapy.",
        ),
    ] = False,
):
    """(1) Download a church register.

While all scanned parish registers can be opened in a web viewer,\
 for example the 7th page of this parish register: https://data.matricula-online.eu/de/oesterreich/kaernten-evAB/eisentratten/01-02D/?pg=7,\
 it has no option to download a single page or the entire book. This command allows you\
 to do just that and download the entire book or a single page.

\n\nExample:\n\n
$ matricula-online-scraper parish fetch https://data.matricula-online.eu/de/oesterreich/kaernten-evAB/eisentratten/01-02D/?pg=7
    """
    # timeout in seconds
    TIMEOUT = 0.1

    if not urls:
        readable, _, _ = select.select([sys.stdin], [], [], TIMEOUT)

        if readable:
            urls = sys.stdin.read().splitlines()
        else:
            stderr.print(
                Badge.Error,
                Text("No URLs provided via stdin.", style=Color.Red),
                "Please provide at least one URL as argument or via stdin.",
                "Use the --help flag for more information.",
            )
            raise typer.Exit(1)

    # won't happen, only to satisfy the type checker
    if not urls:
        raise NotImplementedError()

    # observer = PipelineObserver(start_urls=urls)

    try:
        process = crawler.CrawlerProcess(
            settings={
                "LOG_ENABLED": debug,
                "LOG_LEVEL": "DEBUG" if debug else "CRITICAL",
                "ITEM_PIPELINES": {"scrapy.pipelines.images.ImagesPipeline": 1},
                "IMAGES_STORE": directory.resolve(),
            }
        )
        process.crawl(
            ChurchRegisterSpider,
            # observer=observer,
            start_urls=urls,
        )
        process.start()

    except Exception as err:
        raise typer.Exit(1) from err

    else:
        stderr.print(
            Badge.Success,
            Text("Finished scraping church register images.", style=Color.Green),
        )

    # finally:
    #     observer.update_initiator_statuses()
    #     stderr.print(observer.start_urls)


@app.command()
def list(
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
    """(2) List available parishes.

Matricula has a huge list of all parishes that it possesses digitized records for.\
 It can be directly accessed on the website: https://data.matricula-online.eu/de/bestande/

This command allows you to scrape that list with all available parishes and\
 their metadata.

\n\nExample:\n\n
$ matricula-online-scraper parish list

\n\nNOTE:\n\n
This command will take a while to run, because it fetches all parishes.\
 A GitHub workflow does this once a week and caches the CSV file in the repository.\
 Preferably, you should download that file instead: https://github.com/lsg551/matricula-online-scraper/raw/cache/parishes/parishes.csv.gz
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
def show(
    url: Annotated[
        str,
        typer.Argument(help=("Parish URL to show available registers for.")),
    ],
    output_file_name: OutputFileNameArgument = Path("matricula-newsfeed"),
    output_file_format: OutputFileFormatOption = DEFAULT_OUTPUT_FILE_FORMAT,
    append: AppendOption = DEFAUL_APPEND,
    log_level: LogLevelOption = DEFAULT_SCRAPER_LOG_LEVEL,
    silent: SilentOption = DEFAULT_SCRAPER_SILENT,
):
    """(3) Show available registers in a parish and their metadata.

Each parish on Matricula has its own page, which lists all available registers\
 and their metadata as well as some information about the parish itself.

\n\nExample:\n\n
$ matricula-online-scraper parish show https://data.matricula-online.eu/de/oesterreich/kaernten-evAB/eisentratten/
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

        process.crawl(ParishRegistersSpider, start_urls=[url])  # type: ignore
        process.start()

        print(
            "[green]Scraping completed successfully. "
            f"Output saved to: {output_path.absolute()}[/green]"
        )

    except Exception as exception:
        print("[red]An unknown error occurred while scraping.[/red]")
        raise typer.Exit(code=1) from exception
