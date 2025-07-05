"""Custom pipeline to handle parish items from the `ParishSpider`."""

from typing import Any, override

import scrapy
from scrapy.exceptions import DropItem
from twisted.internet.defer import Deferred

from matricula_online_scraper.spiders.parish import EmptyParish, PlaceholderParish
from matricula_online_scraper.utils.user_console import UserConsole

usrcon = UserConsole()


class CustomParishPipeline:
    """Custom pipeline to handle parish items from the `ParishSpider`."""

    def process_item(  # pyright: ignore[reportIncompatibleMethodOverride]
        self, item: Any, spider: scrapy.Spider
    ) -> scrapy.Item | Deferred:
        """Custom process_item method to handle different item types."""
        match item:
            case PlaceholderParish():
                usrcon.warning(
                    f"The parish {item.parish} appears to be empty,"
                    f" but provides references to other sites: {', '.join(item.reference)}."
                )
                raise DropItem()
            case EmptyParish():
                usrcon.warning(f"The parish {item.parish} appears to be empty.")
                raise DropItem()
            case _:
                return item
