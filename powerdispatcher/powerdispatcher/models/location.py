from django.db import models
from model_utils.models import TimeStampedModel

from powerdispatcher.models import ModifiedTimeStampMixin


class Location(ModifiedTimeStampMixin, TimeStampedModel):
    zip_code = models.CharField(max_length=5, primary_key=True)
    primary_city = models.CharField(max_length=255)
    county = models.CharField(max_length=255)
    state = models.CharField(max_length=255)
    state_short = models.CharField(max_length=255)
    country = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)

    class Meta:
        verbose_name_plural = "Locations"
        ordering = ("country", "state", "primary_city")
        unique_together = ["zip_code", "latitude", "latitude"]

    def __str__(self):
        return f"{self.zip_code} / {self.state_short} - {self.primary_city}"
