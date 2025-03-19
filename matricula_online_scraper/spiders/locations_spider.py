"""
Scrapy spider to scrape locations from Matricula Online.
"""

from urllib.parse import urljoin
from typing import Tuple, TypedDict
import scrapy  # pylint: disable=import-error # type: ignore
from .utils import extract_coordinates

HOST = "https://data.matricula-online.eu"
SCRAPE_ROUTE = "https://data.matricula-online.eu/en/suchen/"


class Location(TypedDict):
    """
    A location of data in question with its country, region, parish name and URL.

    Note that the data is inconsistent (except 'url' and 'country').
    Single fields may contain multiple values, such as annotations or alternative names.
    """

    country: str

    region: str
    """
    Broader state, province or region, sometimes a religious/historical one.
    In some cases virtual locations are used, such as institutions like digital archives.
    """

    name: str
    """Name of the parish or city. Larger cities may have multiple parishes."""

    url: str
    """URL to the location's dedicated Matricula page."""


class LocationsSpider(scrapy.Spider):
    name = "locations"

    def __init__(
        self,
        place: str,
        diocese: int | None,
        date_filter: bool,
        date_range: Tuple[int, int],
        include_coordinates: bool,
        **kwargs,
    ):
        super().__init__(**kwargs)

        # custom arguments
        self.place = place
        self.diocese = diocese
        self.date_filter = date_filter
        self.date_range = date_range

        self.include_coordinates = include_coordinates

        # start URL to begin iteration from
        self.start_urls = [
            (
                "https://data.matricula-online.eu/en/suchen/"
                + f"?place={self.place}"
                + f"&diocese={self.diocese if self.diocese is not None else ''}"
                + f"&date_range={date_range[0]},{date_range[1]}"
                + ("&date_filter=on" if self.date_filter else "")
            )
        ]

        self.logger.debug(f"Start urls: {self.start_urls}")

    def parse(self, response):
        # iterate over each location in the result table
        for location in response.css("div.results a.list-group-item"):
            # extract the location information
            country_region_str = location.css(
                "a.list-group-item span.text-muted::text"
            ).get()
            # and split into country and region
            country, region = [item.strip() for item in country_region_str.split("•")]
            url = urljoin(HOST, location.css("a.list-group-item::attr('href')").get())
            # If search parameters like 'place' are used, the DOM is changed and a <mark>
            # is inserted to highlight text. This gets all text from childnodes and joins them.
            name_parts = location.css(
                "a.list-group-item span.text-primary ::text"
            ).getall()
            name = "".join(name_parts).strip()

            export = {
                "country": country,
                "region": region,
                "name": name,
                "url": url,
            }

            if self.include_coordinates:
                yield scrapy.Request(
                    url=url, callback=self.parse_coordinates, meta={"data": export}
                )
            else:
                # export information
                yield export

        # build next URL to scrape, retrieve from pagination element if available
        next_page = response.css(
            "ul.pagination li.page-item.active + li.page-item a.page-link::attr('href')"
        ).get()

        # stop iteration if no next page is available
        if next_page is not None:
            yield response.follow(urljoin(SCRAPE_ROUTE, next_page), self.parse)

    def parse_coordinates(self, response):
        data = response.meta["data"]
        # coordinates are inside a string inside a javascript script tag
        # but they are not directly accessible, so we have to extract them
        # through each parish's dedicated page
        for script in response.css("html body script:not([src])").getall():
            if "var feature = wktread.readFeature('POINT (" in script:
                coordinates = extract_coordinates(script)
                if coordinates:
                    data["longitude"] = coordinates[0]
                    data["latitude"] = coordinates[1]
                    break

        yield data
