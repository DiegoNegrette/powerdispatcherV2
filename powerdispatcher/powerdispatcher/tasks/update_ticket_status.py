import traceback

from celery.utils.log import get_task_logger
from django.utils import timezone

# TOOLS FOR TESTING
# from selenium.webdriver.common.action_chains import ActionChains
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.support.ui import WebDriverWait
from service.celery import app

from powerdispatcher.models import Status, Ticket
from powerdispatcher.scraper.powerdispatchcom.powerdispatch import (
    PowerdispatchSiteScraper,
)

logger = get_task_logger("scraper")
queue_name = "main_queue"


def log_info(message, scraper_log=None):
    logger.info(message)
    if scraper_log:
        scraper_log.set_last_message(message)


@app.task(queue_name=queue_name)
def update_ticket_status(ticket_ids=[]):
    MAX_TICKETS_TO_UPDATE = 1000
    status, _ = Status.objects.get_or_create(
        name="Canceled",
        who_canceled="Office",
        why_canceled="FU",
    )
    scraper = PowerdispatchSiteScraper()
    try:
        log_info("Initiating Webdriver")

        scraper.init_driver()

        log_info("Login into Powerdispatch")

        scraper.login()

        scraper.filter_job_list(date="today")

        log_info("Going to search menu")

        scraper.goto_search_menu()

        log_info("Calculating date range")

        MIN_DAYS_FROM_TODAY = 10
        current_date = timezone.localtime().date()
        to_date = current_date - timezone.timedelta(days=MIN_DAYS_FROM_TODAY)

        scraper.filter_search(end_date=to_date, status="FOLLOWUP")

        log_info(
            "Scraping ticket ids",
        )

        ticket_ids = scraper.get_ticket_ids_from_search_result(
            max_results=MAX_TICKETS_TO_UPDATE
        )

        ticket_ids = ticket_ids[:MAX_TICKETS_TO_UPDATE]
        for idx, ticket_id in enumerate(ticket_ids):
            log_info(f"{idx+1}/{len(ticket_ids)} Updating ticket {ticket_id}")
            try:
                scraper.update_ticket_status(ticket_id=ticket_id, status="CANCELED")
                Ticket.objects.filter(powerdispatch_ticket_id__in=[ticket_id]).update(
                    status=status
                )
            except Exception as e:
                log_info(e)

    except KeyboardInterrupt:
        pass
    except Exception as e:
        stacktrace = traceback.format_exc()
        scraper.log(stacktrace)
        scraper.log("{} Terminating".format(e))

    scraper.close_driver()
