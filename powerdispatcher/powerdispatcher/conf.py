from appconf import AppConf
from django.conf import settings  # noqa


class PowerdispatcherConf(AppConf):
    POWER_DISPATCH_BASE_URL = "https://lite.serviceslogin.com/appointments.php?init=1"
    TICKET_URL = "https://lite.serviceslogin.com/addjob.php?board=1&jid={ticket_id}"
