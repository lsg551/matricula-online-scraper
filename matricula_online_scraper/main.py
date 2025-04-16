"""CLI entry point for matricula-online-scraper."""
#!/usr/bin/env python3

import logging
from importlib.metadata import version as get_version
from typing import Annotated, Optional

import typer

from matricula_online_scraper.cli.newsfeed import app as newsfeed_app
from matricula_online_scraper.cli.parish import app as parish_app
from matricula_online_scraper.logging_config import LogLevel, setup_logging

app = typer.Typer(
    help="""Command Line Interface (CLI) for scraping Matricula Online https://data.matricula-online.eu.

You can use this tool to scrape the three primary entities from Matricula:\n
1. Scanned parish registers (→ images of baptism, marriage, and death records)\n
2. A list of all available parishes (→ location metadata)\n
3. A list for each parish with metadata about its registers, including dates ranges, type etc.\n
""",
    no_args_is_help=True,
    epilog=(
        """Attach the --help flag to any subcommand for further help and to see its options.
\nSee https://github.com/lsg551/matricula-online-scraper for more information."""
    ),
)
app.add_typer(
    parish_app,
    name="parish",
    help="Scrape parish registers (1), a list with all available parishes (2) or a list of the available registers in a parish (3).",
)
app.add_typer(
    newsfeed_app,
    name="newsfeed",
    help="Scrape Matricula Online's Newsfeed.",
)


def version_callback(value: bool):
    """Print the version of the CLI in the format `0.1.0` and exit."""
    if value:
        version_string = get_version("matricula-online-scraper")
        # remove prefix 'v'
        if version_string.startswith("v"):
            version_string = version_string[1:]
        typer.echo(version_string, err=False)
        raise typer.Exit()


@app.callback()
def main(  # noqa: D103
    version: Annotated[
        Optional[bool],
        typer.Option(
            "--version",
            is_eager=True,
            help="Show the CLI's version.",
        ),
    ] = None,
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-v",
            help="Enable verbose logging (DEBUG).",
        ),
    ] = False,
    quiet: Annotated[
        bool,
        typer.Option(
            "--quiet",
            "-q",
            help="Suppress all output (CRITICAL).",
        ),
    ] = False,
    log_level: Annotated[
        Optional[LogLevel],
        typer.Option(
            "--log-level",
            "-l",
            help="Set the logging level.",
            hidden=True,
        ),
    ] = LogLevel.INFO,
    package_logging: Annotated[
        Optional[LogLevel],
        typer.Option(
            "--package-logging",
            help="Set the logging level for 3rd-party packags.",
            hidden=True,
        ),
    ] = LogLevel.CRITICAL,
):
    if version:
        version_callback(version)

    # --- initialize logging ---
    app_logger = setup_logging(
        log_level or LogLevel.INFO, package_logging or LogLevel.CRITICAL
    )

    # --- logging flags ---
    if quiet and verbose:
        raise typer.BadParameter(
            "The --quiet and --verbose options are mutually exclusive."
        )
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        app_logger.setLevel(logging.DEBUG)
    if quiet:
        logging.getLogger().setLevel(logging.CRITICAL)
        app_logger.setLevel(logging.CRITICAL)
    if log_level:
        app_logger.setLevel(log_level.value)
    if package_logging:
        logging.getLogger().setLevel(package_logging.value)


if __name__ == "__main__":
    app()
