from django.contrib import admin, messages

# Register your models here.

from rangefilter.filters import DateRangeFilter
from brookes.models import BrookesCode

def create_50_codes(modeladmin, request, queryset):
    for count in range(50):
        x = BrookesCode()
        x.save()
    messages.success(request, f"50 Codes created")

@admin.register(BrookesCode)
class BrookesCodeAdmin(admin.ModelAdmin):
    list_display = ['code', 'researcher', 'instrument', 'applied']
    list_filter = [
        ("applied", DateRangeFilter),
        "researcher",
        "instrument"
    ]
    actions = [
        create_50_codes,
    ]
