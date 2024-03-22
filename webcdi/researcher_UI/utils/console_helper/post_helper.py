import datetime

from django.conf import settings
from django.contrib import messages
from django.utils.safestring import mark_safe
from researcher_UI.models import Administration
from researcher_UI.utils.download import (
    download_cat_data,
    download_cdi_format,
    download_data,
    download_dictionary,
    download_links,
    download_summary,
)
from researcher_UI.utils.random_url_generator import random_url_generator


def post_condition(request, ids, study_obj):
    if "administer-selected" in request.POST:
        if not study_obj.valid_code(request.user):
            messages.warning(
                request,
                mark_safe(
                    "Access to this form requires an active license, available for purchase through Brookes Publishing Co (<a href='https://brookespublishing.com/product/cdi' target='_blank'>https://brookespublishing.com/product/cdi</a>)"
                ),
            )
            return None
        else:
            num_ids = map(int, ids)  # Force numeric IDs into a list of integers
            new_administrations = []
            sids_created = set()

            for nid in num_ids:  # For each ID number
                admin_instance = Administration.objects.get(id=nid)
                sid = admin_instance.subject_id
                if sid in sids_created:
                    continue
                old_rep = Administration.objects.filter(
                    study=study_obj, subject_id=sid
                ).count()
                new_administrations.append(
                    Administration(
                        study=study_obj,
                        subject_id=sid,
                        repeat_num=old_rep + 1,
                        url_hash=random_url_generator(),
                        completed=False,
                        due_date=datetime.datetime.now() + datetime.timedelta(days=14),
                    )
                )
                sids_created.add(sid)

            Administration.objects.bulk_create(new_administrations)

    elif "delete-selected" in request.POST:
        num_ids = list(set(map(int, ids)))
        Administration.objects.filter(id__in=num_ids).update(is_active=False)

    elif "download-links" in request.POST:
        administrations = []
        num_ids = list(set(map(int, ids)))  # Force IDs into a list of integers
        administrations = Administration.objects.filter(id__in=ids)
        return download_links.download_links(request, study_obj, administrations)

    elif "download-selected" in request.POST:  # If 'Download Selected Data' was clicked
        num_ids = list(set(map(int, ids)))  # Force IDs into a list of integers
        administrations = Administration.objects.filter(id__in=num_ids)
        if study_obj.instrument.form in settings.CAT_FORMS:
            return download_cat_data.download_cat_data(
                request, study_obj, administrations
            )
        else:
            return download_data.download_data(request, study_obj, administrations)

    elif (
        "download-selected-adjusted" in request.POST
    ):  # If 'Download Selected Data' was clicked
        num_ids = list(set(map(int, ids)))  # Force IDs into a list of integers
        administrations = Administration.objects.filter(id__in=num_ids)
        if study_obj.instrument.form in settings.CAT_FORMS:
            return download_cat_data.download_cat_data(
                request, study_obj, administrations, adjusted=True
            )
        else:
            return download_data.download_data(
                request, study_obj, administrations, adjusted=True
            )

    elif "download-selected-summary" in request.POST:
        num_ids = list(set(map(int, ids)))  # Force IDs into a list of integers
        administrations = Administration.objects.filter(id__in=num_ids)
        if study_obj.instrument.form in settings.CAT_FORMS:
            return download_cat_data.download_cat_data(
                request, study_obj, administrations
            )
        else:
            return download_summary.download_summary(
                request, study_obj, administrations
            )

    elif "delete-study" in request.POST:  # If 'Delete Study' button is clicked
        study_obj.active = False  # soft delete
        study_obj.save()

    elif "download-study-csv" in request.POST:  # If 'Download Data' button is clicked
        administrations = Administration.objects.filter(study=study_obj)
        if study_obj.instrument.form in settings.CAT_FORMS:
            return download_cat_data.download_cat_data(
                request, study_obj, administrations
            )
        else:
            return download_data.download_data(request, study_obj, administrations)

    elif (
        "download-study-csv-adjusted" in request.POST
    ):  # If 'Download Data' button is clicked
        administrations = Administration.objects.filter(study=study_obj)
        if study_obj.instrument.form in settings.CAT_FORMS:
            return download_cat_data.download_cat_data(
                request, study_obj, administrations, adjusted=True
            )
        else:
            return download_data.download_data(
                request, study_obj, administrations, adjusted=True
            )

    elif "download-summary-csv" in request.POST:
        administrations = Administration.objects.filter(study=study_obj)
        if study_obj.instrument.form in settings.CAT_FORMS:
            return download_cat_data.download_cat_data(
                request, study_obj, administrations, summary=True, 
            )
        else:
            return download_summary.download_summary(
                request, study_obj, administrations
            )

    elif "download-study-scoring" in request.POST:
        administrations = Administration.objects.filter(study=study_obj)
        return download_cdi_format.download_cdi_format(
            request, study_obj, administrations
        )

    elif "download-study-scoring-selected" in request.POST:
        num_ids = list(set(map(int, ids)))
        administrations = Administration.objects.filter(id__in=num_ids)
        return download_cdi_format.download_cdi_format(
            request, study_obj, administrations
        )

    elif "download-dictionary" in request.POST:
        return download_dictionary.download_dictionary(request, study_obj)
