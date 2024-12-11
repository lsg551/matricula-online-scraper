"""
Scrapy spider to scrape church registers (= scanned church books) from Matricula Online.
"""

import re
import scrapy
import json
import base64
from rich import console
# from ..utils.pipeline_observer import PipelineObserver

stderr = console.Console(stderr=True)


class ChurchRegisterSpider(scrapy.Spider):
    name = "church_register"

    # see the order of middleware here:  https://doc.scrapy.org/en/latest/topics/settings.html#std-setting-SPIDER_MIDDLEWARES_BASE
    # 51 is right after the built-in middleware `HttpErrorMiddleware` which handles 404s
    custom_settings = {
        "SPIDER_MIDDLEWARES": {
            "matricula_online_scraper.middlewares.Catch404.Catch404": 51
        },
        # "DOWNLOADER_MIDDLEWARES": {
        #     "matricula_online_scraper.middlewares.DownloadMiddleware.DownloadMiddleware": 901
        # },
    }

    # def __init__(self, *args, observer: PipelineObserver, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.pipeline_observer = observer

    def parse(self, response):
        # Note: a "church register url" like https://data.matricula-online.eu/de/deutschland/aachen/aachen-hl-kreuz/KB+001/?pg=1
        # leads to a page where the image with some page number is embedded in a canvas. The user can navigate to the next page,
        # manipulate the image etc.
        # Unfortunatly, there are no direct URLs pointing to a PNG file (see https://github.com/lsg551/matricula-online-scraper/issues/3)
        # which could be easily used to scrape the source image.
        # Instead, Matricula encodes those paths in base64 and loads them via JavaScript. Each page's (whether `?pg=2` or `?pg=3`) HTML
        # has a variable `dv1` in a script tag. This variable contains the base64-encoded image paths to all scanned images of
        # the church register in question. This needs to be extracted and decoded to obtain a list of URLs to the images.

        # self.pipeline_observer.mark_as_started(response.url)

        # found in the last script tag in the body of the HTML
        dv1_var = response.xpath("//body/script[last()]/text()").get()

        # this regex matches the JavaScript variable `dv1` and extracts the values from it
        # keys `labels` and `files` are JSON fields in the variable `dv1`
        # `dv1 = new arc.imageview.MatriculaDocView("document", { "labels": […], "files": […] })`
        pattern = r"dv1\s*=\s*new\s+arc\.imageview\.MatriculaDocView\(\"document\",\s*\{[^}]*\"labels\"\s*:\s*(\[[^\]]*\]),[^}]*\"files\"\s*:\s*(\[[^\]]*\])"
        matches = re.search(pattern, dv1_var, re.DOTALL)

        if not matches:
            self.logger.error(
                "Could not extract 'labels' and 'files' from JavaScript variable 'dv1'"
            )
            return

        labels = matches.group(1)
        labels = json.loads(labels)

        files = matches.group(2)
        files = json.loads(files)
        # [7:][:-1] removes the leading `/image/` and trailing `/`
        # files = [base64.b64decode(file[7:][:-1]).decode("utf-8") for file in files]
        for idx, file in enumerate(files):
            try:
                raw_base64_str = file[7:][:-1]
                # counteract malformed base64 strings with padding
                missing_padding = len(raw_base64_str) % 4
                if missing_padding:
                    raw_base64_str += "=" * (4 - missing_padding)
                files[idx] = base64.b64decode(raw_base64_str).decode("utf-8")
            except Exception as err:
                self.logger.error(
                    f"Could not decode base64-encoded image URL {file}. Error {err}",
                    exc_info=True,
                )
                continue

        # TODO: implement option `--dump-decoded-urls-only` to only output the decoded URLs and labels
        # if dump_decoded_urls_only:
        #     yield from (
        #         {"label": label, "file": file} for label, file in zip(labels, files)
        #     )

        # if len(files) > 0:
        #     for file, label in zip(files, labels):
        #         self.pipeline_observer.observe(file, label, initiator=response.url)
        #     self.pipeline_observer.mark_as_in_process(response.url)

        yield {"image_urls": files}
