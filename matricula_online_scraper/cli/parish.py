"""`parish` command group to interact with the three primary entities of Matricula.

Various subcommands allow to:
1. `fetch` one or more church registers from a given URL (this downloads the images of the register)
2. `list` all available parishes and their metadata
3. `show` the available registers in a parish and their metadata
"""

import select
import sys
from pathlib import Path
from typing import Annotated, Optional, Tuple

import typer
from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from scrapy.crawler import CrawlerRunner
from twisted.internet import reactor

from matricula_online_scraper.spiders.locations_spider import LocationsSpider
from matricula_online_scraper.spiders.parish_registers_spider import (
    ParishRegistersSpider,
)
from matricula_online_scraper.utils.matricula_url import get_parish_name

from ..logging_config import get_logger
from ..spiders.church_register import ChurchRegisterSpider
from ..utils.file_format import FileFormat

logger = get_logger(__name__)

app = typer.Typer()


@app.command()
def fetch(
    urls: Annotated[
        Optional[list[str]],
        typer.Argument(
            help=(
                "One or more URLs to church register pages."
                " The parameter '?pg=1' may or may not be included in the URL."
                " If no URL is provided, read from STDIN."
                # NOTE: It will block until EOF is reached or the pipeline is closed
                # because all data must be gathered from STDIN before proceeding
            )
        ),
    ] = None,
    directory: Annotated[
        Path,
        typer.Option(
            "--outdirectory",
            "-o",
            help="Directory to save the image files in.",
            file_okay=False,
            dir_okay=True,
            resolve_path=True,
        ),
    ] = Path.cwd() / "parish_register_images",
):
    """(1) Download a church register.https://docs.astral.sh/ruff/rules/escape-sequence-in-docstring.

    While all scanned parish registers can be opened in a web viewer,\
 for example the 7th page of this parish register: https://data.matricula-online.eu/de/oesterreich/kaernten-evAB/eisentratten/01-02D/?pg=7,\
 it has no option to download a single page or the entire book. This command allows you\
 to do just that and download the entire book or a single page.

    \n\nExample:\n\n
    $ matricula-online-scraper parish fetch https://data.matricula-online.eu/de/oesterreich/kaernten-evAB/eisentratten/01-02D/?pg=7
    """
    cmd_logger = logger.getChild(fetch.__name__)
    cmd_logger.debug("Start fetching Matricula Online parish registers.")

    # read from stdin if no urls are provided
    if not urls:
        urls = sys.stdin.read().splitlines()

    if not urls:
        raise typer.BadParameter(
            "No URLs provided via terminal or STDIN."
            " Please provide one or more URLs as arguments or via stdin.",
            param_hint="urls",
        )

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        transient=True,
        console=Console(stderr=True),
    ) as progress:
        progress.add_task(
            "Scraping...",
            total=len(urls),  # use the number or urls as a rough estimate
        )

        try:
            runner = CrawlerRunner(
                settings={
                    "ITEM_PIPELINES": {"scrapy.pipelines.images.ImagesPipeline": 1},
                    "IMAGES_STORE": directory.resolve(),
                }
            )
            crawler = runner.create_crawler(ChurchRegisterSpider)

            deferred = runner.crawl(crawler, start_urls=urls)
            deferred.addBoth(lambda _: reactor.stop())  # type: ignore
            reactor.run()  # type: ignore  # blocks until the crawling is finished

        except Exception as exception:
            cmd_logger.exception(
                "An error occurred while scraping Matricula Online parish registers."
            )
            raise typer.Exit(1) from exception

    cmd_logger.info(
        f"Done! Successfully scraped the parish registers. The output was saved to: {directory.resolve()}"
    )


