import sys
import time
from typing import Dict, List, Optional

import deserialize
import praw
import requests
from dotenv import dotenv_values
from loguru import logger
from praw.exceptions import RedditAPIException
from prawcore.exceptions import NotFound

logger.remove(None)
logger.add(
    sys.stderr, format="<green>{time:HH:mm}" "</green> - <level>{message}</level>"
)
logger.add("run.log")


@deserialize.parser("username", str.lower)
class AuthorizedUser:
    username: str
    address: str
    contrib: str
    donut: str
    weight: str


def get_user_list(url: str) -> List[AuthorizedUser]:
    response = requests.get(url, timeout=10)
    response.raise_for_status()

    data = deserialize.deserialize(List[AuthorizedUser], response.json())
    if data:
        return data
    else:
        raise ValueError("Could not deserialize json")


def get_existing_approved(r: praw.Reddit, subreddit: str) -> List[str]:
    return list(
        contributor.name.lower()
        for contributor in r.subreddit(subreddit).contributor(limit=None)
    )


def user_exists(r: praw.Reddit, name: str):
    try:
        r.redditor(name).id
    except (NotFound, AttributeError):
        # NotFound => does not exist, AttributeError => banned
        return False
    return True


def update_reddit(config: Dict) -> Optional[bool]:
    website_users = [
        user.username for user in get_user_list(config["authorized_users_endpoint"])
    ]
    logger.debug(f"Got userlist with {len(website_users)} users.")

    r = praw.Reddit(
        client_id=config["client_id"],
        client_secret=config["client_secret"],
        user_agent=config["user_agent"],
        username=config["username"],
        password=config["password"],
    )

    existing_reddit_approved_users = get_existing_approved(r, config["subreddit"])
    logger.debug(
        f"Got {len(existing_reddit_approved_users)} existing Reddit contributors."
    )

    successfully_added = 0
    for user in website_users:
        if user in existing_reddit_approved_users:
            logger.debug(
                f"Skipping website user {user!r} as they are already approved."
            )
            continue

        if user_exists(r, user):
            successfully_added += 1
            logger.debug(
                f"Adding website user {user!r} to approved list. [{successfully_added}]"
            )
            try:
                r.subreddit(config["subreddit"]).contributor.add(user)
            except RedditAPIException as e:
                reason = e.items[0].error_type
                logger.debug(f"Skipped user {user!r} due to {reason!r}")

    for user in existing_reddit_approved_users:
        if user not in website_users:
            logger.debug(f"Deleting  user {user!r} from approved list.")
            r.subreddit(config["subreddit"]).contributor.remove(user)

    return True


@logger.catch
def main(config: Dict) -> None:
    SIXTY_MINUTES = 60 * 60

    while True:
        try:
            success = update_reddit(config)
        except RedditAPIException as e:
            if e.items[0].error_type == "SUBREDDIT_RATELIMIT":
                logger.error(
                    "Hit the separate hardcoded ratelimit of 100 users. Stopping for now"
                )
            else:
                raise e
            success = False

        if success:
            logger.debug("Completed job. Exiting.")
            break

        logger.error("Sleeping for an hour")
        time.sleep(SIXTY_MINUTES)


if __name__ == "__main__":
    config = dotenv_values(".env")
    if not config:
        logger.error("No config file detected.")
        logger.error("Quitting!")
    else:
        main(config)
