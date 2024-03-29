import datetime
import logging

import requests
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger("callrail")


class CallRailAPI:

    def __init__(self):
        self.BASE_URL = "https://api.callrail.com/v3/a/{account_id}/{endpoint}"
        self.headers = {"Authorization": f"Token {settings.CALLRAIL_ACCOUNT_TOKEN}"}
        self.account_id = settings.CALLRAIL_ACCOUNT_ID
        self.timeout = 240
        self.max_retries = 5

        self.api_map = {
            "get_calls_by_customer_phone_number": {
                "url_info": {
                    "account_id": self.account_id,
                    "endpoint": "calls.json",
                },
                "params": {"fields": "gclid"},
            },
        }

    def log_info(self, obj):
        now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"[{now}] {obj}")

    def log_error(self, obj):
        now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        logger.error(f"[{now}] {obj}")

    def _validate_parameters(self, data, expected_keys):
        if not all(param in data for param in expected_keys):
            _expected_params = ", ".join(expected_keys)
            raise Exception(f"Must specify these params: {_expected_params}")

    def get_calls_by_customer_phone_number(self, customer_phone_number):
        cmd = "get_calls_by_customer_phone_number"
        url = self.BASE_URL.format(**self.api_map[cmd]["url_info"])
        self.log_info(
            f"[{cmd}] Requesting calls for phonenumber: {customer_phone_number}"
        )
        end_date = timezone.now()
        start_date = end_date - datetime.timedelta(days=365)
        params = self.api_map[cmd]["params"].copy()
        params["search"] = customer_phone_number
        params["start_date"] = start_date
        params["end_date"] = end_date
        params["sort"] = "start_time"
        params["order"] = "desc"
        r = requests.get(url, headers=self.headers, timeout=self.timeout, params=params)
        response = r.json()
        if r.status_code == 200 and response.get("calls", None):
            return response["calls"]
        return []
