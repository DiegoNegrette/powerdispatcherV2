from datetime import datetime
import logging
import traceback

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from powerdispatcher.models import Call

logger = logging.getLogger("callrail")


@api_view(["POST"])
def postcall_webhook(request):
    try:
        logger.info(request.data)
        call_data = {
            "phone_number": request.data["formatted_customer_phone_number"],
            "first_time_caller": request.data["first_call"],
            "city": request.data["customer_city"],
            "state": request.data["customer_state"],
            "country": request.data["customer_country"],
            "name": request.data["formatted_customer_name"],
            "source": request.data["source"],
            "keywords": request.data["keywords"],
            "medium": request.data["medium"],
            "campaign": request.data["campaign"],
            "ad_group": "REVISAR CAMPO",
            "call_status": request.data["formatted_call_type"],
            "tracking_number": request.data["formatted_tracking_phone_number"],
            "duration_seconds": request.data["duration"],
            "start_time": datetime.strptime(
                request.data["start_time"], "%Y-%m-%dT%H:%M:%S.%f%z"
            ),
            "company_name": request.data["company_name"],
            "number_name": request.data["utm_campaign"],
            "google_ads_gclid": request.data["gclid"],
            "utm_medium": request.data["utm_medium"],
            "utm_source": request.data["utm_source"],
            "customer_talk_time_percent": (
                request.data["speaker_percent"]["customer"]
                if request.data["speaker_percent"]
                else None
            ),
            "agent_talk_time_percent": (
                request.data["speaker_percent"]["agent"]
                if request.data["speaker_percent"]
                else None
            ),
            "recording_url": request.data["recording"],
            "call_json": request.data,
        }
        Call.objects.create(**call_data)
        return Response(status=status.HTTP_200_OK)
    except Exception as e:
        stacktrace = traceback.format_exc()
        logger.warning(stacktrace)
        logger.warning(e)
        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
