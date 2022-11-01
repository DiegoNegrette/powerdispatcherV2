from django.core.management.base import BaseCommand

from powerdispatcher.tasks import get_tickets_info
from powerdispatcher.service import PowerdispatchManager


TICKET_IDS = [
    "LMFD2",
    "11HVH",
    "B2YY3",
    "FEGV4",
]


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--debug", action='store_true', default=False)
        parser.add_argument('--ticket_id')

    def handle(self, *args, **options):
        ticket_ids = []
        debug = options.get("debug")
        if debug:
            ticket_ids = TICKET_IDS
        ticket_id = options.get("ticket_id")
        if ticket_id:
            ticket_ids.append(ticket_id)

        tickets_info = get_tickets_info(ticket_ids)

        ticket_manager = PowerdispatchManager()
        for ticket_info in tickets_info:
            ticket_manager.upsert_ticket(ticket_info)
