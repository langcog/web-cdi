import csv

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.db.models import Count
from django.http import HttpResponse
from rangefilter.filters import DateRangeFilterBuilder
from researcher_UI.models import *

# Register your models here.
admin.site.register(instrument)
admin.site.register(researcher)
admin.site.register(Demographic)


class SummaryDataAdmin(admin.ModelAdmin):
    list_filter = ["administration__study__instrument", "title"]
    readonly_fields = ["administration", "title", "value"]


admin.site.register(SummaryData, SummaryDataAdmin)


class AdministrationDataAdmin(admin.ModelAdmin):
    list_filter = ["administration__study", "item_ID"]


admin.site.register(administration_data, AdministrationDataAdmin)


class BenchmarkAdmin(admin.ModelAdmin):
    list_display = ["instrument", "instrument_score", "age", "percentile"]
    list_filter = ["instrument__language", "instrument__form", "age", "percentile"]


admin.site.register(Benchmark, BenchmarkAdmin)


class InstrumentScoreAdmin(admin.ModelAdmin):
    list_display = ["instrument", "title"]
    list_filter = ["instrument__language", "instrument__form"]


admin.site.register(InstrumentScore, InstrumentScoreAdmin)


class AdministrationSummaryAdmin(admin.ModelAdmin):
    change_list_template = "admin/administration_summary_change_list.html"
    list_filter = ["completed", "completedBackgroundInfo"]
    ordering = ["study__name"]
    search_fields = ["study__name"]

    def changelist_view(self, request, extra_context=None):
        response = super(AdministrationSummaryAdmin, self).changelist_view(
            request,
            extra_context=extra_context,
        )

        try:
            qs = response.context_data["cl"].queryset
        except (AttributeError, KeyError):
            return response

        response.context_data["summary"] = list(
            qs.values("study__name")
            .annotate(
                total=Count("id"),
            )
            .order_by("-total")
        )

        return response


admin.site.register(AdministrationSummary, AdministrationSummaryAdmin)


class AdministrationAdmin(admin.ModelAdmin):
    list_display = [
        "study",
        "subject_id",
        "completed",
        "completedBackgroundInfo",
        "url_hash",
    ]
    list_filter = ["completed", "completedBackgroundInfo"]
    search_fields = ["study__name", "url_hash"]


admin.site.register(administration, AdministrationAdmin)


# Define an inline admin descriptor for Researcher model
# which acts a bit like a singleton
class ResearcherInline(admin.StackedInline):
    model = researcher
    can_delete = False
    verbose_name_plural = "researchers"
    filter_horizontal = ["allowed_instruments"]


def email_list(modeladmin, request, queryset):
    response = HttpResponse(content_type="text/csv")
    response[
        "Content-Disposition"
    ] = f'attachment; filename="User Email CSV Export for {request.user.email}.csv"'

    response.write("\ufeff".encode("utf8"))
    writer = csv.writer(response, dialect="excel")

    writer.writerow(
        [
            "email",
        ]
    )
    for q in queryset:
        writer.writerow(
            [
                q.email,
            ]
        )
    return response


# Define a new User admin
class UserAdmin(BaseUserAdmin):
    actions = [email_list]
    list_filter = [("date_joined", DateRangeFilterBuilder())]
    inlines = (ResearcherInline,)


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
