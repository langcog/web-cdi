from django.contrib.auth.models import User
from django.test import TestCase, tag
from django.urls import reverse

from researcher_UI.models import Instrument, Study


@tag("url", "smoke")
class ConsolePageSmokeTest(TestCase):
    """Every researcher-facing page renders (200) with a content marker.

    The facelift rewrote the console templates (nav, footer, dashboard, study
    detail, toolbars, profile, instruments); these are the broad net that
    catches a template regression — missing {% load %}, bad {% url %},
    absent context variable — without needing a browser."""

    fixtures = [
        "researcher_UI/fixtures/researcher_UI_test_fixtures.json",
        "cdi_forms/fixtures/cdi_forms_test_fixtures.json",
    ]

    def setUp(self):
        # creating a User auto-creates its Researcher (post_save signal)
        self.user = User.objects.create_user(username="researcher", password="secret")
        self.client.force_login(self.user)
        instrument = Instrument.objects.filter(language="English", form="WS")[0]
        self.study = Study.objects.create(
            researcher=self.user,
            instrument=instrument,
            min_age=instrument.min_age,
            max_age=instrument.max_age,
            name="Smoke Study",
        )

    def assert_ok(self, url, marker=None):
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, f"{url} -> {response.status_code}")
        if marker:
            self.assertContains(response, marker)

    def test_dashboard(self):
        # empty-vs-grid state both render; the grid path exercises the counts
        self.assert_ok(reverse("researcher_ui:console"), "administration group")

    def test_study_detail(self):
        self.assert_ok(
            reverse("researcher_ui:console_study", kwargs={"pk": self.study.pk}),
            self.study.name,
        )

    def test_add_study(self):
        self.assert_ok(reverse("researcher_ui:add_study"))

    def test_profile(self):
        self.assert_ok(reverse("researcher_ui:profile"), "profile")

    def test_instruments(self):
        self.assert_ok(
            reverse(
                "researcher_ui:researcher_add_instruments",
                kwargs={"pk": self.user.researcher.pk},
            ),
            "instruments",
        )
