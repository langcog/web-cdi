import logging
import os

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase, tag
from django.urls import reverse

from researcher_UI.forms import AddPairedStudyForm, AdminNewForm
from researcher_UI.models import (Administration, Instrument, InstrumentFamily,
                                  Researcher, Study)
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
            username="test_user", password=self.password
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
            username="test_user", password=self.password
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

        studies = Study.objects.filter(researcher=self.user).order_by("?")
        self.study = studies[0]
        self.delete_study = studies[1]

        self.url = reverse("researcher_ui:console_study", kwargs={"pk": self.study.pk})
        self.delete_url = reverse(
            "researcher_ui:console_study", kwargs={"pk": self.delete_study.pk}
        )

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

    def test_post_administer_selected(self):
        self.client.force_login(self.user)
        administrations = Administration.objects.filter(study=self.study).values_list(
            "id", flat=True
        )
        payload = {"administer-selected": True, "select_col": administrations}
        response = self.client.post(self.url, payload)
        self.assertRedirects(response, self.url)

    def test_post_delete_selected(self):
        self.client.force_login(self.user)
        administrations = Administration.objects.filter(study=self.study).values_list(
            "id", flat=True
        )[2]
        payload = {"delete-selected": True, "select_col": administrations}
        response = self.client.post(self.url, payload)
        self.assertRedirects(response, self.url)

    def test_post_dowloand_selected(self):
        self.client.force_login(self.user)
        administrations = Administration.objects.filter(study=self.study).values_list(
            "id", flat=True
        )
        payload = {"download-selected": True, "select_col": administrations}
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(str(response), '<HttpResponse status_code=200, "text/csv">')

    def test_post_dowloand_selected_adjusted(self):
        self.client.force_login(self.user)
        administrations = Administration.objects.filter(study=self.study).values_list(
            "id", flat=True
        )
        payload = {"download-selected-adjusted": True, "select_col": administrations}
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(str(response), '<HttpResponse status_code=200, "text/csv">')

    def test_post_download_summary_csv(self):
        self.client.force_login(self.user)
        payload = {"download-summary-csv": True}

        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(str(response), '<HttpResponse status_code=200, "text/csv">')

    def test_post_download_study_scoring(self):
        self.client.force_login(self.user)
        payload = {"download-study-scoring": True}

        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            str(response), '<HttpResponse status_code=200, "application/octet-stream">'
        )

    def test_post_download_study_scoring_selected(self):
        self.client.force_login(self.user)
        administrations = Administration.objects.filter(study=self.study).values_list(
            "id", flat=True
        )
        payload = {
            "download-study-scoring-selected": True,
            "select_col": administrations,
        }

        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            str(response), '<HttpResponse status_code=200, "application/octet-stream">'
        )

    def test_post_download_links(self):
        self.client.force_login(self.user)
        administrations = Administration.objects.filter(study=self.study).values_list(
            "id", flat=True
        )
        payload = {"download-links": True, "select_col": administrations}

        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(str(response), '<HttpResponse status_code=200, "text/csv">')

    def test_post_download_data(self):
        self.client.force_login(self.user)
        administrations = Administration.objects.filter(study=self.study).values_list(
            "id", flat=True
        )
        payload = {"download-study-csv": True, "select_col": administrations}

        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(str(response), '<HttpResponse status_code=200, "text/csv">')

    def test_post_download_data_adjusted(self):
        self.client.force_login(self.user)
        administrations = Administration.objects.filter(study=self.study).values_list(
            "id", flat=True
        )
        payload = {"download-study-csv-adjusted": True, "select_col": administrations}

        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(str(response), '<HttpResponse status_code=200, "text/csv">')

    def test_post_download_selected_summary(self):
        self.client.force_login(self.user)
        administrations = Administration.objects.filter(study=self.study).values_list(
            "id", flat=True
        )
        payload = {"download-selected-summary": True, "select_col": administrations}

        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(str(response), '<HttpResponse status_code=200, "text/csv">')

    def test_post_download_dictionary(self):
        self.client.force_login(self.user)
        administrations = Administration.objects.filter(study=self.study).values_list(
            "id", flat=True
        )
        payload = {"download-dictionary": True, "select_col": administrations}

        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(str(response), '<HttpResponse status_code=200, "text/csv">')

    def test_post_delete_study(self):
        self.client.force_login(self.user)
        payload = {
            "delete-study": True,
        }

        response = self.client.post(self.delete_url, payload)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.delete_url)


