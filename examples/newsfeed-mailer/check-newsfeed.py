#!/usr/bin/env python3

"""
This script uses `matricula-online-scraper fetch newsfeed` to check
Matricula's recent newsfeed articles against a specified set of keywords.
A user will be notified via email if match was found.

* Run `./check-newsfeed.py --help` for more information.

PREREQUISITES
=============

* Make sure `matricula-online-scraper` is installed and available.

HOW IT WORKS
============

If all arguments were provided correctly, this script will:

[...]

EXAMPLE
=======

* See this example's README for details.

"""

from pathlib import Path
from typing import TypedDict
from datetime import datetime, date
import shutil
import smtplib
import logging
import argparse
import subprocess
import uuid
import ssl
import csv
import copy

# please update update this version according to semver for user feature semantics
VERSION = "0.1.0"


# -------------------- logging --------------------


JOB_ID = uuid.uuid4()
JOB_DATE = datetime.now()
LOG_FILE = Path("matricula-newsfeed-mailer.log")

logger = logging.getLogger(__name__)
logger_extra = {
    "job_id": JOB_ID,
    "bot_version": VERSION,
}
logging.basicConfig(
    filename=LOG_FILE,
    encoding="utf-8",
    level=logging.DEBUG,
    format="[%(asctime)s] %(levelname)s (%(job_id)s @ v%(bot_version)s) : %(message)s",
    datefmt="%d.%m.%Y %H:%M:%S",
)
logger_factory = logging.getLogRecordFactory()


def record_factory(*args, **kwargs):
    record = logger_factory(*args, **kwargs)
    record.job_id = JOB_ID
    record.bot_version = VERSION
    return record


logging.setLogRecordFactory(record_factory)


def parse_log(path: Path) -> list[str]:
    return []


class History:
    """Scraping / Job history.
    Useful for debugging.
    """

    def __init__(self, log: Path):
        pass


# -------------------- matricula-online-scraper executable --------------------


EXECUTABLE = shutil.which("matricula-online-scraper")
if not EXECUTABLE:
    logger.error("Could not find executable 'matricula-online-scraper'.")
    raise FileNotFoundError(
        "matricula-online-scraper executable not found. "
        "Please make sure it is installed and available in your PATH."
    )


SCRAPER_VERSION = (
    subprocess.run([EXECUTABLE, "--version"], encoding="utf-8", capture_output=True)
    .stdout.strip()
    .replace("\n", "")
)
if not SCRAPER_VERSION:
    logger.error("Could not get version of executable 'matricula-online-scraper'.")
    raise ValueError("Could not get scraper version.")

logger.debug(
    f"Using matricula-online-scraper (v{SCRAPER_VERSION}) executable at: {EXECUTABLE}"
)


# -------------------- parse args --------------------


class Options(TypedDict):
    sender_mail: str
    sender_password: str
    smtp_server: str
    smtp_port: int
    receiver_mail: str
    schedule: int
    """(in hours) effectively determines the last n days to fetch."""
    keywords: list[str]


def print_args(options: Options):
    options = copy.deepcopy(options)
    options["sender_password"] = "******" if options["sender_password"] else ""
    return ", ".join(f"{k}: {v}" for k, v in options.items())


