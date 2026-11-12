"""Test $ matricula-online-scraper … ."""

from typer.testing import CliRunner

from matricula_online_scraper.main import app

runner = CliRunner()


def test_app():
    """Check that the app is callable."""
    # test `$ matricula-online-scraper`
    # without arguments or options it defaults into the help message;
    # typer/click exit with code 2 when no command is given
    result = runner.invoke(app)

    assert result.exit_code == 2
    assert "Usage:" in result.stdout
    assert "--help" in result.stdout
