#!/usr/bin/env python3

"""
This script uses `matricula-online-scraper fetch newsfeed` to check
Matricula's recent newsfeed articles against a specified set of keywords.
A user will be notified via email if match was found.

PREREQUISITES
=============

* Make sure `matricula-online-scraper` is installed and available.

USAGE
=====

* If you want to run this script periodically, e.g. each day,
set the scrape period to 2 days for deduplication. This will prevent
missing matches due to scrape period overlaps from the last job.

* Run `./check-newsfeed.py --help` for more information.

HOW IT WORKS
============

1. Scrapes newsfeed articles from Matricula's website,
finds matches and rewrites those matches to a data file.
2. Remove potential duplicates (deduplication) in the scraped data
due to scrape period overlaps from the last job's data file.
3. If matches were found, a mail will be sent to the user with the matches.
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
import os

# please update the version according to semver for user feature semantics
# strictly follow the breaking change rules: bump major version
# otherwise unexpected behaviour may occur
VERSION = "0.1.0"
MAJOR_VERSION = VERSION.split(".")[0]

JOB_ID = uuid.uuid4()
JOB_START = datetime.now()

APP_DIR = Path("~/.matricula-online-scraper/").expanduser().absolute()
LOG_FILE = Path(APP_DIR, f"matricula-newsfeed-mailer.v{MAJOR_VERSION}.log")
DATA_STORE = Path(APP_DIR, "scraper-data")  # folder where scraped data is stored
DATA_FILE = Path(DATA_STORE, f"job_{JOB_ID}_v{VERSION.replace(".", "_")}.csv")


TIMESTAMP_FMT = "%d.%m.%Y %H:%M:%S"

# create app dir if non existent
if not APP_DIR.exists():
    APP_DIR.mkdir(parents=True)


# -------------------- logging --------------------


logger = logging.getLogger(__name__)
logger_extra = {
    "job_id": JOB_ID,
    "bot_version": VERSION,
}
logging.basicConfig(
    handlers=[
        logging.FileHandler(LOG_FILE),
    ],
    encoding="utf-8",
    level=logging.DEBUG,
    format="[%(asctime)s] %(levelname)s (%(job_id)s @ v%(bot_version)s) : %(message)s",
    datefmt=TIMESTAMP_FMT,
)
logger_factory = logging.getLogRecordFactory()


def record_factory(*args, **kwargs):
    record = logger_factory(*args, **kwargs)
    record.job_id = JOB_ID
    record.bot_version = VERSION
    return record


logging.setLogRecordFactory(record_factory)


class LogLine(TypedDict):
    timestamp: datetime
    level: str
    job_id: uuid.UUID
    bot_version: str
    message: str


def parse_log_line(line: str) -> LogLine:
    parts = line.split(" ")
    date_str = parts[0][1:]  # remove leading '['
    time_str = parts[1][: len(parts[1]) - 1]  # remove trailing ']'
    timestamp = datetime.strptime(f"{date_str} {time_str}", TIMESTAMP_FMT)
    level = parts[2]
    job_id = uuid.UUID(parts[3][1:])  # remove leading '('
    bot_version = parts[5][: len(parts[5]) - 1]  # remove trailing ')'
    message = " ".join(parts[7:])
    return {
        "timestamp": timestamp,
        "level": level,
        "job_id": job_id,
        "bot_version": bot_version,
        "message": message,
    }


# -------------------- parse args --------------------


class Options(TypedDict):
    sender_mail: str
    sender_password: str
    smtp_server: str
    smtp_port: int
    receiver_mail: str
    scrape_period: int
    keywords: list[str]


def print_args(options: Options):
    options = copy.deepcopy(options)
    options["sender_password"] = "******" if options["sender_password"] else ""
    return ", ".join(f"{k}: {v}" for k, v in options.items())


def parse_args() -> Options:
    parser = argparse.ArgumentParser(
        description=(
            "This script uses `matricula-online-scraper fetch newsfeed` to check"
            " Matricula's recent newsfeed articles against a specified set of keywords."
            " A user will be notified via email if match was found."
        )
    )

    # ----- not part of the app's options -----

    parser.add_argument(
        "-v", "--verbose", help="Print log to stdout too.", action="store_true"
    )
    # exits automatically when invoked
    parser.add_argument(
        "--version",
        help="Print the version of the script and exit.",
        action="version",
        version=VERSION,
    )

    # ----- use cli options -----

    use_cli = parser.add_argument_group("operational arguments")

    use_cli.add_argument(
        "--from",
        type=str,
        help="Sender's email address.",
        required=True,
        dest="sender_mail",
    )
    use_cli.add_argument(
        "--password",
        type=str,
        help="Sender's email password.",
        required=True,
        dest="sender_password",
    )
    use_cli.add_argument(
        "--smtp-server",
        type=str,
        help="SMTP server address.",
        required=True,
        dest="smtp_server",
    )
    use_cli.add_argument(
        "-p" "--smtp-port",
        type=int,
        help="SMTP server port.",
        required=True,
        dest="smtp_port",
    )
    use_cli.add_argument(
        "--to",
        type=str,
        help="Receiver's email address.",
        required=True,
        dest="receiver_mail",
    )
    use_cli.add_argument(
        "-k",
        "--keywords",
        nargs="+",  # e.g. "--keywords keyword1 keyword2 keyword3"
        help="List of keywords used for scraping (separate multiple by spaces).",
        required=True,
    )
    use_cli.add_argument(
        "-n",
        "--scrape-period",
        type=int,
        help=(
            "How many days to scrape back (including today).."
            "Increment this by one day for deduplication if run periodically."
        ),
        dest="scrape_period",
        required=True,
    )

    args = parser.parse_args()

    if args.verbose:
        logger.addHandler(logging.StreamHandler())
        logger.warn(
            (
                "Verbose mode enabled. Logging to stdout too. Some log messages might be omitted."
                f"Check the log file for full details: {LOG_FILE.absolute()}"
            )
        )

    options: Options = {
        "sender_mail": args.sender_mail,
        "sender_password": args.sender_password,
        "smtp_server": args.smtp_server,
        "smtp_port": args.smtp_port,
        "receiver_mail": args.receiver_mail,
        "scrape_period": args.scrape_period,
        "keywords": args.keywords,
    }

    logger.debug(f"Using cli arguments: {print_args(options)}")

    return options


# -------------------- matricula-online-scraper executable --------------------


EXECUTABLE = shutil.which("matricula-online-scraper")
if not EXECUTABLE:
    logger.error("Could not find executable 'matricula-online-scraper'.")
    exit(1)


SCRAPER_VERSION = (
    subprocess.run([EXECUTABLE, "--version"], encoding="utf-8", capture_output=True)
    .stdout.strip()
    .replace("\n", "")
)
if not SCRAPER_VERSION:
    logger.error("Could not get version of executable 'matricula-online-scraper'.")
    exit(1)

logger.debug(
    f"Using matricula-online-scraper (v{SCRAPER_VERSION}) executable at: {EXECUTABLE}"
)


# -------------------- Data processing / CSV parsing --------------------


class NewsfeedArticle(TypedDict):
    headline: str
    url: str
    date: date
    preview: str


def is_eq_newsfeed_article(a: NewsfeedArticle, b: NewsfeedArticle) -> bool:
    return a["url"] == b["url"]


def fetch_newsfeed(*, last_n_days: int) -> Path:
    """Fetches the last n days and returns the path to the scraped data."""
    filename = DATA_FILE.with_suffix("")  # remove '.csv' suffix
    call_args: list[str] = [
        EXECUTABLE,
        "fetch",
        "newsfeed",
        str(filename.absolute()),
        "-e",
        "csv",
        "-n",
        str(last_n_days),
    ]

    logger.debug(f"Running fetch command to scrape newsfeed with args: {call_args}")
    process = subprocess.run(call_args, encoding="utf-8", capture_output=True)
    if process.returncode != 0:
        logger.error(
            f"Scraping the newsfeed failed with exit code {process.returncode}. Captured stdout: {process.stdout}. Captured stderr: {process.stderr}"
        )
        exit(1)

    # output file in stdout after substring 'Output saved to:'
    output = DATA_FILE
    if not output.exists():
        logger.error(f"Scraped newsfeed data not found at: {output}")
        exit(1)

    logger.debug(f"Scraped newsfeed data successfully, saved to: {output}")
    return output


def parse_article_date_str(value: str) -> date:
    # if used write_back_history, then the date was already parsed
    if "-" in value:
        return datetime.strptime(value, "%Y-%m-%d").date()

    # format from Matricula
    return (
        datetime.strptime(value, "%b. %d, %Y").date()
        if "." in value
        else datetime.strptime(value, "%B %d, %Y").date()
    )


def parse_data_file(path: Path) -> list[NewsfeedArticle]:
    # csv format: headline,date,preview,url
    articles: list[NewsfeedArticle] = []
    with open(path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            try:
                date = row["date"]
                date = parse_article_date_str(date)
            except Exception as e:
                logger.error(f"Failed to parse date from row: {row}. Error: {e}")
                exit(1)

            articles.append(
                NewsfeedArticle(
                    headline=row["headline"],
                    url=row["url"],
                    date=date,
                    preview=row["preview"],
                )
            )

    logger.debug(f"Parsed {len(articles)} articles from csv file: {path.absolute()}")
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

    logger.debug(f"Found {len(matches)} matches for keywords: {keywords}")
    return matches


def write_back_history(*, to_data_file: Path, with_matches: list[NewsfeedArticle]):
    with open(to_data_file, "w+", encoding="utf-8") as file:
        # erase file content
        # only store matches in the data file to use for later comparison
        if with_matches:
            writer = csv.DictWriter(file, fieldnames=with_matches[0].keys())
            writer.writeheader()
            writer.writerows(with_matches)
    logger.debug("Erased data file and stored matches for later comparison.")


def deduplicate(
    new_matches: list[NewsfeedArticle], last_data_file: Path | None
) -> list[NewsfeedArticle]:
    """handles duplicates due to scrape period overlaps"""
    len_before_deduplication = len(new_matches)

    if last_data_file is None:
        logger.debug("No last data file found. Skipping deduplication.")
        return new_matches

    last_matches = parse_data_file(last_data_file)

    # remove duplicates
    new_matches = [
        match
        for match in new_matches
        if not any(
            is_eq_newsfeed_article(match, last_match) for last_match in last_matches
        )
    ]
    logger.debug(
        (
            f"Removed {len_before_deduplication-len(new_matches)} duplicates due to scrape period overlaps."
            f" Matches before deduplication: {len_before_deduplication}, after: {len(new_matches)}."
        )
    )

    return new_matches


# -------------------- history --------------------


class Job(TypedDict):
    creation_date: datetime
    matches: list[NewsfeedArticle]


def get_history(*, limit: int = 10) -> tuple[list[Job], int, Path | None]:
    """(list of jobs with limit, number of total jobs, last data file)"""
    data_files = sorted(DATA_STORE.glob("*.csv"), key=os.path.getmtime, reverse=True)
    data_files = [file for file in data_files if file != DATA_FILE]
    total_jobs = len(data_files)
    data_files = data_files[:limit]
    last_data_file = data_files[0] if data_files else None

    jobs = []
    for file in data_files:
        matches = parse_data_file(file)
        creation_date = datetime.fromtimestamp(os.path.getmtime(file))
        jobs.append(Job(creation_date=creation_date, matches=matches))

    return jobs, total_jobs, last_data_file


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
    scrape_period: int,
    keywords: list[str],
    total_jobs: int,
    recent_jobs: list[Job],
    matches: list[NewsfeedArticle],
    # history: History,
) -> str:
    msg = "one new match" if len(matches) <= 1 else f"{len(matches)} new matches"

    if len(matches) == 0:
        logger.error("Implementation error: No matches given.")
        exit(1)

    body = f"""Dear {name},

