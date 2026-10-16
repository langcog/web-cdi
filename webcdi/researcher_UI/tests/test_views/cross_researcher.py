import datetime

from django.contrib.auth.models import User
from django.test import TestCase, tag
from django.urls import reverse
from django.utils import timezone

from researcher_UI.models import Administration, Instrument, Researcher, Study


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
