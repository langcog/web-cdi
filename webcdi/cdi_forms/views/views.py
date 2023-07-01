# -*- coding: utf-8 -*-

import datetime
import json
import logging
import os.path

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.db import models
from django.http import Http404, HttpResponse
from django.shortcuts import  redirect, render
from django.template.loader import get_template
from django.urls import reverse
from django.utils import timezone, translation
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DetailView
from ipware.ip import get_client_ip
from researcher_UI.models import *

from cdi_forms.forms import BackgroundForm, BackpageBackgroundForm, ContactForm
from cdi_forms.models import *
from cdi_forms.views.utils import model_map, PROJECT_ROOT, has_backpage, prefilled_cdi_data, language_map, safe_harbor_zip_code

# Get an instance of a logger
logger = logging.getLogger("debug")

# Gets list of itemIDs 'item_XX' from an instrument model
def get_model_header(name):
    return list(model_map(name).values_list("itemID", flat=True))


# If the BackgroundInfo model was filled out before, populate BackgroundForm with responses based on administation object
def prefilled_background_form(administration_instance, front_page=True):
    background_instance = BackgroundInfo.objects.get(
        administration=administration_instance
    )

    context = {}
    context["language"] = administration_instance.study.instrument.language
    context["instrument"] = administration_instance.study.instrument.name
    context["min_age"] = administration_instance.study.min_age
    context["max_age"] = administration_instance.study.max_age
    context["birthweight_units"] = administration_instance.study.birth_weight_units
    context["study_obj"] = administration_instance.study
    context["study"] = administration_instance.study
    context["source_id"] = administration_instance.backgroundinfo.source_id

    if front_page:
        background_form = BackgroundForm(
            instance=background_instance, context=context, page="front"
        )
    else:
        background_form = BackpageBackgroundForm(
            instance=background_instance, context=context, page="back"
        )
    return background_form


# Find the administration object for a test-taker based on their unique hash code.
def get_administration_instance(hash_id):
    try:
        administration_instance = administration.objects.get(url_hash=hash_id)
    except:
        raise Http404("Administration not found")
    return administration_instance

