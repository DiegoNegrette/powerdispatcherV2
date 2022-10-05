from django.db import models
from model_utils.models import TimeStampedModel

from powerdispatcher.models import ModifiedTimeStampMixin


class Technician(ModifiedTimeStampMixin, TimeStampedModel):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    enabled = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'Technicians'
        ordering = ('first_name',)
        unique_together = ['first_name', 'last_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
