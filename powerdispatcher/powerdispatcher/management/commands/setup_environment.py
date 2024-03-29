from os.path import abspath, dirname, join
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Environment initial setup"

    def handle(self, *args, **options):
        data_path = join(abspath(dirname(__file__)), "data")

        call_command("create_dates", "--file", join(data_path, "dates.csv"))
        call_command("create_locations", "--file", join(data_path, "locations.csv"))
