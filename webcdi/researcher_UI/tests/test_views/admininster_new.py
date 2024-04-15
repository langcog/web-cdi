import logging

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from researcher_UI.models import (Instrument, InstrumentFamily, Researcher,
                                  Study)
from researcher_UI.views import AdminNew

logger = logging.getLogger("selenium")
logger.setLevel(logging.INFO)


class AdminNewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="henry", password="poiuytre12")
        Researcher.objects.get_or_create(user=self.user)
        instrument_family, created = InstrumentFamily.objects.get_or_create(
            name="BigCats", chargeable=False
        )
        instrument, created = Instrument.objects.get_or_create(
            name="lion",
            language="lionish",
            form="roar",
            min_age=3,
            max_age=15,
            family=instrument_family,
        )
        self.user.researcher.allowed_instruments.add(instrument)
        self.user.researcher.allowed_instrument_families.add(instrument_family)
        self.study, created = Study.objects.get_or_create(
            name="TestStudy", researcher=self.user, instrument=instrument
        )
        self.screen = AdminNew
        self.url = reverse("researcher_ui:administer_new", kwargs={"pk": self.study.pk})
        self.invalid_payload = {
            "name": "TestStudy",
        }
        self.valid_payload = {"new_subject_ids": [1, 2, 3], "autogenerate_count": ""}

    def test_get(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    # TODO
    # Code needs changing to use form properly for this test
    def test_post_isInvalid(self):
        pass

    def test_post_isValid(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, self.valid_payload)
        self.assertEqual(response.status_code, 200)
