"""
Scrapy spider to scrape parish registers from a specific location from Matricula Online.
"""

from typing import Dict, List
import scrapy  # pylint: disable=import-error # type: ignore
from urllib.parse import urlencode, urlparse, parse_qs, urljoin, urlunparse

HOST = "https://data.matricula-online.eu"


def create_next_url(current: str, next_page: str) -> str:
    current_url = urlparse(current)
    url_parts = list(current_url)
    query = parse_qs(current_url.query)

    params = {"page": next_page}
    query.update(params)

    url_parts[4] = urlencode(query)
    new_url = urlunparse(url_parts)

    return new_url


class ParishRegistersSpider(scrapy.Spider):
    name = "parish_registers"
    start_urls = [
        "https://data.matricula-online.eu/en/deutschland/muenster/0-status-animarum/",
    ]

    def __init__(self, start_urls: List[str], **kwargs):
        super().__init__(**kwargs)
        self.start_urls = start_urls

    def parse(self, response):
        items = response.css("div.table-responsive tr")

        # in some cases a parish's page is left blank intentionally
        # sometimes an external link is provided instead ... check if the page has a table
        if items is None or len(items) == 0:
            # this element usually contains another element with a link to an external website
            description_container = response.css("div.description")
            urls = description_container.css("a::attr('href')").getall()
            urls = list(set(urls))  # remove duplicates

            # completly blank page
            if urls is None or len(urls) <= 0:
                self.logger.debug(f"No data found for {response.url}")
                yield

            # one or many links found
            if len(urls) >= 1:
                for url in urls:
                    yield {
                        "external_url": url,
                    }

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
                details: Dict[str, str] = {
                    dt.strip().lower().replace(" ", "_"): dd.strip()
                    for dt, dd in zip(
                        details_row.css("tr td dl dt ::text").getall(),
                        details_row.css("tr td dl dd ::text").getall(),
                    )
                }

                yield {
                    "name": name,
                    "url": url,
                    "accession_number": accession_number,
                    "date": date_range_str,
                    **details,
                }

        next_page = response.css(
            "ul.pagination li.page-item.active + li.page-item a.page-link::attr('href')"
        ).get()

        if next_page is not None:
            # next_page will be a url query parameter like '?page=2'
            _, page = next_page.split("=")
            next_url = create_next_url(response.url, page)
            self.logger.debug(f"## Next URL: {next_url}")
            yield response.follow(next_url, self.parse)
