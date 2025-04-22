"""Custom image pipeline to store downloaded images.

This pipeline is used to customized the path where the images are stored.
It can be used by specifying a valid module path in the Scrapy settings.
"""

import hashlib
import re
from pathlib import Path

from attr import dataclass
from scrapy.http.request import Request
from scrapy.http.response import Response
from scrapy.item import Item
from scrapy.pipelines.images import ImagesPipeline

from matricula_online_scraper.logging_config import get_logger

logger = get_logger(__name__)


# @dataclass
# class DecomposedImageURL:
#     """Parts of the URL of an image on Matricula Online.

#     Note that the URL is expected to have the following format,
#     but the parameter `?pg=1` is omitted.

#     Examples:
#     >>> _decompose_image_url("https://data.matricula-online.eu/de/deutschland/augsburg/aach/1-THS/?pg=1")
#     ... DecomposedImageURL(
#     ...     country="deutschland",
#     ...     region="augsburg",
#     ...     parish="aach",
#     ...     fond_id="1-THS",
#     ... )
#     """

#     country: str
#     region: str
#     parish: str
#     fond_id: str


# def _decompose_image_url(url: str) -> DecomposedImageURL:
#     """Decompose the URL of an image on Matricula Online."""

#     match = re.match(
#         r"https://data.matricula-online.eu/(?P<country_code>\w+)/(?P<country>\w+)/(?P<region>\w+)/(?P<parish>\w+)/(?P<fond_id>[\w-]+)",
#         url,
#     )

#     if match is None:
#         raise ValueError(f"Could not decompose URL {url}")

#     country = match.group("country")
#     region = match.group("region")
#     parish = match.group("parish")
#     fond_id = match.group("fond_id")

#     return DecomposedImageURL(country, region, parish, fond_id)


def _extract_unique_id(image_url: str) -> Path:
    """Return the part of an image URL that uniquely identifies the image.

    Examples:
    >>> _extract_unique_id("https://data.matricula-online.eu/de/deutschland/augsburg/aach/1-THS/?pg=1")
    ... "deutschland/augsburg/aach/1-THS"
    >>> _extract_unique_id("https://data.matricula-online.eu/en/deutschland/augsburg/aach/1-THS/")
    ... "deutschland/augsburg/aach/1-THS"
    >>> _extract_unique_id("https://data.matricula-online.eu/en/deutschland/augsburg/aach/1-THS")
    ... "deutschland/augsburg/aach/1-THS"
    """
    # grab part after '.eu/de/' or '.eu/en/' until the last '/' before the query parameter or end of string
    match = re.search(r"\.eu/(?:\w+)/(.+?)(?:/|\?pg=\d+)?$", image_url)

    if match is None:
        raise ValueError(f"Could not extract unique ID from URL {image_url}")

    return Path(match.group(1))


# BUG: Matricula is too inconsistent to extract the page number from the URL.
# def _extract_page_number(image_url: str) -> int:
#     """Return the page number of an image URL.

#     Examples:
#     >>> _extract_page_number("http://hosted-images.matricula-online.eu/images/matricula/BiAA/ABA_Pfarrmatrikeln_Aach_001/ABA_Pfarrmatrikeln_Aach_001_0083.jpg")
#     ... 83

#     Raises:
#         ValueError: If the page number could not be extracted.
#     """

#     # Matricula is very inconsistent. It might use "[…]_0001.jpg", "[…]-01.jpg" or something entirely different.

#     match = re.search(r"(\d+).jpg$", image_url)

#     if match is None:
#         raise ValueError(f"Could not extract page number from URL {image_url}")

#     return int(match.group(1))


def _extract_last_path_segment(image_url: str) -> str:
    """Return the last path segment of an image URL.

    Used as the page number.

    Examples:
    >>> _extract_last_path_segment("http://hosted-images.matricula-online.eu/images/matricula/DAG/MatrikenGraz-Seckau/Ardning/6014/Taufbuch/01/1786-1830/Ardning_6014_Taufbuch_01_1786-1830___Seite__S0004.jpg")
    ... "Ardning_6014_Taufbuch_01_1786-1830___Seite__S0004"
    """
    match = re.search(r"/([^/]+)\.jpg$", image_url)

    if match is None:
        raise ValueError(f"Could not extract last path segment from URL {image_url}")

    return match.group(1)


class CustomImagesPipeline(ImagesPipeline):
    """Custom image pipelines to store images in a structured way (= custom paths)."""

    def file_path(
        self,
        request: Request,
        response: Response | None = None,
        info=None,
        *,
        item: Item | None = None,
    ):
        """Get the full path where the image will be stored."""
        url_hash = hashlib.shake_256(request.url.encode()).hexdigest(8)

        # additional metadata passed to the pipeline
        if item is None or "original_url" not in item:
            logger.error(f"Could not find 'original_url' in item {item}")
            return f"unknown/{url_hash}.jpg"

        original_url = item["original_url"]

        try:
            path = _extract_unique_id(original_url)
        except ValueError as e:
            logger.exception(f"Could not decompose URL {original_url}: {e}")
            path = Path("unknown/")

        page = _extract_last_path_segment(request.url)

        return f"{path}/{page}_{url_hash}.jpg"
