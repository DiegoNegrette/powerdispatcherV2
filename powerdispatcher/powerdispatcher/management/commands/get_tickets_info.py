from django.core.management.base import BaseCommand

from powerdispatcher.tasks import get_ticket_info


TICKET_IDS = [
    "LMFD2",
    "11HVH",
    "B2YY3",
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

        get_ticket_info(ticket_ids)
