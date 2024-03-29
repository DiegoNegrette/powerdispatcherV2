import json
import requests
from celery.utils.log import get_task_logger
from django.db.models import Q
from service.celery import app
from third_party.callrail.api import CallRailAPI

from powerdispatcher.models import ProjectConfiguration, Ticket

logger = get_task_logger("scraper")
queue_name = "main_queue"


REPORT_GCLID_URL = (
    "https://analytics-api.getconversiondata.com/t/serverside-integration"  # noqa
)


def log_info(message):
    logger.info(message)


def log_error(message):
    logger.error(message)


@app.task(queue_name=queue_name)
def report_ticket_gclid(ticket_ids=[]):
    callrail_api = CallRailAPI()
    if ticket_ids:
        target_tickets = (
            Ticket.objects.filter(
                Q(id__in=ticket_ids),
                Q(empty_callrail_logs=False),
                Q(has_reported_gclid=False),
            )
            .select_related("customer")
            .order_by("job_date")
        )
    else:
        project_configuration = ProjectConfiguration.objects.get()
        from_date = project_configuration.first_date_to_report_gclid
        target_tickets = (
            Ticket.objects.filter(
                Q(job_date__gte=from_date),
                Q(empty_callrail_logs=False),
                Q(has_reported_gclid=False),
            )
            .select_related("customer")
            .order_by("job_date")
        )

        # target_tickets = target_tickets[:1000]

    for idx, ticket in enumerate(target_tickets):
        customer_phone_number = f"+1{ticket.customer.phone}"
        # customer_phone_number = '+19566488345'
        print(
            f"******** {idx+1}/{len(target_tickets)} Ticket id: {ticket.powerdispatch_ticket_id} - {customer_phone_number} ********"
        )  # noqa
        gclid = None
        sale_value = ticket.credit_payment + ticket.cash_payment
        sale_value = float(json.dumps(sale_value, default=float))
        calls = callrail_api.get_calls_by_customer_phone_number(customer_phone_number)
        if not calls:
            # What to do when ticket not found in calls
            ticket.mark_empty_callrail_logs()
            continue
        for call in calls:
            if call.get("gclid", None):
                gclid = call.get("gclid", None)
                break
        try:
            data = {
                "phoneNumber": customer_phone_number,
                "AllParams": {"gclid": gclid},
                "eventValue": sale_value,
                "currency": "USD",
                "clientID": "5b4392bb-08c8-4d81-aefa-cd03bbd46794",
                "eventName": "Prolocksmith Sale",
                # "eventName": "Test Sale",
                "OrderID": ticket.powerdispatch_ticket_id,
                "stopEnrich": True,
            }
            print(data)
            r = requests.post(url=REPORT_GCLID_URL, json=data, timeout=240)
            if r.status_code == 200:
                ticket.mark_reported_gclid(gclid)
        except Exception as e:
            log_error(str(e))