def parse_args() -> Options:
    parser = argparse.ArgumentParser(
        description=(
            "This script scrapes Matricula's newsfeed, "
            "checks against keywords and notifies a user if matches were found."
        )
    )
    parser.add_argument(
        "--from",
        type=str,
        help="Sender's email address.",
        required=True,
        dest="sender_mail",
    )
    parser.add_argument(
        "--password",
        type=str,
        help="Sender's email password.",
        required=True,
        dest="sender_password",
    )
    parser.add_argument(
        "--smtp-server",
        type=str,
        help="SMTP server address.",
        required=True,
        dest="smtp_server",
    )
    parser.add_argument(
        "-p" "--smtp-port",
        type=int,
        help="SMTP server port.",
        required=True,
        dest="smtp_port",
    )
    parser.add_argument(
        "--to",
        type=str,
        help="Receiver's email address.",
        required=True,
        dest="receiver_mail",
    )
    parser.add_argument(
        "--schedule",
        type=int,
        help=(
            "Used schedule for this script (e.g. your cronjob schedule; in hours)."
            " This determines the settings for scraping:"
            " e.g. 24, meaning every 24 hours => fetch only the last day."
        ),
        required=True,
    )
    parser.add_argument(
        "-k",
        "--keywords",
        nargs="+",  # e.g. "--keywords keyword1 keyword2 keyword3"
        help="List of keywords used for scraping (separate multiple by spaces).",
        required=True,
    )

    args = parser.parse_args()

    options: Options = {
        "sender_mail": args.sender_mail,
        "sender_password": args.sender_password,
        "smtp_server": args.smtp_server,
        "smtp_port": args.smtp_port,
        "receiver_mail": args.receiver_mail,
        "schedule": args.schedule,
        "keywords": args.keywords,
    }

    logger.debug(f"Using cli arguments: {print_args(options)}")

    return options


# -------------------- Data processing / CSV parsing --------------------

# folder where scraped data is stored
DATA_STORE = Path("~/matricula-newsfeed-scraper").expanduser()


def fetch_newsfeed(*, last_n_days: int) -> Path:
    """Fetches the last n days and returns the path to the scraped data."""
    file = Path(DATA_STORE, f"job_{JOB_ID}")
    format = "csv"
    call_args: list[str] = [
        EXECUTABLE,
        "fetch",
        "newsfeed",
        str(file.absolute()),
        "-e",
        format,
        "-n",
        str(last_n_days),
    ]

    logger.debug(f"Running fetch command to scrape newsfeed with args: {call_args}")
    process = subprocess.run(call_args, encoding="utf-8", capture_output=True)
    if process.returncode != 0:
        logger.error(
            f"Scraping the newsfeed failed with exit code {process.returncode}. Captured stdout: {process.stdout}. Captured stderr: {process.stderr}"
        )
        raise RuntimeError("Error while fetching newsfeed. Aborting.")

    # output file in stdout after substring 'Output saved to:'
    output = process.stdout.strip()
    output = (
        output[output.find("Output saved to:") + len("Output saved to:") :]
        .strip()
        .replace("\n", "")
    )
    output = Path(output)
    if not output.exists():
        logger.error(f"Scraped newsfeed data not found at: {output}")
        raise FileNotFoundError(f"Scraped newsfeed data not found at: {output}")

    logger.debug(f"Scraped newsfeed data successfully, saved to: {output}")
    return output


class NewsfeedArticle(TypedDict):
    headline: str
    url: str
    date: date
    preview: str


def parse_date_str(value: str) -> date:
    return (
        datetime.strptime(value, "%b. %d, %Y").date()
        if "." in value
        else datetime.strptime(value, "%B %d, %Y").date()
    )


