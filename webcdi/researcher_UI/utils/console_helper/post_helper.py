import os
from researcher_UI.models import administration
from researcher_UI.utils.random_url_generator import random_url_generator
from django.conf import settings
import datetime
from researcher_UI.utils.download import (
    download_cat_data,
    download_cat_summary,
    download_cdi_format,
    download_data,
    download_dictionary,
    download_links,
    download_summary,
)

def post_condition(request, ids, study_obj):
    if "administer-selected" in request.POST:
        num_ids = map(int, ids)  # Force numeric IDs into a list of integers
        new_administrations = []
        sids_created = set()

        for nid in num_ids:  # For each ID number
            admin_instance = administration.objects.get(id=nid)
            sid = admin_instance.subject_id
            if sid in sids_created:
                continue
            old_rep = administration.objects.filter(
                study=study_obj, subject_id=sid
            ).count()
            new_administrations.append(
                administration(
                    study=study_obj,
                    subject_id=sid,
                    repeat_num=old_rep + 1,
                    url_hash=random_url_generator(),
                    completed=False,
                    due_date=datetime.datetime.now() + datetime.timedelta(days=14),
                )
            )
            sids_created.add(sid)

        administration.objects.bulk_create(new_administrations)

    elif "delete-selected" in request.POST: 
        num_ids = list(set(map(int, ids)))
        administration.objects.filter(id__in=num_ids).delete()

    elif "download-links" in request.POST:
        administrations = []
        num_ids = list(set(map(int, ids)))  # Force IDs into a list of integers
        administrations = administration.objects.filter(id__in=ids)
        return download_links.download_links(request, study_obj, administrations)

    elif "download-selected" in request.POST:  # If 'Download Selected Data' was clicked
        num_ids = list(set(map(int, ids)))  # Force IDs into a list of integers
        administrations = administration.objects.filter(id__in=num_ids)
        if study_obj.instrument.form in settings.CAT_FORMS:
            return download_cat_data.download_cat_data(
                request, study_obj, administrations
            )
        else:
            return download_data.download_data(request, study_obj, administrations)

    elif "download-selected-summary" in request.POST:
        num_ids = list(set(map(int, ids)))  # Force IDs into a list of integers
        administrations = administration.objects.filter(id__in=num_ids)
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
        administrations = administration.objects.filter(study=study_obj)
        if study_obj.instrument.form in settings.CAT_FORMS:
            return download_cat_data.download_cat_data(
                request, study_obj, administrations
            )
        else:
            return download_data.download_data(request, study_obj, administrations)

    elif "download-summary-csv" in request.POST:
        administrations = administration.objects.filter(study=study_obj)
        if study_obj.instrument.form in settings.CAT_FORMS:
            return download_cat_summary.download_cat_summary(
                request, study_obj, administrations
            )
        else:
            return download_summary.download_summary(
                request, study_obj, administrations
            )

    elif "download-study-scoring" in request.POST:
        administrations = administration.objects.filter(study=study_obj)
        return download_cdi_format.download_cdi_format(
            request, study_obj, administrations
        )

    elif "download-study-scoring-selected" in request.POST:
        num_ids = list(set(map(int, ids)))
        administrations = administration.objects.filter(id__in=num_ids)
        return download_cdi_format.download_cdi_format(
            request, study_obj, administrations
        )

    elif "download-dictionary" in request.POST:
        return download_dictionary.download_dictionary(request, study_obj)
    elif "view_all" in request.POST:  # If 'Show All' or 'Show 20' button is clicked
        if request.POST["view_all"] == "Show All":
            num_per_page = administration.objects.filter(study=study_obj).count()
        elif request.POST["view_all"] == "Show 20":
            num_per_page = 20  # Set num_per_page to 20

def get_helper(request, study_name):
        username = None  # Set username to None at first
        if request.user.is_authenticated:  # If logged in (should be)
            username = request.user.username  # Set username to current user's username

        researcher_obj, created = researcher.objects.get_or_create(user=request.user)

        context = (
            dict()
        )  # Create a dictionary of data related to template rendering such as username, studies associated with username, information on currently viewed study, and number of administrations to show.
        context["username"] = username
        context["studies"] = study.objects.filter(
            researcher=request.user, active=True
        ).order_by("id")
        context["instruments"] = []
        context["study_form"] = AddStudyForm()

        if study_name is not None:
            # try:
            current_study = study.objects.get(researcher=request.user, name=study_name)
            administration_table = StudyAdministrationTable(
                administration.objects.filter(study=current_study)
            )
            if not current_study.confirm_completion:
                administration_table.exclude = ("study", "id", "url_hash", "analysis")

            # remove completedSurvey if no back page for background info
            filename = os.path.realpath(
                settings.BASE_DIR
                + "/cdi_forms/form_data/background_info/"
                + current_study.instrument.name
                + "_back.json"
            )
            if not os.path.isfile(filename):
                excludes = list(administration_table.exclude)
                excludes.append("completedSurvey")
                administration_table.exclude = excludes
            if "view_all" in request.GET:
                study_obj = study.objects.get(researcher=request.user, name=study_name)
                if request.GET["view_all"] == "all":
                    num_per_page = administration.objects.filter(
                        study=study_obj
                    ).count()
            RequestConfig(request, paginate={"per_page": num_per_page}).configure(
                administration_table
            )
            context["current_study"] = current_study.name
            context["study"] = current_study
            context["num_per_page"] = num_per_page
            context["study_instrument"] = current_study.instrument.verbose_name
            context["study_group"] = current_study.study_group
            context["study_administrations"] = administration_table
            context["completed_admins"] = administration.objects.filter(
                study=current_study, completed=True
            ).count()
            context["unique_children"] = count = (
                administration.objects.filter(study=current_study, completed=True)
                .values("subject_id")
                .distinct()
                .count()
            )
            context["allow_payment"] = current_study.allow_payment
            context["available_giftcards"] = payment_code.objects.filter(
                hash_id__isnull=True, study=current_study
            ).count()
            # except:
            pass
       
       