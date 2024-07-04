import datetime
import logging

from django.contrib.auth.models import User
from django.test import TestCase, tag
from django.urls import reverse
from django.utils import timezone

from cdi_forms.models import BackgroundInfo
from researcher_UI.models import Administration, Demographic, Instrument, Study
from researcher_UI.tests.utils import random_password
from researcher_UI.utils.random_url_generator import random_url_generator

logger = logging.getLogger("tests")
logger.setLevel(logging.INFO)


class CreateBackgroundInfoViewTest(TestCase):
    fixtures = [
        "researcher_UI/fixtures/researcher_UI_test_fixtures.json",
        "cdi_forms/fixtures/cdi_forms_test_fixtures.json",
    ]

    def setUp(self):
        self.user = User.objects.create_user(
            username="test_user", password=random_password()
        )

        instrument = Instrument.objects.get(
            language="English",
            form="WS",
        )

        self.study = Study.objects.create(
            researcher=self.user,
            name="Test Study Instance",
            instrument=instrument,
            min_age=12,
            max_age=36,
            redirect_url="https://example.com/redirect/{source_id}",
        )

        self.url = reverse(
            "create-new-background-info",
            kwargs={
                "study_id": self.study.id,
                "bypass": True,
                "source_id": random_password(),
            },
        )

    def test_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_invalid_post(self):
        now = (datetime.datetime.now() - datetime.timedelta(days=500)).strftime(
            "%m/%d/%Y"
        )
        payload = {
            "form_filler": "mother",
            "child_dob": now,
            "sex": "M",
            "birth_weight_lb": "3.5",
            "birth_order": 1,
            "born_on_due_date": 0,
            "multi_birth_boolean": 0,
            "primary_caregiver": "mother",
            "mother_yob": 1966,
            "mother_education": 18,
            "annual_income": "25000-50000",
            "caregiver_info": "1",
            "other_languages_boolean": 0,
            "ear_infections_boolean": 0,
            "hearing_loss_boolean": 0,
            "vision_problems_boolean": 0,
            "illnesses_boolean": 0,
            "services_boolean": 0,
            "worried_boolean": 0,
            #'learning_disability_boolean': 0
        }
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 200)

    def test_valid_post(self):
        now = (datetime.datetime.now() - datetime.timedelta(days=500)).strftime(
            "%m/%d/%Y"
        )
        payload = {
            "form_filler": "mother",
            "child_dob": now,
            "sex": "M",
            "birth_weight_lb": "3.5",
            "birth_order": 1,
            "born_on_due_date": 0,
            "multi_birth_boolean": 0,
            "primary_caregiver": "mother",
            "mother_yob": 1966,
            "mother_education": 18,
            "annual_income": "25000-50000",
            "caregiver_info": "1",
            "other_languages_boolean": 0,
            "ear_infections_boolean": 0,
            "hearing_loss_boolean": 0,
            "vision_problems_boolean": 0,
            "illnesses_boolean": 0,
            "services_boolean": 0,
            "worried_boolean": 0,
            "learning_disability_boolean": 0,
        }
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 302)

    def test_invalid_dependent_field_post(self):
        now = (datetime.datetime.now() - datetime.timedelta(days=500)).strftime(
            "%m/%d/%Y"
        )
        payload = {
            "form_filler": "mother",
            "child_dob": now,
            "sex": "M",
            "birth_weight_lb": "3.5",
            "birth_order": 1,
            "born_on_due_date": 0,
            "multi_birth_boolean": 0,
            "primary_caregiver": "mother",
            "mother_yob": 1966,
            "mother_education": 18,
            "annual_income": "25000-50000",
            "caregiver_info": "1",
            "other_languages_boolean": 0,
            "ear_infections_boolean": 0,
            "hearing_loss_boolean": 0,
            "vision_problems_boolean": 0,
            "illnesses_boolean": 0,
            "services_boolean": 0,
            "worried_boolean": 0,
            "learning_disability_boolean": 1,
        }
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["background_form"].errors["learning_disability"][0],
            "This field cannot be empty",
        )

    def test_valid_dependent_field_post(self):
        now = (datetime.datetime.now() - datetime.timedelta(days=500)).strftime(
            "%m/%d/%Y"
        )
        payload = {
            "form_filler": "mother",
            "child_dob": now,
            "sex": "M",
            "birth_weight_lb": "3.5",
            "birth_order": 1,
            "born_on_due_date": 0,
            "multi_birth_boolean": 0,
            "primary_caregiver": "mother",
            "mother_yob": 1966,
            "mother_education": 18,
            "annual_income": "25000-50000",
            "caregiver_info": "1",
            "other_languages_boolean": 0,
            "ear_infections_boolean": 0,
            "hearing_loss_boolean": 0,
            "vision_problems_boolean": 0,
            "illnesses_boolean": 0,
            "services_boolean": 0,
            "worried_boolean": 0,
            "learning_disability_boolean": 1,
            "learning_disability": "This is a learning disability",
        }
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 302)

    def test_not_born_on_due_date_invalid_post(self):
        now = (datetime.datetime.now() - datetime.timedelta(days=500)).strftime(
            "%m/%d/%Y"
        )
        payload = {
            "form_filler": "mother",
            "child_dob": now,
            "sex": "M",
            "birth_weight_lb": "3.5",
            "birth_order": 1,
            "born_on_due_date": 1,
            "early_or_late": "early",
            "multi_birth_boolean": 0,
            "primary_caregiver": "mother",
            "mother_yob": 1966,
            "mother_education": 18,
            "annual_income": "25000-50000",
            "caregiver_info": "1",
            "other_languages_boolean": 0,
            "ear_infections_boolean": 0,
            "hearing_loss_boolean": 0,
            "vision_problems_boolean": 0,
            "illnesses_boolean": 0,
            "services_boolean": 0,
            "worried_boolean": 0,
            "learning_disability_boolean": 1,
            "learning_disability": "This is a learning disability",
        }
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["background_form"].errors["due_date_diff"][0],
            "This field cannot be empty",
        )

    def test_not_born_on_due_date_too_early_post(self):
        now = (datetime.datetime.now() - datetime.timedelta(days=500)).strftime(
            "%m/%d/%Y"
        )
        payload = {
            "form_filler": "mother",
            "child_dob": now,
            "sex": "M",
            "birth_weight_lb": "3.5",
            "birth_order": 1,
            "born_on_due_date": 1,
            "early_or_late": "early",
            "due_date_diff": 20,
            "multi_birth_boolean": 0,
            "primary_caregiver": "mother",
            "mother_yob": 1966,
            "mother_education": 18,
            "annual_income": "25000-50000",
            "caregiver_info": "1",
            "other_languages_boolean": 0,
            "ear_infections_boolean": 0,
            "hearing_loss_boolean": 0,
            "vision_problems_boolean": 0,
            "illnesses_boolean": 0,
            "services_boolean": 0,
            "worried_boolean": 0,
            "learning_disability_boolean": 1,
            "learning_disability": "This is a learning disability",
        }
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["background_form"].errors["born_on_due_date"][0],
            "Cannot be more than 18 weeks early",
        )

    def test_not_born_on_due_date_too_late_post(self):
        now = (datetime.datetime.now() - datetime.timedelta(days=500)).strftime(
            "%m/%d/%Y"
        )
        payload = {
            "form_filler": "mother",
            "child_dob": now,
            "sex": "M",
            "birth_weight_lb": "3.5",
            "birth_order": 1,
            "born_on_due_date": 1,
            "early_or_late": "late",
            "due_date_diff": 6,
            "multi_birth_boolean": 0,
            "primary_caregiver": "mother",
            "mother_yob": 1966,
            "mother_education": 18,
            "annual_income": "25000-50000",
            "caregiver_info": "1",
            "other_languages_boolean": 0,
            "ear_infections_boolean": 0,
            "hearing_loss_boolean": 0,
            "vision_problems_boolean": 0,
            "illnesses_boolean": 0,
            "services_boolean": 0,
            "worried_boolean": 0,
            "learning_disability_boolean": 1,
            "learning_disability": "This is a learning disability",
        }
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["background_form"].errors["born_on_due_date"][0],
            "Cannot be more than 4 weeks late",
        )

    def test_not_born_on_due_date_valid_post(self):
        now = (datetime.datetime.now() - datetime.timedelta(days=500)).strftime(
            "%m/%d/%Y"
        )
        payload = {
            "form_filler": "mother",
            "child_dob": now,
            "sex": "M",
            "birth_weight_lb": "3.5",
            "birth_order": 1,
            "born_on_due_date": 1,
            "early_or_late": "early",
            "due_date_diff": 2,
            "multi_birth_boolean": 0,
            "primary_caregiver": "mother",
            "mother_yob": 1966,
            "mother_education": 18,
            "annual_income": "25000-50000",
            "caregiver_info": "1",
            "other_languages_boolean": 0,
            "ear_infections_boolean": 0,
            "hearing_loss_boolean": 0,
            "vision_problems_boolean": 0,
            "illnesses_boolean": 0,
            "services_boolean": 0,
            "worried_boolean": 0,
            "learning_disability_boolean": 1,
            "learning_disability": "This is a learning disability",
        }
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 302)

    def test_too_young_post(self):
        now = (datetime.datetime.now() - datetime.timedelta(days=35)).strftime(
            "%m/%d/%Y"
        )
        payload = {
            "form_filler": "mother",
            "child_dob": now,
            "sex": "M",
            "birth_weight_lb": "3.5",
            "birth_order": 1,
            "born_on_due_date": 0,
            "multi_birth_boolean": 0,
            "primary_caregiver": "mother",
            "mother_yob": 1966,
            "mother_education": 18,
            "annual_income": "25000-50000",
            "caregiver_info": "1",
            "other_languages_boolean": 0,
            "ear_infections_boolean": 0,
            "hearing_loss_boolean": 0,
            "vision_problems_boolean": 0,
            "illnesses_boolean": 0,
            "services_boolean": 0,
            "worried_boolean": 0,
            "learning_disability_boolean": 1,
            "learning_disability": "This is a learning disability",
        }
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["background_form"].errors["age"][0],
            "Your baby is too young for this version of the CDI.",
        )

    def test_too_old_post(self):
        now = (datetime.datetime.now() - datetime.timedelta(days=5000)).strftime(
            "%m/%d/%Y"
        )
        payload = {
            "form_filler": "mother",
            "child_dob": now,
            "sex": "M",
            "birth_weight_lb": "3.5",
            "birth_order": 1,
            "born_on_due_date": 0,
            "multi_birth_boolean": 0,
            "primary_caregiver": "mother",
            "mother_yob": 1966,
            "mother_education": 18,
            "annual_income": "25000-50000",
            "caregiver_info": "1",
            "other_languages_boolean": 0,
            "ear_infections_boolean": 0,
            "hearing_loss_boolean": 0,
            "vision_problems_boolean": 0,
            "illnesses_boolean": 0,
            "services_boolean": 0,
            "worried_boolean": 0,
            "learning_disability_boolean": 1,
            "learning_disability": "This is a learning disability",
        }
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["background_form"].errors["age"][0],
            "Your baby is too old for this version of the CDI.",
        )

    def test_invalid_dob_post(self):
        now = (datetime.datetime.now() - datetime.timedelta(days=10)).strftime(
            "%m/%d/%Y"
        )
        payload = {
            "form_filler": "mother",
            "child_dob": now,
            "sex": "M",
            "birth_weight_lb": "3.5",
            "birth_order": 1,
            "born_on_due_date": 0,
            "multi_birth_boolean": 0,
            "primary_caregiver": "mother",
            "mother_yob": 1966,
            "mother_education": 18,
            "annual_income": "25000-50000",
            "caregiver_info": "1",
            "other_languages_boolean": 0,
            "ear_infections_boolean": 0,
            "hearing_loss_boolean": 0,
            "vision_problems_boolean": 0,
            "illnesses_boolean": 0,
            "services_boolean": 0,
            "worried_boolean": 0,
            "learning_disability_boolean": 1,
            "learning_disability": "This is a learning disability",
        }
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["background_form"].errors["age"][0],
            "Please enter your child's DOB in the field above.",
        )

    def test_no_dob_post(self):
        now = (datetime.datetime.now() - datetime.timedelta(days=10)).strftime(
            "%m/%d/%Y"
        )
        payload = {
            "form_filler": "mother",
            "sex": "M",
            "birth_weight_lb": "3.5",
            "birth_order": 1,
            "born_on_due_date": 0,
            "multi_birth_boolean": 0,
            "primary_caregiver": "mother",
            "mother_yob": 1966,
            "mother_education": 18,
            "annual_income": "25000-50000",
            "caregiver_info": "1",
            "other_languages_boolean": 0,
            "ear_infections_boolean": 0,
            "hearing_loss_boolean": 0,
            "vision_problems_boolean": 0,
            "illnesses_boolean": 0,
            "services_boolean": 0,
            "worried_boolean": 0,
            "learning_disability_boolean": 1,
            "learning_disability": "This is a learning disability",
        }
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["background_form"].errors["age"][0],
            "Please enter your child's DOB in the field above.",
        )

    def test_no_weight_post(self):
        now = (datetime.datetime.now() - datetime.timedelta(days=10)).strftime(
            "%m/%d/%Y"
        )
        payload = {
            "form_filler": "mother",
            "sex": "M",
            # "birth_weight_lb": "3.5",
            "birth_order": 1,
            "born_on_due_date": 0,
            "multi_birth_boolean": 0,
            "primary_caregiver": "mother",
            "mother_yob": 1966,
            "mother_education": 18,
            "annual_income": "25000-50000",
            "caregiver_info": "1",
            "other_languages_boolean": 0,
            "ear_infections_boolean": 0,
            "hearing_loss_boolean": 0,
            "vision_problems_boolean": 0,
            "illnesses_boolean": 0,
            "services_boolean": 0,
            "worried_boolean": 0,
            "learning_disability_boolean": 1,
            "learning_disability": "This is a learning disability",
        }
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["background_form"].errors["birth_weight_lb"][0],
            "This field cannot be empty",
        )


