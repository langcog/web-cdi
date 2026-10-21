import csv
import io

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from researcher_UI.models import Administration, Instrument, Researcher, Study
from researcher_UI.tests import generate_fake_results


class SummaryDownloadTextTest(TestCase):
    """Blanking "nan"/"None" cells must not cut those letters out of real text
    (a substring replace turned "Fernanda" into "Ferda")."""

    fixtures = [
        "researcher_UI/fixtures/researcher_UI_test_fixtures.json",
        "cdi_forms/fixtures/cdi_forms_test_fixtures.json",
    ]

    def test_text_containing_nan_or_none_survives(self):
        user = User.objects.create_user("summary-text", password="x-test-only")
        Researcher.objects.get_or_create(user=user)
        study = Study.objects.create(
            researcher=user, name="NoneSuch group",
            instrument=Instrument.objects.get(language="English", form="WS"),
        )
        generate_fake_results(study, 1)
        admin = Administration.objects.filter(study=study, completed=True).first()
        admin.local_lab_id = "Fernanda"
        admin.save()
        call_command("update_summary_data", study_id=study.pk)
        self.client.force_login(user)
        response = self.client.post(
            reverse("researcher_ui:console_study", args=[study.pk]),
            {"download-summary-csv": "download-summary-csv"},
        )
        self.assertEqual(response.status_code, 200)
        rows = list(csv.DictReader(io.StringIO(response.content.decode())))
        self.assertEqual(rows[0]["local_lab_id"], "Fernanda")
        self.assertEqual(rows[0]["study_name"], "NoneSuch group")


class StudySpecificBackgroundColumnsTest(TestCase):
    """Columns asked only by particular studies' background forms (the
    Centiment and Argentine extras) appeared, empty, in every study's CSV."""

    fixtures = SummaryDownloadTextTest.fixtures

    def header_for(self, demographic_file):
        from researcher_UI.models import Demographic
        from researcher_UI.utils.background_header import get_background_header

        user = User.objects.create_user(f"bg-{demographic_file}", password="x-test-only")
        demographic, _ = Demographic.objects.get_or_create(
            name=demographic_file, path="/form_data/background_info/" + demographic_file
        )
        study = Study.objects.create(
            researcher=user, name=f"bg {demographic_file}",
            instrument=Instrument.objects.get(language="English", form="WS"),
            demographic=demographic,
        )
        return get_background_header(study)

    def test_extra_columns_only_for_forms_that_ask_them(self):
        ordinary = self.header_for("English_Split.json")
        self.assertNotIn("children_comforted", ordinary)
        self.assertNotIn("kindergarten_dpw", ordinary)
        self.assertIn("annual_income", ordinary)  # standard columns stay
        centiment = self.header_for("English_Centiment.json")
        self.assertIn("children_comforted", centiment)