in the last scheduled interval period I found {msg}:

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
- job id: {JOB_ID}
- job date: {JOB_START.strftime("%d.%m.%Y %H:%M:%S")}
- matricula-online-scraper version: v{SCRAPER_VERSION}
- scrape period: {scrape_period} day{"" if scrape_period == 1 else "s"} (deduplicated)
- keywords: {", ".join(keywords)}

The following log lists this bot's recent activity since the last message sent to you. Ensure that the bot is running as expected.

Total jobs: {total_jobs}
Recent jobs: {"/" if len(recent_jobs) == 0 else ""}
{"\n".join(f"- {job['creation_date'].strftime('%d.%m.%Y %H:%M:%S')} - {len(job['matches'])} matches" for job in recent_jobs)}

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
            exit(1)
        else:
            timedelta = datetime.now() - JOB_START
            logger.info(f"Mail sent successfully. Terminating job after {timedelta}")
        finally:
            server.quit()


# -------------------- main --------------------


if __name__ == "__main__":
    args = parse_args()

    recent_jobs, total_jobs, last_data_file = get_history()

    # scrape and find matches
    file = fetch_newsfeed(last_n_days=args["scrape_period"])
    articles = parse_data_file(file)
    keywords = args["keywords"]
    matches = find(keywords=keywords, in_articles=articles)
    write_back_history(to_data_file=DATA_FILE, with_matches=matches)
    matches = deduplicate(matches, last_data_file=last_data_file)

    if len(matches) == 0:
        timedelta = datetime.now() - JOB_START
        logger.info(
            f"No matches found. Terminating early without dilerving email notification. Job duration: {timedelta}."
        )
        exit(0)

    # build message
    subject = Subject(num_matches=len(matches))
    body = Body(
        name="User",
        keywords=args["keywords"],
        scrape_period=args["scrape_period"],
        total_jobs=total_jobs,
        recent_jobs=recent_jobs,
        matches=matches,
        # log=History(LOG_FILE),
    )
    message = Message(subject=subject, body=body, options=args)

    # send mail
    send_mail(
        options=args,
        message=message,
    )
