from datetime import timedelta
import traceback

from celery.utils.log import get_task_logger
from django.conf import settings
from django.db.models import F, Q
from django.utils import timezone

from powerdispatcher.scraper.powerdispatchcom import PowerdispatchSiteScraper
from powerdispatcher.models import ProjectConfiguration, Ticket
from service.celery import app

logger = get_task_logger("scraper")
queue_name = "main_queue"


@app.task(queue_name=queue_name)
def review_follow_up_tickets(ticket_ids=[]):

    if ticket_ids:
        target_tickets = (
            Ticket.objects.filter(
                Q(id__in=ticket_ids),
            )
            .select_related("customer")
            .order_by("job_date")
        )
    else:
        project_configuration = ProjectConfiguration.objects.get()
        from_date = project_configuration.first_date_to_review_follow_up_tickets
        max_date = timezone.now() - timedelta(days=30)
        target_tickets = (
            Ticket.objects.filter(
                Q(created__gte=from_date),
                Q(status__name="Follow Up"),
                Q(last_scraping_attempt__isnull=True)
                | Q(last_scraping_attempt__lt=max_date),
            )
            .select_related("status", "technician")
            .order_by(F("last_scraping_attempt").asc(nulls_first=True))
        )
        # .order_by("job_date")
        target_tickets = target_tickets[0:100]

    scraper = PowerdispatchSiteScraper()
    try:
        scraper.log("Initiating Webdriver")

        scraper.init_driver()

        scraper.log("Login into Powerdispatch")

        scraper.login()

        scraper.log(
            "Scraping ticket ids",
        )

        for idx, ticket in enumerate(ticket):
            ticket_id = ticket.powerdispatch_ticket_id
            scraper.log(f"{idx+1}/{len(ticket_ids)} Updating ticket {ticket_id}")
            try:
                ticket_permalink = settings.POWERDISPATCHER_TICKET_URL.format(
                    ticket_id=ticket_id
                )
                scraper.navigate_to(ticket_permalink)
                technician = scraper.get_ticket_technician()
                status, who_canceled_str, why_canceled_str = scraper.get_ticket_status()
                if ticket.status.name != status:
                    # Update status
                    pass
                if status != "Canceled":
                    #
                    pass
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
