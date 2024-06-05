import logging

from django.contrib.auth.models import User
from django.test import TestCase, tag
from django.urls import reverse

from researcher_UI.models import Administration, Instrument, Study
from researcher_UI.tests import generate_fake_results

logger = logging.getLogger("tests")
logger.setLevel(logging.INFO)


class PDFAdministrationDetailViewTest(TestCase):
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
            redirect_url="https://redirect_url.com/redirect/{source_id}",
        )

    def test_get(self):
        self.client.force_login(self.user)
        generate_fake_results(self.study, 1)
        administration = Administration.objects.filter(completed=True)[0]
        url = reverse("administration-pdf-view", kwargs={"pk": administration.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_korean_get(self):
        instrument = Instrument.objects.get(language="Korean", form="WS")
        study = Study.objects.create(
            researcher=self.user,
            name="Korean Test Study Instance",
            instrument=instrument,
            redirect_url="https://redirect_url.com/redirect/{source_id}",
        )
        generate_fake_results(study, 1)
        administration = Administration.objects.filter(completed=True)[0]
        url = reverse("administration-pdf-view", kwargs={"pk": administration.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
