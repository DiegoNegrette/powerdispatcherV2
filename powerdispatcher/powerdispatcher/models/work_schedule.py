from django.db import models
from model_utils.models import TimeStampedModel

from powerdispatcher.models import Branch, Date, ModifiedTimeStampMixin


class WorkSchedule(ModifiedTimeStampMixin, TimeStampedModel):

    id = models.AutoField(primary_key=True)
    date = models.ForeignKey(Date, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    technician_availability = models.IntegerField(default=0)
    open_day = models.BooleanField(default=True)
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
