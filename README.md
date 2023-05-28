Approved User Syncer
====================

Reddit bot to sync a userlist to the Reddit approved users for a subreddit.

**Note:** There is a separate, undocumented ratelimit on adding approved users. This seems to be approx 100/hour. The bot will automatically sleep for an hour when the ratelimit has been hit.


## Installing

Install python 3.8+:

    apt install python3 python3-pip

Install python dependancies:

    pip install -U deserialize praw requests dotenv loguru


## Configuration

Create a `.env` file in the project root directory.

Include:

    username=""
    password=""
    client_id=""
    client_secret=""
    subreddit=""
    user_agent="u/hillsd user comparer"
    authorized_users_endpoint="https://raw.githubusercontent.com/EthTrader/donut.distribution/main/docs/users.json"


## Running

Perhaps set a cron job to run every 5 days. EG:

    * * */5 * * /usr/bin/python3 /root/usersync/usersync.py >/dev/null 2>&1
