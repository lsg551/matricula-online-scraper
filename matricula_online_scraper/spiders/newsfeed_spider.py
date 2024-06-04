"""
Scrapy spider to scrape parish registers from a specific location from Matricula Online.
"""

from datetime import date, datetime
from typing import Optional
import scrapy  # pylint: disable=import-error # type: ignore
from urllib.parse import urlencode, urlparse, parse_qs, urljoin, urlunparse

HOST = "https://data.matricula-online.eu"


def parse_date_str(value: str) -> date:
    # example: "June 3, 2024" or "Dec. 19, 2023"
    if "." in value:
        # shorted month name
        return datetime.strptime(value, "%b. %d, %Y").date()

    # full month name
    return datetime.strptime(value, "%B %d, %Y").date()


def create_next_url(current: str, next_page: str) -> str:
    current_url = urlparse(current)
    url_parts = list(current_url)
    query = parse_qs(current_url.query)

    params = {"page": next_page}
    query.update(params)

    url_parts[4] = urlencode(query)
    new_url = urlunparse(url_parts)

    return new_url


class NewsfeedSpider(scrapy.Spider):
    name = "newsfeed"

    def __init__(
        self, limit: Optional[int] = None, last_n_days: Optional[int] = None, **kwargs
    ):
        super().__init__(**kwargs)
        self.start_urls = ["https://data.matricula-online.eu/en/nachrichten/"]
        # TODO: this is not thread-safe (?), it seems to work though ... investigate
        self.counter = 0

        if limit is not None and limit <= 1:
            self.logger.error(
                f"Parameter 'limit' must be greater than 1. Received: {limit}"
            )
            raise ValueError(
                f"Parameter 'limit' must be greater than 1. Received: {limit}"
            )

        if last_n_days is not None and last_n_days <= 0:
            self.logger.error(
                f"Parameter 'last_n_days' must be greater than 0. Received: {last_n_days}"
            )
            raise ValueError(
                f"Parameter 'last_n_days' must be greater than 0. Received: {last_n_days}"
            )

        self.limit = limit
        self.last_n_days = last_n_days

    def parse(self, response):
        items = response.css('#page-main-content div[id^="news-"]')

        for news_article in items:
            if self.limit is not None and self.counter >= self.limit:
                self.close(self, reason="Limit reached")
                break
            self.counter += 1

            headline_container = news_article.css("h3")
            headline = headline_container.css("a::text").get().strip()
            article_url = headline_container.css("a::attr('href')").get()
            article_date_str = headline_container.css("small::text").get()
            try:
                article_date = parse_date_str(article_date_str)
                if self.last_n_days is not None:
                    today = date.today()
                    delta = today - article_date
                    if delta.days > self.last_n_days:
                        continue
            except Exception as e:
                self.logger.error(f"Failed to evaluate parameter 'last_n_days': {e}")

            preview = news_article.css("p.text-justify + p::text").get()

            yield {
                "headline": headline,
                "date": article_date_str,
                "preview": preview,
                "url": urljoin(HOST, article_url),
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
