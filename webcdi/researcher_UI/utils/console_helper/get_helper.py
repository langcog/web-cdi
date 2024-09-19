import logging
import os

from django.conf import settings
from django.db.models import Q
from django_tables2 import RequestConfig

from researcher_UI.forms import AddStudyForm
from researcher_UI.models import Administration, PaymentCode, Study
from researcher_UI.tables import StudyAdministrationTable

logger = logging.getLogger("debug")


def get_helper(request, study_name, num_per_page):
    username = None  # Set username to None at first
    if request.user.is_authenticated:
        username = request.user.username

    context = {}
    context["username"] = username
    context["studies"] = Study.objects.filter(
        researcher=request.user, active=True
    ).order_by("id")
    context["instruments"] = []
    context["study_form"] = AddStudyForm()

    if study_name is not None:
        current_study = Study.objects.get(researcher=request.user, name=study_name)
        query = Q(study=current_study, is_active=True)
        if "search" in request.GET:
            try:
                if len(request.GET["search"]) < 1:
                    query = query
                else:
                    query = Q(query) & Q(
                        Q(subject_id=int(request.GET["search"]))
                        | Q(local_lab_id=request.GET["search"])
                    )
            except ValueError:
                query = Q(query) & Q(local_lab_id=request.GET["search"])
        administration_table = StudyAdministrationTable(
            Administration.objects.filter(query)
        )
        if not current_study.confirm_completion:
            administration_table.exclude = ("study", "id", "url_hash", "analysis")

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
            study_obj = Study.objects.get(researcher=request.user, name=study_name)
            if request.GET["view_all"] == "all":
                num_per_page = Administration.objects.filter(study=study_obj).count()
        RequestConfig(request, paginate={"per_page": num_per_page}).configure(
            administration_table
        )
        context["current_study"] = current_study
        context["study"] = current_study
        context["num_per_page"] = num_per_page
        context["study_instrument"] = current_study.instrument.verbose_name
        context["study_group"] = current_study.study_group
        context["study_administrations"] = administration_table
        context["completed_admins"] = Administration.objects.filter(
            study=current_study, completed=True
        ).count()
        context["unique_children"] = (
            Administration.objects.filter(study=current_study, completed=True)
            .values("subject_id")
            .distinct()
            .count()
        )
        context["allow_payment"] = current_study.allow_payment
        context["available_giftcards"] = PaymentCode.objects.filter(
            hash_id__isnull=True, study=current_study
        ).count()

    return context
