"""Utility functions to work with Matricula's pagination and URLs."""

from urllib.parse import parse_qs, urlencode, urlparse, urlunparse


def create_next_url(current: str, next_page: str) -> str:
    """Combines the current Matricula URL with the next page number.

    Many (not all!) Matricula pages have a pagination at the bottom.
    This information can be used to construct a URL for the next page.

    Assuming the pagination was scraped and the next page number extracted
    from the pagination components, see the example below.

    Example:
    >>> scraped_pagination = "2"
    >>> create_next_url("https://data.matricula-online.eu/de/nachrichten/", scraped_pagination)
    ... "https://data.matricula-online.eu/de/nachrichten/?page=2"

    Args:
        current (str): Current URL to be modified with the next page number.
        next_page (str): Stringified integer, pager number that will be concatenated to the URL.

    Returns:
        str: The new URL with the next page number.
    """
    current_url = urlparse(current)
    url_parts = list(current_url)
    query = parse_qs(current_url.query)

    params = {"page": next_page}
    query.update(params)  # type: ignore # NOTE: it's fine, leave it as is

    url_parts[4] = urlencode(query)
    new_url = urlunparse(url_parts)

    return new_url
