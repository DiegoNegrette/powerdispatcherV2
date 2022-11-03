from django.core.management.base import BaseCommand

from powerdispatcher.tasks import (
    scrape_and_upsert_powerdispatch_job_descriptions
)


class Command(BaseCommand):

    def handle(self, *args, **options):
        scrape_and_upsert_powerdispatch_job_descriptions()
