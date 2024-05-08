import logging

from django.contrib.auth.models import User
from django.test import TestCase, tag
from django.urls import reverse
from django.utils import timezone

from cdi_forms.models import BackgroundInfo
from researcher_UI.models import Administration, Instrument, Study
from researcher_UI.utils.random_url_generator import random_url_generator

logger = logging.getLogger("tests")
logger.setLevel(logging.INFO)


class InstructionDetailViewTest(TestCase):
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

        BackgroundInfo.objects.create(
            administration=self.administration, age=12, source_id="123456"
        )

        self.url = reverse(
            "instructions", kwargs={"hash_id": self.administration.url_hash}
        )

    def test_get(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
