#!/usr/bin/env python3

"""
CLI entry point for scraping Matricula Online.
"""

from importlib.metadata import version as get_version
from typing import Annotated, Optional

import typer

from matricula_online_scraper.cli.newsfeed import app as newsfeed_app
from matricula_online_scraper.cli.parish import app as parish_app

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


@app.callback()
def version_callback(value: bool):
    if value:
        version = get_version("matricula-online-scraper")
        # remove prefix 'v'
        if version.startswith("v"):
            version = version[1:]
        typer.echo(version)
        raise typer.Exit()


# this will be executed when no command is called
# i.e. `$ matricula_online_scraper`
@app.callback()
def callback(
    version: Annotated[
        Optional[bool],
        typer.Option(
            "--version",
            callback=version_callback,
            is_eager=True,
            help="Show the CLI's version.",
        ),
    ] = None,
):
    pass


if __name__ == "__main__":
    app()
