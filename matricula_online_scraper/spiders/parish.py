"""Scrapy spider to scrape a parish's homepage and metadata about its registers.

Example:
Scraping https://data.matricula-online.eu/de/deutschland/aachen/aachen-st-adalbert/
will yield all the metadata in the table on that page.
"""

from dataclasses import dataclass
from urllib.parse import parse_qs, urlencode, urljoin, urlparse, urlunparse

import scrapy  # pylint: disable=import-error # type: ignore
import scrapy.exceptions
from scrapy.exceptions import CloseSpider
from scrapy.http.response import Response

from matricula_online_scraper.utils.matricula_pagination import create_next_url
from matricula_online_scraper.utils.user_console import UserConsole

HOST = "https://data.matricula-online.eu"


@dataclass
class ParishRegisterMetadata:
    """Metadata for a parish register scraped from the parish page."""

    name: str
    """Name of the parish register."""
    url: str
    """Points to the first page of the parish register."""
    accession_number: str
    """Accession number of the parish register (not guaranteed to be unique)."""
    date: str
    """Date range of the parish register."""
    details: dict[str, str]
    """Additional key-value pairs with metadata."""


@dataclass
class EmptyParish:
    """Yielded when a parish page is empty and does NOT provide an external link."""

    parish: str
    """URL of the parish missing its registers."""


@dataclass
class PlaceholderParish:
    """Yielded when a parish page is empty but provides an external link."""

    parish: str
    """URL of the parish missing its registers."""
    reference: list[str]
    """One or more URLs to some external resource."""


class ParishSpider(scrapy.Spider):
    """Scrapy spider to scrape parish registers from a specific location from Matricula Online."""

    name = "parish_registers"
    custom_settings = {
        "ITEM_PIPELINES": {
            "matricula_online_scraper.pipelines.parish_pipeline.CustomParishPipeline": 1
        },
        # TODO: inject through settings object
        "SPIDER_MIDDLEWARES": {
            "matricula_online_scraper.middlewares.custom_http_error.HTTPErrorLoggingMiddleware": 49
        },
    }

    def parse(self, response: Response):
        items = response.css("div.table-responsive tr")

        # in some cases, a parish's page is left blank intentionally
        # sometimes an external link is provided instead ... check if the page has a table
        if items is None or len(items) == 0:
            # this element usually contains another element with a link to an external website
            description_container = response.css("div.description")
            urls = description_container.css("a::attr('href')").getall()
            urls = list(set(urls))

            if urls is None or len(urls) <= 0:
                self.logger.debug(f"No data found for {response.url}")
                yield EmptyParish(response.url)
            else:
                self.logger.debug(f"External URLs found for {response.url}: {urls}")
                yield PlaceholderParish(response.url, urls)

        # page has a table with parish registers
        else:
            items.pop(0)  # Remove the header row
            if len(items) % 2 != 0:
                raise ValueError("Unexpected number of rows in the table.")
            # most two adjacent rows are the main row and the details row
            parish_registers = [items[i : i + 2] for i in range(0, len(items), 2)]

            for main_row, details_row in parish_registers:
                # from consistent main row
                name = main_row.css("tr td:nth-child(3)::text").get()
                href = main_row.css(
                    "tr td:nth-child(1) a:nth-child(1)::attr('href')"
                ).get()
                url = None if href is None or href == "" else urljoin(HOST, href)
                accession_number = main_row.css("tr td:nth-child(2)::text").get()
                date_range_str = main_row.css("tr td:nth-child(4)::text").get()

                # from inconsistent expandable details row
                # a <dl> with <dt>s as keys and <dd>s as values
                details: dict[str, str] = {
                    dt.strip().lower().replace(" ", "_"): dd.strip()
                    for dt, dd in zip(
                        details_row.css("tr td dl dt ::text").getall(),
                        details_row.css("tr td dl dd ::text").getall(),
                    )
                }

                if not name:
                    self.logger.warning(f"No name found for {response.url}. Skipping")
                    continue
                if not url:
                    self.logger.error(f"No URL found for {response.url}. Skipping.")
                    continue
                if not accession_number:
                    self.logger.error(
                        f"No accession number found for {response.url}. Skipping"
                    )
                    continue
                if not date_range_str:
                    self.logger.error(
                        f"No date range found for {response.url}. Skipping"
                    )
                    continue

                yield ParishRegisterMetadata(
                    name=name,
                    url=url,
                    accession_number=accession_number,
                    date=date_range_str,
                    details=details,
                )

        next_page = response.css(
            "ul.pagination li.page-item.active + li.page-item a.page-link::attr('href')"
        ).get()

        if next_page is not None:
            # next_page will be a url query parameter like '?page=2'
            _, page = next_page.split("=")
            next_url = create_next_url(response.url, page)
            self.logger.debug(f"## Next URL: {next_url}")
            yield response.follow(next_url, self.parse)
