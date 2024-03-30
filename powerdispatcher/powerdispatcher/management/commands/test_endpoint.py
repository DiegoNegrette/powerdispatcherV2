from django.core.management.base import BaseCommand

from powerdispatcher.tasks import report_ticket_gclid


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--debug", action="store_true", default=False)

    def handle(self, *args, **options):
        report_ticket_gclid()
