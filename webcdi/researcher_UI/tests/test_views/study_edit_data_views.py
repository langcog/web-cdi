import os

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase, tag
from django.urls import reverse

from researcher_UI.models import Instrument, Study
from researcher_UI.tests.utils import random_password

class ImportDataTest(TestCase):
    fixtures = [
        "researcher_UI/fixtures/researcher_UI_test_fixtures.json",
        "cdi_forms/fixtures/cdi_forms_test_fixtures.json",
    ]

    def setUp(self):
        self.password = random_password()
        self.user = User.objects.create_user(
            username="test_user", password=self.password
        )

        self.instrument = Instrument.objects.filter(
            language="English",
            form="WS",
        )[0]

        self.study = Study.objects.create(
            researcher=self.user,
            instrument=self.instrument,
            min_age=self.instrument.min_age,
            max_age=self.instrument.max_age,
            name="Test Instrument 1",
        )

        self.instrument_WG = Instrument.objects.filter(
            language="English",
            form="WG",
        )[0]

        self.study_WG = Study.objects.create(
            researcher=self.user,
            instrument=self.instrument_WG,
            min_age=self.instrument.min_age,
            max_age=self.instrument.max_age,
            name="Test Instrument WG 1",
        )

    def test_get(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("researcher_ui:import_data", kwargs={"pk": self.study.id})
        )
        self.assertEqual(response.status_code, 200)

    def test_post_WS(self):
        self.client.force_login(self.user)
        PROJECT_ROOT = settings.BASE_DIR
        with open(
            os.path.realpath(
                f"{PROJECT_ROOT}/researcher_UI/tests/data/import_data_WS.csv"
            )
        ) as fp:
            payload = {"study": self.study.id, "imported_file": fp, "csv-header": False}
            response = self.client.post(
                reverse("researcher_ui:import_data", kwargs={"pk": self.study.id}),
                payload,
            )
        self.assertEqual(response.json()["stat"], "ok")
        self.assertEqual(
            response.json()["redirect_url"],
            reverse("researcher_ui:console_study", kwargs={"pk": self.study.pk}),
        )  # , status_code=200, target_status_code=302)


    def test_post_WG(self):
        self.client.force_login(self.user)
        PROJECT_ROOT = settings.BASE_DIR
        with open(
            os.path.realpath(
                f"{PROJECT_ROOT}/researcher_UI/tests/data/import_data_WG.csv"
            )
        ) as fp:
            payload = {
                "study": self.study_WG.id,
                "imported_file": fp,
                "csv-header": False,
            }
            response = self.client.post(
                reverse("researcher_ui:import_data", kwargs={"pk": self.study_WG.id}),
                payload,
            )
        self.assertEqual(response.json()["stat"], "ok")
        self.assertEqual(
            response.json()["redirect_url"],
            reverse("researcher_ui:console_study", kwargs={"pk": self.study_WG.pk}),
        )  # , status_code=200, target_status_code=302)
