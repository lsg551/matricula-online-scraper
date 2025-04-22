"""Utility functions for handling Matricula Online URLs."""


def get_parish_name(url: str) -> str:
    """Extract the parish name from the URL.

    Example:
    >>> get_parish_name("https://data.matricula-online.eu/de/LU/luxemburg/aspelt/")
    ... "aspelt"

    Args:
        url (str): The URL of the parish.

    Returns:
        str: The parish name.
    """
    return url.split("/")[-2]
