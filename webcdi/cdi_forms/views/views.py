# -*- coding: utf-8 -*-

import json
import logging
import os.path

import requests
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone, translation
from django.utils.translation import gettext_lazy as _
from ipware.ip import get_client_ip

from cdi_forms.forms.forms import BackgroundForm
from cdi_forms.models import *
from cdi_forms.views.utils import (PROJECT_ROOT, get_administration_instance,
                                   has_backpage, language_map, model_map,
                                   prefilled_cdi_data)
from researcher_UI.models import *

# Get an instance of a logger
logger = logging.getLogger("debug")


# Gets list of itemIDs 'item_XX' from an instrument model
def get_model_header(name):
    return list(model_map(name).values_list("itemID", flat=True))


# Convert string boolean to true boolean
def parse_analysis(raw_answer):
    if raw_answer == "True":
        answer = True
    elif raw_answer == "False":
        answer = False
    else:
        answer = None
    return answer


# Render CDI form. Dependent on prefilled_cdi_data
# I think this can probably be deleted.  It is now only called from administer_cdi_form and I don't think the if statement is ever hit
def cdi_form(request, hash_id):
    administration_instance = get_administration_instance(
        hash_id
    )  # Get administration instance.
    if administration_instance.study.instrument.form in settings.CAT_FORMS:
        return redirect("cat_forms:administer_cat_form", hash_id=hash_id)

    instrument_name = (
        administration_instance.study.instrument.name
    )  # Get instrument name associated with study
    instrument_model = model_map(
        instrument_name
    )  # Fetch instrument model based on instrument name.
    refresh = False

    user_language = language_map(administration_instance.study.instrument.language)

    translation.activate(user_language)

    if request.method == "POST":  # If submitting responses to CDI form
        if (
            not administration_instance.completed
            and administration_instance.due_date > timezone.now()
        ):  # If form has not been completed and it has not expired
            for (
                key
            ) in (
                request.POST
            ):  # Parse responses and individually save each item's response (empty checkboxes or radiobuttons are not saved)
                items = instrument_model.filter(itemID=key)
                if len(items) == 1:
                    item = items[0]
                    value = request.POST[key]
                    if item.choices:
                        choices = map(str.strip, item.choices.choice_set_en.split(";"))
                        if value in choices:
                            administration_data.objects.update_or_create(
                                administration=administration_instance,
                                item_ID=key,
                                defaults={"value": value},
                            )
                    else:
                        if value:
                            administration_data.objects.update_or_create(
                                administration=administration_instance,
                                item_ID=key,
                                defaults={"value": value},
                            )

            if "btn-save" in request.POST and request.POST["btn-save"] == _(
                "Save"
            ):  # If the save button was pressed
                Administration.objects.filter(url_hash=hash_id).update(
                    last_modified=timezone.now()
                )  # Update administration object with date of last modification
                if "analysis" in request.POST:
                    analysis = parse_analysis(
                        request.POST["analysis"]
                    )  # Note whether test-taker asserted that the child's age was accurate and form was filled out to best of ability
                    Administration.objects.filter(url_hash=hash_id).update(
                        analysis=analysis
                    )  # Update administration object

                if "page_number" in request.POST:
                    page_number = (
                        int(request.POST["page_number"])
                        if request.POST["page_number"].isdigit()
                        else 0
                    )  # Note the page number for completion
                    Administration.objects.filter(url_hash=hash_id).update(
                        page_number=page_number
                    )  # Update administration object

                refresh = True
            elif "btn-back" in request.POST and request.POST["btn-back"] == _(
                "Go back to Background Info"
            ):  # If Back button was pressed
                Administration.objects.filter(url_hash=hash_id).update(
                    last_modified=timezone.now()
                )  # Update last_modified
                request.method = "GET"
                background_instance = BackgroundInfo.objects.get(
                    administration=administration_instance
                )
                return redirect("background-info", pk=background_instance.pk)

            elif "btn-submit" in request.POST and request.POST["btn-submit"] == _(
                "Submit"
            ):  # If 'Submit' button was pressed
                # Some studies may require successfully passing a ReCaptcha test for submission. If so, get for a passing response before marking form as complete.
                result = {"success": None}
                recaptcha_response = request.POST.get("g-recaptcha-response", None)
                if recaptcha_response:
                    dt = {
                        "secret": settings.RECAPTCHA_PRIVATE_KEY,
                        "response": recaptcha_response,
                    }
                    r = requests.post(
                        "https://www.google.com/recaptcha/api/siteverify", data=dt
                    )
                    result = r.json()

                # If study allows for subject payment and has yet to hit its cap on subjects, try to provide the test-taker with a gift card code.
                if (
                    administration_instance.study.allow_payment
                    and administration_instance.bypass is None
                ):
                    if (
                        administration_instance.study.confirm_completion
                        and result["success"]
                    ) or not administration_instance.study.confirm_completion:
                        if not PaymentCode.objects.filter(hash_id=hash_id).exists():
                            if (
                                administration_instance.study.name
                                == "Wordful Study (Official)"
                            ):  # for wordful study: if its second admin, give 25 bucks else 5
                                if administration_instance.repeat_num == 2:
                                    # if this subject already has claimed $25: give them $5 this time
                                    if PaymentCode.objects.filter(
                                        hash_id=administration_instance.url_hash,
                                        gift_amount=25.0,
                                    ).exists():
                                        gift_amount_search = 5.0
                                    else:
                                        gift_amount_search = 25.0
                                else:
                                    gift_amount_search = 5.0
                                given_code = PaymentCode.objects.filter(
                                    hash_id__isnull=True,
                                    study=administration_instance.study,
                                    gift_amount=gift_amount_search,
                                ).first()
                            else:
                                given_code = PaymentCode.objects.filter(
                                    hash_id__isnull=True,
                                    study=administration_instance.study,
                                ).first()

                            if given_code:
                                given_code.hash_id = hash_id
                                given_code.assignment_date = timezone.now()
                                given_code.save()

                # If the study is run by langcoglab and the study allows for subject payments, store the IP address for security purposes
                # if administration_instance.study.researcher.username == "langcoglab" and administration_instance.study.allow_payment:
                if administration_instance.study.allow_payment:
                    user_ip = get_client_ip(request)

                    if user_ip and user_ip != "None":
                        ip_address.objects.create(
                            study=administration_instance.study, ip_address=user_ip
                        )

                try:
                    analysis = parse_analysis(
                        request.POST["analysis"]
                    )  # Note whether the response given to the analysis question
                    Administration.objects.filter(url_hash=hash_id).update(
                        last_modified=timezone.now(), analysis=analysis
                    )  # Update administration object
                except:  # If grabbing the analysis response failed
                    Administration.objects.filter(url_hash=hash_id).update(
                        last_modified=timezone.now()
                    )  # Update last_modified

                # check if we have a background info page after the survey and act accordingly
                try:
                    filename = os.path.realpath(
                        PROJECT_ROOT + administration_instance.study.demographic.path
                    )
                except:
                    filename = "None"
                if has_backpage(filename):
                    Administration.objects.filter(url_hash=hash_id).update(
                        completedSurvey=True
                    )
                    request.method = "GET"
                    background_instance = BackgroundInfo.objects.get(
                        administration=administration_instance
                    )
                    return redirect(
                        "backpage-background-info", pk=background_instance.pk
                    )  # Render back page
                else:
                    Administration.objects.filter(url_hash=hash_id).update(
                        completed=True
                    )  # Mark test as complete
                    return redirect(
                        reverse("administration_summary_view", args=(hash_id,))
                    )

    # Fetch prefilled responses
    data = dict()
    if request.method == "GET" or refresh:
        data = prefilled_cdi_data(administration_instance)
        data["created_date"] = administration_instance.created_date.strftime(
            "%b %d, %Y, %I:%M %p"
        )
        data["captcha"] = None
        data["language"] = administration_instance.study.instrument.language
        data["form"] = administration_instance.study.instrument.form
        data["language_code"] = user_language

        # if administration_instance.study.confirm_completion and administration_instance.study.researcher.username == "langcoglab" and administration_instance.study.allow_payment:
        if (
            administration_instance.study.confirm_completion
            and administration_instance.study.allow_payment
        ):
            data["captcha"] = "True"

    # Render CDI form with prefilled responses and study context
    response = render(
        request, "cdi_forms/cdi_form.html", data
    )  # Render contact form template

    response.set_cookie(settings.LANGUAGE_COOKIE_NAME, user_language)
    return response


