import csv
import io

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase, tag
from django.urls import reverse

from cdi_forms.cat_forms.models import CatResponse
from researcher_UI.models import Administration, Benchmark, Instrument, Study
from researcher_UI.tests import generate_fake_results
from researcher_UI.utils.clinical_report import clinical_template_name


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

    def page_texts(self, response):
        """The text of each page of the PDF, so a blank page shows up as ''."""
        return [
            "".join(
                box.text
                for box in page._page_box.descendants()
                if hasattr(box, "text")
            ).strip()
            for page in response.get_document().pages
        ]

    def report_url(self, study, admins):
        url = reverse("researcher_ui:pdf_summary", kwargs={"pk": study.id})
        return url + "?" + "&".join(f"id={a.pk}" for a in admins)

    def test_mixed_selection_reports_only_the_completed_without_blank_pages(self):
        # staging QA: "blank pages for the incomplete participants". The view
        # does leave those out; the blank page was the forced page break after
        # the last report, so 1 completed + 1 incomplete looked like one each.
        admins = list(Administration.objects.filter(study=self.study).order_by("id"))
        Administration.objects.filter(pk__in=[a.pk for a in admins[1:3]]).update(
            completed=False
        )
        for name, selected, expected in [
            ("1 completed + 1 incomplete", admins[:2], admins[:1]),
            ("2 completed + 2 incomplete", admins[:4], [admins[0], admins[3]]),
            ("1 completed", admins[:1], admins[:1]),
        ]:
            with self.subTest(name):
                response = self.client.get(self.report_url(self.study, selected))
                self.assertEqual(response.status_code, 200)
                self.assertEqual(
                    {a.pk for a in response.context_data["administrations"]},
                    {a.pk for a in expected},
                )
                pages = self.page_texts(response)
                self.assertEqual(len(pages), len(expected))
                self.assertTrue(all("Child ID" in page for page in pages), pages)

    def test_no_clinical_template_ends_in_a_blank_page(self):
        checked = []
        for instrument in Instrument.objects.order_by("name"):
            # the test fixtures have no benchmarks for Canadian English
            if not (
                clinical_template_name(instrument)
                and Benchmark.objects.filter(instrument=instrument).exists()
            ):
                continue
            checked.append(instrument.name)
            with self.subTest(instrument=instrument.name):
                study = Study.objects.create(
                    researcher=self.user, instrument=instrument,
                    min_age=instrument.min_age, max_age=instrument.max_age,
                    name=f"blank pages {instrument.name}",
                )
                generate_fake_results(study, 2)
                admins = list(Administration.objects.filter(study=study))
                Administration.objects.filter(pk=admins[1].pk).update(completed=False)
                if instrument.form in settings.CAT_FORMS:
                    CatResponse.objects.create(administration=admins[0], est_theta=0)
                pages = self.page_texts(self.client.get(self.report_url(study, admins)))
                self.assertTrue(pages)
                self.assertTrue(all(pages), f"blank page in {len(pages)}-page report")
        self.assertGreaterEqual(len(checked), 10)

    def test_only_incomplete_selected_message_is_shown_on_the_group_page(self):
        # staging QA: "refreshes the page with no message"
        admin = Administration.objects.filter(study=self.study).first()
        Administration.objects.filter(pk=admin.pk).update(completed=False)
        group_url = reverse("researcher_ui:console_study", kwargs={"pk": self.study.pk})
        for action in (
            "download-selected-summary",
            "download-selected",
            "download-selected-adjusted",
        ):
            with self.subTest(action=action):
                response = self.client.post(
                    # "search" is always posted by the group page's form
                    group_url, {action: action, "select_col": [admin.pk], "search": ""},
                    follow=True,
                )
                self.assertEqual(response.redirect_chain[0][0], f"{group_url}?search=")
                self.assertContains(response, "has been completed yet")
                self.assertContains(response, 'class="alert alert-info')

    def test_mixed_selection_csv_downloads(self):
        admins = list(Administration.objects.filter(study=self.study).order_by("id"))[:3]
        Administration.objects.filter(pk=admins[0].pk).update(completed=False)
        group_url = reverse("researcher_ui:console_study", kwargs={"pk": self.study.pk})
        for action in (
            "download-selected-summary",
            "download-selected",
            "download-selected-adjusted",
        ):
            with self.subTest(action=action):
                response = self.client.post(
                    group_url, {action: action, "select_col": [a.pk for a in admins]}
                )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response["Content-Type"], "text/csv")
                rows = list(csv.DictReader(io.StringIO(response.content.decode())))
                self.assertEqual(
                    {int(r["administration_id"]) for r in rows}, {a.pk for a in admins}
                )

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
