# Mailing Service for the Matricula Online Newsfeed Scraper

This example demonstrates how to utilize the `matricula-online-scraper` to scrape the newsfeed of the Matricula Online platform and send an email, if a keyword appears in one or more of the newsfeed articles. The script is fully functional and can be used as is.
I recommend running it in conjunction with a cronjob / systemd timer unit to check the newsfeed periodically. A systemd example is included.

## Prerequisites

- Make sure `matricula-online-scraper` is installed and working properly as well as its own prerequisites, follow the instructions in the [README](../../README.md).
- Note that if you are using gmail to send emails, you need to set up a so called _app password_. Otherwise you will get a `SMTPAuthenticationError`. Use this app password instead of your regular password.

## Installation

Basically, you only need to call the python script [`check-newsfeed.py`](./check-newsfeed.py) with the necessary arguments and – if you like – add a cronjob / launchd / systemd service to call the script periodically. The script will scrape parts of the newsfeed (e.g. the last 24 hours if your cronjob runs daily) and send an email with the newsfeed articles containing one or more keywords specified by you.

Run

```bash
$ ./check-newsfeed.py --help
```

for more information on how to use the script.

> **NOTE**: The script implements deduplication for redundant newsfeed articles. If you want to check the newsfeed daily, set `--scrape-period` to `2` [days]. This is necessary because articles do not have a datetime of publication, only the date. Therefore, the script will scrape the newsfeed of the last 48 hours and deduplicate the articles from the last scrape. Read the notes in [`check-newsfeed.py`](./check-newsfeed.py) for more information.

## Example: Using `systemd` Service and Timer Units

Clone the repository, copy the relevant files to a dedicated location.

```bash
$ mkdir ~/scripts
$ mkdir ~/Developer && cd ~/Developer && git clone https://github.com/lsg551/matricula-online-scraper
$ cp matricula-online-scraper/examples/newsfeed-mailer/check-newsfeed.py ~/scripts/check-newsfeed.py
$ cp matricula-online-scraper/examples/newsfeed-mailer/config.env ~/scripts/config.env
$ cp matricula-online-scraper/examples/newsfeed-mailer/check-newsfeed.service /etc/systemd/system/check-newsfeed.service
$ cp matricula-online-scraper/examples/newsfeed-mailer/check-newsfeed.timer /etc/systemd/system/check-newsfeed.timer
```

Edit each file to your needs. Fill in missing variables.

```bash
$ vim ~/scripts/config.env
$ vim /etc/systemd/system/check-newsfeed.service
$ vim /etc/systemd/system/check-newsfeed.timer
```

Enable the systemd units.

```bash
$ systemctl --user daemon-reload
$ sudo systemctl enable check-newsfeed.timer
```
