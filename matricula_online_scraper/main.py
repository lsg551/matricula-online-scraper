#!/usr/bin/env python3

"""
CLI entry point for scraping Matricula Online.
"""

from typing import Annotated, Optional
import pkg_resources
import typer
from matricula_online_scraper.cli.fetch import app as fetch_app

app = typer.Typer(
    help="Command Line Interface tool for scraping Matricula Online https://data.matricula-online.eu.",
    no_args_is_help=True,
)
app.add_typer(
    fetch_app,
    name="fetch",
)


@app.callback()
def version_callback(value: bool):
    if value:
        version = pkg_resources.get_distribution("matricula_online_scraper").version
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
