from datetime import timedelta
import traceback

from celery.utils.log import get_task_logger
from django.conf import settings
from django.db import transaction
from django.db.models import F, Q
from django.utils import timezone

from powerdispatcher.scraper.powerdispatchcom.powerdispatch import (
    PowerdispatchSiteScraper,
)
from powerdispatcher.models import ProjectConfiguration, Ticket
from powerdispatcher.service.powerdispatch import PowerdispatchManager
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
                # Q(description=CLO, LO, RESIDENTIAL LO),
                Q(status__name__in=["Follow Up", "Estimate", "On hold", "Appointment"]),
                Q(follow_up_reviewed_failed_times__lt=3),
                Q(last_scraping_attempt__isnull=True)
                | Q(last_scraping_attempt__lt=max_date),
            )
            .select_related("status", "technician")
            .order_by(F("last_scraping_attempt").asc(nulls_first=True))
        )
        # .order_by("job_date")
        target_tickets = target_tickets[0:100]
    
    ticket_id_to_obj_dict = {ticket.id: ticket for ticket in target_tickets}

    scraper = PowerdispatchSiteScraper()
    tickets_reviewed_successfully_dict = {}
    tickets_failed = []
    try:
        scraper.log("Initiating Webdriver")

        scraper.init_driver()

        scraper.log("Login into Powerdispatch")

        scraper.login()
        for idx, ticket in enumerate(target_tickets):
            ticket_id = ticket.powerdispatch_ticket_id
            scraper.log(f"{idx+1}/{len(ticket_ids)} Updating ticket {ticket_id}")
            try:
                ticket_permalink = settings.POWERDISPATCHER_TICKET_URL.format(
                    ticket_id=ticket_id
                )
                scraper.navigate_to(ticket_permalink)
                technician = scraper.get_ticket_technician()
                status, who_canceled_str, why_canceled_str = scraper.get_ticket_status()
                (
                    alternative_technician,
                    follow_up_given_by_alternative_technician,
                    follow_up_strategy_successfull,
                ) = scraper.get_ticket_follow_up_info()
                tickets_reviewed_successfully_dict[ticket.id] = {
                    "technician": technician,
                    "status": status,
                    "who_canceled_str": who_canceled_str,
                    "why_canceled_str": why_canceled_str,
                    "alternative_technician": alternative_technician,
                    "follow_up_given_by_alternative_technician": follow_up_given_by_alternative_technician,
                    "follow_up_strategy_successfull": follow_up_strategy_successfull,
                }
            except Exception as e:
                scraper.log(f"{str(e)} Skipping ticket: {ticket_id}")
                tickets_failed[ticket.id] = {"follow_up_reviewed_failed_last_reason": str(e)}
    except KeyboardInterrupt:
        pass
    except Exception as e:
        stacktrace = traceback.format_exc()
        scraper.log(stacktrace)
        scraper.log("{} Terminating".format(e))

    scraper.close_driver()
    
    powerdispatch_manager = PowerdispatchManager()
    
    for ticket_id, updated_info in tickets_reviewed_successfully_dict:
        try:
            technician = (
                powerdispatch_manager.upsert_technician(updated_info["technician"])
                if updated_info["technician"]
                else None
            )
            alternative_technician = (
                powerdispatch_manager.upsert_technician(updated_info["alternative_technician"])
                if updated_info["alternative_technician"]
                else None
            )
            status = powerdispatch_manager.get_status(
                status_str=updated_info["status"],
                who_canceled=updated_info["who_canceled"],
                why_canceled=updated_info["why_canceled"],
            )
        except Exception as e:
            stacktrace = traceback.format_exc()
            logger.warning(stacktrace)
            logger.warning(e)
            tickets_failed[ticket_id] = {"follow_up_reviewed_failed_last_reason": str(e)}
        # follow_up_reviewed_failed_times
        # follow_up_reviewed_failed_last_reason
    with transaction.atomic():
        pass
