from django.urls import path

from .views.callrail import postcall_webhook


app_name = "powerdispatcher"


urlpatterns = [
    path("postcall_webhook/", postcall_webhook),
]
