from django.db import models
from model_utils.models import TimeStampedModel

from powerdispatcher.models import Branch, Date, ModifiedTimeStampMixin


class WorkSchedule(ModifiedTimeStampMixin, TimeStampedModel):

    date = models.ForeignKey(Date, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    technician_availability = models.BooleanField(default=True)
    open_day = models.TimeField(
        null=False,
        blank=False,
    )
    open_time = models.TimeField(
        null=False,
        blank=False,
    )
    closed_time = models.TimeField(
        null=False,
        blank=False,
    )

    class Meta:
        verbose_name_plural = 'Work Schedules'
        ordering = ('-date',)
        unique_together = ['date', 'branch']

    def __str__(self):
        return f"{self.branch} - {self.date}"
