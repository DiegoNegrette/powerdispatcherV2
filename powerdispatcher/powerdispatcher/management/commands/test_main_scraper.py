from django.core.management.base import BaseCommand

from powerdispatcher.tasks import scrape_and_upsert_powerdispatch_tickets


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--debug", action='store_true', default=False)

    def handle(self, *args, **options):
        scrape_and_upsert_powerdispatch_tickets()
