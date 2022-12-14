from django.db import models
from model_utils.models import TimeStampedModel

from powerdispatcher.models import ModifiedTimeStampMixin


class Customer(ModifiedTimeStampMixin, TimeStampedModel):
    id = models.AutoField(primary_key=True)
    phone = models.CharField(max_length=10)

    class Meta:
        verbose_name_plural = 'Customers'
        ordering = ('id',)
        constraints = [
            models.UniqueConstraint(
                fields=['phone'], name='customer_phone_unique'
            )
        ]

    def __str__(self):
        return f"{self.phone}"
