from django.contrib import admin

from .models import Instrument_Forms
# Register your models here.

class InstrumentFormsAdmin(admin.ModelAdmin):
    search_fields = ['gloss','definition']
admin.site.register(Instrument_Forms, InstrumentFormsAdmin)

