"""Test $ matricula-online-scraper … ."""

from typer.testing import CliRunner

from matricula_online_scraper.main import app

runner = CliRunner()


def test_app():
    """Check that the app is callable."""
    # test `$ matricula-online-scraper`
    # this should call without arguments or options should default into the help message
    result = runner.invoke(app)

    assert result.exit_code == 0
    assert "Usage:" in result.stdout
    assert "--help" in result.stdout
