from django.db import models
from model_utils.models import TimeStampedModel

from powerdispatcher.models import ModifiedTimeStampMixin


class Branch(ModifiedTimeStampMixin, TimeStampedModel):

    name = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    zip_code = models.CharField(max_length=5)

    class Meta:
        verbose_name_plural = 'Branches'
        ordering = ('name',)
        unique_together = ['name', 'city', 'zip_code']

    def __str__(self):
        return f"{self.name} - {self.city} - {self.zip_code}"
