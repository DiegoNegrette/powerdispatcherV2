from django.db import models
from model_utils.models import TimeStampedModel

from powerdispatcher.models import ModifiedTimeStampMixin


class Call(ModifiedTimeStampMixin, TimeStampedModel):
    """CallRail call model

    Args:
        answered (boolean): Whether the call was answered (true) or not answered (false).
        business_phone_number (string): The phone number of the person or business who answered the call from the dialed tracking number.
        customer_city (string): The customer’s city, based on the original assigned location of their phone number.
        customer_country (string): The customer’s country, based on the area code of their phone number.
        customer_name (string): The customer’s name, as reported by Caller ID.
        customer_phone_number (string): The customer’s phone number (in E.164 format).
        customer_state (string): The 2-character abbreviation for the customer’s state, based on the original assigned location of their phone number.
        direction (string): Whether the call was inbound (from a customer to you) or outbound (from you to a customer).
        duration (integer): The duration of the call in seconds.
        id (string): Unique identifier for the call.
        recording (string): A URL pointing to the recording of the call, if available. This URL redirects to the actual audio file of the recording in MP3 format.
        recording_duration (string): The length in seconds of the recording, if available.
        recording_player (string): The URL for a stand-alone recording player for this call, if available.
        start_time (string): The date and time the call started in the current timezone (ISO 8601 format) with an offset.
        tracking_phone_number (string): The business’ tracking phone number for this call (in E.164 format).
        voicemail (boolean): Whether the call ended with a voicemail (true) or not (false).

    """
    answered = models.BooleanField()
    business_phone_number = models.CharField(max_length=255)
    customer_city = models.CharField(max_length=255)
    customer_country = models.CharField(max_length=255)
    customer_name = models.CharField(max_length=255)
    customer_phone_number = models.CharField(max_length=255)
    customer_state = models.CharField(max_length=255)
    direction = models.CharField(max_length=255)
    duration = models.IntegerField()
    call_id = models.CharField(max_length=255)
    recording = models.CharField(max_length=255)
    recording_duration = models.CharField(max_length=255)
    recording_player = models.CharField(max_length=255)
    start_time = models.CharField(max_length=255)
    tracking_phone_number = models.CharField(max_length=255)
    voicemail = models.BooleanField()