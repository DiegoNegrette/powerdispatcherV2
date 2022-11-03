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

    MIN_DAYS_FROM_TODAY = 2
    current_date = timezone.localtime().date()
    to_date = current_date - timezone.timedelta(days=MIN_DAYS_FROM_TODAY)
    project_configuration = ProjectConfiguration.objects.get()
    if last_scraper_log:
        from_date = last_scraper_log.to_date + timezone.timedelta(days=1)
    elif project_configuration.first_scraping_date:
        from_date = project_configuration.first_scraping_date
    else:
        from_date = current_date - timezone.timedelta(days=5)

    if from_date > to_date:
        log_info(
            f"Records must be at least {MIN_DAYS_FROM_TODAY} days old"
            " to be scraped"
        )
        return

    max_scraping_days = project_configuration.max_scraping_days
    days_to_be_scraped = (to_date - from_date).days
    if max_scraping_days and days_to_be_scraped > max_scraping_days:
        to_date = from_date + timezone.timedelta(days=max_scraping_days)

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

        log_info("Calculating date range", scraper_log=scraper_log)

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

    scraper.close_driver()

    if not scraping_completed:
        return

    powerdispatch_manager = PowerdispatchManager()

    new_tickets = 0
    try:
        for idx, ticket_info in enumerate(tickets_info):
            log_info(
                f"{idx+1}/{len(ticket_ids)} Upserting ticket {ticket_id}",
                scraper_log=scraper_log
            )
            _, created = powerdispatch_manager.upsert_ticket(ticket_info)
            if created:
                new_tickets += 1
        scraper_log \
            .end_as(status=ScraperLog.STATUS_SUCCESS, reason="End of task reached")  # noqa
    except Exception as e:
        logger.error(e)
        scraper_log.end_as(status=ScraperLog.STATUS_FAILED, reason=str(e))

    scraper_log.scraped_tickets = len(tickets_info)
    scraper_log.added_tickets = new_tickets
    scraper_log.save(update_fields=["scraped_tickets", "added_tickets"])


@app.task(queue=queue_name)
def scrape_job_descriptions():
    job_descriptions = []
    scraper = PowerdispatchSiteScraper()
    try:
        scraper.init_driver()

        scraper.login()

        job_descriptions = scraper.get_job_descriptions()

        for job_description in job_descriptions:
            scraper.log(job_description)

    except KeyboardInterrupt:
        pass
    except Exception as e:
        stacktrace = traceback.format_exc()
        scraper.log(stacktrace)
        scraper.log('{} Terminating'.format(e))

    scraper.close_driver()

    return job_descriptions


@app.task(queue=queue_name)
def scrape_and_upsert_powerdispatch_job_descriptions():
    job_descriptions = scrape_job_descriptions()
    powerdispatch_manager = PowerdispatchManager()
    for idx, job_description in enumerate(job_descriptions):
        log_info(
            f"{idx+1}/{len(job_descriptions)} "
            f"Upserting job description: {job_description}"
        )
        powerdispatch_manager.upsert_job_descriptions(job_description)
