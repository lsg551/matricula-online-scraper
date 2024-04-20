#!/usr/bin/env python3

"""
CLI entry point for scraping Matricula Online.
"""

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

if __name__ == "__main__":
    app()
