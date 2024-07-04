import datetime
import json
import logging
import os
from typing import Any

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db.models import Max
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone, translation
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, UpdateView

from cdi_forms.forms.forms import BackgroundForm, BackpageBackgroundForm
from cdi_forms.models import BackgroundInfo
from cdi_forms.utils import get_demographic_filename
from cdi_forms.views.utils import (PROJECT_ROOT, language_map,
                                   safe_harbor_zip_code)
from researcher_UI.models import Administration, PaymentCode, Study
from researcher_UI.utils import max_subject_id

# Get an instance of a logger
logger = logging.getLogger("debug")

"""
There is a lot of duplication of code here because it is based on the original request views
and we do not want to create an object until the form is submitted.  So we have to set
all the values we're going to use early.

For this reason the BackgroundInfor view templates continue to use the cdi_base.html template
"""


class AdministrationMixin(object):
    hash_id = None
    administration_instance = None
    study_context = {}
    user_language = None

    def get_administration_instance(self):
        self.administration_instance = self.get_object().administration
        return self.administration_instance

    def get_hash_id(self):
        self.hash_id = self.get_administration_instance().url_hash
        return self.hash_id

    def get_study_context(self):
        self.study_context = {}
        self.study_context["language"] = (
            self.administration_instance.study.instrument.language
        )
        self.study_context["instrument"] = (
            self.administration_instance.study.instrument.name
        )
        self.study_context["min_age"] = self.administration_instance.study.min_age
        self.study_context["max_age"] = self.administration_instance.study.max_age
        self.study_context["birthweight_units"] = (
            self.administration_instance.study.birth_weight_units
        )
        self.study_context["child_age"] = None
        self.study_context["zip_code"] = ""
        self.study_context["language_code"] = self.user_language
        self.study_context["study"] = self.administration_instance.study
        self.study_context["source_id"] = (
            self.administration_instance.backgroundinfo.source_id
        )
        self.study_context["study_obj"] = self.administration_instance.study
        return self.study_context

    def get_user_language(self):
        self.user_language = language_map(
            self.administration_instance.study.instrument.language
        )
        # set countries first in certain situations
        if self.administration_instance.study.instrument.language == "French French":
            settings.COUNTRIES_FIRST = ["FR", "CH", "BE", "LU"]
        translation.activate(self.user_language)
        return self.user_language


