from django.contrib import admin

from powerdispatcher.models import (
    Customer,
    Dispatcher,
    Status,
    StatusCategory,
    Technician,
    Ticket,
)

admin.site.register(Customer)
admin.site.register(Dispatcher)
admin.site.register(Status)
admin.site.register(StatusCategory)
admin.site.register(Technician)
admin.site.register(Ticket)
