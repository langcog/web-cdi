from django.contrib import admin

from .models import InstrumentItem

# Register your models here.


class InstrumentItemAdmin(admin.ModelAdmin):
    search_fields = ["definition"]
    list_filter = ["instrument"]
    list_display = [
        "definition",
        "instrument",
        "discrimination",
        "difficulty",
        "guessing",
        "upper_asymptote",
    ]


admin.site.register(InstrumentItem, InstrumentItemAdmin)
