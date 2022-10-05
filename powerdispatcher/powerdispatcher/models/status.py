from django.db import models
from model_utils.models import TimeStampedModel

from powerdispatcher.models import ModifiedTimeStampMixin
from powerdispatcher.models.status_category import StatusCategory


class Status(ModifiedTimeStampMixin, TimeStampedModel):
    # This feel was added but it was not on the table
    name = models.CharField(max_length=20)
    status_category = models.ForeignKey(StatusCategory, on_delete=models.PROTECT)  # noqa
    who_cancelled = models.CharField(max_length=255)
    who_cancelled_description = models.CharField(
        max_length=255, null=True, blank=True
    )

    class Meta:
        verbose_name_plural = 'Status'
        ordering = ('name',)
        constraints = [
            models.UniqueConstraint(
                fields=['name'], name='status_name_unique'
            )
        ]

    def __str__(self):
        return self.name
