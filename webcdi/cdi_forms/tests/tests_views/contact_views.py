import logging

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from cdi_forms.models import BackgroundInfo
from cdi_forms.views import AdministrationContactView
from researcher_UI.models import (Administration, Instrument, InstrumentFamily,
                                  Study)

logger = logging.getLogger("tests")
logger.setLevel(logging.INFO)


class AdministrationContactViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="test_user", password="secret")

        instrument_family = InstrumentFamily.objects.create(
            name="Instrument Family Test Model", chargeable=False
        )

        instrument = Instrument.objects.create(
            name="Test Instrument",
            language="English",
            form="Test Form",
            min_age=3,
            max_age=15,
            family=instrument_family,
        )

        study = Study.objects.create(
            researcher=self.user,
            name="Test Study Instance",
            instrument=instrument,
            redirect_url="https://redirect_url.com/redirect/{source_id}",
        )

        self.administration = Administration.objects.create(
            study=study,
            subject_id=1,
            repeat_num=1,
            url_hash="0123456789012345678901234567890123456789012345678901234567890123",
            completed=False,
            due_date=timezone.now(),
        )

        BackgroundInfo.objects.create(
            administration=self.administration, age=12, source_id="123456"
        )

        self.url = reverse("contact", kwargs={"hash_id": self.administration.url_hash})

    def test_get(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_post_isValid(self):
        self.client.force_login(self.user)
        payload = {
            "contact_name": "Test Contact",
            "contact_id": "http://some.url.path",
            "content": "This is what I want to say",
            "contact_email": "test@email.com",
        }
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 302)
