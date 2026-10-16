import datetime

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from researcher_UI.models import Administration, Instrument, Study

UNKNOWN = "0" * 64


class ParticipantUrlTest(TestCase):
    """#696: mistyped or stale participant links are 404s, not 500s, and
    HEAD requests (email link scanners) don't crash the form view."""

    fixtures = [
        "researcher_UI/fixtures/researcher_UI_test_fixtures.json",
        "cdi_forms/fixtures/cdi_forms_test_fixtures.json",
    ]

    def test_unknown_hash_is_404(self):
        for name, kwargs in [
            ("administer_cdi_form", {}),
            ("instructions", {}),
            ("update_administration", {}),
            ("update_administration_section", {"section": 1}),
            ("administration_summary_view", {}),
            ("contact", {}),
        ]:
            with self.subTest(view=name):
                url = reverse(name, kwargs={"hash_id": UNKNOWN, **kwargs})
                self.assertEqual(self.client.get(url).status_code, 404)

    def test_head_on_form_link_is_not_an_error(self):
        user = User.objects.create_user("head_test", password="x-test-only")
        study = Study.objects.create(
            researcher=user,
            name="HEAD",
            instrument=Instrument.objects.get(language="English", form="WS"),
        )
        admin = Administration.objects.create(
            study=study,
            subject_id=1,
            repeat_num=1,
            url_hash="a" * 64,
            completed=False,
            due_date=timezone.now() + datetime.timedelta(days=14),
        )
        response = self.client.head(
            reverse("administer_cdi_form", kwargs={"hash_id": admin.url_hash})
        )
        self.assertIn(response.status_code, (200, 302))