@app.command()
def list(
    outfile: Annotated[
        Path,
        typer.Option(
            "-o",
            "--outfile",
            help=(
                f"File to which the data is written (formats: {', '.join(FileFormat)})"
                " Use '-' to write to STDOUT."
            ),
            exists=False,
            file_okay=True,
            dir_okay=False,
            resolve_path=True,
            allow_dash=True,  # use '-' to write to stdout
        ),
    ] = Path("matricula_parishes.jsonl"),
    place: Annotated[
        Optional[str], typer.Option(help="Full text search for a location.")
    ] = None,
    diocese: Annotated[
        Optional[int],
        typer.Option(
            help="Enum value of the diocese. (See their website for the list of dioceses.)",
            min=0,
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
            "--exclude-coordinates",
            help=(
                "Exclude coordinates from the output to speed up the scraping process."
                " Coordinates will be scraped by default."
            ),
        ),
    ] = False,
    skip_prompt: Annotated[
        bool,
        typer.Option(
            "--yes",
            "-y",
            help="Skip any prompt with YES.",
        ),
    ] = False,
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
    cmd_logger = logger.getChild(fetch.__name__)
    cmd_logger.debug("Start fetching Matricula Online parishes.")

    use_stdout = outfile == Path("-")
    feed: dict[str, dict[str, str]]

    if use_stdout:
        feed = {"stdout:": {"format": "jsonlines"}}
    else:
        try:
            format = FileFormat(outfile.suffix[1:])
        except Exception as e:
            raise typer.BadParameter(
                f"Invalid file format: '{outfile.suffix[1:]}'. Allowed file formats are: {', '.join(FileFormat)}",
                param_hint="outfile",
            )

        # seems like this is not handled by typer even if suggested through `exists=False`
        # maybe only `exists=True` has meaning and is checked
        if outfile.exists():
            raise typer.BadParameter(
                f"A file with the same path as the outfile already exists: {outfile.resolve()}."
                " Will not overwrite it. Delete the file or choose a different path. Aborting.",
                param_hint="outfile",
            )

        feed = {str(outfile): {"format": format.to_scrapy()}}

    # all search parameters are unused => fetching everything takes some time
    if (
        place is None
        or place == ""
        and diocese is None
        and date_filter is False
        and date_range is None
    ):
        cmd_logger.warning(
            "No search parameters were provided to restrict the search."
            " This will create a list with all available parishes."
            " To avoid lengthy scraping times, use --exclude-coordinates to speed up the process"
            " or download the cached CSV file from the repository:"
            " https://github.com/lsg551/matricula-online-scraper/raw/cache/parishes/parishes.csv.gz"
        )
        if not skip_prompt:
            typer.confirm(
                "Are you sure you want to proceed scraping without any filters?",
                default=True,
                abort=True,
                err=True,
            )

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        transient=True,
        console=Console(stderr=True),
    ) as progress:
        progress.add_task("Scraping...", total=None)

        try:
            runner = CrawlerRunner(settings={"FEEDS": feed})
            crawler = runner.create_crawler(LocationsSpider)
            deferred = runner.crawl(
                crawler,
                place=place or "",
                diocese=diocese,
                date_filter=date_filter,
                date_range=date_range or (0, 9999),
                include_coordinates=not exclude_coordinates,
            )
            deferred.addBoth(lambda _: reactor.stop())  # type: ignore
            reactor.run()  # type: ignore  # blocks until the crawling is finished

        except Exception as exception:
            cmd_logger.exception(
                "An error occurred while scraping Matricula Online parishes."
            )
            raise typer.Exit(code=1) from exception

    cmd_logger.info(
        f"Done! Successfully scraped the parish list."
        + (f" The output was saved to: {outfile.resolve()}" if not use_stdout else "")
    )


@app.command()
def show(
    parish: Annotated[
        Optional[str],
        typer.Argument(
            help=(
                "Parish URL to scrape available registers and metadata for. Reads from STDIN if not provided."
            )
        ),
    ] = None,
    outfile: Annotated[
        Optional[Path],
        typer.Option(
            "-o",
            "--outfile",
            help=(
                f"File to which the data is written (formats: {', '.join(FileFormat)})."
                " Use '-' to write to STDOUT."
                r" Default is `matricula_parish_{name}.jsonl`."
            ),
            show_default=False,
            exists=False,
            file_okay=True,
            dir_okay=False,
            resolve_path=True,
            allow_dash=True,  # use '-' to write to stdout
        ),
    ] = None,
):
    """(3) Show available registers in a parish and their metadata.

    Each parish on Matricula has its own page, which lists all available registers\
 and their metadata as well as some information about the parish itself.

    \n\nExample:\n\n
    $ matricula-online-scraper parish show https://data.matricula-online.eu/de/oesterreich/kaernten-evAB/eisentratten/
    """
    cmd_logger = logger.getChild(fetch.__name__)
    cmd_logger.debug("Start fetching Matricula Online parish.")

    # read from stdin if no parish is provided
    if not parish:
        cmd_logger.debug(
            f"Reading from STDIN as no argument for 'parish' was provided."
        )
        parish = sys.stdin.read().strip()

    if not parish:
        raise typer.BadParameter(
            "No parish URL provided via terminal or STDIN."
            " Please provide a parish URL as an argument or via STDIN.",
            param_hint="parish",
        )

    use_stdout = outfile == Path("-")
    feed: dict[str, dict[str, str]]

    if use_stdout:
        feed = {"stdout:": {"format": "jsonlines"}}
    else:
        if not outfile or outfile == "":
            outfile = Path(f"matricula_parish_{get_parish_name(parish)}.jsonl")
            cmd_logger.debug(
                f"No outfile provided. Using constructed default name: {outfile.resolve()}"
            )

        try:
            format = FileFormat(outfile.suffix[1:])
        except Exception as e:
            raise typer.BadParameter(
                f"Invalid file format: '{outfile.suffix[1:]}'. Allowed file formats are: {', '.join(FileFormat)}",
                param_hint="outfile",
            )

        # seems like this is not handled by typer even if suggested through `exists=False`
        # maybe only `exists=True` has meaning and is checked
        if outfile.exists():
            raise typer.BadParameter(
                f"A file with the same path as the outfile already exists: {outfile.resolve()}."
                " Will not overwrite it. Delete the file or choose a different path. Aborting.",
                param_hint="outfile",
            )

        feed = {str(outfile): {"format": format.to_scrapy()}}

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        transient=True,
        console=Console(stderr=True),
    ) as progress:
        progress.add_task("Scraping...", total=None)

        try:
            runner = CrawlerRunner(settings={"FEEDS": feed})

            crawler = runner.create_crawler(ParishRegistersSpider)

            deferred = runner.crawl(crawler, start_urls=[parish])
            deferred.addBoth(lambda _: reactor.stop())  # type: ignore
            reactor.run()  # type: ignore  # blocks until the crawling is finished

        except Exception as exception:
            cmd_logger.exception(
                "An error occurred while scraping Matricula Online's newsfeed."
            )
            raise typer.Exit(code=1) from exception

    cmd_logger.info(
        f"Done! Successfully scraped the parish."
        + (f" The output was saved to: {outfile.resolve()}" if not use_stdout else "")  # type: ignore
    )
