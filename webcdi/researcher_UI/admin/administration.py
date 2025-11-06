from django.contrib import admin, messages

from brookes.filters import DropdownFilter
from researcher_UI.models import Administration


def set_is_active_true(modeladmin, request, queryset):
    messages.success(request, f"{len(queryset)} administrations set to active")

    queryset.update(is_active=True)


class AdministrationAdmin(admin.ModelAdmin):
    list_display = [
        "study",
        "subject_id",
        "completed",
        "completedBackgroundInfo",
        "is_active",
        "url_hash",
    ]
    list_filter = [
        "completed",
        "completedBackgroundInfo",
        "is_active",
        ("study__name", DropdownFilter),
        ("study__researcher__username", DropdownFilter),
    ]
    search_fields = ["study__name", "url_hash","id","subject_id"]
    actions = [
        set_is_active_true,
    ]


admin.site.register(Administration, AdministrationAdmin)
