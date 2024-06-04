#!/bin/bash

# ! ATTENTION !
# =============
#
# This file automatically adds a cron job to the user's crontab.
#
# Please fill in the following variables with your data.
#

# email, e.g. your@email.com
FROM=
# your email's password
PASSWORD=
# to whom the email should be sent, to@me.com
TO=
# smtp server, e.g. smtp.gmail.com
SMTP_SERVER=
# smtp port, e.g. 465
SMTP_PORT=
# space separated keywords, e.g. "keyword1 keyword2"
KEYWORDS=
# int, e.g. 24 (it will look for news every 24 hours)
SCHEDULE=
# cron schedule, e.g. "0 16 * * *" (every day at 16:00)
CRON=

# -------------------------------------------- #
# END OF USER VARIABLES | DO NOT CHANGE BELOW  #
# -------------------------------------------- #

# check variables are set
if [ -z "$FROM" ] || [ -z "$PASSWORD" ] || [ -z "$TO" ] || [ -z "$SMTP_SERVER" ] || [ -z "$SMTP_PORT" ] || [ -z "$KEYWORDS" ] || [ -z "$SCHEDULE" ] || [ -z "$CRON" ]; then
    echo "Error: Please fill in the variables in the script."
    exit 1
fi

# check execution path is correct
SCRIPT_PATH="$PWD/check-newsfeed.py"
if [ ! -f "$SCRIPT_PATH" ]; then
    echo "Error: Script not found at $SCRIPT_PATH"
    exit 1
fi

CMD="$SCRIPT_PATH --from $FROM --password $PASSWORD --smtp-server $SMTP_SERVER -p $SMTP_PORT --to $TO --schedule $SCHEDULE -k $KEYWORDS"
CRONJOB="$CRON $CMD"
COMMENT="# cronjob for https://github.com/lsg551/matricula-online-scraper/tree/main/examples/newsfeed-mailer"
COMMENT2="# see $SCRIPT_PATH for more details"

# add cronjob to user's crontab
TMP_FILE="user_crontab_l"
crontab -l > $TMP_FILE
echo "$COMMENT" >> $TMP_FILE
echo "$COMMENT2" >> $TMP_FILE
echo "$CRONJOB" >> $TMP_FILE
crontab $TMP_FILE
rm $TMP_FILE

echo "Cronjob added successfully: $CRONJOB"
