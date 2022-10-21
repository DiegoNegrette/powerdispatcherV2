import datetime
import ipdb
import traceback

from django.core.management.base import BaseCommand

# TOOLS FOR TESTING
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from powerdispatcher.scraper.powerdispatchcom.powerdispatch \
    import PowerdispatchSiteScraper


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--debug", action='store_true', default=False)

    def handle(self, *args, **options):
        scraper = PowerdispatchSiteScraper()
        debug = options.get("debug")

        try:
            scraper.init_driver()

            scraper.login()

            scraper.goto_search_menu()

            target_date = datetime.datetime(2022, 4, 12)
            target_date1 = datetime.datetime(2022, 4, 14)

            scraper.filter_search(target_date, target_date1)

            ticket_ids = scraper.get_ticket_ids_from_search_result()

            # TODO THIS COULD BE A GOOD PLACE TO SELECT ONLY NEW TICKETS

            tickets = {}

            # for ticket_id in ticket_ids:
            #     # TODO THIS SHOULD BE A GOOD PLACE TO UPSERT TICKET INFO SINCE
            #     # SCRAPER COULD FAIL
            #     ticket_info = scraper.get_ticket_info(ticket_id)
            #     tickets[ticket_id] = ticket_info

            if debug:
                ipdb.set_trace()

        except KeyboardInterrupt:
            pass
        except Exception as e:
            stacktrace = traceback.format_exc()
            scraper.log(stacktrace)
            scraper.log('{} Terminating'.format(e))

            ipdb.set_trace()

            # MAX_RETRIES = 10
            # i = 0
            # while i <= MAX_RETRIES:
            #     i += 1
            #     scraper.driver.current_url

        scraper.close_driver()
