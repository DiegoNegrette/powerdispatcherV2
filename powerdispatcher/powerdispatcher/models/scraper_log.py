from django.db import models
from django.utils import timezone
from model_utils.models import TimeStampedModel

from powerdispatcher.models import ModifiedTimeStampMixin


class ScraperLog(ModifiedTimeStampMixin, TimeStampedModel):

    STATUS_PENDING = 'Pending'
    STATUS_FAILED = 'Failed'
    STATUS_SUCCESS = 'Success'
    STATUS_EXPIRED = 'Expired'

    CH_STATUS = (
        (STATUS_PENDING, STATUS_PENDING),
        (STATUS_FAILED, STATUS_FAILED),
        (STATUS_SUCCESS, STATUS_SUCCESS),
    )

    from_date = models.DateField()
    to_date = models.DateField()

    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    scraped_tickets = models.IntegerField(default=0)
    added_tickets = models.IntegerField(default=0)
    status = models \
        .CharField(max_length=255, choices=CH_STATUS, default=STATUS_PENDING)
    reason = models.CharField(max_length=255, null=True, blank=True)
    last_message = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        verbose_name_plural = 'Scraper Logs'
        ordering = ('-id',)

    def __str__(self):
        return f"{self.from_date}/{self.to_date} - {self.status}"

    def end_as(self, status, reason=None):
        self.status = status
        if reason is not None:
            reason = reason[:255]
        self.reason = reason
        self.end_time = timezone.now()
        self.save(update_fields=['status', 'reason', 'end_time'])

    def set_last_message(self, message):
        self.last_message = message
        self.save(update_fields=['last_message'])
