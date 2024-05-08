import logging
import datetime

from django.contrib.auth.models import User
from django.test import TestCase, tag
from django.urls import reverse
from django.utils import timezone

from cdi_forms.models import BackgroundInfo
from researcher_UI.models import Administration, Instrument, Study
from researcher_UI.utils.random_url_generator import random_url_generator

logger = logging.getLogger("tests")
logger.setLevel(logging.INFO)


class CreateBackgroundInfoViewTest(TestCase):
    fixtures = [
        "researcher_UI/fixtures/researcher_UI_test_fixtures.json",
        "cdi_forms/fixtures/cdi_forms_test_fixtures.json",
    ]

    def setUp(self):
        self.user = User.objects.create_user(username="test_user", password="secret")

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
                            "source_id": "123456",
                        },
                    )

    def test_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_invalid_post(self):
        now = (datetime.datetime.now() - datetime.timedelta(days=500)).strftime('%m/%d/%Y')
        payload = {
            'form_filler': 'mother',
            'child_dob': now,
            'sex': 'M',
            'birth_weight_lb': '3.5',
            'birth_order': 1,
            'born_on_due_date': 0,
            'multi_birth_boolean': 0,
            'primary_caregiver': 'mother',
            'mother_yob': 1966,
            'mother_education': 18,
            'annual_income': '25000-50000',
            'caregiver_info': '1',
            'other_languages_boolean': 0,
            'ear_infections_boolean': 0,
            'hearing_loss_boolean': 0,
            'vision_problems_boolean': 0,
            'illnesses_boolean': 0,
            'services_boolean': 0,
            'worried_boolean': 0,
            #'learning_disability_boolean': 0
        }
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 200)

    def test_valid_post(self):
        now = (datetime.datetime.now() - datetime.timedelta(days=500)).strftime('%m/%d/%Y')
        payload = {
            'form_filler': 'mother',
            'child_dob': now,
            'sex': 'M',
            'birth_weight_lb': '3.5',
            'birth_order': 1,
            'born_on_due_date': 0,
            'multi_birth_boolean': 0,
            'primary_caregiver': 'mother',
            'mother_yob': 1966,
            'mother_education': 18,
            'annual_income': '25000-50000',
            'caregiver_info': '1',
            'other_languages_boolean': 0,
            'ear_infections_boolean': 0,
            'hearing_loss_boolean': 0,
            'vision_problems_boolean': 0,
            'illnesses_boolean': 0,
            'services_boolean': 0,
            'worried_boolean': 0,
            'learning_disability_boolean': 0
        }
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 302)


class BackgroundInfoViewTest(TestCase):
    fixtures = [
        "researcher_UI/fixtures/researcher_UI_test_fixtures.json",
        "cdi_forms/fixtures/cdi_forms_test_fixtures.json",
    ]

    def setUp(self):
        self.user = User.objects.create_user(username="test_user", password="secret")

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
            administration=self.administration, age=12, source_id="123456"
        )

        self.url = reverse(
                        "background-info",
                        kwargs={'pk': background_info.pk }
                    )

    def test_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
