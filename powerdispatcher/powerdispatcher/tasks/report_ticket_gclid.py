import aiohttp
import asyncio
import json

from celery.utils.log import get_task_logger
from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from ..utils import (
    make_post_request,
    report_to_slack,
)
from powerdispatcher.models import ProjectConfiguration, Ticket
from service.celery import app
from third_party.callrail.api import CallRailAPI


logger = get_task_logger("callrail")
queue_name = "main_queue"


REPORT_GCLID_URL = (
    "https://send-conversions-to-google-ads-t2px3tzmra-uc.a.run.app/conversion"
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

    target_tickets = target_tickets[0:100]

    tickets_in_container = []
    conversions_container = []

    discarded_tickets = ["Discarded tickets:"]

    for idx, ticket in enumerate(target_tickets):
        customer_phone_number = f"+1{ticket.customer.phone}"
        print(
            f"******** {idx+1}/{len(target_tickets)} Ticket id: {ticket.powerdispatch_ticket_id} - {customer_phone_number} ********"  # noqa
        )  # noqa
        gclid = None
        sale_value = ticket.credit_payment + ticket.cash_payment
        sale_value = float(json.dumps(sale_value, default=float))
        calls = callrail_api.get_calls_by_customer_phone_number(customer_phone_number)
        if not calls:
            # What to do when ticket not found in calls
            ticket.mark_empty_callrail_logs()
            discarded_tickets.append(f"- {ticket.id}")
            continue
        for call in calls:
            if call.get("gclid", None):
                gclid = call.get("gclid", None)
                break

        if not gclid:
            ticket.mark_empty_callrail_logs()
            discarded_tickets.append(f"- {ticket.id}")
            continue

        # Assuming ticket.created_at is your datetime object
        ticket_created_at = ticket.created_at

        # Format the datetime part
        formatted_datetime = ticket_created_at.strftime("%Y-%m-%d %H:%M:%S")

        # Format the timezone offset part
        offset_hours = ticket_created_at.utcoffset().seconds // 3600
        offset_minutes = (ticket_created_at.utcoffset().seconds // 60) % 60
        timezone_offset = "{:02d}:{:02d}".format(offset_hours, offset_minutes)

        # Concatenate datetime and timezone offset with a colon
        formatted_date_with_colon = formatted_datetime + "+" + timezone_offset
        data = {
            "conversion_action_id": "704314739",
            "conversion_date_time": formatted_date_with_colon,
            "gclid": gclid,  # noqa
            "order_id": ticket.powerdispatch_ticket_id,
            "conversion_value": sale_value,
        }
        conversions_container.append(data)
        tickets_in_container.append({"ticket_obj": ticket, "gclid": gclid})

    if not settings.GOOGLE_ADS_AUTH_TOKEN:
        raise Exception("GOOGLE_ADS_AUTH_TOKEN needs to be set")

    batch_size = 10
    tickets_in_batch = [
        tickets_in_container[i : i + batch_size]  # noqa
        for i in range(0, len(tickets_in_container), batch_size)
    ]

    headers = {
        "auth_key": settings.GOOGLE_ADS_AUTH_TOKEN,
        "Content-Type": "application/json",
    }

    async def main():
        async with aiohttp.ClientSession(headers=headers) as session:
            tasks = []
            for i in range(0, len(conversions_container), batch_size):
                conversions = conversions_container[i : i + batch_size]  # noqa
                tasks.append(
                    make_post_request(
                        REPORT_GCLID_URL,
                        session,
                        {
                            "customer_id": "2874732500",
                            "mcc_id": "5764436564",
                            "conversions": conversions,
                        },
                    )
                )
            responses = await asyncio.gather(*tasks)
            return responses

    responses = asyncio.run(main())

    update_list = []
    update_date = timezone.now()
    report_lines = []
    for idx, status in enumerate(responses):
        if status == 200:
            for ticket_dict in tickets_in_batch[idx]:
                ticket = ticket_dict["ticket_obj"]
                ticket.reported_gclid = ticket_dict["gclid"]
                ticket.has_reported_gclid = True
                ticket.reported_gclid_at = update_date
                update_list.append(ticket)
                # report_lines.append(
                #     f"******** Ticket id: {ticket.powerdispatch_ticket_id} - Phone: +1{ticket.customer.phone} - GCLID: {ticket.reported_gclid} ********"  # noqa
                # )
    # report_lines = report_lines + discarded_tickets
    Ticket.objects.bulk_update(
        update_list, ["reported_gclid", "has_reported_gclid", "reported_gclid_at"]
    )
    success_message = f'\nReported {len(update_list)} ticket{"s" if len(update_list) > 1 else "" } to google ads'
    report_lines.append(success_message)
    report_to_slack(
        "REPORT TICKET GCLID TASK",
        report_lines,
        settings.HOOK_SLACK_PROLOCKSMITHS_ALERTS,
        logger,
    )
