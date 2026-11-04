from django.contrib import admin

from brookes.filters import DropdownFilter
from researcher_UI.models import Study

from .admin_actions import scoring_data, scoring_summary


class StudyAdmin(admin.ModelAdmin):
    def has_delete_permission(self, request, obj=None):
        # groups are only ever made inactive; this also stops a delete of a
        # user or instrument that would take its groups with it
        return False

    list_display = [
        "name",
        "get_responses",
        "instrument",
        "researcher",
        "demographic",
        "share_opt_out",
        "get_chargeable",
    ]
    list_filter = [
        "share_opt_out",
        ("researcher__username", DropdownFilter),
        ("instrument__verbose_name", DropdownFilter),
        "active",
    ]
    search_fields = ["instrument__name", "researcher__username", "name"]
    actions = [scoring_data, scoring_summary]

    def get_responses(self, obj):
        return len(obj.administration_set.all())

    get_responses.short_description = "Responses"

    def get_chargeable(self, obj):
        try:
            result = obj.instrument.family.chargeable
        except Exception as e:  # noqa
            result = False
        return result

    get_chargeable.short_description = "Chargeable"


admin.site.register(Study, StudyAdmin)