class AdminNewTest(TestCase):
    def setUp(self):
        self.password = random_password()
        self.user = User.objects.create_user(
            username="test_user", password=self.password
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

    def test_post_load_subject_ids_from_csv(self):
        self.client.force_login(self.user)
        PROJECT_ROOT = settings.BASE_DIR
        with open(
            os.path.realpath(f"{PROJECT_ROOT}/researcher_UI/tests/data/subject_ids.csv")
        ) as fp:
            payload = {
                "study": self.study.id,
                "subject-ids-csv": fp,
                "new_subject_ids": "",
                "autogenerate_count": "",
            }
            form = AdminNewForm(payload)
            self.assertTrue(form.is_valid())

            response = self.client.post(
                reverse("researcher_ui:administer_new", kwargs={"pk": self.study.id}),
                payload,
            )
        self.assertEqual(response.json()["stat"], "ok")
        self.assertEqual(
            response.json()["redirect_url"],
            f'{reverse("researcher_ui:console_study", kwargs={"pk": self.study.pk})}?sort=-created_date',
        )  # , status_code=200, target_status_code=302)
        administrations = Administration.objects.filter(study=self.study)
        self.assertEqual(len(administrations), 7)

    def test_post_load_subject_ids_from_csv_invalid_id(self):
        self.client.force_login(self.user)
        PROJECT_ROOT = settings.BASE_DIR
        with open(
            os.path.realpath(
                f"{PROJECT_ROOT}/researcher_UI/tests/data/subject_ids_with_header.csv"
            )
        ) as fp:
            payload = {
                "study": self.study.id,
                "subject-ids-csv": fp,
                "new_subject_ids": "",
                "autogenerate_count": "",
                "subject-ids-column": "",
            }
            form = AdminNewForm(payload)
            self.assertTrue(form.is_valid())

            response = self.client.post(
                reverse("researcher_ui:administer_new", kwargs={"pk": self.study.id}),
                payload,
            )
        self.assertEqual(response.json()["stat"], "error")
        self.assertEqual(
            response.json()["error_message"],
            "Non integer subject ids. Make sure first row is numeric\n",
        )

    def test_post_load_subject_ids_from_csv_with_header(self):
        self.client.force_login(self.user)
        PROJECT_ROOT = settings.BASE_DIR
        with open(
            os.path.realpath(
                f"{PROJECT_ROOT}/researcher_UI/tests/data/subject_ids_with_header.csv"
            )
        ) as fp:
            payload = {
                "study": self.study.id,
                "csv-header": True,
                "subject-ids-csv": fp,
                "new_subject_ids": "",
                "autogenerate_count": "",
                "subject-ids-column": "",
            }
            form = AdminNewForm(payload)
            self.assertTrue(form.is_valid())

            response = self.client.post(
                reverse("researcher_ui:administer_new", kwargs={"pk": self.study.id}),
                payload,
            )
        self.assertEqual(response.json()["stat"], "ok")
        self.assertEqual(
            response.json()["redirect_url"],
            f'{reverse("researcher_ui:console_study", kwargs={"pk": self.study.pk})}?sort=-created_date',
        )  # , status_code=200, target_status_code=302)
        administrations = Administration.objects.filter(study=self.study)
        self.assertEqual(len(administrations), 7)

    def test_post_load_subject_ids_from_csv_with_header_and_column_header(self):
        self.client.force_login(self.user)
        PROJECT_ROOT = settings.BASE_DIR
        with open(
            os.path.realpath(
                f"{PROJECT_ROOT}/researcher_UI/tests/data/subject_ids_with_header.csv"
            )
        ) as fp:
            payload = {
                "study": self.study.id,
                "csv-header": True,
                "subject-ids-column": "header",
                "subject-ids-csv": fp,
                "new_subject_ids": "",
                "autogenerate_count": "",
            }
            form = AdminNewForm(payload)
            self.assertTrue(form.is_valid())

            response = self.client.post(
                reverse("researcher_ui:administer_new", kwargs={"pk": self.study.id}),
                payload,
            )
        self.assertEqual(response.json()["stat"], "ok")
        self.assertEqual(
            response.json()["redirect_url"],
            f'{reverse("researcher_ui:console_study", kwargs={"pk": self.study.pk})}?sort=-created_date',
        )  # , status_code=200, target_status_code=302)
        administrations = Administration.objects.filter(study=self.study)
        self.assertEqual(len(administrations), 7)

    def test_post_autogenerate_10(self):
        self.client.force_login(self.user)
        PROJECT_ROOT = settings.BASE_DIR

        payload = {
            "study": self.study.id,
            "new_subject_ids": "",
            "autogenerate_count": 10,
        }
        form = AdminNewForm(payload)
        self.assertTrue(form.is_valid())

        response = self.client.post(
            reverse("researcher_ui:administer_new", kwargs={"pk": self.study.id}),
            payload,
        )

        self.assertEqual(response.json()["stat"], "ok")
        self.assertEqual(
            response.json()["redirect_url"],
            f'{reverse("researcher_ui:console_study", kwargs={"pk": self.study.pk})}?sort=-created_date',
        )  # , status_code=200, target_status_code=302)
        administrations = Administration.objects.filter(study=self.study)
        self.assertEqual(len(administrations), 10)

    def test_post_autogenerate_greater_100(self):
        self.client.force_login(self.user)
        PROJECT_ROOT = settings.BASE_DIR

        payload = {
            "study": self.study.id,
            "new_subject_ids": "",
            "autogenerate_count": 101,
        }
        form = AdminNewForm(payload)
        self.assertTrue(form.is_valid())

        response = self.client.post(
            reverse("researcher_ui:administer_new", kwargs={"pk": self.study.id}),
            payload,
        )

        self.assertEqual(response.json()["stat"], "error")
        self.assertEqual(
            response.json()["error_message"],
            "Maximum autogenerated administrations is 100\n",
        )

    def test_post_empty_form(self):
        self.client.force_login(self.user)
        PROJECT_ROOT = settings.BASE_DIR

        payload = {
            "study": self.study.id,
            "new_subject_ids": "",
            "autogenerate_count": "",
        }
        form = AdminNewForm(payload)
        self.assertTrue(form.is_valid())

        response = self.client.post(
            reverse("researcher_ui:administer_new", kwargs={"pk": self.study.id}),
            payload,
        )

        self.assertEqual(response.json()["stat"], "error")
        self.assertEqual(response.json()["error_message"], "Form is empty\n")


class OverflowTest(TestCase):
    def setUp(self):
        self.password = random_password()
        self.user = User.objects.create_user(
            username="test_user", password=self.password
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