# As the entire test (background --> CDI --> completion page) share the same URL, access the database to determine current status of test and render the appropriate template
def administer_cdi_form(request, hash_id):
    try:
        administration_instance = Administration.objects.get(url_hash=hash_id)
    except:
        raise Http404("Administration not found")

    if not administration_instance.study.single_reuseable_link.active:
        return render(request, 'cdi_forms/single_reuseable_link_inactive.html' ) 

    if administration_instance.study.instrument.form in settings.CAT_FORMS:
        return redirect("cat_forms:administer_cat_form", hash_id=hash_id)
 
    refresh = False
    if request.method == "POST":
        if (
            not administration_instance.completed
            and administration_instance.due_date > timezone.now()
        ):
            requests_log.objects.create(url_hash=hash_id, request_type="POST")

            if "background-info-form" in request.POST:
                return redirect(
                    "background-info", pk=administration_instance.backgroundinfo.pk
                )

            elif "cdi-form" in request.POST:
                return cdi_form(request, hash_id)

            elif "back-page" in request.POST:
                return redirect(
                    "backpage-background-info",
                    pk=administration_instance.backgroundinfo.pk,
                )

            else:
                refresh = True
        else:
            request.method = "GET"

    if request.method == "GET" or refresh:
        requests_log.objects.create(url_hash=hash_id, request_type="GET")
        if (
            not administration_instance.completed
            and administration_instance.due_date > timezone.now()
        ):
            background_instance, created = BackgroundInfo.objects.get_or_create(
                administration=administration_instance
            )
            if administration_instance.completedSurvey:
                return redirect("backpage-background-info", pk=background_instance.pk)
            elif administration_instance.completedBackgroundInfo:
                if administration_instance.page_number > 0:
                    return redirect(
                        "update_administration_section",
                        hash_id=administration_instance.url_hash,
                        section=administration_instance.page_number + 1,
                    )
                else:
                    return redirect(
                        "instructions", hash_id=administration_instance.url_hash
                    )
            else:
                return redirect("background-info", pk=background_instance.pk)
        else:
            # only printable
            return redirect(reverse("administration_summary_view", args=(hash_id,)))


