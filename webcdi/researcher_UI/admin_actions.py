from django.contrib import admin
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _

from .models import administration
from .views import download_data, download_summary

def scoring_data(modeladmin, request, queryset):
    study_obj = queryset[0]
    
    for q in queryset:
        if q.instrument != study_obj.instrument:
            messages.error(request, _('Instruments for all Studies must be the same'))
            return
        if len(q.administration_set.all()) < 1:
            messages.error(request, _('Studies must have at least 1 responsent. %s has none' % (q.name)))
            return

    administrations = administration.objects.filter(study__in=queryset)
    return download_data(request, study_obj, administrations)

def scoring_summary(modeladmin, request, queryset):
    study_obj = queryset[0]
    
    for q in queryset:
        if q.instrument != study_obj.instrument:
            messages.error(request, _('Instruments for all Studies must be the same'))
            return
        if len(q.administration_set.all()) < 1:
            messages.error(request, _('Studies must have at least 1 responsent. %s has none' % (q.name)))
            return

    administrations = administration.objects.filter(study__in=queryset)
    return download_summary(request, study_obj, administrations)
