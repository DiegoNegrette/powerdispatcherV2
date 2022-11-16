from django.db import models
from model_utils.models import TimeStampedModel

from powerdispatcher.models import ModifiedTimeStampMixin


class Technician(ModifiedTimeStampMixin, TimeStampedModel):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    address = models.TextField(null=True, blank=True)
    city = models.TextField(null=True, blank=True)
    zip_code = models.CharField(max_length=5, null=True, blank=True)
    phone = models.CharField(max_length=10, null=True, blank=True)
    contact_type = models.CharField(max_length=255, null=True, blank=True)
    first_job_date = models.DateField(null=True, blank=True)
    last_job_date = models.DateField(null=True, blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'Technicians'
        ordering = ('name',)
        constraints = [
            models.UniqueConstraint(
                fields=['name'], name='technician_name_unique'  # noqa
            )
        ]

    def __str__(self):
        return f"{self.name}"
