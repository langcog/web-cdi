import json
import logging

from django.contrib.auth.models import User
from django.test import TestCase, tag
from django.urls import reverse

from researcher_UI.models import Instrument, Study
from researcher_UI.tests import generate_fake_results

logger = logging.getLogger("selenium")
logger.setLevel(logging.INFO)


class StudyAPIViewTest(TestCase):
    fixtures = [
        "researcher_UI/fixtures/researcher_UI_test_fixtures.json",
        "cdi_forms/fixtures/cdi_forms_test_fixtures.json",
    ]

    def setUp(self):
        self.user = User.objects.create_user(
            username="PaulMcCartney", password="PaulMcCartney"
        )
        self.invalid_user = User.objects.create_user(
            username="JohnLennon", password="JohnLennon"
        )

        instrument = Instrument.objects.filter(form__in=["WS", "WG"]).order_by("?")[0]
        print(instrument)
        self.study = Study.objects.create(
            researcher=self.user, name="Test Study Instance", instrument=instrument
        )

        self.url = reverse("api:study_api", kwargs={"pk": self.study.id})

        self.empty_study = Study.objects.create(
            researcher=self.user,
            name="Empty Test Study Instance",
            instrument=instrument,
        )
        self.empty_url = reverse("api:study_api", kwargs={"pk": self.empty_study.id})

        english_instrument = Instrument.objects.filter(
            language="English", form__in=["WS", "WG"]
        ).order_by("?")[0]
        self.english_study = Study.objects.create(
            researcher=self.user,
            name="English Test Study Instance",
            instrument=english_instrument,
        )
        self.english_url = reverse(
            "api:study_api", kwargs={"pk": self.english_study.id}
        )

        self.payload = {"username": "PaulMcCartney", "password": "PaulMcCartney"}

        self.invalid_payload = {"username": "JohnLennon", "password": "JohnLennon"}

        self.invalid_user_payload = {
            "username": "JohnLennon",
            "password": "PaulMcCartney",
        }

        generate_fake_results(self.study, 10)
        generate_fake_results(self.english_study, 10)

    def test_study_api(self):
        response = self.client.generic("POST", self.url, json.dumps(self.payload))
        self.assertEqual(response.status_code, 200)

    def test_english_study_api(self):
        response = self.client.generic(
            "POST", self.english_url, json.dumps(self.payload)
        )
        self.assertEqual(response.status_code, 200)

    def test_api_permission_denied(self):
        response = self.client.generic(
            "POST", self.url, json.dumps(self.invalid_payload)
        )
        self.assertEqual(response.status_code, 403)

    def test_api_invalid_user(self):
        response = self.client.generic(
            "POST", self.url, json.dumps(self.invalid_user_payload)
        )
        self.assertEqual(response.status_code, 401)

    def test_api_no_completed_administrations(self):
        response = self.client.generic("POST", self.empty_url, json.dumps(self.payload))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["Error"], "You must select at least 1 completed survey"
        )

    def test_api_force_fail(self):
        response = self.client.generic("POST", self.empty_url, json.dumps(self.payload))
        self.assertEqual(response.status_code, 302)