class BackgroundInfoViewTest(TestCase):
    fixtures = [
        "researcher_UI/fixtures/researcher_UI_test_fixtures.json",
        "cdi_forms/fixtures/cdi_forms_test_fixtures.json",
    ]

    def setUp(self):
        self.user = User.objects.create_user(
            username="test_user", password=random_password()
        )

        instrument = Instrument.objects.get(
            language="English",
            form="WS",
        )

        self.study = Study.objects.create(
            researcher=self.user,
            name="Test Study Instance",
            instrument=instrument,
            redirect_url="https://example.com/redirect/{source_id}",
        )

        self.administration = Administration.objects.create(
            study=self.study,
            subject_id=1,
            repeat_num=1,
            url_hash=random_url_generator(),
            completed=False,
            due_date=timezone.now(),
        )

        background_info = BackgroundInfo.objects.create(
            administration=self.administration, age=12, source_id=random_password()
        )

        self.url = reverse("background-info", kwargs={"pk": background_info.pk})

    def test_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)


class CreateBackgroundInfoNotDefaultDemographicViewTest(TestCase):
    fixtures = [
        "researcher_UI/fixtures/researcher_UI_test_fixtures.json",
        "cdi_forms/fixtures/cdi_forms_test_fixtures.json",
    ]

    def setUp(self):
        self.user = User.objects.create_user(
            username="test_user", password=random_password()
        )

    def test_valid_post(self):
        for instrument in Instrument.objects.all():
            if instrument.language in ["English", "Spanish"]:
                now = (datetime.datetime.now() - datetime.timedelta(days=500)).strftime(
                    "%m/%d/%Y"
                )
            else:
                now = (datetime.datetime.now() - datetime.timedelta(days=500)).strftime(
                    "%d/%m/%Y"
                )
            for demographic in instrument.demographics.all():
                study = Study.objects.create(
                    researcher=self.user,
                    name=f"{instrument.name} {demographic.name}",
                    instrument=instrument,
                    min_age=12,
                    max_age=36,
                    redirect_url="https://example.com/redirect/{source_id}",
                    demographic=demographic,
                )

                payload = {
                    "form_filler": "mother",
                    "child_dob": now,
                    "sex": "M",
                    "birth_weight_lb": "3.5",
                    "birth_weight_kg": "3.5",
                    "birth_order": 1,
                    "born_on_due_date": 0,
                    "multi_birth_boolean": 0,
                    "primary_caregiver": "mother",
                    "mother_yob": 1966,
                    "mother_education": 18,
                    "annual_income": "25000-50000",
                    "caregiver_info": "1",
                    "other_languages_boolean": 0,
                    "ear_infections_boolean": 0,
                    "hearing_loss_boolean": 0,
                    "vision_problems_boolean": 0,
                    "illnesses_boolean": 0,
                    "services_boolean": 0,
                    "worried_boolean": 0,
                    "learning_disability_boolean": 0,
                    "source_id": random_password(),
                    "primary_caregiver_occupation": random_password(),
                    "sibling_count": 1,
                    "generic_health_question": "Yes",
                }
                url = reverse(
                    "create-new-background-info",
                    kwargs={
                        "study_id": study.id,
                        "bypass": True,
                        "source_id": random_password(),
                    },
                )
                response = self.client.post(url, payload)
                if response.status_code == 200:
                    print(
                        f"{study.name} has {response.context['background_form'].errors} in CreateBackgroundInfoNotDefaultDemographicViewTest"
                    )
                self.assertEqual(response.status_code, 302)
                self.assertEqual(Administration.objects.filter(study=study).count(), 1)
                administration = Administration.objects.get(study=study)
                self.assertRedirects(
                    response,
                    reverse("administer_cdi_form", args=[administration.url_hash]),
                    target_status_code=302,
                )
                administration.completedSurvey = True
                administration.save()
                url = reverse(
                    "backpage-background-info",
                    kwargs={
                        "pk": administration.backgroundinfo.id,
                    },
                )
                payload["btn-next"] = "Next"
                response = self.client.post(url, payload)
                if response.status_code == 200:
                    print(
                        f"{study.name} has {response.context['background_form'].errors} in CreateBackgroundInfoNotDefaultDemographicViewTest"
                    )
                self.assertEqual(response.status_code, 302)