# For studies that are grouped together, render a modal form that properly displays information regarding each study.
def find_paired_studies(request, username, study_name, source_id):
    data = {}
    researcher = User.objects.get(username=username)
    study = Study.objects.get(name=study_name, researcher=researcher)
    possible_studies = (
        Study.objects.filter(study_group=study.study_group, researcher=researcher)
        .annotate(
            admin_count=models.Sum(
                models.Case(
                    models.When(administration__completed=True, then=1),
                    default=0,
                    output_field=models.IntegerField(),
                )
            )
        )
        .annotate(
            slots_left=models.F("subject_cap") - models.F("admin_count"),
            user_language=models.Case(
                models.When(instrument__language="English", then=models.Value("en")),
                models.When(instrument__language="Spanish", then=models.Value("es")),
                models.When(
                    instrument__language="French Quebec", then=models.Value("fr_ca")
                ),
                models.When(
                    instrument__language="Canadian English", then=models.Value("en_ca")
                ),
                default=models.Value("en"),
                output_field=models.CharField(),
            ),
        )
        .order_by("min_age")
    )

    context = {}
    context["language"] = study.instrument.language
    context["instrument"] = study.instrument.name
    context["min_age"] = study.min_age
    context["max_age"] = study.max_age
    context["birthweight_units"] = study.birth_weight_units
    context["study"] = context["study_obj"] = study
    context["source_id"] = source_id

    # user_language = language_map(administration_instance.study.instrument.language)
    user_language = language_map(study.instrument.language)

    translation.activate(user_language)

    data["background_form"] = BackgroundForm(context=context)
    data["possible_studies"] = possible_studies

    data["lang_list"] = (
        possible_studies.order_by("user_language")
        .values_list("user_language", flat=True)
        .distinct()
    )
    data["username"] = username

    response = render(request, "cdi_forms/study_group.html", data)
    response.set_cookie(settings.LANGUAGE_COOKIE_NAME, user_language)
    return response


def save_answer(request):
    hash_id = request.POST.get("hash_id")
    administration_instance = get_administration_instance(hash_id)

    instrument_name = (
        administration_instance.study.instrument.name
    )  # Get instrument name associated with study
    instrument_model = model_map(instrument_name).filter(
        itemID__in=request.POST
    )  # Fetch instrument model based on instrument name.

    for (
        key
    ) in (
        request.POST
    ):  # Parse responses and individually save each item's response (empty checkboxes or radiobuttons are not saved)
        items = instrument_model.filter(itemID=key)
        if len(items) == 1:
            item = items[0]
            value = request.POST[key]

            if "textbox" in item.item:
                if value:
                    administration_data.objects.update_or_create(
                        administration=administration_instance,
                        item_ID=key,
                        defaults={"value": value},
                    )
            if item.choices:
                choices = map(str.strip, item.choices.choice_set_en.split(";"))
                if value in choices:
                    administration_data.objects.update_or_create(
                        administration=administration_instance,
                        item_ID=key,
                        defaults={"value": value},
                    )
            else:
                if value:
                    administration_data.objects.update_or_create(
                        administration=administration_instance,
                        item_ID=key,
                        defaults={"value": value},
                    )

    Administration.objects.filter(url_hash=hash_id).update(last_modified=timezone.now())
    return HttpResponse(json.dumps([{}]), content_type="application/json")
