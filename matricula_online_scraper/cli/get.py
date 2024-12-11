from typing import Annotated, List, Optional
import sys
import typer
from pathlib import Path
from rich import console
from rich.text import Text
from .cli_utils.badges import Badge
from .cli_utils.color import Color
import logging
from ..spiders.church_register import ChurchRegisterSpider
from scrapy import crawler
import select
# from ..utils.pipeline_observer import PipelineObserver


logger = logging.getLogger(__name__)
stderr = console.Console(stderr=True)

app = typer.Typer()


@app.command()
def church_register(
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