class BackgroundInfoView(AdministrationMixin, UpdateView):
    template_name = "cdi_forms/background_info.html"
    model = BackgroundInfo
    form_class = BackgroundForm
    background_form = None
    which_page = "front"

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        language = language_map(
            self.get_object().administration.study.instrument.language
        )
        translation.activate(language)
        request.LANGUAGE_CODE = translation.get_language()
        return super().dispatch(request, *args, **kwargs)

    def get_explanation_text(self):
        try:
            filename = os.path.realpath(
                PROJECT_ROOT + self.study_context["study"].demographic.path
            )
            if os.path.isfile(filename):
                pages = json.load(open(filename, encoding="utf-8"))
                for page in pages:
                    if page["page"] == self.which_page:
                        if "help-text" in page:
                            return page["help-text"]
        except:
            pass
        return ""

    def get_context_data(self, **kwargs):
        # data = super(BackgroundInfoView, self).get_context_data(**kwargs)
        data = {}
        data["object"] = self.administration_instance
        data["background_form"] = self.background_form
        data["hash_id"] = self.hash_id
        data["username"] = self.administration_instance.study.researcher.username
        data["completed"] = self.administration_instance.completed
        data["due_date"] = self.administration_instance.due_date.strftime(
            "%b %d, %Y, %I:%M %p"
        )
        data["language"] = self.administration_instance.study.instrument.language
        data["language_code"] = self.user_language
        data["title"] = self.administration_instance.study.instrument.verbose_name
        data["max_age"] = self.administration_instance.study.max_age
        data["min_age"] = self.administration_instance.study.min_age
        data["study_waiver"] = self.administration_instance.study.waiver
        data["allow_payment"] = self.administration_instance.study.allow_payment
        data["hint"] = _(
            f'Your child should be between {data["min_age"]} to {data["max_age"]} months of age.'
        )
        data["form"] = self.administration_instance.study.instrument.form
        data["explanation"] = mark_safe(self.get_explanation_text())

        if data["allow_payment"] and self.administration_instance.bypass is None:
            try:

                data["payment_code"] = PaymentCode.objects.filter(
                    study=self.administration_instance.study, hash_id__isnull=True
                ).first()
            except:
                data["payment_code"] = None
        study_name = self.administration_instance.study.name
        study_group = self.administration_instance.study.study_group
        if study_group:
            data["study_group"] = study_group
            data["alt_study_info"] = (
                Study.objects.filter(
                    study_group=study_group,
                    researcher=self.administration_instance.study.researcher,
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
        return data

    def get_background_form(self):
        try:
            # Fetch responses stored in BackgroundInfo model
            if self.object.age:
                self.study_context["child_age"] = self.object.age
            if len(self.object.zip_code) == 3:
                self.object.zip_code = self.object.zip_code + "**"
            background_form = self.form_class(
                instance=self.object, context=self.study_context, page=self.which_page
            )
        except:
            if (
                self.administration_instance.repeat_num > 1
                or self.administration_instance.study.study_group
            ) and self.administration_instance.study.prefilled_data >= 1:
                if self.administration_instance.study.study_group:
                    related_studies = Study.objects.filter(
                        researcher=self.administration_instance.study.researcher,
                        study_group=self.administration_instance.study.study_group,
                    )
                elif (
                    self.administration_instance.repeat_num > 1
                    and not self.administration_instance.study.study_group
                ):
                    related_studies = Study.objects.filter(
                        id=self.administration_instance.study.id
                    )
                old_admins = Administration.objects.filter(
                    study__in=related_studies,
                    subject_id=self.administration_instance.subject_id,
                    completedBackgroundInfo=True,
                )
                if old_admins:
                    self.get_object = BackgroundInfo.objects.get(
                        administration=old_admins.latest("last_modified")
                    )
                    self.object.pk = None
                    self.object.administration = self.administration_instance
                    self.object.age = None
                    background_form = self.form_class(
                        instance=self.get_object,
                        context=self.study_context,
                        page=self.which_page,
                    )
                else:
                    background_form = self.form_class(
                        context=self.study_context, page=self.which_page
                    )
            else:
                # If you cannot fetch responses, render a blank form
                background_form = self.form_class(
                    context=self.study_context, page=self.which_page
                )
        return background_form

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.get_administration_instance()
        if (
            self.which_page == "back"
            and not self.administration_instance.study.backpage_boolean
        ):
            self.administration_instance.completed = True
            self.administration_instance.save()
            return redirect(self.administration_instance.get_absolute_url())

        self.get_study_context()
        self.get_user_language()
        self.background_form = self.get_background_form()

        response = render(
            request, self.template_name, self.get_context_data()
        )  # Render form template
        response.set_cookie(settings.LANGUAGE_COOKIE_NAME, self.user_language)
        return response

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.get_administration_instance()
        self.get_hash_id()
        self.get_study_context()
        self.get_user_language()
        if (
            not self.administration_instance.completed
            and self.administration_instance.due_date > timezone.now()
        ):  # And test has yet to be completed and has not timed out
            try:
                if self.object.age:
                    self.study_context["child_age"] = (
                        self.object.age
                    )  # Populate dictionary with child's age for validation in forms.py.
                self.background_form = self.form_class(
                    request.POST,
                    instance=self.object,
                    context=self.study_context,
                    page=self.which_page,
                )  # Save filled out form as an object
            except:
                self.background_form = BackgroundForm(
                    request.POST, context=self.study_context, page=self.which_page
                )  # Pull up an empty BackgroundForm with information regarding only the instrument.

            if (
                self.background_form.is_valid()
            ):  # If form passed forms.py validation (clean function)
                obj = self.background_form.save(
                    commit=False
                )  # Save but do not commit form just yet.

                child_dob = self.background_form.cleaned_data.get(
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
                    obj.age = age

                if obj.child_hispanic_latino == "":
                    obj.child_hispanic_latino = None

                # Find the raw zip code value and make it compliant with Safe Harbor guidelines. Only store the first 3 digits if the total population for that prefix is greataer than 20,000 (found prohibited prefixes via Census API data). If prohibited zip code, replace value with state abbreviations.
                if self.object.country == "US":
                    obj.zip_code = safe_harbor_zip_code(self.object)
                else:
                    obj.zip_code = self.object.zip_code

                # Save model object to database
                obj.administration = self.administration_instance
                obj.save()

                # If 'Next' button is pressed, update last_modified and mark completion of BackgroundInfo. Fetch CDI form by hash ID.
                if "btn-next" in request.POST and request.POST["btn-next"] in [
                    "Next",
                    _("Next"),
                ]:
                    Administration.objects.filter(url_hash=self.hash_id).update(
                        last_modified=timezone.now()
                    )
                    Administration.objects.filter(url_hash=self.hash_id).update(
                        completedBackgroundInfo=True
                    )
                    request.method = "GET"
                    return redirect("administer_cdi_form", hash_id=self.hash_id)

                elif "btn-next" in request.POST and request.POST["btn-next"] == _(
                    "Finish"
                ):
                    Administration.objects.filter(url_hash=self.hash_id).update(
                        last_modified=timezone.now()
                    )
                    Administration.objects.filter(url_hash=self.hash_id).update(
                        completed=True
                    )
                    request.method = "GET"
                    return redirect("administer_cdi_form", hash_id=self.hash_id)

                elif "btn-back" in request.POST and request.POST["btn-back"] == _(
                    "Go back to Background Info"
                ):  # If Back button was pressed
                    Administration.objects.filter(url_hash=self.hash_id).update(
                        last_modified=timezone.now()
                    )  # Update last_modified
                    request.method = "GET"
                    background_instance = BackgroundInfo.objects.get(
                        administration=self.administration_instance
                    )
                    return redirect("background-info", pk=background_instance.pk)

            else:
                logger.debug(
                    f"Background info errors for { self.object } are { self.background_form.errors }"
                )

        response = render(
            request, self.template_name, self.get_context_data()
        )  # Render template
        response.set_cookie(settings.LANGUAGE_COOKIE_NAME, self.user_language)
        return response


class BackpageBackgroundInfoView(BackgroundInfoView):
    form_class = BackpageBackgroundForm
    template_name = "cdi_forms/backpage_info.html"
    which_page = "back"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["dont_show_waiver"] = True
        return ctx


class CreateBackgroundInfoView(CreateView):
    template_name = "cdi_forms/background_info.html"
    model = BackgroundInfo
    form_class = BackgroundForm
    background_form = None
    study = None
    bypass = None
    hash_id = None
    source_id = None
    which_page = "front"

    def get_bypass(self):
        self.bypass = self.kwargs["bypass"]

    def get_study(self):
        self.study = Study.objects.get(id=int(self.kwargs["study_id"]))

        # check if valid study and send email if not
        if not self.study.valid_code(self.study.researcher):
            # send email to remind researcher

            subject = "WebCDI - Please purchase a licence"
            from_email = settings.DEFAULT_FROM_EMAIL
            to = f"{self.study.researcher.email}"
            html_content = f""" 
               A parent has accessed an administration for study {self.study}.  Access to this form requires an active license, available for purchase through Brookes Publishing Co (<a href='https://brookespublishing.com/product/cdi' target='_blank'>https://brookespublishing.com/product/cdi</a>)"
            """
            text_content = strip_tags(html_content)
            msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
            msg.attach_alternative(html_content, "text/html")
            msg.send()

    def get_source_id(self):
        self.source_id = self.kwargs["source_id"]
        return self.source_id

    def get_explanation_text(self):
        filename = get_demographic_filename(self.study_context["study"])
        if os.path.isfile(filename):
            pages = json.load(open(filename, encoding="utf-8"))
            for page in pages:
                if page["page"] == self.which_page:
                    if "help-text" in page:
                        return page["help-text"]
        return ""

    def get_study_context(self):
        self.study_context = {}
        self.study_context["language"] = self.study.instrument.language
        self.study_context["instrument"] = self.study.instrument.name
        self.study_context["min_age"] = self.study.min_age
        self.study_context["max_age"] = self.study.max_age
        self.study_context["birthweight_units"] = self.study.birth_weight_units
        self.study_context["child_age"] = None
        self.study_context["zip_code"] = ""
        self.study_context["language_code"] = self.user_language
        self.study_context["study"] = self.study
        self.study_context["source_id"] = self.get_source_id()
        self.study_context["study_obj"] = self.study
        return self.study_context

    def get_user_language(self):
        self.user_language = language_map(self.study.instrument.language)
        translation.activate(self.user_language)
        return self.user_language

    def get_context_data(self, **kwargs):
        data = {}
        data["background_form"] = self.background_form
        data["username"] = self.study.researcher.username
        data["completed"] = False
        data["due_date"] = (
            datetime.datetime.now().date()
            + datetime.timedelta(days=self.study.test_period)
        ).strftime("%b %d, %Y, %I:%M %p")
        data["language"] = self.study.instrument.language
        data["language_code"] = self.user_language
        data["title"] = self.study.instrument.verbose_name
        data["max_age"] = self.study.max_age if self.study.max_age else 0
        data["min_age"] = self.study.min_age if self.study.min_age else 0
        data["study_waiver"] = self.study.waiver
        data["allow_payment"] = self.study.allow_payment
        data["hint"] = _(
            "Your child should be between %(min_age)d to %(max_age)d months of age."
        ) % {"min_age": data["min_age"], "max_age": data["max_age"]}
        data["form"] = self.study.instrument.form
        data["explanation"] = mark_safe(self.get_explanation_text())

        if data["allow_payment"] and self.bypass is None:
            try:
                data["payment_code"] = PaymentCode.objects.filter(
                    study=self.study, hash_id__isnull=True
                ).first()
            except:
                data["payment_code"] = None
        study_name = self.study.name
        study_group = self.study.study_group
        if study_group:
            data["study_group"] = study_group
            data["alt_study_info"] = (
                Study.objects.filter(
                    study_group=study_group, researcher=self.study.researcher
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
        return data

    def get_background_form(self):
        background_form = self.form_class(
            context=self.study_context, page=self.which_page
        )
        return background_form

    def get(self, request, *args, **kwargs):
        self.get_bypass()
        self.get_study()
        self.get_user_language()
        self.get_study_context()
        self.background_form = self.get_background_form()

        response = render(
            request, self.template_name, self.get_context_data()
        )  # Render form template
        response.set_cookie(settings.LANGUAGE_COOKIE_NAME, self.user_language)
        return response

    def form_valid(self, form):
        from researcher_UI.utils.random_url_generator import \
            random_url_generator

        # new_admin = Administration.objects.create(study =self.study, subject_id = max_subject_id+1, repeat_num = 1, url_hash = random_url_generator(), completed = False, due_date = datetime.datetime.now()+datetime.timedelta(days=self.study.test_period)) # Create an administration object for participant within database
        new_admin = Administration.objects.create(
            study=self.study,
            subject_id=max_subject_id(self.study) + 1,
            repeat_num=1,
            url_hash=random_url_generator(),
            completed=False,
            due_date=timezone.now() + datetime.timedelta(days=self.study.test_period),
        )  # Create an administration object for participant within database
        self.hash_id = new_admin.url_hash
        if (
            self.bypass
        ):  # If the user explicitly wanted to continue with the test despite being told they would not be compensated
            new_admin.bypass = True  # Mark administration object with 'bypass'
            new_admin.save()  # Update object in database

        # for field in new_admin._fields:  print(field)
        form = BackgroundForm(
            self.request.POST,
            instance=new_admin,
            context=self.study_context,
            page=self.which_page,
        )

        self.object = form.save()
        return

    def get_success_url(self, *args, **kwargs):
        self.request.method = "GET"
        return reverse("administer_cdi_form", args=[self.hash_id])

    def post(self, request, *args, **kwargs):
        self.get_bypass()
        self.get_study()
        self.get_user_language()
        self.get_study_context()
        self.background_form = self.get_background_form()

        self.background_form = BackgroundForm(
            request.POST, context=self.study_context, page=self.which_page
        )

        if self.background_form.is_valid():
            # First create the administration_instance
            if self.study.study_group:
                related_studies = Study.objects.filter(
                    researcher=self.study.researcher, study_group=self.study.study_group
                )
                max_subject_id = Administration.objects.filter(
                    study__in=related_studies
                ).aggregate(Max("subject_id"))["subject_id__max"]
            else:
                max_subject_id = Administration.objects.filter(
                    study=self.study
                ).aggregate(Max("subject_id"))[
                    "subject_id__max"
                ]  # Find the subject ID in this study with the highest number

            if (
                max_subject_id is None
            ):  # If the max subject ID could not be found (e.g., study has 0 participants)
                max_subject_id = 0  # Mark as zero
            from researcher_UI.utils.random_url_generator import \
                random_url_generator

            administration_instance = Administration.objects.create(
                study=self.study,
                subject_id=max_subject_id + 1,
                repeat_num=1,
                url_hash=random_url_generator(),
                completed=False,  # due_date = datetime.datetime.now()+datetime.timedelta(days=self.study.test_period)) # Create an administration object for participant within database
                due_date=timezone.now()
                + datetime.timedelta(days=self.study.test_period),
            )  # Create an administration object for participant within database
            self.hash_id = administration_instance.url_hash
            if (
                self.bypass
            ):  # If the user explicitly wanted to continue with the test despite being told they would not be compensated
                administration_instance.bypass = (
                    True  # Mark administration object with 'bypass'
                )
                administration_instance.save()  # Update object in database

            obj = self.background_form.save(commit=False)
            child_dob = self.background_form.cleaned_data.get(
                "child_dob"
            )  # Try to fetch DOB

            if (
                child_dob
            ):  # If DOB was entered into form, calculate age based on DOB and today's date.
                raw_age = datetime.date.today() - child_dob
                age = int(float(raw_age.days) / (365.2425 / 12.0))
            else:
                age = None

            # If age was properly calculated from 'child_dob', save it to the model object
            if age:
                obj.age = age

            if obj.child_hispanic_latino == "":
                obj.child_hispanic_latino = None

            # Find the raw zip code value and make it compliant with Safe Harbor guidelines. Only store the first 3 digits if the total population for that prefix is greataer than 20,000 (found prohibited prefixes via Census API data). If prohibited zip code, replace value with state abbreviations.
            if obj.country == "US":
                obj.zip_code = safe_harbor_zip_code(obj)

            # Save model object to database
            obj.administration = administration_instance
            obj.save()
            Administration.objects.filter(url_hash=self.hash_id).update(
                last_modified=timezone.now()
            )
            Administration.objects.filter(url_hash=self.hash_id).update(
                completedBackgroundInfo=True
            )
            self.request = "GET"
            return redirect("administer_cdi_form", hash_id=self.hash_id)

        response = render(
            request, self.template_name, self.get_context_data()
        )  # Render template
        response.set_cookie(settings.LANGUAGE_COOKIE_NAME, self.user_language)
        return response
