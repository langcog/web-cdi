import logging
import os

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase, tag
from django.urls import reverse

from researcher_UI.forms import AdminNewForm
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
        # not sure this is testing anything
        self.client.force_login(self.user)
        payload = {
            "study_group": "StudyGroup",
            "paired_studies": [self.study.id, self.delete_study.id],
        }

        response = self.client.post(self.url, payload)
        self.assertRedirects(
            response, reverse("researcher_ui:console_study", args=(self.study.pk,))
        )

    def test_search(self):
        self.client.force_login(self.user)
        payload = {"search": 1}

        # test search on subject_id
        response = self.client.post(f"{self.url}?search=1", payload, follow=True)
        self.assertRedirects(response, f"{self.url}?search=1")

        # test search on local_lab_id
        administration = Administration.objects.filter(study=self.study)[0]
        some_string = random_password
        administration.local_lab_id = some_string
        administration.save()
        payload = {"search": some_string}
        response = self.client.post(
            f"{self.url}?search={some_string}", payload, follow=True
        )
        self.assertRedirects(response, f"{self.url}?search={some_string}")

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

    def test_post_download_dictionary_english(self):
        # English WS/WG take the footer branch; setUp's random instrument rarely hits it
        study = Study.objects.create(
            researcher=self.user,
            name="English dictionary",
            instrument=Instrument.objects.get(name="English_WS"),
        )
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("researcher_ui:console_study", kwargs={"pk": study.pk}),
            {"download-dictionary": True},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")

    def test_post_delete_study(self):
        self.client.force_login(self.user)
        payload = {
            "delete-study": True,
        }

        response = self.client.post(self.delete_url, payload)
        self.assertEqual(response.status_code, 302)
        # deleting a group lands on the dashboard, not the deleted group's page
        self.assertRedirects(response, reverse("researcher_ui:console"))
        self.delete_study.refresh_from_db()
        self.assertFalse(self.delete_study.active)


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

    def test_post_rejects_zero_padded_ids(self):
        # #569: "007" would be stored as 7, silently changing the researcher's id
        from django.core.files.uploadedfile import SimpleUploadedFile

        from researcher_UI.utils.admin_new import ZERO_PADDED_MESSAGE

        self.client.force_login(self.user)
        typed = {"new_subject_ids": "8 007", "autogenerate_count": ""}
        csv = {
            "subject-ids-csv": SimpleUploadedFile("ids.csv", b"8\n007\n"),
            "new_subject_ids": "",
            "autogenerate_count": "",
        }
        for name, payload in {"typed": typed, "csv": csv}.items():
            with self.subTest(input=name):
                response = self.client.post(self.url, payload)
                self.assertEqual(response.json()["stat"], "error")
                self.assertEqual(response.json()["error_message"], ZERO_PADDED_MESSAGE)
        self.assertFalse(Administration.objects.filter(study=self.study).exists())

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


class CdiFormatDownloadTest(TestCase):
    """CDI-format (zip) download for instruments with both item-ID styles.

    #649: the export looked for a column named "item_1", but Argentine Spanish
    WS names its items "item1", so the download crashed for that instrument
    (and intermittently in CI, where setUp picks a random WS instrument).
    """

    fixtures = [
        "researcher_UI/fixtures/researcher_UI_test_fixtures.json",
        "cdi_forms/fixtures/cdi_forms_test_fixtures.json",
    ]

    def test_each_item_id_style(self):
        import io
        import zipfile

        user = User.objects.create_user(username="cdi_fmt", password=random_password())
        Researcher.objects.get_or_create(user=user)
        self.client.force_login(user)
        for name in ["English_WS", "Argentine_Spanish_WS"]:
            with self.subTest(instrument=name):
                instrument = Instrument.objects.get(name=name)
                study = Study.objects.create(
                    researcher=user, name=f"fmt {name}", instrument=instrument,
                    min_age=instrument.min_age, max_age=instrument.max_age,
                )
                generate_fake_results(study, 2)
                response = self.client.post(
                    reverse("researcher_ui:console_study", kwargs={"pk": study.pk}),
                    {"download-study-scoring": True},
                )
                self.assertEqual(response.status_code, 200)
                archive = zipfile.ZipFile(io.BytesIO(response.content))
                self.assertEqual(len(archive.namelist()), 2)
                text = archive.read(archive.namelist()[0]).decode()
                # 34 fixed-width (25-char) admin/background fields, then the
                # vocabulary answers: one digit per item
                vocab = text[34 * 25:]
                self.assertGreater(len(vocab.strip()), 100)
                self.assertRegex(vocab.strip(), r"^[0-9\s.]+$")


