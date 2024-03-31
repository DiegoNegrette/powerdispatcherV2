import traceback

import ipdb
from celery.utils.log import get_task_logger
from django.utils import timezone
from django.conf import settings

# TOOLS FOR TESTING
# from selenium.webdriver.common.action_chains import ActionChains
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.support.ui import WebDriverWait
from powerdispatcher.powerdispatcher.utils import report_to_slack
from service.celery import app

from powerdispatcher.models import ProjectConfiguration, ScraperLog
from powerdispatcher.scraper.powerdispatchcom.powerdispatch import (
    PowerdispatchSiteScraper,
)
from powerdispatcher.service import PowerdispatchManager

logger = get_task_logger("scraper")
queue_name = "main_queue"


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
        scraper.log("{} Terminating".format(e))

    scraper.close_driver()

    return tickets_info


@app.task(queue=queue_name)
def scrape_and_upsert_powerdispatch_tickets():
    task_title = "SCRAPE AND UPSERT POWERDISPATCH TICKETS"

    last_scraper_log = ScraperLog.objects.filter(
        status=ScraperLog.STATUS_SUCCESS
    ).first()

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
            f"Records must be at least {MIN_DAYS_FROM_TODAY} days old" " to be scraped"
        )
        return

    max_scraping_days = project_configuration.max_scraping_days
    days_to_be_scraped = (to_date - from_date).days
    if max_scraping_days and days_to_be_scraped >= max_scraping_days:
        to_date = from_date + timezone.timedelta(days=max_scraping_days - 1)

    scraper_log = ScraperLog.objects.create(
        from_date=from_date, to_date=to_date, start_time=timezone.now()
    )

    scraper = PowerdispatchSiteScraper()

    scraping_completed = False
    report_lines = []
    error_lines = ["🆘 Task errors:"]
    try:
        log_info("Initiating Webdriver", scraper_log=scraper_log)

        scraper.init_driver()

        log_info("Login into Powerdispatch", scraper_log=scraper_log)

        scraper.login()

        log_info("Going to search menu", scraper_log=scraper_log)

        scraper.goto_search_menu()

        log_info("Calculating date range", scraper_log=scraper_log)

        log_info(
            f"Filtering tickets from {scraper_log.from_date} to {scraper_log.to_date}",
            scraper_log=scraper_log,
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
                scraper_log=scraper_log,
            )
            ticket_info = scraper.get_ticket_info(ticket_id)
            tickets_info.append(ticket_info)
        scraping_completed = True
    except KeyboardInterrupt:
        pass
    except Exception as e:
        stacktrace = traceback.format_exc()
        scraper.log(stacktrace)
        scraper.log("{} Terminating".format(e))
        scraper_log.end_as(status=ScraperLog.STATUS_FAILED, reason=str(e))
        error_lines.append(str(e))

    scraper.close_driver()

    if not scraping_completed:
        report_lines.append("Scraper Log:")
        report_lines.append(f"Id: {scraper_log.id}")
        report_lines.append(f"From date: {scraper_log.from_date.strftime("%Y-%m-%d %H:%M:%S")}")
        report_lines.append(f"To date: {scraper_log.to_date.strftime("%Y-%m-%d %H:%M:%S")}")
        report_lines.append(f"Start time: {scraper_log.start_time.strftime("%Y-%m-%d %H:%M:%S")}")
        report_lines.append(f"End time: {scraper_log.end_time.strftime("%Y-%m-%d %H:%M:%S")}")
        report_lines.append(f"Scraped_tickets: {scraper_log.scraped_tickets}")
        report_lines.append(f"Added_tickets: {scraper_log.added_tickets}")
        report_lines.append(f"Status: {scraper_log.status}")
        report_lines.append(f"Reason: {scraper_log.reason}")
        report_lines.append(f"Last message: {scraper_log.last_message}")
        report_to_slack(
            task_title,
            report_lines + error_lines,
            settings.HOOK_SLACK_PROLOCKSMITHS_ERRORS,
            logger,
        )
        return

    powerdispatch_manager = PowerdispatchManager()

    new_tickets = 0
    try:
        for idx, ticket_info in enumerate(tickets_info):
            ticket_id = ticket_info["powerdispatch_ticket_id"]
            log_info(
                f"{idx+1}/{len(ticket_ids)} Upserting ticket {ticket_id}",
                scraper_log=scraper_log,
            )
            _, created = powerdispatch_manager.upsert_ticket(ticket_info)
            if created:
                new_tickets += 1
        scraper_log.end_as(
            status=ScraperLog.STATUS_SUCCESS, reason="End of task reached"
        )
    except Exception as e:
        stacktrace = traceback.format_exc()
        logger.error(stacktrace)
        logger.error("{} Terminating".format(e))
        scraper_log.end_as(status=ScraperLog.STATUS_FAILED, reason=str(e))
        error_lines.append(str(e))

    scraper_log.scraped_tickets = len(tickets_info)
    scraper_log.added_tickets = new_tickets
    scraper_log.save(update_fields=["scraped_tickets", "added_tickets"])
    report_lines.append("Scraper Log:")
    report_lines.append(f"Id: {scraper_log.id}")
    report_lines.append(f"From date: {scraper_log.from_date.strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"To date: {scraper_log.to_date.strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"Start time: {scraper_log.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"End time: {scraper_log.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"Scraped_tickets: {scraper_log.scraped_tickets}")
    report_lines.append(f"Added_tickets: {scraper_log.added_tickets}")
    report_lines.append(f"Status: {scraper_log.status}")
    report_lines.append(f"Reason: {scraper_log.reason}")
    report_lines.append(f"Last message: {scraper_log.last_message}")
    if len(error_lines) > 1:
        report_to_slack(
            task_title,
            report_lines + error_lines,
            settings.HOOK_SLACK_PROLOCKSMITHS_ERRORS,
            logger,
        )
    else:
        report_to_slack(
            task_title,
            report_lines,
            settings.HOOK_SLACK_PROLOCKSMITHS_ALERTS,
            logger,
        )


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
        scraper.log("{} Terminating".format(e))

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
