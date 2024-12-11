from typing import Any, Iterable
import logging

import pip
from scrapy.spidermiddlewares.httperror import HttpError
from scrapy import Spider
from scrapy.http.response import Response

from rich import console
from rich.text import Text
from matricula_online_scraper.cli.cli_utils.color import Color
from matricula_online_scraper.cli.cli_utils.badges import Badge
from matricula_online_scraper.utils.pipeline_observer import PipelineObserver

logger = logging.getLogger(__name__)
stderr = console.Console(stderr=True)


class Catch404:
    # This runs directly after the scrapy.spidermiddlewares.httperror.HttpErrorMiddleware
    # It catches 404 errors and prints a message to the user

    def process_spider_exception(
        self, response: Response, exception: Exception, spider: Spider
    ) -> Iterable[Any] | None:
        # try:
        #     observer: PipelineObserver | None = spider.__dict__["pipeline_observer"]

        #     if observer is None or not isinstance(observer, PipelineObserver):
        #         raise AttributeError()

        # except AttributeError as err:
        #     observer = None
        #     logger.exception(f"PipelineObserver not found in spider: {err}")

        # if observer:
        #     url = response.url
        #     status = "failed"
        #     try:
        #         observer.update(url, status)
        #     except Exception as err:
        #         logger.exception(
        #             f"Failed to update observer for {url} with new status '{status}': {err}"
        #         )

        if isinstance(exception, HttpError):
            if exception.response.status == 404:
                stderr.print(
                    Badge.Error,
                    Text(
                        f"The URL {exception.response.url} returned a 404 status code."
                        " This is likely due to the page not existing or the URL being incorrect."
                        " Please check the URL and try again.",
                        style=Color.Red,
                    ),
                )

            else:
                stderr.print(
                    Badge.Error,
                    Text(
                        f"The URL {exception.response.url} returned a {exception.response.status} status code.",
                        style=Color.Red,
                    ),
                )

        return None  # pass to next middleware
