from django.contrib import admin

from .models import BackgroundInfo, Choices, Instrument_Forms

from .cat_forms.models import CatResponse
# Register your models here.


class InstrumentFormsAdmin(admin.ModelAdmin):
    search_fields = ["gloss", "definition", "itemID"]
    list_filter = ["instrument"]


admin.site.register(Instrument_Forms, InstrumentFormsAdmin)

admin.site.register(Choices)


class BackgroundInfoAdmin(admin.ModelAdmin):
    readonly_fields = ["administration"]


admin.site.register(BackgroundInfo, BackgroundInfoAdmin)


# Register your models here.

admin.site.register(CatResponse)