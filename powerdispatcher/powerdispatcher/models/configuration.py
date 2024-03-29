from django.db import models
from django.utils import timezone
from solo.models import SingletonModel


class ProjectConfiguration(SingletonModel):
    """
    https://github.com/lazybird/django-solo/
    """

    # TODO might need to add max scraping days
    powerdispatch_account = models.CharField(
        default="Account placeholder",
        max_length=100,
        verbose_name="Account id used to connect to powerdispatch app",
    )

    powerdispatch_username = models.CharField(
        default="Username placeholder",
        max_length=100,
        verbose_name="Account username used to connect to powerdispatch app",
    )

    powerdispatch_password = models.CharField(
        default="Account placeholder",
        max_length=100,
        verbose_name="Account password used to connect to powerdispatch app",
    )

    first_scraping_date = models.DateField(
        default=timezone.localtime,
        verbose_name="All scraped records will start from this date",
    )

    max_scraping_days = models.IntegerField(
        default=7, verbose_name="Max amount of days to scrape"
    )

    first_date_to_report_gclid = models.DateField(
        default=timezone.localtime,
        verbose_name="All tickets from this date will report their gclid",
    )

    class Meta:
        verbose_name = "Project configuration"
        verbose_name_plural = "Project configurations"

    def __str__(self):
        return "Project configuration"
