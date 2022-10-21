import ipdb
import time
import traceback

from celery.utils.log import get_task_logger
# TOOLS FOR TESTING
from selenium.webdriver.common.action_chains import ActionChains  # noqa
from selenium.webdriver.common.by import By  # noqa
from selenium.webdriver.support import expected_conditions as EC  # noqa
from selenium.webdriver.support.ui import WebDriverWait  # noqa

from powerdispatcher.scraper.powerdispatchcom.powerdispatch \
    import PowerdispatchSiteScraper
from service.celery import app

logger = get_task_logger('scraper')
queue_name = 'main_queue'


@app.task(queue_name=queue_name)
def get_ticket_info(ticket_ids=[], debug=False):
    scraper = PowerdispatchSiteScraper()
    try:
        scraper.init_driver()

        scraper.login()

        for ticket_id in ticket_ids:

            ticket_info = scraper.get_ticket_info(ticket_id)

            scraper.log(ticket_info)

        if debug:
            ipdb.set_trace()

    except KeyboardInterrupt:
        pass
    except Exception as e:
        stacktrace = traceback.format_exc()
        scraper.log(stacktrace)
        scraper.log('{} Terminating'.format(e))

    scraper.close_driver()


@app.task(queue=queue_name)
def scrape_and_upsert_powerdispatch_tickets():
    logger.info("STARTING TEST ASYNC TASK")
    time.sleep(60)
    logger.info("FINISHED TEST ASYNC TASK")