# Finds and renders BackgroundForm based on given hash ID code.
def background_info_form(request, hash_id):
    administration_instance = get_administration_instance(
        hash_id
    )  # Get administation object based on hash ID

    # Populate a dictionary with information regarding the instrument (age range, language, and name) along with information on child's age and zipcode for modification. Will be sent to forms.py for form validation.
    context = {}
    context["language"] = administration_instance.study.instrument.language
    context["instrument"] = administration_instance.study.instrument.name
    context["min_age"] = administration_instance.study.min_age
    context["max_age"] = administration_instance.study.max_age
    context["birthweight_units"] = administration_instance.study.birth_weight_units
    context["child_age"] = None
    context["zip_code"] = ""

    user_language = language_map(administration_instance.study.instrument.language)
    translation.activate(user_language)

    refresh = False  # Refreshing page is automatically off
    background_form = None

    if request.method == "POST":  # if test-taker is sending in form responses
        if (
            not administration_instance.completed
            and administration_instance.due_date > timezone.now()
        ):  # And test has yet to be completed and has not timed out
            try:
                background_instance = BackgroundInfo.objects.get(
                    administration=administration_instance
                )  # Try to fetch BackgroundInfo model already stored in database.
                if background_instance.age:
                    context[
                        "child_age"
                    ] = (
                        background_instance.age
                    )  # Populate dictionary with child's age for validation in forms.py.
                background_form = BackgroundForm(
                    request.POST, instance=background_instance, context=context
                )  # Save filled out form as an object
            except:
                background_form = BackgroundForm(
                    request.POST, context=context
                )  # Pull up an empty BackgroundForm with information regarding only the instrument.

            if (
                background_form.is_valid()
            ):  # If form passed forms.py validation (clean function)
                background_instance = background_form.save(
                    commit=False
                )  # Save but do not commit form just yet.

                child_dob = background_form.cleaned_data.get(
                    "child_dob"
                )  # Try to fetch DOB

                if (
                    child_dob
                ):  # If DOB was entered into form, calculate age based on DOB and today's date.
                    raw_age = datetime.date.today() - child_dob
                    age = int(float(raw_age.days) / (365.2425 / 12.0))
                    # day_diff = datetime.date.today().day - child_dob.day
                    # age = (datetime.date.today().year - child_dob.year) * 12 +  (datetime.date.today().month - child_dob.month) + (1 if day_diff >=15 else 0)
                else:
                    age = None

                # If age was properly calculated from 'child_dob', save it to the model object
                if age:
                    background_instance.age = age

                if background_instance.child_hispanic_latino == "":
                    background_instance.child_hispanic_latino = "None"

                # Find the raw zip code value and make it compliant with Safe Harbor guidelines. Only store the first 3 digits if the total population for that prefix is greataer than 20,000 (found prohibited prefixes via Census API data). If prohibited zip code, replace value with state abbreviations.
                if background_instance.country == "US":
                    background_instance.zip_code = safe_harbor_zip_code(
                        background_instance
                    )

                # Save model object to database
                background_instance.administration = administration_instance
                background_instance.save()

                # If 'Next' button is pressed, update last_modified and mark completion of BackgroundInfo. Fetch CDI form by hash ID.
                if "btn-next" in request.POST and request.POST["btn-next"] == _("Next"):
                    administration.objects.filter(url_hash=hash_id).update(
                        last_modified=timezone.now()
                    )
                    administration.objects.filter(url_hash=hash_id).update(
                        completedBackgroundInfo=True
                    )
                    request.method = "GET"
                    return cdi_form(request, hash_id)

    # For fetching or refreshing background form.
    if request.method == "GET" or refresh:
        try:
            # Fetch responses stored in BackgroundInfo model
            background_instance = BackgroundInfo.objects.get(
                administration=administration_instance
            )
            if background_instance.age:
                context["child_age"] = background_instance.age
            if len(background_instance.zip_code) == 3:
                background_instance.zip_code = background_instance.zip_code + "**"
            background_form = BackgroundForm(
                instance=background_instance, context=context
            )
        except:
            if (
                administration_instance.repeat_num > 1
                or administration_instance.study.study_group
            ) and administration_instance.study.prefilled_data >= 1:
                if administration_instance.study.study_group:
                    related_studies = study.objects.filter(
                        researcher=administration_instance.study.researcher,
                        study_group=administration_instance.study.study_group,
                    )
                elif (
                    administration_instance.repeat_num > 1
                    and not administration_instance.study.study_group
                ):
                    related_studies = study.objects.filter(
                        id=administration_instance.study.id
                    )
                old_admins = administration.objects.filter(
                    study__in=related_studies,
                    subject_id=administration_instance.subject_id,
                    completedBackgroundInfo=True,
                )
                if old_admins:
                    background_instance = BackgroundInfo.objects.get(
                        administration=old_admins.latest(field_name="last_modified")
                    )
                    background_instance.pk = None
                    background_instance.administration = administration_instance
                    background_instance.age = None
                    background_form = BackgroundForm(
                        instance=background_instance, context=context
                    )
                else:
                    background_form = BackgroundForm(context=context)
            else:
                # If you cannot fetch responses, render a blank form
                background_form = BackgroundForm(context=context)

    # Store relevant variables in a dictionary for template rendering. Includes prefilled responses, hash ID, data on study (researcher's name, instrument language, age range, related studies, etc.)
    data = {}
    data["background_form"] = background_form
    data["hash_id"] = hash_id
    data["username"] = administration_instance.study.researcher.username
    data["completed"] = administration_instance.completed
    data["due_date"] = administration_instance.due_date.strftime("%b %d, %Y, %I:%M %p")
    data["language"] = administration_instance.study.instrument.language
    data["language_code"] = user_language
    data["title"] = administration_instance.study.instrument.verbose_name
    data["max_age"] = administration_instance.study.max_age
    data["min_age"] = administration_instance.study.min_age
    data["study_waiver"] = administration_instance.study.waiver
    data["allow_payment"] = administration_instance.study.allow_payment
    data["hint"] = _(
        "Your child should be between %(min_age)d to %(max_age)d months of age."
    ) % {"min_age": data["min_age"], "max_age": data["max_age"]}
    data["form"] = administration_instance.study.instrument.form

    if data["allow_payment"] and administration_instance.bypass is None:
        try:
            data["gift_amount"] = (
                payment_code.objects.filter(study=administration_instance.study)
                .values_list("gift_amount", flat=True)
                .first()
            )
        except:
            data["gift_amount"] = None
    study_name = administration_instance.study.name
    study_group = administration_instance.study.study_group
    if study_group:
        data["study_group"] = study_group
        data["alt_study_info"] = (
            study.objects.filter(
                study_group=study_group,
                researcher=administration_instance.study.researcher,
            )
            .exclude(name=study_name)
            .values_list(
                "name",
                "instrument__min_age",
                "instrument__max_age",
                "instrument__language",
            )
        )
        data["study_group_hint"] = _(
            " Not the right age? <a href='%(sgurl)s'> Click here</a>"
        ) % {
            "sgurl": reverse(
                "find_paired_studies", args=[data["username"], data["study_group"]]
            )
        }
    else:
        data["study_group"] = None
        data["alt_study_info"] = None
        data["study_group_hint"] = _(
            " Not the right age? You should contact your researcher for steps on what to do next."
        )

    # Render CDI form with prefilled responses and study context
    response = render(
        request, "cdi_forms/background_info.html", data
    )  # Render contact form template

    response.set_cookie(settings.LANGUAGE_COOKIE_NAME, user_language)
    return response

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
                administration.objects.filter(url_hash=hash_id).update(
                    last_modified=timezone.now()
                )  # Update administration object with date of last modification
                if "analysis" in request.POST:
                    analysis = parse_analysis(
                        request.POST["analysis"]
                    )  # Note whether test-taker asserted that the child's age was accurate and form was filled out to best of ability
                    administration.objects.filter(url_hash=hash_id).update(
                        analysis=analysis
                    )  # Update administration object

                if "page_number" in request.POST:
                    page_number = (
                        int(request.POST["page_number"])
                        if request.POST["page_number"].isdigit()
                        else 0
                    )  # Note the page number for completion
                    administration.objects.filter(url_hash=hash_id).update(
                        page_number=page_number
                    )  # Update administration object

                refresh = True
            elif "btn-back" in request.POST and request.POST["btn-back"] == _(
                "Go back to Background Info"
            ):  # If Back button was pressed
                administration.objects.filter(url_hash=hash_id).update(
                    last_modified=timezone.now()
                )  # Update last_modified
                request.method = "GET"
                background_instance = BackgroundInfo.objects.get(
                    administration=administration_instance
                )
                return redirect(
                    "background-info", pk=background_instance.pk
                )  
            
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
                        if not payment_code.objects.filter(hash_id=hash_id).exists():
                            if (
                                administration_instance.study.name
                                == "Wordful Study (Official)"
                            ):  # for wordful study: if its second admin, give 25 bucks else 5
                                if administration_instance.repeat_num == 2:
                                    # if this subject already has claimed $25: give them $5 this time
                                    if payment_code.objects.filter(
                                        hash_id=administration_instance.url_hash,
                                        gift_amount=25.0,
                                    ).exists():
                                        gift_amount_search = 5.0
                                    else:
                                        gift_amount_search = 25.0
                                else:
                                    gift_amount_search = 5.0
                                given_code = payment_code.objects.filter(
                                    hash_id__isnull=True,
                                    study=administration_instance.study,
                                    gift_amount=gift_amount_search,
                                ).first()
                            else:
                                given_code = payment_code.objects.filter(
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
                    administration.objects.filter(url_hash=hash_id).update(
                        last_modified=timezone.now(), analysis=analysis
                    )  # Update administration object
                except:  # If grabbing the analysis response failed
                    administration.objects.filter(url_hash=hash_id).update(
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
                    administration.objects.filter(url_hash=hash_id).update(
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
                    administration.objects.filter(url_hash=hash_id).update(
                        completed=True
                    )  # Mark test as complete
                    return printable_view(request, hash_id)  # Render completion page

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


# Render completion page
def printable_view(request, hash_id):
    administration_instance = get_administration_instance(
        hash_id
    )  # Get administration object based on hash ID
    user_language = language_map(administration_instance.study.instrument.language)
    translation.activate(user_language)

    if not administration_instance.completed:
        response = render(
            request, "cdi_forms/expired.html", {}
        )  # Render contact form template
        response.set_cookie(settings.LANGUAGE_COOKIE_NAME, user_language)
        return response

    completed = int(
        request.get_signed_cookie("completed_num", "0")
    )  # If there is a cookie for a previously completed test, get it

    # Create a blank dictionary and then fill it with prefilled background and CDI data, along with hash ID and information regarding the gift card code if subject is to be paid
    prefilled_data = dict()
    prefilled_data = prefilled_cdi_data(administration_instance)

    context = {}
    context["language"] = administration_instance.study.instrument.language
    context["instrument"] = administration_instance.study.instrument.name
    context["min_age"] = administration_instance.study.min_age
    context["max_age"] = administration_instance.study.max_age
    context["birthweight_units"] = administration_instance.study.birth_weight_units
    context["source_id"] = administration_instance.backgroundinfo.source_id
    context["study_obj"] = administration_instance.study
    context["study"] = administration_instance.study
    # try:
    # Get form from database
    background_form = prefilled_background_form(administration_instance)
    try:
        filename = os.path.realpath(
            PROJECT_ROOT + administration_instance.study.demographic.path
        )
    except:
        filename = "None"
    if has_backpage(filename):
        backpage_background_form = prefilled_background_form(
            administration_instance, False
        )
    # except:
    # Blank form
    #    background_form = BackgroundForm(context = context, page="front")

    prefilled_data["language"] = administration_instance.study.instrument.language
    prefilled_data["background_form"] = background_form
    try:
        prefilled_data["backpage_background_form"] = backpage_background_form
    except:
        pass
    prefilled_data["hash_id"] = hash_id
    prefilled_data["gift_code"] = None
    prefilled_data["gift_amount"] = None
    prefilled_data["min_age"] = administration_instance.study.instrument.min_age
    prefilled_data["max_age"] = administration_instance.study.instrument.max_age
    prefilled_data["show_feedback"] = administration_instance.study.show_feedback

    if (
        administration_instance.study.allow_payment
        and administration_instance.bypass is None
    ):
        amazon_urls = {
            "English": {
                "redeem_url": "http://www.amazon.com/redeem",
                "legal_url": "http://www.amazon.com/gc-legal",
            },
            "Spanish": {
                "redeem_url": "http://www.amazon.com/gc/redeem/?language=es_US",
                "legal_url": "http://www.amazon.com/gc-legal/?language=es_US",
            },
            "French Quebec": {
                "redeem_url": "http://www.amazon.ca/gc/redeem/?language=fr_CA",
                "legal_url": "http://www.amazon.ca/gc-legal/?language=fr_CA",
            },
        }
        url_obj = amazon_urls[administration_instance.study.instrument.language]
        if payment_code.objects.filter(hash_id=hash_id).exists():
            gift_card = payment_code.objects.get(hash_id=hash_id)
            prefilled_data["gift_code"] = gift_card.gift_code
            prefilled_data["gift_amount"] = "${:,.2f}".format(gift_card.gift_amount)
            prefilled_data["redeem_url"] = url_obj["redeem_url"]
            prefilled_data["legal_url"] = url_obj["legal_url"]
        else:
            prefilled_data["gift_code"] = "ran out"
            prefilled_data["gift_amount"] = "ran out"
            prefilled_data["redeem_url"] = None
            prefilled_data["legal_url"] = None

    prefilled_data["allow_sharing"] = administration_instance.study.allow_sharing

    # calculate graph data
    cdi_items = json.loads(prefilled_data["cdi_items"])
    categories = {}
    from cdi_forms.management.commands.populate_items import unicode_csv_reader

    categories_data = list(
        unicode_csv_reader(
            open(
                os.path.realpath(
                    settings.BASE_DIR + "/static/data_csv/word_categories.csv"
                ),
                encoding="utf8",
            )
        )
    )

    col_names = categories_data[0]
    nrows = len(categories_data)
    get_row = lambda row: categories_data[row]
    categories = {}
    totals = {"produces": 0, "understands": 0}
    for row in range(1, nrows):
        row_values = get_row(row)
        if len(row_values) > 1:
            if row_values[
                col_names.index(administration_instance.study.instrument.name)
            ]:
                mapped_name = row_values[
                    col_names.index(administration_instance.study.instrument.name)
                ]
            else:
                mapped_name = row_values[col_names.index("id")]
            categories[row_values[col_names.index("id")]] = {
                "produces": 0,
                "understands": 0,
                "count": 0,
                "mappedName": mapped_name,
            }
    for row in cdi_items:
        if row["item_type"] == "word":
            categories[row["category"]]["count"] += 1

    prefilled_data_list = administration_data.objects.filter(
        administration=administration_instance
    ).values("item_ID", "value")
    for item in prefilled_data_list:
        instance = Instrument_Forms.objects.get(
            itemID=item["item_ID"], instrument=administration_instance.study.instrument
        )
        if instance.item_type == "word":
            if item["value"] == "produces":
                categories[instance.category]["produces"] += 1
                categories[instance.category]["understands"] += 1
            if item["value"] == "understands":
                categories[instance.category]["understands"] += 1

    prefilled_data["graph_data"] = categories
    prefilled_data["instrument"] = administration_instance.study.instrument.name
    prefilled_data["object"] = administration_instance
    prefilled_data["language_code"] = settings.LANGUAGE_DICT[
        administration_instance.study.instrument.language
    ]

    response = render(
        request, "cdi_forms/printable_cdi.html", prefilled_data
    )  # Render contact form template
    response.set_cookie(settings.LANGUAGE_COOKIE_NAME, user_language)

    # if administration_instance.study.researcher.username == "langcoglab" and administration_instance.study.allow_payment:
    if administration_instance.study.allow_payment:
        response.set_signed_cookie("completed_num", completed)
    return response


# As the entire test (background --> CDI --> completion page) share the same URL, access the database to determine current status of test and render the appropriate template
def administer_cdi_form(request, hash_id):
    logger.debug(f"Administering CDI form for { hash_id }")
    try:
        administration_instance = administration.objects.get(url_hash=hash_id)
    except:
        raise Http404("Administration not found")

    if administration_instance.study.instrument.form in settings.CAT_FORMS:
        logger.debug(f"Administration { hash_id } is a CAT administration")
        logger.debug(f"This is a { request.method } redirect")
        return redirect("cat_forms:administer_cat_form", hash_id=hash_id)

    refresh = False
    if request.method == "POST":
        if (
            not administration_instance.completed
            and administration_instance.due_date > timezone.now()
        ):
            requests_log.objects.create(url_hash=hash_id, request_type="POST")

            if "background-info-form" in request.POST:
                return background_info_form(request, hash_id)

            elif "cdi-form" in request.POST:
                return cdi_form(request, hash_id)

            elif "back-page" in request.POST:
                return background_info_form(request, hash_id)

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
                return cdi_form(request, hash_id)
            else:
                return redirect("background-info", pk=background_instance.pk)
                # return background_info_form(request, hash_id)
        else:
            # only printable
            return printable_view(request, hash_id)


# For studies that are grouped together, render a modal form that properly displays information regarding each study.
def find_paired_studies(request, username, study_group):
    data = {}
    researcher = User.objects.get(username=username)
    possible_studies = (
        study.objects.filter(study_group=study_group, researcher=researcher)
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

    first_study = study.objects.filter(study_group=study_group, researcher=researcher)[
        :1
    ].get()

    context = {}
    context["language"] = first_study.instrument.language
    context["instrument"] = first_study.instrument.name
    context["min_age"] = first_study.min_age
    context["max_age"] = first_study.max_age
    context["birthweight_units"] = first_study.birth_weight_units

    # user_language = language_map(administration_instance.study.instrument.language)
    user_language = language_map(first_study.instrument.language)

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


# For test-takers contacting a Web-CDI admin
def contact(request, hash_id):
    administration_instance = get_administration_instance(hash_id)
    # Determine administration URL
    redirect_url = "".join(
        [
            "http://",
            get_current_site(request).domain,
            reverse("administer_cdi_form", args=[hash_id]),
        ]
    )

    # Render bare contact form
    form = ContactForm(redirect_url=redirect_url)

    if request.method == "POST":  # If submitting a responses
        form = ContactForm(request.POST, redirect_url=redirect_url)

        if form.is_valid():  # If form is validated
            # Access responses and render an email to be sent to administrator.
            contact_name = request.POST.get("contact_name", "")
            contact_email = request.POST.get("contact_email", "")
            contact_id = request.POST.get("contact_id", "")
            form_content = request.POST.get("content", "")
            template = get_template("cdi_forms/contact_template.txt")
            context = {
                "contact_name": contact_name,
                "contact_id": contact_id,
                "contact_email": contact_email,
                "form_content": form_content,
            }
            content = template.render(context)
            email = EmailMessage(
                "New contact form submission",
                content,
                "webcdi.stanford.edu" + "",
                ["dkellier@stanford.edu"],
                headers={"Reply-To": contact_email},
            )
            email.send()
            messages.success(
                request, "Form submission successful!"
            )  # Provide sender with a message the form was properly sent.

    user_language = language_map(administration_instance.study.instrument.language)

    translation.activate(user_language)
    response = render(
        request, "cdi_forms/contact.html", {"form": form}
    )  # Render contact form template
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

    administration.objects.filter(url_hash=hash_id).update(last_modified=timezone.now())
    return HttpResponse(json.dumps([{}]), content_type="application/json")


def update_administration_data_item(request):
    if not request.POST:
        return

    hash_id = request.POST.get("hash_id")
    administration_instance = get_administration_instance(hash_id)
    instrument_name = (
        administration_instance.study.instrument.name
    )  # Get instrument name associated with study
    instrument_model = model_map(instrument_name).filter(
        itemID__in=request.POST
    )  # Fetch instrument model based on instrument name.

    value = ""
    if request.POST["check"] == "true":
        value = request.POST["value"]

    if len(value) > 0:
        administration_data.objects.update_or_create(
            administration=administration_instance,
            item_ID=request.POST["item"],
            defaults={"value": value},
        )
    elif administration_data.objects.filter(
        administration=administration_instance, item_ID=request.POST["item"]
    ).exists():
        administration_data.objects.get(
            administration=administration_instance, item_ID=request.POST["item"]
        ).delete()
    administration.objects.filter(url_hash=hash_id).update(last_modified=timezone.now())
    return HttpResponse(json.dumps([{}]), content_type="application/json")
