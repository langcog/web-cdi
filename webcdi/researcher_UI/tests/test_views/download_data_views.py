from django.test import TestCase, tag
from django.urls import reverse
from researcher_UI.models import Instrument, Study, Administration
from django.contrib.auth.models import User

from researcher_UI.tests import generate_fake_results

class PDFAdministrationDetailViewTest(TestCase):
    fixtures = [
        "researcher_UI/fixtures/researcher_UI_test_fixtures.json",
        "cdi_forms/fixtures/cdi_forms_test_fixtures.json",
    ]
    def setUp(self):
        
        self.user = User.objects.create_user(
            username="PaulMcCartney", password="PaulMcCartney"
        )

        instrument = Instrument.objects.filter(
            language="English",
            form="WS",
        )[0]

        self.study = Study.objects.create(
            researcher = self.user,
            instrument=instrument,
            min_age = instrument.min_age,
            max_age = instrument.max_age,
            name='Test Instrument 1'
        )

        instrument = Instrument.objects.filter(
            language="Dutch",
            form="WS",
        )[0]

        self.no_template_study  = Study.objects.create(
            researcher = self.user,
            instrument=instrument,
            min_age = instrument.min_age,
            max_age = instrument.max_age,
            name='Test Instrument 2'
        )

        generate_fake_results(self.study, 10)
        self.ids = ''
        for id in Administration.objects.filter(study=self.study).values('id'):
            if len(self.ids) > 0:
                self.ids += f'&id={id["id"]}'
            else:
                self.ids += f'?id={id["id"]}'
        
    def test_get(self):
        response = self.client.get(f'{reverse("researcher_ui:pdf_summary", kwargs={"pk": self.study.id})}{self.ids}')
        self.assertEqual(response.status_code, 200)

    def test_get_adjusted(self):
        response = self.client.get(f'{reverse("researcher_ui:pdf_summary_adjusted", kwargs={"pk": self.study.id})}{self.ids}')
        self.assertEqual(response.status_code, 200)

    def test_get_no_template(self):
        response = self.client.get(reverse("researcher_ui:pdf_summary", kwargs={'pk': self.no_template_study.id}))
        self.assertEqual(response.status_code, 302)