class EmptySelectionDownloadTest(TestCase):
    """#675: posting a selected-rows download with no rows selected returned
    a 500. It should go back to the group page with a message instead."""

    fixtures = [
        "researcher_UI/fixtures/researcher_UI_test_fixtures.json",
        "cdi_forms/fixtures/cdi_forms_test_fixtures.json",
    ]

    def test_no_rows_selected(self):
        from django.contrib.messages import get_messages

        user = User.objects.create_user(username="nosel", password=random_password())
        Researcher.objects.get_or_create(user=user)
        self.client.force_login(user)
        for name in ["English_WS", "English_CAT"]:
            instrument = Instrument.objects.get(name=name)
            study = Study.objects.create(
                researcher=user, name=f"no selection {name}", instrument=instrument,
                min_age=instrument.min_age, max_age=instrument.max_age,
            )
            generate_fake_results(study, 2)
            url = reverse("researcher_ui:console_study", kwargs={"pk": study.pk})
            for action in [
                "download-selected",
                "download-selected-adjusted",
                "download-selected-summary",
                "download-study-scoring-selected",
                "download-links",
            ]:
                with self.subTest(instrument=name, action=action):
                    response = self.client.post(url, {action: True})
                    self.assertRedirects(response, url, fetch_redirect_response=False)
                    self.assertIn(
                        "Select at least one administration to download.",
                        [str(m) for m in get_messages(response.wsgi_request)],
                    )


class NoCompletedDownloadTest(TestCase):
    """#741: data and summary downloads of only incomplete administrations
    (selected, or a whole group with none completed) returned a 500. They
    should go back to the group page with a message instead. #757: the same
    for CAT groups and for the scoring-format (zip) download."""

    fixtures = [
        "researcher_UI/fixtures/researcher_UI_test_fixtures.json",
        "cdi_forms/fixtures/cdi_forms_test_fixtures.json",
    ]

    def test_no_completed_administrations(self):
        user = User.objects.create_user(username="nocompl", password=random_password())
        Researcher.objects.get_or_create(user=user)
        self.client.force_login(user)
        for name in ["English_WS", "English_CAT"]:
            self.check_no_completed(user, name)

    def check_no_completed(self, user, name):
        from django.contrib.messages import get_messages

        instrument = Instrument.objects.get(name=name)
        study = Study.objects.create(
            researcher=user, name=f"no completed {name}", instrument=instrument,
            min_age=instrument.min_age, max_age=instrument.max_age,
        )
        generate_fake_results(study, 2)
        Administration.objects.filter(study=study).update(completed=False)
        ids = [str(pk) for pk in Administration.objects.filter(study=study).values_list("pk", flat=True)]
        url = reverse("researcher_ui:console_study", kwargs={"pk": study.pk})
        for action, selected in [
            ("download-selected", True),
            ("download-selected-adjusted", True),
            ("download-selected-summary", True),
            ("download-study-scoring-selected", True),
            ("download-study-csv", False),
            ("download-study-csv-adjusted", False),
            ("download-summary-csv", False),
            ("download-study-scoring", False),
        ]:
            if "scoring" in action and instrument.form in settings.CAT_FORMS:
                continue  # refused for CAT forms; see CompletedNotReadyDownloadTest
            with self.subTest(instrument=name, action=action):
                payload = {action: True}
                if selected:
                    payload["select_col"] = ids
                response = self.client.post(url, payload)
                self.assertRedirects(response, url, fetch_redirect_response=False)
                self.assertIn(
                    "None of these administrations has been completed yet, so there is nothing to download.",
                    [str(m) for m in get_messages(response.wsgi_request)],
                )


