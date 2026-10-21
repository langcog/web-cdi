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
