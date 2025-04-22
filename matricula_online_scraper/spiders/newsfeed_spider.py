"""Scrapy spider to scrape Matricula Online's newsfeed."""

from datetime import date, datetime
from typing import Optional
from urllib.parse import parse_qs, urlencode, urljoin, urlparse, urlunparse

import scrapy  # pylint: disable=import-error # type: ignore
from scrapy.http.response import Response

from matricula_online_scraper.logging_config import get_logger
from matricula_online_scraper.utils.matricula_datestring import (
    parse_matricula_datestr,
)
from matricula_online_scraper.utils.matricula_pagination import create_next_url

logger = get_logger(__name__)


HOST = "https://data.matricula-online.eu"


class NewsfeedSpider(scrapy.Spider):
    """Scrapy spider to scrape Matricula Online's newsfeed."""

    name = "newsfeed"

    def __init__(
        self, limit: Optional[int] = None, last_n_days: Optional[int] = None, **kwargs
    ):
        super().__init__(**kwargs)
        self.start_urls = ["https://data.matricula-online.eu/en/nachrichten/"]
        # TODO: this is not thread-safe (?), it seems to work though ... investigate
        self.counter = 0

        self.limit = limit
        self.last_n_days = last_n_days

    def parse(self, response: Response):
        items = response.css('#page-main-content div[id^="news-"]')

        for news_article in items:
            if self.limit is not None and self.counter >= self.limit:
                self.close(self, reason="Limit reached")
                break
            self.counter += 1

            headline_container = news_article.css("h3")
            headline = (headline_container.css("a::text").get() or "").strip()
            article_url = headline_container.css("a::attr('href')").get()
            article_date_str = headline_container.css("small::text").get() or ""

            try:
                article_date = parse_matricula_datestr(article_date_str)
            except Exception as e:
                reason = (
                    f"Failed to parse Matricula date string '{article_date_str}': {e}"
                )
                logger.exception(reason)
                self.close(self, reason)
            else:
                # check if the article is older than the last_n_days
                if (
                    self.last_n_days
                    and (delta := date.today() - article_date)
                    and delta.days > self.last_n_days
                ):
                    reason = f"Article is older than {self.last_n_days} days: {article_date_str}. Breaking scrape loop."
                    logger.debug(reason)
                    break

            preview = news_article.css("p.text-justify + p::text").get()

            yield {
                "headline": headline,
                "date": article_date_str,
                "preview": preview,
                "url": urljoin(HOST, article_url),
            }

        # queries the pagination component at the bottom of the page
        # to find the next page, if it exists
        next_page = response.css(
            "ul.pagination li.page-item.active + li.page-item a.page-link::attr('href')"
        ).get()

        if next_page is not None:
            # construct a valid url from that information
            # next_page will be a url query parameter like '?page=2'
            _, page = next_page.split("=")
            next_url = create_next_url(response.url, page)
            logger.debug(f"Next URL to scrape: {next_url}")
            yield response.follow(next_url, self.parse)
