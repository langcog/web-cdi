import logging

from django.contrib.auth.models import User
from django.test import TestCase, tag
from django.urls import reverse

from researcher_UI.forms import AddPairedStudyForm
from researcher_UI.models import (Instrument, InstrumentFamily, Researcher,
                                  Study, Administration)
from researcher_UI.tests import generate_fake_results
from researcher_UI.tests.utils import random_password

logger = logging.getLogger("debug")


class ConsoleTest(TestCase):
    fixtures = [
        "researcher_UI/fixtures/researcher_UI_test_fixtures.json",
        "cdi_forms/fixtures/cdi_forms_test_fixtures.json",
    ]

    def setUp(self) -> None:
        super().setUp()
        self.password = random_password()
        self.user = User.objects.create_user(
            username="testuser", password=self.password
        )
        Researcher.objects.get_or_create(user=self.user)

        self.url = reverse("researcher_ui:console")

    def test_get(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)


class StudyCreateViewTest(TestCase):
    fixtures = [
        "researcher_UI/fixtures/researcher_UI_test_fixtures.json",
        "cdi_forms/fixtures/cdi_forms_test_fixtures.json",
    ]

    def setUp(self) -> None:
        super().setUp()
        self.password = random_password()
        self.user = User.objects.create_user(
            username="testuser", password=self.password
        )
        Researcher.objects.get_or_create(user=self.user)

        for counter in range(3):
            instrument = Instrument.objects.filter(form="WS").order_by("?")[0]
            study = Study.objects.create(
                researcher=self.user,
                name=f"Study {counter}",
                instrument=instrument,
                max_age=instrument.max_age,
                min_age=instrument.min_age,
            )
            generate_fake_results(study, 20)

        self.study = Study.objects.filter(researcher=self.user).order_by("?")[0]

        self.url = reverse("researcher_ui:console_study", kwargs={"pk": self.study.pk})

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

    def test_post(self):
        self.client.force_login(self.user)
        payload = {"study_group": "StudyGroup", "paired_studies": [self.study.id]}
        form = AddPairedStudyForm(data=payload)
        self.assertTrue(form.is_valid())

        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 302)

    def test_post_download_summary_csv(self):
        self.client.force_login(self.user)
        payload = {"download-summary-csv": True}

        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            str(response), '<HttpResponse status_code=200, "text/csv">'
        )

    def test_post_download_study_scoring(self):
        self.client.force_login(self.user)
        payload = {"download-study-scoring": True}

        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            str(response), '<HttpResponse status_code=200, "application/octet-stream">'
        )

    def test_post_download_links(self):
        self.client.force_login(self.user)
        administrations = Administration.objects.filter(study=self.study).values_list('id', flat=True)
        payload = {
            "download-links": True,
            "select_col": administrations
        }

        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            str(response), '<HttpResponse status_code=200, "text/csv">'
        )

    def test_post_download_data(self):
        self.client.force_login(self.user)
        administrations = Administration.objects.filter(study=self.study).values_list('id', flat=True)
        payload = {
            "download-study-csv": True,
            "select_col": administrations
        }

        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            str(response), '<HttpResponse status_code=200, "text/csv">'
        )

    def test_post_download_dictionary(self):
        self.client.force_login(self.user)
        administrations = Administration.objects.filter(study=self.study).values_list('id', flat=True)
        payload = {
            "download-dictionary": True,
            "select_col": administrations
        }

        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            str(response), '<HttpResponse status_code=200, "text/csv">'
        )


class AdminNewTest(TestCase):
    def setUp(self):
        self.password = random_password()
        self.user = User.objects.create_user(
            username="testuser", password=self.password
        )
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


class OverflowTest(TestCase):
    def setUp(self):
        self.password = random_password()
        self.user = User.objects.create_user(
            username="testuser", password=self.password
        )
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
        self.url = reverse("researcher_ui:overflow", kwargs={"pk": self.study.pk})
        self.invalid_payload = {
            "name": "TestStudy",
        }
        self.payload = {"new_subject_ids": [1, 2, 3], "autogenerate_count": ""}

    def test_get(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_post_is_inValid(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, self.payload)
        self.assertEqual(response.status_code, 405)
