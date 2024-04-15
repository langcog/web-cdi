import json
import logging

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from cdi_forms.models import BackgroundInfo
from researcher_UI.models import (Administration, Instrument, InstrumentFamily,
                                  Study)

logger = logging.getLogger("selenium")
logger.setLevel(logging.INFO)


class SourceAPIViewTest(TestCase):

    def setUp(self):
        user = User.objects.create_user(
            username="PaulMcCartney", password="PaulMcCartney"
        )

        instrument_family = InstrumentFamily.objects.create(
            name="Instrument Family Test Model", chargeable=False
        )

        instrument = Instrument.objects.create(
            name="Test Instrument",
            language="Test Language",
            form="Test Form",
            min_age=3,
            max_age=15,
            family=instrument_family,
        )

        study = Study.objects.create(
            researcher=user,
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

        background_info = BackgroundInfo.objects.create(
            administration=self.administration, age=12, source_id="123456"
        )

        self.url = reverse(
            "api:source_api",
            kwargs={"pk": study.id, "source_id": background_info.source_id},
        )

        self.payload = {"username": "PaulMcCartney", "password": "PaulMcCartney"}

    def test_source_api(self):
        response = self.client.generic("POST", self.url, json.dumps(self.payload))
        self.assertEqual(response.status_code, 200)


class EventAPIViewTest(TestCase):

    def setUp(self):
        user = User.objects.create_user(
            username="PaulMcCartney", password="PaulMcCartney"
        )

        instrument_family = InstrumentFamily.objects.create(
            name="Instrument Family Test Model", chargeable=False
        )

        instrument = Instrument.objects.create(
            name="Test Instrument",
            language="Test Language",
            form="Test Form",
            min_age=3,
            max_age=15,
            family=instrument_family,
        )

        study = Study.objects.create(
            researcher=user,
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

        background_info = BackgroundInfo.objects.create(
            administration=self.administration,
            age=12,
            source_id="123456",
            event_id="new event",
        )

        self.url = reverse(
            "api:event_api",
            kwargs={
                "pk": study.id,
                "source_id": background_info.source_id,
                "event_id": background_info.event_id,
            },
        )

        self.payload = {"username": "PaulMcCartney", "password": "PaulMcCartney"}

    def test_event_api(self):
        response = self.client.generic("POST", self.url, json.dumps(self.payload))
        self.assertEqual(response.status_code, 200)
