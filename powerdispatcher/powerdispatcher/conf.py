from django.conf import settings  # noqa
from appconf import AppConf


class PowerdispatcherConf(AppConf):
    POWER_DISPATCH_BASE_URL = "https://lite.serviceslogin.com/appointments.php?init=1"  # noqa
    TICKET_URL = "https://lite.serviceslogin.com/addjob.php?board=1&jid={ticket_id}"  # noqa
