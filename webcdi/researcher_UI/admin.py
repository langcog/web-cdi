from django.contrib import admin
from .models import *
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.db.models import Count 

# Register your models here.
admin.site.register(instrument)
admin.site.register(administration_data)
admin.site.register(researcher)
admin.site.register(Benchmark)

class InstrumentScoreAdmin(admin.ModelAdmin):
    list_display = ['instrument','title']
    list_filter = ['instrument__language','instrument__form']
admin.site.register(InstrumentScore,InstrumentScoreAdmin)

class AdministrationSummaryAdmin(admin.ModelAdmin):
    change_list_template = 'admin/administration_summary_change_list.html'
    list_filter = ['completed','completedBackgroundInfo']
    ordering = ['study__name']
    search_fields = ['study__name']

    def changelist_view(self, request, extra_context=None):
        response = super(AdministrationSummaryAdmin, self).changelist_view(
            request,
            extra_context=extra_context,
        )

        try:
            qs = response.context_data['cl'].queryset
        except (AttributeError, KeyError):
            return response
        
        metrics = {
            'total': Count('id'),
        }

        response.context_data['summary'] = list(
            qs
            .values('study__name')
            .annotate(
                total = Count('id'),
            )
            .order_by('-total')
        )
        
        return response
admin.site.register(AdministrationSummary, AdministrationSummaryAdmin)

class AdministrationAdmin(admin.ModelAdmin):
    list_display = ['study','subject_id','completed','completedBackgroundInfo']
    list_filter = ['completed','completedBackgroundInfo']
    search_fields = ['study__name']
admin.site.register(administration, AdministrationAdmin)

class StudyAdmin(admin.ModelAdmin):
    list_display=['name','instrument','researcher']
    list_filter = ['instrument','researcher']
    search_fields = ['instrument','researcher','name']
admin.site.register(study, StudyAdmin)

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