from django.db import models
from model_utils.models import TimeStampedModel

from powerdispatcher.models import ModifiedTimeStampMixin


class Calendar(ModifiedTimeStampMixin, TimeStampedModel):
    pass
    # year = models.IntegerField()
    # year = models.IntegerField()
    # technician_availability = models.IntegerField()
    # open_day = models.TimeField(
    #     null=False,
    #     blank=False,
    # )
    # open_time = models.TimeField(
    #     null=False,
    #     blank=False,
    # )
    # closed_time = models.TimeField(
    #     null=False,
    #     blank=False,
    # )

    # class Meta:
    #     verbose_name_plural = 'Work Schedules'
    #     ordering = ('-date',)
    #     unique_together = ['date', 'branch']

    # def __str__(self):
    #     return f"{self.branch} - {self.date}"
