"""Test $ matricula-online-scraper fetch … ."""

from typer.testing import CliRunner

from matricula_online_scraper.main import app

runner = CliRunner()


def test_fetch_command():
    """Check that the fetch command is callable but errors without any arguments or options."""
    # 'fetch' command does not default into the help message
    # instead it prints a warning and exits with error code 2
    result = runner.invoke(app, ["fetch"])

    assert result.exit_code == 2  # exit code for missing command
    assert "Error" in result.stdout
    assert "Missing command." in result.stdout


def test_fetch_command_help():
    """Check that the fetch command's help is reachable."""
    result = runner.invoke(app, ["fetch", "--help"])

    assert result.exit_code == 0
    assert "Usage:" in result.stdout
    assert "Commands" in result.stdout
    assert "location" in result.stdout
    assert "parish" in result.stdout


def test_fetch_location_command():
    """Check that the fetch location command is callable but errors without any arguments or options."""
    # this should error bc an argument is missing
    result = runner.invoke(app, ["fetch", "location"])

    assert result.exit_code == 2
    assert "Error" in result.stdout
    assert "Missing argument 'OUTPUT_FILE'." in result.stdout

    pass


def test_fetch_parish_command():
    """Check that the fetch parish command is callable but errors without any arguments or options."""
    pass
