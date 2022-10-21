from django.db import models
from model_utils.models import TimeStampedModel

from powerdispatcher.models import ModifiedTimeStampMixin


class JobDescription(ModifiedTimeStampMixin, TimeStampedModel):
    description = models.CharField(max_length=255)
    category = models.CharField(max_length=255)
    zip_code = models.CharField(max_length=5)

    class Meta:
        verbose_name_plural = 'Job Descriptions'
        ordering = ('description',)
        constraints = [
            models.UniqueConstraint(
                fields=['description'], name='job_description_unique'
            )
        ]

    def __str__(self):
        return self.description
