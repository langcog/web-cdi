from django.contrib.auth.models import User
from django.test import TestCase, tag
from django.urls import reverse

from researcher_UI.models import Administration, Instrument, Study
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
        # the clinical PDF exposes child data; the view now requires the
        # owning researcher to be logged in
        self.client.force_login(self.user)

        instrument = Instrument.objects.filter(
            language="English",
            form="WS",
        )[0]

        self.study = Study.objects.create(
            researcher=self.user,
            instrument=instrument,
            min_age=instrument.min_age,
            max_age=instrument.max_age,
            name="Test Instrument 1",
        )

        instrument = Instrument.objects.filter(
            language="Dutch",
            form="WS",
        )[0]

        self.no_template_study = Study.objects.create(
            researcher=self.user,
            instrument=instrument,
            min_age=instrument.min_age,
            max_age=instrument.max_age,
            name="Test Instrument 2",
        )

        generate_fake_results(self.study, 10)
        self.ids = ""
        for id in Administration.objects.filter(study=self.study).values("id"):
            if len(self.ids) > 0:
                self.ids += f'&id={id["id"]}'
            else:
                self.ids += f'?id={id["id"]}'

    def test_get(self):
        response = self.client.get(
            f'{reverse("researcher_ui:pdf_summary", kwargs={"pk": self.study.id})}{self.ids}'
        )
        self.assertEqual(response.status_code, 200)

    def test_get_adjusted(self):
        response = self.client.get(
            f'{reverse("researcher_ui:pdf_summary_adjusted", kwargs={"pk": self.study.id, "adjusted": True})}{self.ids}'
        )
        self.assertEqual(response.status_code, 200)

    def test_get_no_template(self):
        response = self.client.get(
            reverse(
                "researcher_ui:pdf_summary", kwargs={"pk": self.no_template_study.id}
            )
        )
        self.assertEqual(response.status_code, 302)

    def test_anonymous_is_redirected(self):
        # child data must not be reachable without logging in
        self.client.logout()
        response = self.client.get(
            f'{reverse("researcher_ui:pdf_summary", kwargs={"pk": self.study.id})}{self.ids}'
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login", response.url)

    def test_other_researcher_cannot_access(self):
        # a logged-in researcher cannot read another researcher's study
        other = User.objects.create_user(username="RingoStarr", password="RingoStarr")
        self.client.force_login(other)
        response = self.client.get(
            f'{reverse("researcher_ui:pdf_summary", kwargs={"pk": self.study.id})}{self.ids}'
        )
        self.assertEqual(response.status_code, 404)

    def test_no_completed_administrations_redirects_with_message(self):
        # a report of only incomplete administrations used to be a blank PDF
        pending = Administration.objects.create(
            study=self.study, subject_id=999, repeat_num=1, url_hash="f" * 64,
            completed=False, due_date=self.study.administration_set.first().due_date,
        )
        url = reverse("researcher_ui:pdf_summary", kwargs={"pk": self.study.id})
        response = self.client.get(f"{url}?id={pending.id}", follow=True)
        self.assertEqual(
            response.redirect_chain[0][0],
            reverse("researcher_ui:console_study", kwargs={"pk": self.study.id}),
        )
        self.assertContains(response, "has been completed yet")
    def test_adjusted_report_with_early_birth_but_no_weeks(self):
        # staging QA: early/late with no weeks recorded crashed the adjusted report (500)
        admin = Administration.objects.filter(study=self.study, completed=True).first()
        admin.backgroundinfo.early_or_late = "early"
        admin.backgroundinfo.due_date_diff = None
        admin.backgroundinfo.save()
        url = reverse(
            "researcher_ui:pdf_summary_adjusted", kwargs={"pk": self.study.id, "adjusted": True}
        )
        response = self.client.get(f"{url}?id={admin.id}")
        self.assertEqual(response.status_code, 200)