class RepeatedItemLabelDownloadTest(TestCase):
    """#755: some forms use the same label for two items (Dutch WS "eten",
    Argentine Spanish WS "como"). The item CSV renamed item columns to labels
    and then selected by label, so the second item repeated the first item's
    answers. Repeats now get _1, _2, ... in form order, as in the API (#747).
    """

    fixtures = [
        "researcher_UI/fixtures/researcher_UI_test_fixtures.json",
        "cdi_forms/fixtures/cdi_forms_test_fixtures.json",
    ]

    def test_each_item_keeps_its_own_value(self):
        import csv
        import io

        from cdi_forms.models import Instrument_Forms
        from cdi_forms.views import get_model_header
        from researcher_UI.models import administration_data

        user = User.objects.create_user(username="labels", password=random_password())
        Researcher.objects.get_or_create(user=user)
        self.client.force_login(user)
        for name in ["Dutch_WS", "Argentine_Spanish_WS"]:
            with self.subTest(instrument=name):
                instrument = Instrument.objects.get(name=name)
                study = Study.objects.create(
                    researcher=user, name=f"labels {name}", instrument=instrument,
                    min_age=instrument.min_age, max_age=instrument.max_age,
                )
                generate_fake_results(study, 2)
                labels = {}
                for item_id, label in Instrument_Forms.objects.filter(
                    instrument=instrument
                ).values_list("itemID", "item"):
                    labels.setdefault(label, []).append(item_id)
                label, item_ids = next(
                    (k, v) for k, v in sorted(labels.items()) if len(v) > 1
                )
                administration = Administration.objects.filter(
                    study=study, completed=True
                ).first()
                values = {}
                for n, item_id in enumerate(item_ids):
                    values[item_id] = f"value {n}"
                    administration_data.objects.update_or_create(
                        administration=administration,
                        item_ID=item_id,
                        defaults={"value": values[item_id]},
                    )

                response = self.client.post(
                    reverse("researcher_ui:console_study", kwargs={"pk": study.pk}),
                    {"download-study-csv": True},
                )
                self.assertEqual(response.status_code, 200)
                rows = list(csv.reader(io.StringIO(response.content.decode())))
                header = rows[0]
                self.assertEqual(len(header), len(set(header)))
                row = next(
                    r for r in rows[1:]
                    if r[header.index("administration_id")] == str(administration.pk)
                )
                ordered = sorted(item_ids, key=get_model_header(name).index)
                keys = [label] + [f"{label}_{n}" for n in range(1, len(ordered))]
                self.assertEqual(
                    [row[header.index(k)] if k in header else None for k in keys],
                    [values[i] for i in ordered],
                )


class DownloadCleanupTest(TestCase):
    """#756: under pandas 3, `df[col].replace(..., inplace=True)` is a silent
    no-op, so count scores missing from the stored summaries came out blank
    instead of 0, and empty ethnicity/language lists came out as "[]"."""

    fixtures = [
        "researcher_UI/fixtures/researcher_UI_test_fixtures.json",
        "cdi_forms/fixtures/cdi_forms_test_fixtures.json",
    ]

    def setUp(self):
        from cdi_forms.models import BackgroundInfo
        from researcher_UI.models import InstrumentScore, SummaryData

        self.user = User.objects.create_user(
            username="cleanup", password=random_password()
        )
        Researcher.objects.get_or_create(user=self.user)
        self.client.force_login(self.user)
        instrument = Instrument.objects.get(name="English_WS")
        self.study = Study.objects.create(
            researcher=self.user, name="cleanup English_WS", instrument=instrument,
            min_age=instrument.min_age, max_age=instrument.max_age,
        )
        generate_fake_results(self.study, 2)
        self.administration = Administration.objects.filter(study=self.study).first()
        BackgroundInfo.objects.filter(administration=self.administration).update(
            child_ethnicity=[], other_languages=[]
        )
        # a count score with no stored value for anyone in the group (e.g. a
        # score added after these administrations were scored)
        self.count_title = (
            InstrumentScore.objects.filter(instrument=instrument, kind="count")
            .first()
            .title
        )
        SummaryData.objects.filter(
            administration__study=self.study, title=self.count_title
        ).delete()

    def download(self, action):
        import csv
        import io

        response = self.client.post(
            reverse("researcher_ui:console_study", kwargs={"pk": self.study.pk}),
            {action: True},
        )
        self.assertEqual(response.status_code, 200)
        rows = list(csv.DictReader(io.StringIO(response.content.decode())))
        return next(
            r for r in rows if r["administration_id"] == str(self.administration.pk)
        )

    def test_items_csv(self):
        row = self.download("download-study-csv")
        self.assertEqual(row[self.count_title], "0")
        self.assertEqual(row["child_ethnicity"], "")
        self.assertEqual(row["other_languages"], "")

    def test_summary_csv(self):
        row = self.download("download-summary-csv")
        self.assertEqual(row["child_ethnicity"], "")
        self.assertEqual(row["other_languages"], "")


