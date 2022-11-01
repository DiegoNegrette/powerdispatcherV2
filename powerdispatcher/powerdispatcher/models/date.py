from django.db import models
from model_utils.models import TimeStampedModel

from powerdispatcher.models import ModifiedTimeStampMixin


class Date(ModifiedTimeStampMixin, TimeStampedModel):
    date = models.DateField(primary_key=True)
    year = models.IntegerField()
    quarter_number = models.IntegerField()
    quarter_name = models.CharField(max_length=2)
    month_number = models.IntegerField()
    month_name = models.CharField(max_length=10)
    month_short_name = models.CharField(max_length=4)
    week_of_year = models.IntegerField()
    week_of_month = models.IntegerField()
    day = models.IntegerField()
    day_of_week = models.IntegerField()
    day_of_year = models.IntegerField()
    day_name = models.CharField(max_length=10)
    day_short_name = models.CharField(max_length=3)

    class Meta:
        verbose_name_plural = 'Dates'
        ordering = ('-date',)

    def __str__(self):
        return f"{self.date}"
