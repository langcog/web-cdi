import csv
import datetime
import io
import json

from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.test import TestCase, tag
from django.urls import reverse
from django.utils import timezone

from researcher_UI.models import Administration, Instrument, Researcher, Study
from researcher_UI.tests import generate_fake_results
from researcher_UI.utils.console_helper.post_helper import SELECTED_DOWNLOADS


@tag("security")
class CrossResearcherAccessTest(TestCase):
    """A logged-in researcher must not read or change another researcher's
    groups, administrations or account settings by editing IDs in URLs."""

    fixtures = [
        "researcher_UI/fixtures/researcher_UI_test_fixtures.json",
        "cdi_forms/fixtures/cdi_forms_test_fixtures.json",
    ]

    def setUp(self):
        self.owner = User.objects.create_user("owner", password="x-test-only")
        self.other = User.objects.create_user("intruder", password="x-test-only")
        for u in (self.owner, self.other):
            Researcher.objects.get_or_create(user=u)
        self.study = Study.objects.create(
            researcher=self.owner,
            name="Owner's private group",
            instrument=Instrument.objects.get(language="English", form="WS"),
        )
        self.admin = Administration.objects.create(
            study=self.study,
            subject_id=7,
            repeat_num=1,
            url_hash="b" * 64,
            completed=False,
            due_date=timezone.now() + datetime.timedelta(days=14),
        )
        self.client.force_login(self.other)

    def owner_urls(self):
        return {
            "console_study": reverse("researcher_ui:console_study", args=[self.study.pk]),
            "administer_new": reverse("researcher_ui:administer_new", args=[self.study.pk]),
            "import_data": reverse("researcher_ui:import_data", args=[self.study.pk]),
            "rename_study": reverse("researcher_ui:rename_study", args=[self.study.pk]),
            "edit_study_new": reverse("researcher_ui:edit_study_new", args=[self.admin.pk]),
            "pdf_summary": reverse("researcher_ui:pdf_summary", args=[self.study.pk]) + f"?id={self.admin.pk}",
            "researcher_add_instruments": reverse(
                "researcher_ui:researcher_add_instruments",
                args=[Researcher.objects.get(user=self.owner).pk],
            ),
        }

    def test_get_is_refused(self):
        for name, url in self.owner_urls().items():
            with self.subTest(view=name):
                response = self.client.get(url)
                self.assertIn(response.status_code, (403, 404), url)
                self.assertNotContains(response, "Owner&#x27;s private group", status_code=response.status_code)

    def test_post_changes_nothing(self):
        before_admins = Administration.objects.filter(study=self.study).count()
        owner_researcher = Researcher.objects.get(user=self.owner)
        owner_researcher.allowed_instrument_families.set(
            [self.study.instrument.family]
        )
        before_families = set(owner_researcher.allowed_instrument_families.all())
        urls = self.owner_urls()
        attempts = {
            "console_study": {"delete-selected": "", "select_col": [self.admin.pk]},
            "administer_new": {"new-subject-ids": "99"},
            "import_data": {"study": self.study.pk},
            "rename_study": {"name": "hijacked"},
            "edit_study_new": {"subject_id": 123, "subject_id_old": 7},
            "researcher_add_instruments": {},
        }
        for name, data in attempts.items():
            with self.subTest(view=name):
                response = self.client.post(urls[name], data)
                # logged in, so a 302 would mean "saved, redirecting"
                self.assertIn(response.status_code, (403, 404), urls[name])
        self.study.refresh_from_db()
        self.admin.refresh_from_db()
        self.assertEqual(self.study.name, "Owner's private group")
        self.assertTrue(self.study.active)
        self.assertTrue(self.admin.is_active)
        self.assertEqual(self.admin.subject_id, 7)
        self.assertEqual(Administration.objects.filter(study=self.study).count(), before_admins)
        self.assertEqual(
            set(owner_researcher.allowed_instrument_families.all()), before_families
        )

    def test_owner_still_has_access(self):
        self.client.force_login(self.owner)
        for name in ["console_study", "administer_new", "rename_study", "researcher_add_instruments"]:
            with self.subTest(view=name):
                self.assertEqual(self.client.get(self.owner_urls()[name]).status_code, 200)

    def test_study_grouping_offers_and_accepts_only_own_studies(self):
        # #449: the "group studies" picker once listed every researcher's studies
        own = Study.objects.create(
            researcher=self.other,
            name="Intruder's own group",
            instrument=self.study.instrument,
        )
        url = reverse("researcher_ui:add_paired_study")
        response = self.client.get(url)
        self.assertContains(response, "Intruder&#x27;s own group")
        self.assertNotContains(response, "Owner&#x27;s private group")

        self.client.post(
            url, {"study_group": "hijack", "paired_studies": [self.study.pk, own.pk]}
        )
        self.study.refresh_from_db()
        self.assertEqual(self.study.study_group, "")

    # Rows are chosen by id in the request. Whatever ids arrive, an action on a
    # group applies only to that group's own administrations; other ids count
    # as not selected.

    def own_group(self, instrument="English_WS", name="Second researcher's group"):
        instrument = Instrument.objects.get(name=instrument)
        group = Study.objects.create(
            researcher=self.other, name=name, instrument=instrument,
            min_age=instrument.min_age, max_age=instrument.max_age,
        )
        generate_fake_results(group, 1)
        return group, Administration.objects.get(study=group)

    def row_in_first_group(self):
        generate_fake_results(self.study, 1)
        return Administration.objects.filter(study=self.study, completed=True).get()

    def post_selected(self, group, action, *rows):
        return self.client.post(
            reverse("researcher_ui:console_study", args=[group.pk]),
            {action: action, "select_col": [row.pk for row in rows]},
        )

    def test_selected_downloads_of_other_rows_count_as_no_selection(self):
        group, _ = self.own_group()
        other_row = self.row_in_first_group()
        url = reverse("researcher_ui:console_study", args=[group.pk])
        for action in SELECTED_DOWNLOADS:
            with self.subTest(action=action):
                response = self.post_selected(group, action, other_row)
                self.assertRedirects(response, url, fetch_redirect_response=False)
                self.assertIn(
                    "Select at least one administration to download.",
                    [str(m) for m in get_messages(response.wsgi_request)],
                )

    def test_selected_downloads_contain_only_the_current_groups_rows(self):
        group, own_row = self.own_group()
        other_row = self.row_in_first_group()
        for action in (
            "download-links",
            "download-selected",
            "download-selected-adjusted",
            "download-selected-summary",
        ):
            with self.subTest(action=action):
                response = self.post_selected(group, action, own_row, other_row)
                self.assertEqual(response.status_code, 200)
                rows = list(csv.DictReader(io.StringIO(response.content.decode())))
                self.assertEqual(
                    [int(row["administration_id"]) for row in rows], [own_row.pk]
                )

    def test_delete_selected_applies_to_the_current_group(self):
        group, own_row = self.own_group()
        other_row = self.row_in_first_group()
        self.post_selected(group, "delete-selected", own_row, other_row)
        own_row.refresh_from_db()
        other_row.refresh_from_db()
        self.assertFalse(own_row.is_active)
        self.assertTrue(other_row.is_active)

    def test_readminister_selected_applies_to_the_current_group(self):
        # a form with no licence requirement, so re-administering is allowed
        group, own_row = self.own_group(instrument="Dutch_WS")
        other_row = self.row_in_first_group()
        Administration.objects.filter(pk=other_row.pk).update(subject_id=500)
        self.post_selected(group, "administer-selected", own_row, other_row)
        self.assertEqual(
            sorted(
                Administration.objects.filter(study=group).values_list(
                    "subject_id", "repeat_num"
                )
            ),
            [(own_row.subject_id, 1), (own_row.subject_id, 2)],
        )

    def test_rows_in_the_researchers_other_group_are_not_selected(self):
        group, own_row = self.own_group()
        _, second_group_row = self.own_group(name="Second researcher's other group")
        self.post_selected(group, "delete-selected", second_group_row)
        second_group_row.refresh_from_db()
        self.assertTrue(second_group_row.is_active)

    def test_ids_of_no_administration_are_ignored(self):
        group, own_row = self.own_group(instrument="Dutch_WS")
        response = self.client.post(
            reverse("researcher_ui:console_study", args=[group.pk]),
            {
                "administer-selected": "administer-selected",
                "select_col": ["2147483647", "99999999999999999999"],
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Administration.objects.filter(study=group).count(), 1)

    def test_clinical_report_selection_applies_to_the_group_in_the_url(self):
        group, own_row = self.own_group()
        other_row = self.row_in_first_group()
        url = reverse("researcher_ui:pdf_summary", args=[group.pk])

        response = self.client.get(f"{url}?id={other_row.pk}")
        self.assertEqual(response.status_code, 302)

        response = self.client.get(f"{url}?id={other_row.pk}&id={own_row.pk}")
        self.assertEqual(
            [a.pk for a in response.context_data["administrations"]], [own_row.pk]
        )

    def test_clinical_report_ignores_ids_that_are_not_numbers(self):
        group, own_row = self.own_group()
        url = reverse("researcher_ui:pdf_summary", args=[group.pk])
        self.assertEqual(self.client.get(f"{url}?id=abc").status_code, 302)

    def test_edit_applies_to_the_rows_own_participant_id(self):
        # subject_id_old comes from the request; it must not pick another child
        group, own_row = self.own_group()
        sibling = Administration.objects.create(
            study=group, subject_id=50, repeat_num=1, url_hash="c" * 64,
            completed=False, due_date=timezone.now() + datetime.timedelta(days=14),
        )
        response = self.client.post(
            reverse("researcher_ui:edit_study_new", args=[own_row.pk]),
            {
                "subject_id": 60,
                "subject_id_old": sibling.subject_id,
                "local_lab_id": "",
                "opt_out": "None",
            },
        )
        self.assertEqual(response.status_code, 200)
        own_row.refresh_from_db()
        sibling.refresh_from_db()
        self.assertEqual((own_row.subject_id, sibling.subject_id), (60, 50))

    def test_administration_api_applies_to_the_study_in_the_url(self):
        group, own_row = self.own_group()
        other_row = self.row_in_first_group()
        payload = {"username": "intruder", "password": "x-test-only"}
        response = self.client.generic(
            "POST",
            reverse(
                "api:administration_api",
                kwargs={"pk": group.pk, "administration_id": other_row.pk},
            ),
            json.dumps(payload),
        )
        self.assertEqual(
            response.json(), {"Error": "You must select at least 1 completed survey"}
        )
