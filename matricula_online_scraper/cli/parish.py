"""`parish` command group to interact with the three primary entities of Matricula.

Various subcommands allow to:
1. `fetch` one or more church registers from a given URL (this downloads the images of the register)
2. `list` all available parishes and their metadata
3. `show` the available registers in a parish and their metadata
"""

import sys
from pathlib import Path
from typing import Annotated, Any, Optional, Tuple

import typer
from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table
from scrapy import signals
from scrapy.crawler import CrawlerRunner
from twisted.internet import reactor

from matricula_online_scraper.spiders.parish import (
    ParishRegisterMetadata,
    ParishRegistersSpider,
)
from matricula_online_scraper.spiders.parish_list import (
    ParishMetadata,
    ParishMetadataSpider,
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
                    # NOTE: Force a non-asyncio reactor (https://docs.scrapy.org/en/2.13/topics/asyncio.html#switching-to-a-non-asyncio-reactor).
                    # Scrapy 3.12.0 made the asyncio reactor the default one (https://docs.scrapy.org/en/2.13/news.html#scrapy-2-13-0-2025-05-08).
                    # which causes the process to run indefinitely and never finish,
                    # see https://github.com/lsg551/matricula-online-scraper/issues/100
                    # For now, use a sync reactor to avoid this issue.
                    "TWISTED_REACTOR": None,
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


@app.command("list")
def list_parishes(
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
    # NOTE: https://data.matricula-online.eu/en/suchen/ has a dropdown with diocese names
    # that can be used for filtering. The HTML components uses integers to represent such options.
    # Unfortunately, that value is just passed around in Matricula and even used in the URL.
    # So one would have to scrape that dump dropdown to get the integer values.
    diocese: Annotated[
        Optional[int],
        typer.Option(
            help="Enum value of the diocese. (See their website for the list of dioceses.)",
            min=0,
        ),
    ] = None,
    # TODO: refactor this awful design, just make it a single option
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
    human_readable: Annotated[
        bool,
        typer.Option(
            "--human-readable",
            "-h",
            help=(
                "Print the ouput in a human readable format. Ignores the outfile option"
                " and writes to STDOUT instead."
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

    use_stdout = outfile == Path("-")
    collected_items: list[ParishMetadata] = []
    settings: dict[str, Any]

    if human_readable:
        settings = {}
    elif use_stdout:
        settings = {"FEEDS": {"stdout:": {"format": "jsonlines"}}}
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

        settings = {"FEEDS": {str(outfile): {"format": format.to_scrapy()}}}

    # NOTE: Force a non-asyncio reactor (https://docs.scrapy.org/en/2.13/topics/asyncio.html#switching-to-a-non-asyncio-reactor).
    # Scrapy 3.12.0 made the asyncio reactor the default one (https://docs.scrapy.org/en/2.13/news.html#scrapy-2-13-0-2025-05-08).
    # which causes the process to run indefinitely and never finish,
    # see https://github.com/lsg551/matricula-online-scraper/issues/100
    # For now, use a sync reactor to avoid this issue.
    settings["TWISTED_REACTOR"] = None

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
        if human_readable:
            cmd_logger.warning(
                "The --human-readable option should only be used if filters are applied to shrink potentially large output."
                " This might cause unexpected behavior in your terminal."
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
            runner = CrawlerRunner(settings=settings)
            crawler = runner.create_crawler(ParishMetadataSpider)

            if human_readable:

                def collect(item, response, spider):
                    collected_items.append(item)

                crawler.signals.connect(collect, signal=signals.item_scraped)

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
        + (
            f" The output was saved to: {outfile.resolve()}"
            if outfile and not use_stdout and not human_readable
            else ""
        )  # type: ignore
    )

    if human_readable:
        collected_items.sort(key=lambda item: item["region"])

        table = Table(
            title="Parishes in Matricula Online.",
            caption=f"{len(collected_items)} parishes found.",
        )
        table.add_column("Name", justify="left")
        table.add_column("Region", justify="left")
        table.add_column("Country", justify="left")
        table.add_column("URL", justify="left")
        if not exclude_coordinates:
            table.add_column("Coordinates", justify="left")

        for item in collected_items:
            table.add_row(
                item["name"],
                item["region"],
                item["country"],
                f"[link={item['url']}]URL[/link]",
                (
                    f"{item['latitude']}, {item['longitude']}"
                    if not exclude_coordinates
                    and "latitude" in item
                    and "longitude" in item
                    else None
                ),
            )

        console = Console()
        console.print(table)


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
    human_readable: Annotated[
        bool,
        typer.Option(
            "--human-readable",
            "-h",
            help=(
                "Print the ouput in a human readable format. Ignores the outfile option"
                " and writes to STDOUT instead."
            ),
        ),
    ] = False,
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
    settings: dict[str, Any]
    collected_items: list[ParishRegisterMetadata] = []

    if human_readable:
        settings = {}
    elif use_stdout:
        settings = {"FEEDS": {"stdout:": {"format": "jsonlines"}}}
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

        settings = {"FEEDS": {str(outfile): {"format": format.to_scrapy()}}}

    # NOTE: Force a non-asyncio reactor (https://docs.scrapy.org/en/2.13/topics/asyncio.html#switching-to-a-non-asyncio-reactor).
    # Scrapy 3.12.0 made the asyncio reactor the default one (https://docs.scrapy.org/en/2.13/news.html#scrapy-2-13-0-2025-05-08).
    # which causes the process to run indefinitely and never finish,
    # see https://github.com/lsg551/matricula-online-scraper/issues/100
    # For now, use a sync reactor to avoid this issue.
    settings["TWISTED_REACTOR"] = None

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        transient=True,
        console=Console(stderr=True),
    ) as progress:
        progress.add_task("Scraping...", total=None)

        try:
            runner = CrawlerRunner(settings=settings)
            crawler = runner.create_crawler(ParishRegistersSpider)

            if human_readable:

                def collect(item, response, spider):
                    collected_items.append(item)

                crawler.signals.connect(collect, signal=signals.item_scraped)

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
        + (
            f" The output was saved to: {outfile.resolve()}"
            if outfile and not use_stdout and not human_readable
            else ""
        )  # type: ignore
    )

    if human_readable:
        table = Table(
            # title="" # TODO: get name of parish
            caption=f"{len(collected_items)} parish registers found for {parish}",
        )
        table.add_column("Name", justify="left")
        table.add_column("Accession Num.", justify="left")
        table.add_column("Date", justify="left")
        table.add_column("URL", justify="left")
        table.add_column("Details", justify="left")

        for item in collected_items:
            table.add_row(
                item.name,
                item.accession_number,
                item.date,
                f"[link={item.url}]URL[/link]",
                ", ".join(f'{key}="{value}"' for key, value in item.details.items()),
            )

        console = Console()
        console.print(table)
