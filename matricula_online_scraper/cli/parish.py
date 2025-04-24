"""`parish` command group to interact with the three primary entities of Matricula.

Various subcommands allow to:
1. `fetch` one or more church registers from a given URL (this downloads the images of the register)
2. `list` all available parishes and their metadata
3. `show` the available registers in a parish and their metadata
"""

import select
import sys
from pathlib import Path
from typing import Annotated, List, Optional, Tuple

import typer
from rich.console import Console
from rich.progress import (
    DownloadColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
    TransferSpeedColumn,
)
from rich.text import Text
from scrapy import crawler
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
            "--outdirectory",
            "-o",
            help="Directory to save the image files in.",
            file_okay=False,
            dir_okay=True,
            resolve_path=True,
            # allow_dash=True, # see issue #75
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

    # timeout in seconds to wait for stdin input
    TIMEOUT = 0.1
    # read from stdin if no urls are provided
    if not urls:
        readable, _, _ = select.select([sys.stdin], [], [], TIMEOUT)
        if readable:
            urls = sys.stdin.read().splitlines()
        else:
            raise typer.BadParameter(
                "No URLs provided via terminal or STDIN."
                " Please provide at least one URL as an argument or via stdin.",
                param_hint="urls",
            )

    # only to satisfy the type checker, should never happen
    if not urls:
        raise NotImplementedError("No URLs provided and stdin is empty.")

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
            help=f"File to which the data is written (formats: {', '.join(FileFormat)})",
            exists=False,
            file_okay=True,
            dir_okay=False,
            resolve_path=True,
            # allow_dash=True, # TODO: see issue #75
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

    # all search parameters are unused => fetching everything takes some time
    if (
        place is None
        or place == ""
        and diocese is None
        and date_filter is False
        and date_range is None
    ):
        # TODO: prompt the user before continuing, add option -y,--yes to skip
        cmd_logger.warning(
            "No search parameters were provided to restrict the search."
            " This will create a list with all available parishes."
            " To avoid lengthy scraping times, use --exclude-coordinates to speed up the process"
            " or download the cached CSV file from the repository:"
            " https://github.com/lsg551/matricula-online-scraper/raw/cache/parishes/parishes.csv.gz"
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
            runner = CrawlerRunner(
                settings={"FEEDS": {str(outfile): {"format": format.to_scrapy()}}}
            )

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
        f"Done! Successfully scraped the parish list. The output was saved to: {outfile.resolve()}"
    )


@app.command()
def show(
    parish: Annotated[
        str,
        typer.Argument(help=("Parish URL to show available registers for.")),
    ],
    outfile: Annotated[
        Optional[Path],
        typer.Option(
            "-o",
            "--outfile",
            help=(
                f"File to which the data is written (formats: {', '.join(FileFormat)})."
                r" Default is `matricula_parish_{name}.jsonl`."
            ),
            show_default=False,
            exists=False,
            file_okay=True,
            dir_okay=False,
            resolve_path=True,
            # allow_dash=True, # TODO: see issue #75
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

    if outfile.exists():
        raise typer.BadParameter(
            f"A file with the same path as the outfile already exists: {outfile.resolve()}."
            " Will not overwrite it. Delete the file or choose a different path. Aborting.",
            param_hint="outfile",
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
            runner = CrawlerRunner(
                settings={"FEEDS": {str(outfile): {"format": format.to_scrapy()}}}
            )

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
        f"Done! Successfully scraped the parish. The output was saved to: {outfile.resolve()}"
    )
