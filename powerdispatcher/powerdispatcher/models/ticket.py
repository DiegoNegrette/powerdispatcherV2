from django.db import models
from django.utils import timezone
from model_utils.models import TimeStampedModel

from powerdispatcher.models import (
    Branch,
    Customer,
    Date,
    Dispatcher,
    JobDescription,
    Location,
    ModifiedTimeStampMixin,
    Status,
    Technician,
)


class Ticket(ModifiedTimeStampMixin, TimeStampedModel):

    id = models.AutoField(primary_key=True)
    powerdispatch_ticket_id = models.CharField(max_length=5)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT)
    status = models.ForeignKey(Status, on_delete=models.PROTECT)
    technician = models.ForeignKey(Technician, on_delete=models.PROTECT)
    job_description = models.ForeignKey(JobDescription, on_delete=models.PROTECT)
    created_by = models.ForeignKey(
        Dispatcher, on_delete=models.PROTECT, related_name="tickets_created"
    )
    closed_by = models.ForeignKey(
        Dispatcher,
        on_delete=models.PROTECT,
        related_name="tickets_closed",
        null=True,
        blank=True,
    )
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT)
    zip_code = models.ForeignKey(
        Location, on_delete=models.PROTECT, null=True, blank=True
    )
    address = models.TextField(null=True, blank=True)
    credit_payment = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    cash_payment = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    technician_parts = models.CharField(max_length=255)
    company_parts = models.CharField(max_length=255)

    job_date = models.ForeignKey(Date, on_delete=models.PROTECT)

    created_at = models.DateTimeField()
    sent_at = models.DateTimeField(null=True, blank=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    first_call_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    empty_callrail_logs = models.BooleanField(default=False)
    reported_gclid = models.CharField(max_length=255, null=True, blank=True)
    has_reported_gclid = models.BooleanField(default=False)
    reported_gclid_at = models.DateTimeField(null=True, blank=True)

    alternative_source = models.TextField()

    alternative_technician = models.ForeignKey(Technician, on_delete=models.PROTECT)
    follow_up_reviewed_times = models.IntegerField(default=0)
    follow_up_last_reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "Tickets"
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=["powerdispatch_ticket_id"], name="powerdispatch_ticket_unique"
            )
        ]

    def __str__(self):
        return f"{self.powerdispatch_ticket_id} - {self.status}"

    def mark_empty_callrail_logs(self):
        self.empty_callrail_logs = True
        self.save(update_fields=["empty_callrail_logs"])

    def mark_reported_gclid(self, gclid):
        self.reported_gclid = gclid
        self.has_reported_gclid = True
        self.reported_gclid_at = timezone.now()
        self.save(
            update_fields=["reported_gclid", "has_reported_gclid", "reported_gclid_at"]
        )

    def update_after_review(self, technician, status):
        if self.technician != technician:
            pass
        else:
            self.alternative_technician = None
        self.status = status
        self.follow_up_reviewed_times += 1
        self.follow_up_last_reviewed_at = timezone.now()
        self.save(
            update_fields=[
                "technician",
                "alternative_technician",
                "status",
                "follow_up_reviewed_times",
                "follow_up_last_reviewed_at",
            ]
        )
