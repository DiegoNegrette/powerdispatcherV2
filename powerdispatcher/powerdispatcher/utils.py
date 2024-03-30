import aiohttp
from aiohttp_retry import RetryClient
import asyncio
import datetime
import json
import requests
from typing import List, Optional

from dateutil import relativedelta
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
    max_retries = 3
    wait_time = 2
    retries = 0
    while retries < max_retries:
        try:
            response = await session.post(url, json=data, timeout=240)
            response.raise_for_status()
            return response.status
        except (
            Exception,
            aiohttp.ClientResponseError,
            aiohttp.ClientConnectionError,
        ) as e:
            retries += 1
            print(f"Retrying request after exception: {e}")  # noqa
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
