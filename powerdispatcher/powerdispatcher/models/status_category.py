from django.db import models
from model_utils.models import TimeStampedModel

from powerdispatcher.models import ModifiedTimeStampMixin


class StatusCategory(ModifiedTimeStampMixin, TimeStampedModel):
    name = models.CharField(max_length=20)

    class Meta:
        verbose_name_plural = 'Status Categories'
        ordering = ('name',)
        constraints = [
            models.UniqueConstraint(
                fields=['name'], name='status_category_unique'
            )
        ]

    def __str__(self):
        return self.name
