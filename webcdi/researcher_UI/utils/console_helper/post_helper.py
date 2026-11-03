import datetime

from django.conf import settings
from django.contrib import messages
from django.utils.safestring import mark_safe

from researcher_UI.models import Administration
from researcher_UI.utils.download import (download_cat_data, download_data,
                                          download_dictionary, download_links,
                                          download_summary)
from researcher_UI.utils.random_url_generator import random_url_generator


SELECTED_DOWNLOADS = (
    "download-selected",
    "download-selected-adjusted",
    "download-selected-summary",
    "download-links",
)


def post_condition(request, ids, study_obj):
    # selected-row actions apply to this group's rows; other ids count as unselected
    selected = Administration.objects.filter(study=study_obj, id__in=ids)
    if not selected.exists() and any(
        action in request.POST for action in SELECTED_DOWNLOADS
    ):
        # returning None sends the researcher back to the group page (#675)
        messages.info(request, "Select at least one administration to download.")
        return None

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
            new_administrations = []
            sids_created = set()

            for admin_instance in selected:
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
        selected.update(is_active=False)

    elif "download-links" in request.POST:
        return download_links.download_links(request, study_obj, selected)

    elif "download-selected" in request.POST:  # If 'Download Selected Data' was clicked
        administrations = selected
        if study_obj.instrument.form in settings.CAT_FORMS:
            return download_cat_data.download_cat_data(
                request, study_obj, administrations
            )
        else:
            return download_data.download_data(request, study_obj, administrations)

    elif (
        "download-selected-adjusted" in request.POST
    ):  # If 'Download Selected Data' was clicked
        administrations = selected
        if study_obj.instrument.form in settings.CAT_FORMS:
            return download_cat_data.download_cat_data(
                request, study_obj, administrations, adjusted=True
            )
        else:
            return download_data.download_data(
                request, study_obj, administrations, adjusted=True
            )

    elif "download-selected-summary" in request.POST:
        administrations = selected
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
                request,
                study_obj,
                administrations,
                summary=True,
            )
        else:
            return download_summary.download_summary(
                request, study_obj, administrations
            )

    elif "download-dictionary" in request.POST:
        return download_dictionary.download_dictionary(request, study_obj)
