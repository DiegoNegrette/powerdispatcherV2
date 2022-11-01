import csv
import datetime

from django.core.management.base import BaseCommand

from powerdispatcher.models import Date


class Command(BaseCommand):
    help = 'Load the current database with Dates'

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str)

    def handle(self, *args, **options):
        cmd_name = 'create_dates'
        filename = options.get('file')

        processed = 0
        with open(filename, 'r') as f:
            csv_reader = csv.DictReader(f)
            rows = list(csv_reader)

        for row in rows:
            date_str = row["date"]
            date_obj = datetime.datetime.strptime(date_str, "%m/%d/%Y")
            Date.objects.get_or_create(
                date=date_obj,
                defaults={
                    "year": row["year"],
                    "quarter_number": row["quarter_number"],
                    "quarter_name": row["quarter_name"],
                    "month_number": row["month_number"],
                    "month_name": row["month_name"],
                    "month_short_name": row["month_short_name"],
                    "week_of_year": row["week_of_year"],
                    "week_of_month": row["week_of_month"],
                    "day": row["day"],
                    "day_of_week": row["day_of_week"],
                    "day_of_year": row["day_of_year"],
                    "day_name": row["day_name"],
                    "day_short_name": row["day_short_name"],
                }
            )
            processed += 1
        self.stdout.write(self.style.SUCCESS(
            f'[{cmd_name}] Successfully created {processed} Dates'
        ))
