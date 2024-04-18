"""
Scrapy spider to scrape parish registers from a specific location from Matricula Online.
"""

from typing import List
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
        items.pop(0)  # Remove the header row
        if len(items) % 2 != 0:
            raise ValueError("Unexpected number of rows in the table.")
        parish_registers = [items[i : i + 2] for i in range(0, len(items), 2)]

        # BUG: sometimes no result box is available. instead a url to an external website is provided

        for main_row, details_row in parish_registers:

            name = main_row.css("tr td:nth-child(3)::text").get()
            href = main_row.css("tr td:nth-child(1) a:nth-child(1)::attr('href')").get()
            url = None if href is None or href == "" else urljoin(HOST, href)
            date_range_str = main_row.css("tr td:nth-child(4)::text").get()
            accession_number = main_row.css("tr td:nth-child(2)::text").get()
            type = details_row.css("tr td dl dd:nth-of-type(1)::text").get()
            # TODO: select 4-last and put it here
            comment = details_row.css("tr td dl dd:nth-of-type(4)::text").get()

            yield {
                "name": name,
                "url": url,
                "accession_number": accession_number,
                "date": date_range_str,
                "type": type,
                # BUG: inconsistent, not always present or other type of information
                "comment": comment.strip() if comment is not None else None,
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
