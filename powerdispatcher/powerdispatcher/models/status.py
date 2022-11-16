from django.db import models
from model_utils.models import TimeStampedModel

from powerdispatcher.models import ModifiedTimeStampMixin


class Status(ModifiedTimeStampMixin, TimeStampedModel):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=20)
    who_canceled = models.CharField(
        max_length=255, null=True, blank=True
    )
    why_canceled = models.CharField(
        max_length=255, null=True, blank=True
    )

    class Meta:
        verbose_name_plural = 'Status'
        ordering = ('-id',)

    def __str__(self):
        return self.name
