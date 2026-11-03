import datetime

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from researcher_UI.models import Administration, Instrument, Researcher, Study


class MigrationAnnouncementTest(TestCase):
    """Researchers see the move notice and changelog; parents filling in a form don't."""

    fixtures = [
        "researcher_UI/fixtures/researcher_UI_test_fixtures.json",
        "cdi_forms/fixtures/cdi_forms_test_fixtures.json",
    ]
    banner = 'id="wcdi-announcement"'

    def test_changelog_is_public_and_linked_from_the_footer(self):
        response = self.client.get(reverse("changelog"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "What stays the same")
        self.assertContains(
            self.client.get(reverse("about")),
            f'<a href="{reverse("changelog")}">What\'s new</a>',
        )

    def test_banner_on_public_and_console_pages_links_to_changelog(self):
        user = User.objects.create_user("announce", password="x-test-only")
        Researcher.objects.get_or_create(user=user)
        for url in [reverse("home"), reverse("about")]:
            response = self.client.get(url)
            self.assertContains(response, self.banner)
            self.assertContains(response, f'href="{reverse("changelog")}"')
        self.client.force_login(user)
        self.assertContains(self.client.get(reverse("researcher_ui:console")), self.banner)

    def test_parent_form_has_no_banner(self):
        user = User.objects.create_user("announce", password="x-test-only")
        study = Study.objects.create(
            researcher=user,
            name="announce group",
            instrument=Instrument.objects.get(language="English", form="WS"),
        )
        administration = Administration.objects.create(
            study=study,
            subject_id=1,
            repeat_num=1,
            url_hash="a" * 64,
            completed=False,
            due_date=timezone.now() + datetime.timedelta(days=14),
        )
        response = self.client.get(
            reverse("administer_cdi_form", args=[administration.url_hash]), follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.banner)
