import csv
from django.core.management.base import BaseCommand

from powerdispatcher.models import Location


class Command(BaseCommand):
    help = 'Load the current database with Locations'

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str)

    def handle(self, *args, **options):
        cmd_name = 'create_locations'
        filename = options.get('file')

        processed = 0
        with open(filename, 'r') as f:
            csv_reader = csv.DictReader(f)
            rows = list(csv_reader)

        for row in rows:
            latitude = row["latitude"].replace(',', '.')
            longitude = row["longitude"].replace(',', '.')
            Location.objects.get_or_create(
                zip_code=row["zip_code"],
                defaults={
                    "primary_city": row["primary_city"],
                    "county": row["county"],
                    "state": row["state"],
                    "state_short": row["state_short"],
                    "country": row["country"],
                    "latitude": latitude,
                    "longitude": longitude,
                }
            )
            processed += 1
        self.stdout.write(self.style.SUCCESS(
            f'[{cmd_name}] Successfully created {processed} Locations'
        ))
