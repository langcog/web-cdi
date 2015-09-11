from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(instrument)
admin.site.register(study)
admin.site.register(administration)
admin.site.register(administration_data)
