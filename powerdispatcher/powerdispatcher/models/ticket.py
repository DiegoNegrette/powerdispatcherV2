from django.db import models
from model_utils.models import TimeStampedModel

from powerdispatcher.models import (
    Branch,
    Calendar,
    Customer,
    Dispatcher,
    JobDescription,
    Location,
    ModifiedTimeStampMixin,
    Status,
    Technician
)


class Ticket(ModifiedTimeStampMixin, TimeStampedModel):

    powerdispatcher_ticket_id = models.CharField(max_length=255)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT)
    status = models.ForeignKey(Status, on_delete=models.PROTECT)
    technician = models.ForeignKey(Technician, on_delete=models.PROTECT)
    job_description = models.ForeignKey(
        JobDescription, on_delete=models.PROTECT
    )
    created_by = models.ForeignKey(
        Dispatcher, on_delete=models.PROTECT, related_name='tickets_created'
    )
    closed_by = models.ForeignKey(
        Dispatcher, on_delete=models.PROTECT, related_name='tickets_closed'
    )
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT)
    zip_code = models.ForeignKey(Location, on_delete=models.PROTECT)
    address = models.CharField(max_length=255)
    credit_payment = models.DecimalField(
        max_digits=7, decimal_places=2, default=0
    )
    cash_payment = models.DecimalField(
        max_digits=7, decimal_places=2, default=0
    )
    technician_parts = models.CharField(max_length=255)
    company_parts = models.CharField(max_length=255)

    job_date = models.ForeignKey(Calendar, on_delete=models.PROTECT)

    created_at = models.DateTimeField()
    sent_at = models.DateTimeField(null=True, blank=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    first_call_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)

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
