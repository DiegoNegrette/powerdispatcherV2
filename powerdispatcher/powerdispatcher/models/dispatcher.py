from django.db import models
from model_utils.models import TimeStampedModel

from powerdispatcher.models import ModifiedTimeStampMixin


class Dispatcher(ModifiedTimeStampMixin, TimeStampedModel):

    user = models.CharField(max_length=255, null=True, blank=True)
    name = models.CharField(max_length=255)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    enabled = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'Dispatchers'
        ordering = ('name',)
        unique_together = ['user', 'name']

    def __str__(self):
        return f"{self.name}"
