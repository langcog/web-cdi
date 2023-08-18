from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from researcher_UI.utils.download import download_data, download_summary

from researcher_UI.models import administration


def scoring_data(modeladmin, request, queryset):
    study_obj = queryset[0]

    for q in queryset:
        if q.instrument != study_obj.instrument:
            messages.error(request, _("Instruments for all Studies must be the same"))
            return
        if len(q.administration_set.all()) < 1:
            messages.error(
                request,
                _("Studies must have at least 1 responsent. %s has none" % (q.name)),
            )
            return
        if q.instrument.family.chargeable and q.share_opt_out:
            messages.error(
                request,
                _(
                    f"You cannot download data for {q.name}.  The study has opted out of datasharing"
                ),
            )
            return

    administrations = administration.objects.filter(study__in=queryset).exclude(
        opt_out=True
    )
    return download_data.download_data(request, study_obj, administrations)


def scoring_summary(modeladmin, request, queryset):
    study_obj = queryset[0]

    for q in queryset:
        if q.instrument != study_obj.instrument:
            messages.error(request, _("Instruments for all Studies must be the same"))
            return
        if len(q.administration_set.all()) < 1:
            messages.error(
                request,
                _("Studies must have at least 1 responsent. %s has none" % (q.name)),
            )
            return
        if q.instrument.family.chargeable and q.share_opt_out:
            messages.error(
                request,
                _(
                    f"You cannot download data for {q.name}.  The study has opted out of datasharing"
                ),
            )
            return

    administrations = administration.objects.filter(study__in=queryset).exclude(
        opt_out=True
    )
    return download_summary.download_summary(request, study_obj, administrations)
