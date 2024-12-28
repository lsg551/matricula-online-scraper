import hashlib
import re
import logging
from pathlib import Path
from attr import dataclass
from scrapy.pipelines.images import ImagesPipeline
from scrapy.http.request import Request
from scrapy.http.response import Response
from scrapy.item import Item

logger = logging.getLogger(__name__)


@dataclass
class DecomposedImageURL:
    """Parts of the URL of an image on Matricula Online.

    Note that the URL is expected to have the following format,
    but the parameter `?pg=1` is omitted.

    Examples:
    >>> _decompose_image_url("https://data.matricula-online.eu/de/deutschland/augsburg/aach/1-THS/?pg=1")
    ... DecomposedImageURL(
    ...     country="deutschland",
    ...     region="augsburg",
    ...     parish="aach",
    ...     fond_id="1-THS",
    ... )
    """

    country: str
    region: str
    parish: str
    fond_id: str


def _decompose_image_url(url: str) -> DecomposedImageURL:
    """Decompose the URL of an image on Matricula Online."""

    match = re.match(
        r"https://data.matricula-online.eu/(?P<country_code>\w+)/(?P<country>\w+)/(?P<region>\w+)/(?P<parish>\w+)/(?P<fond_id>[\w-]+)",
        url,
    )

    if match is None:
        raise ValueError(f"Could not decompose URL {url}")

    country = match.group("country")
    region = match.group("region")
    parish = match.group("parish")
    fond_id = match.group("fond_id")

    return DecomposedImageURL(country, region, parish, fond_id)


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


def _extract_page_number(image_url: str) -> int:
    """Return the page number of an image URL.

    Examples:
    >>> _extract_page_number("http://hosted-images.matricula-online.eu/images/matricula/BiAA/ABA_Pfarrmatrikeln_Aach_001/ABA_Pfarrmatrikeln_Aach_001_0083.jpg")
    ... 83

    Raises:
        ValueError: If the page number could not be extracted.
    """

    # Matricula is very inconsistent. It might use "[…]_0001.jpg", "[…]-01.jpg" or something entirely different.

    match = re.search(r"(\d+).jpg$", image_url)

    if match is None:
        raise ValueError(f"Could not extract page number from URL {image_url}")

    return int(match.group(1))


class ImagesPipeline(ImagesPipeline):
    """Custom image pipelines helps to store images in a structured way (= custom paths)."""

    def file_path(
        self,
        request: Request,
        response: Response | None = None,
        info=None,
        *,
        item: Item | None = None,
    ):
        url_hash = hashlib.shake_256(request.url.encode()).hexdigest(8)

        # additional metadata passed to the pipeline
        if item is None or "original_url" not in item:
            logger.error(f"Could not find 'original_url' in item {item}")
            return f"unknown/{url_hash}.jpg"

        original_url = item["original_url"]
        path: Path
        try:
            path = _extract_unique_id(original_url)
        except ValueError as e:
            logger.error(f"Could not decompose URL {original_url}: {e}", exc_info=True)
            path = Path("unknown/")

        page_number: int | None = None
        try:
            page_number = _extract_page_number(request.url)
        except ValueError as e:
            logger.error(
                f"Could not extract page number from URL {request.url}: {e}",
                exc_info=True,
            )

        if page_number is not None:
            return f"{path}/page{page_number}_{url_hash}.jpg"
        else:
            return f"{path}/unknown_{url_hash}.jpg"
