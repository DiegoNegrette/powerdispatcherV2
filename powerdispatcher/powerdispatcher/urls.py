from django.urls import path

from .views.callrail import call_modified_webhook, postcall_webhook


app_name = "powerdispatcher"


urlpatterns = [
    path("call_modified_webhook/", call_modified_webhook),
    path("postcall_webhook/", postcall_webhook),
]
