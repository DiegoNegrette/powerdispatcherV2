import aiohttp
from aiohttp_retry import RetryClient
import asyncio
import datetime
import json
import requests
from typing import List, Optional

from dateutil import relativedelta
from celery.utils.log import get_task_logger
from django.conf import settings


def get_datetime_obj_from_str(datetime_str, pattern):
    cleaned_str = datetime_str.strip().rsplit(" ", 1)[0]
    datetime_obj = datetime.datetime.strptime(cleaned_str, pattern)
    return datetime_obj


def months_difference_between_dates(end_date, start_date):
    # Get the relativedelta between two dates
    delta = relativedelta.relativedelta(end_date, start_date)

    # get months difference
    res_months = delta.months + (delta.years * 12)

    return res_months


def trunc_date(someDate):
    return someDate.replace(day=1)


async def make_post_request(url, session, data):
    logger = get_task_logger("callrail")
    max_retries = 3
    wait_time = 2
    retries = 0
    while retries < max_retries:
        try:
            response = await session.post(url, json=data, timeout=240)
            json = await response.json()
            response.raise_for_status()
            return response.status
        except (
            Exception,
            aiohttp.ClientResponseError,
            aiohttp.ClientConnectionError,
        ) as e:
            retries += 1
            logger.error(f"Retrying request after exception: {e}")  # noqa
            logger.error(json)
            await asyncio.sleep(wait_time)
    return 500


# async def make_post_request(url, data):
#     retry_options = {
#         "max_retries": 3,  # Maximum number of retries
#         "retry_exceptions": [
#             aiohttp.ClientResponseError,
#             aiohttp.ClientConnectionError,
#         ],
#         "retry_wait_min": 2,  # Minimum wait time between retries (in seconds)
#         "retry_wait_max": 10,  # Maximum wait time between retries (in seconds)
#     }

#     async with RetryClient() as session:
#         async with session.post(
#             url, json=data, timeout=240, retry_options=retry_options
#         ) as response:
#             response.raise_for_status()
#             return response.status


def split_string(input_string, max_length=3000):
    # Initialize an empty list to store the substrings
    substrings = []

    # Iterate over the input string with a step of max_length
    for i in range(0, len(input_string), max_length):
        # Extract a substring of maximum length max_length
        substring = input_string[i : i + max_length]
        # Append the substring to the list
        substrings.append(substring)

    return substrings


def convert_array_of_strings_in_array_of_strings_with_limited_length(
    input_list, max_length=3000
):
    """

    Having a list of string create a new array where each item contains a string formmed by joining as much items of the first list as i can before reaching a predefined max length

    This function, create_new_array, takes the input list of strings and a maximum length parameter. It iterates through the input list, concatenating strings until the maximum length is reached. When the maximum length is reached, it adds the concatenated string to the new array and starts a new string with the current string. Finally, it returns the new array containing the concatenated strings.

    Args:
        input_list (string[]): _description_
        max_length (int, optional): _description_. Defaults to 3000.

    Returns:
        string[]
    """
    new_array = []
    current_string = ""

    for string in input_list:
        if len(current_string) + len(string) <= max_length:
            current_string += string + "\n"
        else:
            new_array.append(current_string)
            current_string = string + "\n"

    if current_string:
        new_array.append(current_string)

    return new_array


def report_to_slack(task_title, report_lines, hook_url, logger):
    MAX_LENGTH_SLACK_MESSAGE = 3000
    TASK_TITLE = f"{task_title}:\n\n"
    text_report_array = (
        convert_array_of_strings_in_array_of_strings_with_limited_length(
            report_lines, MAX_LENGTH_SLACK_MESSAGE - 20
        )
    )
    blocks = []
    for idx, text in enumerate(text_report_array):
        message = f"```\n{TASK_TITLE if idx == 0 else ''}{text}```"
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": message,
                },
            }
        )
        logger.info(message)

    send_slack_notification(
        blocks=blocks,
        url=hook_url,
    )


def send_slack_notification(
    text: str = None,
    blocks: Optional[List[dict]] = None,
    attachments: Optional[List[dict]] = None,
    url=settings.HOOK_SLACK_PROLOCKSMITHS_ALERTS,
    template=None,
    mention_users=[],
):
    if text is not None and blocks is not None:
        raise Exception("text and blocks can't be set at the same time.")

    if text is None and blocks is None:
        raise Exception("Either text or blocks should be set.")

    payload = None
    if text is not None:
        if mention_users:
            text += " " + " ".join("<@{}>".format(userid) for userid in mention_users)
        payload = {"text": text}

    if blocks is not None:
        payload = {"blocks": blocks}

    if attachments is not None:
        payload["attachments"] = attachments

    if url and payload is not None:
        headers = {"content-type": "application/json"}
        if template is not None:
            payload.update(template)

        requests.post(url, data=json.dumps(payload), headers=headers)
