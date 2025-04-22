"""CLI entry point for matricula-online-scraper."""
#!/usr/bin/env python3

import logging
from importlib.metadata import version as get_version
from typing import Annotated, Optional

import typer

from matricula_online_scraper.cli.newsfeed import app as newsfeed_app
from matricula_online_scraper.cli.parish import app as parish_app
from matricula_online_scraper.logging_config import Logging, LogLevel, get_logger

app = typer.Typer(
    help="""Command Line Interface (CLI) for scraping Matricula Online https://data.matricula-online.eu.

You can use this tool to scrape the three primary entities from Matricula:\n
1. Scanned parish registers (→ images of baptism, marriage, and death records)\n
2. A list of all available parishes (→ location metadata)\n
3. A list for each parish with metadata about its registers, including dates ranges, type etc.\n
""",
    no_args_is_help=True,
    epilog=(
        """Attach the --help flag to any subcommand for further help and to see its options. Press CTRL+C to exit at any time.\n
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
        if version_string.startswith("v"):
            version_string = version_string[1:]
        typer.echo(version_string, err=False)
        raise typer.Exit()


@app.callback()
def main(  # noqa: D103
    verbose: Annotated[
        Optional[bool],
        typer.Option(
            "--verbose",
            "-v",
            # is_eager=True,
            # callback=set_verbose_logging,
            help="Enable verbose logging (DEBUG).",
        ),
    ] = None,
    quiet: Annotated[
        Optional[bool],
        typer.Option(
            "--quiet",
            "-q",
            # callback=set_quiet_logging,
            help="Suppress all output (CRITICAL).",
        ),
    ] = None,
    log_level: Annotated[
        Optional[LogLevel],
        typer.Option(
            "--loglevel",
            "-l",
            help="Set the logging level.",
            hidden=True,
        ),
    ] = None,
    package_logging: Annotated[
        Optional[LogLevel],
        typer.Option(
            "--package-logging",
            help="Set the logging level for 3rd-party packags.",
            hidden=True,
        ),
    ] = None,
    version: Annotated[
        Optional[bool],
        typer.Option(
            "--version",
            is_eager=True,
            callback=version_callback,
            help="Show the CLI's version.",
        ),
    ] = None,
):
    logconf = Logging()

    if quiet and verbose:
        raise typer.BadParameter(
            "The --quiet and --verbose options are mutually exclusive."
        )
    if (verbose or quiet) and log_level:
        raise typer.BadParameter(
            "The --verbose or --quiet options are mutually exclusive with --loglevel."
        )
    if (verbose or quiet) and package_logging:
        raise typer.BadParameter(
            "The --verbose or --quiet options are mutually exclusive with --package-logging."
        )

    if verbose:
        logconf.log_level = LogLevel.DEBUG
        logconf.package_log_level = LogLevel.DEBUG
    if quiet:
        logconf.log_level = LogLevel.CRITICAL
        logconf.package_log_level = LogLevel.CRITICAL
    if log_level:
        logconf.log_level = log_level
    if package_logging:
        logconf.package_log_level = package_logging

    # NOTE: The loggers are using handlers. These are acting as additional filters.
    # They would need to be updated too. In this case, it is easier to parse all logging
    # flags first, and then initialize the logging.

    app_logger = logconf.setup_logging()


if __name__ == "__main__":
    app()
