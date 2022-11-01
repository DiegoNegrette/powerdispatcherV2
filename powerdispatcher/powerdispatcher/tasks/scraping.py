import ipdb
import traceback

from celery.utils.log import get_task_logger
from django.utils import timezone
# TOOLS FOR TESTING
from selenium.webdriver.common.action_chains import ActionChains  # noqa
from selenium.webdriver.common.by import By  # noqa
from selenium.webdriver.support import expected_conditions as EC  # noqa
from selenium.webdriver.support.ui import WebDriverWait  # noqa

from powerdispatcher.models import ProjectConfiguration, ScraperLog
from powerdispatcher.service import PowerdispatchManager
from powerdispatcher.scraper.powerdispatchcom.powerdispatch \
    import PowerdispatchSiteScraper
from service.celery import app

logger = get_task_logger('scraper')
queue_name = 'main_queue'


def log_info(message, scraper_log=None):
    logger.info(message)
    if scraper_log:
        scraper_log.set_last_message(message)


@app.task(queue_name=queue_name)
def get_tickets_info(ticket_ids=[], debug=False):
    scraper = PowerdispatchSiteScraper()
    try:
        scraper.init_driver()

        scraper.login()

        tickets_info = []

        for idx, ticket_id in enumerate(ticket_ids):

            log_info(f"{idx+1}/{len(ticket_ids)} Scraping ticket: {ticket_id}")

            ticket_info = scraper.get_ticket_info(ticket_id)

            scraper.log(ticket_info)

            tickets_info.append(ticket_info)

        if debug:
            ipdb.set_trace()

    except KeyboardInterrupt:
        pass
    except Exception as e:
        stacktrace = traceback.format_exc()
        scraper.log(stacktrace)
        scraper.log('{} Terminating'.format(e))

    scraper.close_driver()

    return tickets_info


@app.task(queue=queue_name)
def scrape_and_upsert_powerdispatch_tickets():

    last_scraper_log = ScraperLog.objects \
        .filter(status=ScraperLog.STATUS_SUCCESS).last()

    current_date = timezone.localtime(timezone.now()).date()
    to_date = current_date - timezone.timedelta(days=2)
    project_configuration = ProjectConfiguration.objects.get()
    if last_scraper_log:
        from_date = last_scraper_log.to_date + timezone.timedelta(days=1)
    elif project_configuration.first_scraping_date:
        from_date = project_configuration.first_scraping_date
    else:
        from_date = current_date - timezone.timedelta(days=5)

    scraper_log = ScraperLog.objects.create(
        from_date=from_date,
        to_date=to_date,
        start_time=timezone.now()
    )

    scraper = PowerdispatchSiteScraper()

    scraping_completed = False
    try:
        log_info("Initiating Webdriver", scraper_log=scraper_log)

        scraper.init_driver()

        log_info("Login into Powerdispatch", scraper_log=scraper_log)

        scraper.login()

        log_info("Going to search menu", scraper_log=scraper_log)

        scraper.goto_search_menu()

        log_info("Calculating target date", scraper_log=scraper_log)

        log_info(
            f"Filtering tickets from {scraper_log.from_date} to {scraper_log.to_date}",  # noqa
            scraper_log=scraper_log
        )

        scraper.filter_search(from_date, to_date)

        log_info("Scraping ticket ids", scraper_log=scraper_log)

        ticket_ids = scraper.get_ticket_ids_from_search_result()

        # TODO THIS COULD BE A GOOD PLACE TO SELECT ONLY NEW TICKETS
        # Wont do it since number of tickets is a growing number
        # Repeated tickets should not be found

        tickets_info = []

        for idx, ticket_id in enumerate(ticket_ids):
            # TODO THIS SHOULD BE A GOOD PLACE TO UPSERT TICKET INFO SINCE
            # SCRAPER COULD FAIL
            log_info(
                f"{idx+1}/{len(ticket_ids)} Scraping ticket {ticket_id}",
                scraper_log=scraper_log
            )
            ticket_info = scraper.get_ticket_info(ticket_id)
            tickets_info.append(ticket_info)
        scraping_completed = True
    except KeyboardInterrupt:
        pass
    except Exception as e:
        stacktrace = traceback.format_exc()
        scraper.log(stacktrace)
        scraper.log('{} Terminating'.format(e))
        logger.error(e)
        scraper_log.end_as(status=ScraperLog.STATUS_FAILED, reason=str(e))

        ipdb.set_trace()

    scraper.close_driver()

    if not scraping_completed:
        return

    ticket_manager = PowerdispatchManager()

    new_tickets = 0
    try:
        for idx, ticket_info in enumerate(tickets_info):
            log_info(
                f"{idx+1}/{len(ticket_ids)} Upserting ticket {ticket_id}",
                scraper_log=scraper_log
            )
            _, created = ticket_manager.upsert_ticket(ticket_info)
            if created:
                new_tickets += 1
        scraper_log \
            .end_as(status=ScraperLog.STATUS_SUCCESS, reason="End of task reached")  # noqa
    except Exception as e:
        logger.error(e)
        scraper_log.end_as(status=ScraperLog.STATUS_FAILED, reason=str(e))

    scraper.scraped_tickets = len(tickets_info)
    scraper.added_tickets = new_tickets
    scraper.save(update_fields=["scraped_tickets", "added_tickets"])


@app.task(queue=queue_name)
def scrape_and_upsert_powerdispatch_job_descriptions():
    pass
