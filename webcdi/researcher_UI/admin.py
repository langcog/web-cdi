from django.contrib import admin
from .models import *
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User


# Register your models here.
admin.site.register(instrument)
admin.site.register(study)
admin.site.register(administration)
admin.site.register(administration_data)
admin.site.register(researcher)

# Define an inline admin descriptor for Researcher model
# which acts a bit like a singleton
class ResearcherInline(admin.StackedInline):
    model = researcher
    can_delete = False
    verbose_name_plural = 'researchers'

# Define a new User admin
class UserAdmin(BaseUserAdmin):
    inlines = (ResearcherInline, )

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)