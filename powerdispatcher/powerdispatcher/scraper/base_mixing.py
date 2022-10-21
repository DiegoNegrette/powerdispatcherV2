import logging
import time

from django.conf import settings
from django.utils import dateformat, timezone

logger = logging.getLogger('scraper')


class ScraperBaseMixin:

    BROWSER_CHROME = 'chrome'
    BROWSER_FIREFOX = 'firefox'

    def __init__(self, webdriver_url=settings.WEB_DRIVER_URL):
        self.driver = None
        self.sleep_total = 0
        self.webdriver_url = webdriver_url
        self.browser_type = settings.BROWSER
        self.webdriver_container_host = None
        self.webdriver_container_port = None
        self.account_identifier = None

    def sleep(self, seconds):
        self.sleep_total += seconds
        time.sleep(seconds)

    def log(self, obj, label=None):
        _id = ''
        _label = f'[{label}]' if label else ''
        if self.account_identifier:
            webdriver_host = self.webdriver_container_host or ''
            webdriver_port = self.webdriver_container_port or ''
            _now = dateformat.format(timezone.now(), 'Y-m-d H:i:s')
            _id = f'[{_now}][{webdriver_host}:{webdriver_port}]' \
                  f'[{self.account_identifier}]{_label}'
        logger.info(f'{_id} {obj}')

    def navigate_to(self, target_url):
        self.log(f"Navigating to {target_url}")
        self.driver.get(target_url)
