from django.db import models
from model_utils.models import TimeStampedModel

from powerdispatcher.models import ModifiedTimeStampMixin


class Call(ModifiedTimeStampMixin, TimeStampedModel):
    phone_number = models.CharField(max_length=255, null=True, blank=True)
    first_time_caller = models.BooleanField(null=True, blank=True)
    city = models.CharField(max_length=255, null=True, blank=True)
    state = models.CharField(max_length=255, null=True, blank=True)
    country = models.CharField(max_length=255, null=True, blank=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    source = models.CharField(max_length=500, null=True, blank=True)
    keywords = models.CharField(max_length=500, null=True, blank=True)
    medium = models.CharField(max_length=500, null=True, blank=True)
    campaign = models.CharField(max_length=500, null=True, blank=True)
    ad_group = models.CharField(max_length=500, null=True, blank=True)
    call_status = models.CharField(max_length=500, null=True, blank=True)
    tracking_number = models.CharField(max_length=500, null=True, blank=True)
    duration_seconds = models.IntegerField(null=True, blank=True)
    start_time = models.DateTimeField(null=True, blank=True)
    company_name = models.CharField(max_length=500, null=True, blank=True)
    number_name = models.CharField(max_length=500, null=True, blank=True)
    google_ads_gclid = models.CharField(max_length=500, null=True, blank=True)
    utm_medium = models.CharField(max_length=500, null=True, blank=True)
    utm_source = models.CharField(max_length=500, null=True, blank=True)
    customer_talk_time_percent = models.IntegerField(null=True, blank=True)
    agent_talk_time_percent = models.IntegerField(null=True, blank=True)
    recording_url = models.CharField(max_length=1000, null=True, blank=True)
    call_json = models.JSONField(null=True, blank=True)
