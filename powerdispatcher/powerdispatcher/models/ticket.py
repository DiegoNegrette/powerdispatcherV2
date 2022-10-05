from django.db import models
from model_utils.models import TimeStampedModel

from powerdispatcher.models import (
    Customer, ModifiedTimeStampMixin, Status, Technician
)


class Ticket(ModifiedTimeStampMixin, TimeStampedModel):

    powerdispatcher_ticket_id = models.CharField(max_length=255)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT)
    status = models.ForeignKey(Status, on_delete=models.PROTECT)
    technician = models.ForeignKey(Technician, on_delete=models.PROTECT)

    created_at = models.DateTimeField()
    sent_at = models.DateTimeField()
    accepted_at = models.DateTimeField()
    closed_at = models.DateTimeField()

    class Meta:
        verbose_name_plural = 'Tickets'
        ordering = ('-created_at',)
        constraints = [
            models.UniqueConstraint(
                fields=['powerdispatcher_ticket_id'], name='powerdispatcher_ticket_unique'  # noqa
            )
        ]

    def __str__(self):
        return f'{self.powerdispatcher_ticket_id} - {self.status}'
