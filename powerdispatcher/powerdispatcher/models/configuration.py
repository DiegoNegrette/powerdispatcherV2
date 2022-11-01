from django.db import models
from solo.models import SingletonModel


class ProjectConfiguration(SingletonModel):
    """
        https://github.com/lazybird/django-solo/
    """

    # TODO might need to add max scraping days
    powerdispatch_account = models.CharField(
        max_length=100,
        verbose_name='Account id used to connect to powerdispatch app'
    )

    powerdispatch_username = models.CharField(
        max_length=100,
        verbose_name='Account username used to connect to powerdispatch app'
    )

    powerdispatch_password = models.CharField(
        max_length=100,
        verbose_name='Account password used to connect to powerdispatch app'
    )

    first_scraping_date = models.DateField(
        verbose_name='All scraped records will start from this date'
    )

    class Meta:
        verbose_name = 'Project configurations'
        verbose_name_plural = 'Project configurations'

    def __str__(self):
        return 'Project configurations'
