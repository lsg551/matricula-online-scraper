"""
Ping the host and check if it is reachable.
"""

import requests
import pytest

HOST = "https://data.matricula-online.eu/en/"
LOCATION_SEARCH = "https://data.matricula-online.eu/en/suchen/"
LOCATION_SEARCH_ALL = (
    "https://data.matricula-online.eu/en/suchen/?place=&diocese=&date_range="
)


def test_ping_host():
    """Check that Matricula Online is reachable."""
    response = requests.head(HOST, timeout=5)
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "text/html; charset=utf-8"


def test_location_search():
    """Check that the location search works."""
    search_result = requests.get(LOCATION_SEARCH_ALL, timeout=5)
    assert search_result.status_code == 200
    assert search_result.headers["Content-Type"] == "text/html; charset=utf-8"
    assert "hits" in search_result.text


def test_parish_page():
    pytest.skip("Not implemented yet.")
