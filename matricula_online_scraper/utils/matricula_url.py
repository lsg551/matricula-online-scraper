"""This module handles validation and categorization of Matricula URLs.

It's solely a user feature to inform them about potentially invalid URLs
or the wrong subcommand for a specific URL type.


Matricula URL Structure
=======================

General:
- HOST: https://data.matricula-online.eu/
- LOCALE: /de/ or /en/

Pages:
- SEARCH: /de/suchen/
- COUNTRY: /de/<COUNTRY> e.g. /de/deutschland
- REGION: /de/<COUNTRY>/<REGION>/ e.g. /de/deutschland/aachen
- PARISH: /de/<COUNTRY>/<REGION>/<PARISH>/ e.g. /de/deutschland/aachen/hellenthal-st-anna/
- PARISH REGISTER: /de/<COUNTRY>/<REGION>/<PARISH>/<REGISTER> e.g. /de/deutschland/aachen/hellenthal-st-anna/KB+194_2
  and optionally some URL parameters like ?pg=2
"""

from urllib.parse import urlsplit

from matricula_online_scraper.logging_config import get_logger
from matricula_online_scraper.utils.user_console import UserConsole

logger = get_logger(__name__)


class MatriculaURL:
    """Base class for Matricula URLs."""

    def __init__(self, url: str):
        """Create a new Matricula URL instance."""
        self.url = url
        self.parsed = urlsplit(url, allow_fragments=False)

    def __str__(self) -> str:  # noqa: D105
        return self.url

    def __repr__(self) -> str:  # noqa: D105
        return f"{self.__class__.__name__}({self.url!r})"

    @property
    def _segments(self) -> list[str]:
        """Get the segments of the URL path.

        Same as `self.parsed.path.split("/")` but removes empty segments `""`.

        Returns:
            list[str]: The segments of the URL path.
        """
        return list(filter(lambda x: x != "", self.parsed.path.split("/")))

    @property
    def is_valid(self) -> bool:
        """Check if the URL is valid.

        NOTE: On the base class, this only checks if the URL is well-formed,
        specifically if the host is Matricula Online. Other than that, it does
        not validate if the URL follows the expected Matricula Online structure.

        Returns:
            bool: True if the URL is valid, False otherwise.
        """
        return (
            self.parsed.scheme == "https"
            and self.parsed.netloc == "data.matricula-online.eu"
        )

    @classmethod
    def _from_arg(cls, value: str) -> "MatriculaURL":
        """Create a MatriculaURL instance from a string value.

        NOTE: This method is intended to be used as a typer parser for CLIs.

        Example:
        - https://typer.tiangolo.com/tutorial/parameter-types/custom-types/#type-parser

        Args:
            value (str): The URL string to create the instance from.

        Returns:
            MatriculaURL: An instance of the appropriate subclass of MatriculaURL.
        """
        instance = cls(value)
        if not instance.is_valid:
            raise ValueError(f"Invalid Matricula URL: {value}")
        return instance


class ParishPageURL(MatriculaURL):
    """Class representing a Matricula URL for a parish page and only a parish page.

    Other than the base class, this class validates to true iff the URL is a
    parish page URL, for example:
    - https://data.matricula-online.eu/de/deutschland/aachen/hellenthal-st-anna
    """

    @property
    def is_valid(self) -> bool:
        """Check if the URL is a valid parish page URL.

        Returns:
            bool: True if the URL is a valid parish page URL, False otherwise.
        """
        return (
            MatriculaURL.is_valid
            and len(self._segments) == 4  # /de/<COUNTRY>/<REGION>/<PARISH>
            and self.parsed.query == ""
        )

    @property
    def locale(self) -> str:
        """Get the locale of the parish page URL.

        Returns:
            str: The locale of the parish page URL, e.g., "de" or "en".
        """
        return self.parsed.path.split("/")[1]

    @property
    def country(self) -> str:
        """Get the country from the parish page URL.

        Returns:
            str: The country part of the parish page URL, e.g., "deutschland".
        """
        return self.parsed.path.split("/")[2]

    @property
    def region(self) -> str:
        """Get the region from the parish page URL.

        Returns:
            str: The region part of the parish page URL, e.g., "aachen".
        """
        return self.parsed.path.split("/")[3]

    @property
    def name(self) -> str:
        """Get the name of the parish from the parish page URL.

        Returns:
            str: The parish part of the parish page URL, e.g., "hellenthal-st-anna".
        """
        return self.parsed.path.split("/")[4]


class ParishRegisterURL(ParishPageURL):
    """Class representing a Matricula URL for a specific parish register.

    This class validates to true iff the URL is a parish register URL, for example:
    - https://data.matricula-online.eu/de/deutschland/aachen/hellenthal-st-anna/KB+194_2
    - https://data.matricula-online.eu/de/deutschland/aachen/hellenthal-st-anna/KB+194_2?pg=2
    """

    @property
    def is_valid(self) -> bool:
        """Check if the URL is a valid parish register URL.

        Returns:
            bool: True if the URL is a valid parish register URL, False otherwise.
        """
        return (
            MatriculaURL.is_valid
            and len(self._segments) == 5  # /de/<COUNTRY>/<REGION>/<PARISH>/<REGISTER>
            and (
                self.parsed.query == "" or self.parsed.query.startswith("pg=")
            )  # optional query parameter
        )

    @property
    def register(self) -> str:
        """Get the register from the parish register URL.

        Returns:
            str: The register part of the parish register URL, e.g., "KB+194_2".
        """
        return self._segments[-1]

    @property
    def register_page(self) -> int | None:
        """Get the page number from the parish register URL.

        Returns:
            int: The page number if present, otherwise None.
        """
        return (
            int(self.parsed.query.split("pg=")[-1]) if self.parsed.query != "" else None
        )