@tag("new")
class StudyRedirectTests(TestCase):
    fixtures = [
        "researcher_UI/fixtures/researcher_UI_test_fixtures.json",
        "cdi_forms/fixtures/cdi_forms_test_fixtures.json",
    ]

    def setUp(self):
        self.user = User.objects.create_user(
            username="test_user", password=random_password()
        )

        instrument = Instrument.objects.get(
            language="English",
            form="WS",
        )

        self.study = Study.objects.create(
            researcher=self.user,
            name="Test Study Instance",
            instrument=instrument,
            min_age=12,
            max_age=36,
            redirect_url="https://example.com/redirect/{source_id}",
            redirect_boolean=True,
            direct_redirect_boolean=True,
            timing=0,
            demographic=Demographic.objects.get(name="English_Split.json"),
        )

        self.url = reverse(
            "create-new-background-info",
            kwargs={
                "study_id": self.study.id,
                "bypass": True,
                "source_id": random_password(),
            },
        )

    def test_valid_post(self):
        now = (datetime.datetime.now() - datetime.timedelta(days=500)).strftime(
            "%m/%d/%Y"
        )
        payload = {
            "form_filler": "mother",
            "child_dob": now,
            "sex": "M",
            "birth_weight_lb": "3.5",
            "birth_order": 1,
            "born_on_due_date": 0,
            "multi_birth_boolean": 0,
            "primary_caregiver": "mother",
            "mother_yob": 1966,
            "mother_education": 18,
            "annual_income": "25000-50000",
            "caregiver_info": "1",
            "other_languages_boolean": 0,
            "ear_infections_boolean": 0,
            "hearing_loss_boolean": 0,
            "vision_problems_boolean": 0,
            "illnesses_boolean": 0,
            "services_boolean": 0,
            "worried_boolean": 0,
            "learning_disability_boolean": 0,
        }
        response = self.client.post(self.url, payload)
        administration = Administration.objects.get(study=self.study)
        self.assertRedirects(
            response,
            reverse("administer_cdi_form", args=[administration.url_hash]),
            target_status_code=302,
        )
        administration.completedSurvey = True
        administration.save()
        url = reverse(
            "backpage-background-info",
            kwargs={
                "pk": administration.backgroundinfo.id,
            },
        )
        payload["btn-next"] = "Next"
        response = self.client.post(url, payload)
        self.assertRedirects(
            response,
            reverse("administer_cdi_form", args=[administration.url_hash]),
            target_status_code=302,
        )
        administration.completed = True
        administration.save()
        response = self.client.get(
            reverse("administration_summary_view", args=[administration.url_hash])
        )
        redirect_url = administration.study.redirect_url.replace(
            "{{source_id}}", str(administration.backgroundinfo.source_id)
        ).replace("{{event_id}}", str(administration.backgroundinfo.event_id))
        self.assertEquals(
            response.context["redirect_url"],
            redirect_url,
        )
