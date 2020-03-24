from django.contrib import admin

from .models import Instrument_Forms, Choices
# Register your models here.

class InstrumentFormsAdmin(admin.ModelAdmin):
    search_fields = ['gloss','definition']
    list_filter = ['instrument']
admin.site.register(Instrument_Forms, InstrumentFormsAdmin)

#admin.site.register(Choices)