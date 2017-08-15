from django.contrib import admin

from .models import English_WS, English_WG, Spanish_WS
# Register your models here.

admin.site.register(English_WS)
admin.site.register(English_WG)
admin.site.register(Spanish_WS)