def parse_csv(path: Path) -> list[NewsfeedArticle]:
    # csv format: headline,date,preview,url
    articles: list[NewsfeedArticle] = []
    with open(path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            try:
                date = row["date"]
                date = parse_date_str(date)
            except Exception as e:
                logger.error(f"Failed to parse date from row: {row}. Error: {e}")
                raise ValueError(f"Failed to parse date from row: {row}.") from e

            articles.append(
                NewsfeedArticle(
                    headline=row["headline"],
                    url=row["url"],
                    date=date,
                    preview=row["preview"],
                )
            )
    return articles


def find(
    *, keywords: list[str], in_articles: list[NewsfeedArticle]
) -> list[NewsfeedArticle]:
    """Searches for substrings of `keywords` in article headlines and previews."""
    matches = []
    for article in in_articles:
        for keyword in keywords:
            if (
                keyword.lower() in article["headline"].lower()
                or keyword.lower() in article["preview"].lower()
            ):
                matches.append(article)
                break
    return matches


# -------------------- mail parts --------------------


def Subject(*, num_matches: int) -> str:
    return "MATRICULA-BOT | " + (
        "New match found" if num_matches <= 1 else f"{num_matches} new matches found"
    )


def format_newsfeed_article(article: NewsfeedArticle) -> str:
    headline = f"({article["date"]}) {article["headline"]}"
    underscores = "-" * len(headline)
    return f"""
\t{headline}
\t{underscores}
\t{article["preview"]}
\t[{article["url"]}]
"""


def Body(
    *,
    name: str,
    schedule: int,
    keywords: list[str],
    matches: list[NewsfeedArticle],
    # history: History,
) -> str:
    msg = "one new match" if len(matches) <= 1 else f"{len(matches)} new matches"

    schedule_str: str = (
        f"every {schedule} hour"
        if schedule == 1
        else f"every {schedule} hours"
        if schedule < 3 * 24
        else f"every {schedule/24:.1f} days"
    )

    body = f"""Dear {name},

in the last scheduled interval period (the last {schedule/24:.1f} days) I found {msg}:

{
   "\n\n".join(f"- {idx+1} -\n" + format_newsfeed_article(match) for idx, match in enumerate(matches))
}

---------- END OF MESSAGE ----------

This message was automatically generated on your behalf by the MATRICULA-BOT.
This bot frequently searches https://data.matricula-online.eu/en/nachrichten/ in a specified interval and with a set of keywords according to your settings (see below).
You will be notified if at least one match was found in the newsfeed article of this interval.
Note that this is prone to errors, because job recovery is not supported (e.g. system shutdown = lost interval).
See https://github.com/lsg551/matricula-online-scraper for more information.

- bot version: v{VERSION}
- job-id: {JOB_ID}
- job-date: {JOB_DATE.isoformat()}
- matricula-online-scraper version: v{SCRAPER_VERSION}
- schedule: {schedule_str} (scraped range)
- keywords: {", ".join(keywords)}

The following log lists this bot's recent activity since the last message sent to you. Ensure that the bot is running as expected.

str(log)

PLEASE REPORT ANY ISSUES HERE: https://github.com/lsg551/matricula-online-scraper/issues
"""
    return body


def Message(subject: str, body: str, options: Options) -> bytes:
    return f"""From: {options["sender_mail"]}
To: {options["receiver_mail"]}
Subject: {subject}

{body}""".encode("utf-8")


# -------------------- SMTP --------------------


def send_mail(
    message: bytes,
    options: Options,
):
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(
        options["smtp_server"], options["smtp_port"], context=context
    ) as server:
        try:
            server.login(
                user=options["sender_mail"], password=options["sender_password"]
            )
            err = server.sendmail(
                from_addr=options["sender_mail"],
                to_addrs=options["receiver_mail"],
                msg=message,
            )
            if err:
                raise Exception(err)
        except Exception as e:
            logger.error(f"Failed to send mail: {e}")
            raise RuntimeError("Failed to send mail.") from e
        else:
            logger.debug("Mail sent successfully.")
        finally:
            server.quit()


# -------------------- main --------------------


if __name__ == "__main__":
    args = parse_args()

    # scrape and process csv data
    days = args["schedule"] // 24
    file = fetch_newsfeed(last_n_days=days)
    articles = parse_csv(file)
    logger.debug(f"Parsed {len(articles)} articles from csv file: {file.absolute()}")
    keywords = args["keywords"]
    matches = find(keywords=keywords, in_articles=articles)
    logger.debug(
        f"Found {len(matches)} matches for keywords {keywords} in: {file.absolute()}"
    )

    # build message
    # history = History(LOG_FILE)
    subject = Subject(num_matches=len(matches))
    body = Body(
        name="User",
        schedule=args["schedule"],
        keywords=args["keywords"],
        matches=matches,
        # log=History(LOG_FILE),
    )
    message = Message(subject=subject, body=body, options=args)

    # send mail
    send_mail(
        options=args,
        message=message,
    )
