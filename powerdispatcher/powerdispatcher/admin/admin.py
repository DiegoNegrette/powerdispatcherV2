from django.contrib import admin

# from import_export.admin import (
#   ImportExportActionModelAdmin, ImportExportModelAdmin
# )
from solo.admin import SingletonModelAdmin

from powerdispatcher.admin.utils import format_link, linkify
from powerdispatcher.conf import settings
from powerdispatcher.models import (
    Branch,
    Customer,
    Date,
    Dispatcher,
    Expense,
    JobDescription,
    Location,
    ProjectConfiguration,
    Source,
    ScraperLog,
    Status,
    Technician,
    Ticket,
    WorkSchedule,
)

admin.site.register(Branch)
admin.site.register(Customer)
admin.site.register(JobDescription)
admin.site.register(Location)
admin.site.register(ProjectConfiguration, SingletonModelAdmin)
admin.site.register(Source)
admin.site.register(Technician)


@admin.register(Date)
class DateAdmin(admin.ModelAdmin):
    search_fields = ["date"]


@admin.register(Dispatcher)
class Dispatcher(admin.ModelAdmin):
    search_fields = ["name", "user"]
    list_display = ("id", "name", "user", "start_date", "end_date", "enabled")


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    autocomplete_fields = ["date"]
    list_select_related = (
        "date",
        "branch",
        "source",
    )
    list_display = (
        "id",
        "date",
        linkify("branch"),
        linkify("source"),
        "amount",
    )


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "get_powerdispatch_ticket",
        "job_date",
        linkify("technician"),
        linkify("created_by"),
        linkify("closed_by"),
        linkify("status")
    )
    list_filter = ("branch", "status__name")
    list_select_related = (
        "branch",
        "created_by",
        "closed_by",
        "job_date",
        "job_description",
        "technician",
        "alternative_technician",
        "status",
    )
    readonly_fields = ("powerdispatch_ticket_id",)
    search_fields = (
        "created_by__name",
        "created_by__user",
        "closed_by__name",
        "closed_by__user",
        "job_description__category",
        "job_description__description",
        "powerdispatch_ticket_id",
        "technician__name",
    )

    def get_powerdispatch_ticket(self, obj):
        if obj.powerdispatch_ticket_id:
            ticket_permalink = settings.POWERDISPATCHER_TICKET_URL.format(
                ticket_id=obj.powerdispatch_ticket_id
            )
            return format_link(ticket_permalink, obj.powerdispatch_ticket_id)

    get_powerdispatch_ticket.short_description = "Powerdispatch Id"


@admin.register(ScraperLog)
class ScraperLog(admin.ModelAdmin):
    list_display = (
        "id",
        "from_date",
        "to_date",
        "start_time",
        "end_time",
        "scraped_tickets",
        "added_tickets",
        "status",
        "reason",
        "last_message",
    )


@admin.register(Status)
class StatusAdmin(admin.ModelAdmin):
    search_fields = ["name", "who_canceled", "why_canceled"]
    list_display = ("id", "name", "who_canceled", "why_canceled")


@admin.register(WorkSchedule)
class WorkScheduleAdmin(admin.ModelAdmin):
    autocomplete_fields = ["date"]
