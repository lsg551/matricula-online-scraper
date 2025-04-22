"""Utility functions for parsing date strings from Matricula Online."""

from datetime import date, datetime


def parse_matricula_datestr(value: str) -> date:
    """Parse a date string into a date object.

    This function parses typical date strings from Matricula Online's newsfeed
    and converts them into a date object.

    Typical date strings used by Matricula Online are:
    - "June 3, 2024"
    - "Dec. 19, 2023"

    Args:
        value (str): The date string to parse.

    Returns:
        date: The parsed date object.
    """
    # example: "June 3, 2024" or "Dec. 19, 2023"
    if "." in value:
        # shorted month name
        return datetime.strptime(value, "%b. %d, %Y").date()

    # full month name
    return datetime.strptime(value, "%B %d, %Y").date()