class CompletedNotReadyDownloadTest(TestCase):
    """#757: downloads of completed administrations that are missing
    something the download expected returned a 500."""

    fixtures = [
        "researcher_UI/fixtures/researcher_UI_test_fixtures.json",
        "cdi_forms/fixtures/cdi_forms_test_fixtures.json",
    ]

    def setUp(self):
        self.user = User.objects.create_user(
            username="notready", password=random_password()
        )
        Researcher.objects.get_or_create(user=self.user)
        self.client.force_login(self.user)

    def make_study(self, name):
        instrument = Instrument.objects.get(name=name)
        study = Study.objects.create(
            researcher=self.user, name=f"not ready {name}", instrument=instrument,
            min_age=instrument.min_age, max_age=instrument.max_age,
        )
        generate_fake_results(study, 2)
        return study

    def test_cat_without_cat_responses(self):
        # completed CAT administrations with no CatResponse (e.g. finished
        # the background pages only) raised KeyError: 'administration_id'
        import csv
        import io

        from cdi_forms.cat_forms.models import CatResponse

        study = self.make_study("English_CAT")
        self.assertFalse(CatResponse.objects.filter(administration__study=study).exists())
        url = reverse("researcher_ui:console_study", kwargs={"pk": study.pk})
        for action in [
            "download-study-csv",
            "download-study-csv-adjusted",
            "download-summary-csv",
        ]:
            with self.subTest(action=action):
                response = self.client.post(url, {action: True})
                self.assertEqual(response.status_code, 200)
                rows = list(csv.DictReader(io.StringIO(response.content.decode())))
                self.assertEqual(len(rows), 2)
                self.assertTrue(all(r["est_theta"] == "" for r in rows))

        # one administration with a CAT response: its theta and words come
        # through, the other row stays blank
        administration = Administration.objects.filter(study=study).first()
        CatResponse.objects.create(
            administration=administration,
            administered_words=["ball"],
            administered_responses=[True],
            est_theta=0.5,
        )
        response = self.client.post(url, {"download-study-csv": True})
        self.assertEqual(response.status_code, 200)
        rows = list(csv.DictReader(io.StringIO(response.content.decode())))
        self.assertEqual(
            sorted((r["est_theta"], r["ball"]) for r in rows),
            [("", ""), ("0.5", "True")],
        )

    def test_french_cat_small_n_note(self):
        # #764: the French CAT download is meant to end with a note that its
        # by-sex norms rest on small Ns; since the pandas-2 port the row was
        # built and discarded. English CAT has no such note.
        import csv
        import io

        note = "NOTE:  The Ns for the by sex norms are small (some are <5)."
        for name, expected in [("French_French_CAT", True), ("English_CAT", False)]:
            study = self.make_study(name)
            url = reverse("researcher_ui:console_study", kwargs={"pk": study.pk})
            for action in ["download-study-csv", "download-summary-csv"]:
                with self.subTest(instrument=name, action=action):
                    response = self.client.post(url, {action: True})
                    self.assertEqual(response.status_code, 200)
                    rows = list(csv.DictReader(io.StringIO(response.content.decode())))
                    self.assertEqual(
                        [r["study_name"] for r in rows].count(note), int(expected)
                    )
                    if expected:
                        self.assertEqual(rows[-1]["study_name"], note)

    def test_links_download_for_every_form(self):
        # #764: the participant-links download was hidden for CAT (not CAT2)
        # groups; it needs no item list, so it is offered for every form
        import csv
        import io

        cat2 = Instrument.objects.get(name="English_CAT")
        cat2.pk = cat2.name = "English_CAT2"
        cat2.form = "CAT2"
        cat2.save()
        for name in ["English_WS", "English_CAT", "English_CAT2"]:
            with self.subTest(instrument=name):
                study = self.make_study(name)
                url = reverse("researcher_ui:console_study", kwargs={"pk": study.pk})
                page = self.client.get(url).content.decode()
                self.assertIn('name="download-links"', page)
                ids = [str(pk) for pk in Administration.objects.filter(study=study).values_list("pk", flat=True)]
                response = self.client.post(
                    url, {"download-links": True, "select_col": ids}
                )
                self.assertEqual(response.status_code, 200)
                rows = list(csv.DictReader(io.StringIO(response.content.decode())))
                self.assertEqual(len(rows), 2)
                self.assertTrue(all(r["link"].startswith("http") for r in rows))

    def test_summary_before_scoring(self):
        # completed but not yet scored (the scoring job runs every 10
        # minutes): back to the group page with a message, not a 500
        from django.contrib.messages import get_messages

        from researcher_UI.models import SummaryData

        study = self.make_study("English_WS")
        SummaryData.objects.filter(administration__study=study).delete()
        Administration.objects.filter(study=study).update(scored=False)
        ids = [str(pk) for pk in Administration.objects.filter(study=study).values_list("pk", flat=True)]
        url = reverse("researcher_ui:console_study", kwargs={"pk": study.pk})
        for payload in [
            {"download-summary-csv": True},
            {"download-selected-summary": True, "select_col": ids},
        ]:
            with self.subTest(payload=payload):
                response = self.client.post(url, payload)
                self.assertRedirects(response, url, fetch_redirect_response=False)
                self.assertTrue(
                    any(
                        "not been scored yet" in str(m)
                        for m in get_messages(response.wsgi_request)
                    )
                )

    def test_scoring_format_refused_for_cat_forms(self):
        # CAT forms have no item list, so the CDI scoring-program (zip)
        # download raised AssertionError in model_map (500); staging showed
        # it for English_CAT2. Both CAT form codes go back with a message.
        from django.contrib.messages import get_messages

        cat2 = Instrument.objects.get(name="English_CAT")
        cat2.pk = cat2.name = "English_CAT2"
        cat2.form = "CAT2"
        cat2.save()
        self.assertEqual(sorted(settings.CAT_FORMS), ["CAT", "CAT2"])
        for name in ["English_CAT", "English_CAT2"]:
            study = self.make_study(name)
            ids = [str(pk) for pk in Administration.objects.filter(study=study).values_list("pk", flat=True)]
            url = reverse("researcher_ui:console_study", kwargs={"pk": study.pk})
            for payload in [
                {"download-study-scoring": True},
                {"download-study-scoring-selected": True, "select_col": ids},
            ]:
                with self.subTest(instrument=name, payload=payload):
                    response = self.client.post(url, payload)
                    self.assertRedirects(response, url, fetch_redirect_response=False)
                    self.assertIn(
                        "The CDI scoring-program format is not available for CAT forms. Please use the items download.",
                        [str(m) for m in get_messages(response.wsgi_request)],
                    )

    def test_summary_for_form_without_scores(self):
        # Argentine Spanish WG has no scoring definitions, so it never has
        # summary scores; say so rather than "try again shortly"
        from django.contrib.messages import get_messages

        study = self.make_study("Argentine_Spanish_WG")
        url = reverse("researcher_ui:console_study", kwargs={"pk": study.pk})
        response = self.client.post(url, {"download-summary-csv": True})
        self.assertRedirects(response, url, fetch_redirect_response=False)
        self.assertIn(
            "This form has no summary scores. Please use the items download.",
            [str(m) for m in get_messages(response.wsgi_request)],
        )
