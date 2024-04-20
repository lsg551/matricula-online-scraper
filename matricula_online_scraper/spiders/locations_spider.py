"""
Scrapy spider to scrape locations from Matricula Online.
"""

from urllib.parse import urljoin
from typing import Tuple, TypedDict
import scrapy  # pylint: disable=import-error # type: ignore

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
        **kwargs,
    ):
        super().__init__(**kwargs)

        # custom arguments
        self.place = place
        self.diocese = diocese
        self.date_filter = date_filter
        self.date_range = date_range

        # start URL to begin iteration from
        self.start_urls = [
            (
                "https://data.matricula-online.eu/en/suchen/"
                + f"?place={self.place}"
                + f"&diocese={self.diocese if self.diocese is not None else ""}"
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

            # export information
            yield {
                "country": country,
                "region": region,
                "name": location.css("a.list-group-item span.text-primary::text").get(), # BUG: if 'place' is used, the text might be highlighted and <mark> inside
                "url": urljoin(
                    HOST, location.css("a.list-group-item::attr('href')").get()
                ),
            }

        # build next URL to scrape, retrieve from pagination element if available
        next_page = response.css(
            "ul.pagination li.page-item.active + li.page-item a.page-link::attr('href')"
        ).get()

        # stop iteration if no next page is available
        if next_page is not None:
            yield response.follow(urljoin(SCRAPE_ROUTE, next_page), self.parse)
