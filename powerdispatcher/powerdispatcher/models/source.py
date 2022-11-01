from django.db import models
from model_utils.models import TimeStampedModel

from powerdispatcher.models import ModifiedTimeStampMixin


class Source(ModifiedTimeStampMixin, TimeStampedModel):
    name = models.TextField()
    category = models.TextField()

    class Meta:
        verbose_name_plural = 'Sources'
        ordering = ('name',)
        unique_together = ["name", "category"]

    def __str__(self):
        return f"{self.name} - {self.category}"
