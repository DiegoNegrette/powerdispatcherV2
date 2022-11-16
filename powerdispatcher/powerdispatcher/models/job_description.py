from django.db import models
from model_utils.models import TimeStampedModel

from powerdispatcher.models import ModifiedTimeStampMixin


class JobDescription(ModifiedTimeStampMixin, TimeStampedModel):
    id = models.AutoField(primary_key=True)
    description = models.CharField(max_length=255)
    category = models.CharField(max_length=255, null=True, blank=True)
    enabled = models.BooleanField(default=True)

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
