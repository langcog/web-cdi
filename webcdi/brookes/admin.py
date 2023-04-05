from brookes.models import BrookesCode
from django.contrib import admin, messages
from rangefilter.filters import DateRangeFilter

# Register your models here.


def create_50_codes(modeladmin, request, queryset):
    for count in range(50):
        x = BrookesCode()
        x.save()
    messages.success(request, f"50 Codes created")


@admin.register(BrookesCode)
class BrookesCodeAdmin(admin.ModelAdmin):
    list_display = ["code", "researcher", "instrument_family", "applied"]
    list_filter = [("applied", DateRangeFilter), "researcher", "instrument_family"]
    actions = [
        create_50_codes,
    ]
