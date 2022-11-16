from django.db import models
from model_utils.models import TimeStampedModel

from powerdispatcher.models import ModifiedTimeStampMixin


class Branch(ModifiedTimeStampMixin, TimeStampedModel):

    id = models.AutoField(primary_key=True)

    name = models.CharField(max_length=255)
    city = models.CharField(max_length=255, null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    zip_code = models.CharField(max_length=5, null=True, blank=True)

    class Meta:
        verbose_name_plural = 'Branches'
        ordering = ('name',)
        constraints = [
            models.UniqueConstraint(
                fields=['name'], name='branch_name_unique'  # noqa
            )
        ]

    def __str__(self):
        return f"{self.name}"
