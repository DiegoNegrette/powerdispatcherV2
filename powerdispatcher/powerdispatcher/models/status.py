from django.db import models
from model_utils.models import TimeStampedModel

from powerdispatcher.models import ModifiedTimeStampMixin
from powerdispatcher.models.status_category import StatusCategory


class Status(ModifiedTimeStampMixin, TimeStampedModel):
    status_category = models.ForeignKey(StatusCategory, on_delete=models.PROTECT)  # noqa
    who_cancelled = models.CharField(max_length=255)
    why_cancelled = models.CharField(
        max_length=255, null=True, blank=True
    )

    class Meta:
        verbose_name_plural = 'Status'
        ordering = ('-id',)

    def __str__(self):
        return self.status_category.name
