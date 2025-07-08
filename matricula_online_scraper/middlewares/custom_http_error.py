"""Custom HTTP error middleware for Matricula Online Scraper."""

from typing import override

import scrapy
from scrapy.http.response import Response
from scrapy.spidermiddlewares.httperror import HttpErrorMiddleware

from matricula_online_scraper.utils.user_console import UserConsole

usrcon = UserConsole()


class HTTPErrorLoggingMiddleware(HttpErrorMiddleware):
    """Overrides the default HTTP error middleware to log specific HTTP errors to the user."""

    @override
    def process_spider_input(self, response: Response, spider: scrapy.Spider) -> None:
        match response.status:
            case status if 200 <= status < 300:
                pass
            case 404:
                usrcon.error(
                    f"Invalid URL: {response.url} - The requested page was not found (404)."
                )
            case 500:
                usrcon.error(
                    f"Server Error: {response.url} - An internal server error occurred at Matricula Online (500)."
                )
            case 429:
                usrcon.warning(
                    f"Rate Limit Exceeded: {response.url} - Too many requests sent to Matricula Online (429)."
                    " (Request will be retried automatically.)"
                )
            case _:
                # NOTE: this is probably too verbose, maybe add a flag to enable it?
                # usrcon.warning(
                #     f"Unexpected HTTP status code {response.status} for URL: {response.url}"
                # )
                pass

        return super().process_spider_input(response, spider)
