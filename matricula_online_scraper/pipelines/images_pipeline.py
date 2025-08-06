"""Custom image pipeline to store downloaded images.

This pipeline is used to customized the path where the images are stored.
It can be used by specifying a valid module path in the Scrapy settings.
"""

import hashlib
import re
from pathlib import Path
from typing import override
from urllib.parse import urlparse

from attr import dataclass
from scrapy.http.request import Request
from scrapy.http.response import Response
from scrapy.item import Item
from scrapy.pipelines.images import ImagesPipeline

from matricula_online_scraper.logging_config import get_logger
from matricula_online_scraper.spiders.church_register import (
    ChurchRegisterDownloadItem,
    ImageDirStructure,
)
from matricula_online_scraper.utils.matricula_url import ParishRegisterURL

logger = get_logger(__name__)


class CustomImagesPipeline(ImagesPipeline):
    """Custom image pipeline for `spiders.ChurchRegisterSpider` to handle path creation of individual images.

    `spiders.ImageDirStructure` specifies two options for writing the images to
    the user-specified output directory:
    1. `nested` (default) – mimic the URL structure by creating nested
        subdirectories to store the images in
    2. `flat` – store all images in the same root directory specified by the user

    The naming schema for individual image files is `HASH_IMG.jpg`. `IMG` refers
    to the last path segment used in the image URL. The hash is a SHAKE-256,
    hexadecimal 8 character long hash of the image URL.

    For example, taken this parish register:
    - https://data.matricula-online.eu/en/deutschland/aachen/aachen-st-adalbert/KB+004/?pg=1

    The download URL for the first image is:
    - http://hosted-images.matricula-online.eu/images/matricula/DE-BDAA/images/17%20Matricula/DE_2187_KB_004/DE_2187_KB_004_0001.jpg

    Examples:
    >>> # -o ~/matricula_images --nested
    ... "~/matricula_images/deutschland/aachen/aachen-st-adalbert/KB+004/e98cafb17df66667_DE_2187_KB_004_0001.jpg"
    >>> # -o ~/matricula_images --flat
    ... "~/matricula_images/e98cafb17df66667_DE_2187_KB_004_0001.jpg"
    """

    @override
    def file_path(
        self,
        request: Request,
        response: Response | None = None,
        info=None,
        *,
        item: ChurchRegisterDownloadItem | None = None,
    ):
        hash = hashlib.shake_256(request.url.encode()).hexdigest(
            4
        )  # 4 bytes = 8 characters

        if item is None:
            return f"unknown_{hash}.jpg"

        # additional metadata passed to the pipeline via the item
        original_url: str = item["original_url"]
        image_dir_structure: ImageDirStructure = item["image_dir_structure"]

        url = ParishRegisterURL(original_url)

        image_filename = request.url.split("/")[-1]
        if Path(image_filename).suffix == "":
            # if the image filename does not have a suffix, append '.jpg'
            # it usually has one
            image_filename += ".jpg"

        # NOTE: the last path segment of the image URL `/FILENAME.jpg` is very likely the
        # the original image filename, probably stored on a Windows server.
        # At this point, that value should be sanitized – but I trust the engineers of
        # Matricula to have done that already.
        # TODO: for the future, maybe still sanitize the filename to be safe

        # relative base to the outdir for nested and flat directory structures
        relative_filepath = Path(f"{hash}_{image_filename}")

        if image_dir_structure == "nested":
            nested_path = f"/{url.country}/{url.region}/{url.parish}/{url.register}"
            relative_filepath = nested_path / relative_filepath

        return str(relative_filepath)
