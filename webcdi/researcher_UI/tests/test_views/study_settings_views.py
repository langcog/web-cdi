import logging

from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase, tag
from django.urls import reverse

from researcher_UI.forms import AddPairedStudyForm
from researcher_UI.models import (Instrument, InstrumentFamily, Researcher,
                                  Study)
from researcher_UI.tests import generate_fake_results
from researcher_UI.tests.utils import random_password
from researcher_UI.views import AddStudy


class AddStudyViewTest(TestCase):
    def setUp(self):
        self.password = random_password()
        self.user = User.objects.create_user(username="henry", password=self.password)
        Researcher.objects.get_or_create(user=self.user)
        instrument_family = InstrumentFamily.objects.create(
            name="BigCats", chargeable=False
        )
        instrument = Instrument.objects.create(
            name="lion",
            language="lionish",
            form="roar",
            min_age=3,
            max_age=15,
            family=instrument_family,
        )
        self.user.researcher.allowed_instruments.add(instrument)
        self.user.researcher.allowed_instrument_families.add(instrument_family)

        self.user.researcher.save()
        self.screen = AddStudy
        self.url = reverse("researcher_ui:add_study")
        self.invalid_payload = {
            "name": "TestStudy",
        }
        self.valid_payload = {
            "name": "TestStudy",
            "instrument": "lion",
            "researcher": self.user,
            "prefilled_data": 0,
            "birth_weight_units": "lb",
            "timing": 6,
            "participant_source_boolean": 0,
            "end_message": "standard",
            "gift_card_provider": "Amazon",
        }

    def test_get(self):
        request = RequestFactory().get(self.url)
        request.user = self.user
        response = self.screen.as_view()(request)
        self.assertEqual(response.status_code, 200)

    def test_post_isInvalid(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, self.invalid_payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["form"].errors["instrument"][0], "This field is required."
        )
        self.assertIn("researcher", response.context)

    def test_post_isValid(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, self.valid_payload)
        self.assertEqual(response.status_code, 302)


class AddPairedStudyTest(TestCase):
    fixtures = [
        "researcher_UI/fixtures/researcher_UI_test_fixtures.json",
        "cdi_forms/fixtures/cdi_forms_test_fixtures.json",
    ]

    def setUp(self) -> None:
        super().setUp()
        self.password = random_password()
        self.user = User.objects.create_user(username="henry", password=self.password)
        Researcher.objects.get_or_create(user=self.user)

        for counter in range(3):
            instrument = Instrument.objects.all().order_by("?")[0]
            study = Study.objects.create(
                researcher=self.user,
                name=f"Study {counter}",
                instrument=instrument,
                max_age=instrument.max_age,
                min_age=instrument.min_age,
            )
            generate_fake_results(study, 10)

        self.study = Study.objects.filter(researcher=self.user).order_by("?")[0]

        self.url = reverse("researcher_ui:add_paired_study")

    def test_get(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        self.client.force_login(self.user)
        payload = {"study_group": "StudyGroup", "paired_studies": [self.study.id]}
        form = AddPairedStudyForm(data=payload)
        self.assertTrue(form.is_valid())

        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 302)
