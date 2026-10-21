import datetime
from html.parser import HTMLParser

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from researcher_UI.models import Administration, Instrument, Researcher, Study


class FormNesting(HTMLParser):
    """Record nested <form> tags and which form each named button is in."""

    def __init__(self):
        super().__init__()
        self.stack, self.nested, self.button_form = [], 0, {}

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "form":
            self.nested += bool(self.stack)
            self.stack.append(attrs.get("id"))
        elif tag == "button" and attrs.get("name"):
            self.button_form[attrs["name"]] = self.stack[-1] if self.stack else None

    def handle_endtag(self, tag):
        if tag == "form" and self.stack:
            self.stack.pop()


class ConsoleMarkupTest(TestCase):
    """Browsers ignore a nested <form> tag but honour its </form>, which ended the
    study form early, so the delete confirmation posted nothing (staging QA)."""

    fixtures = [
        "researcher_UI/fixtures/researcher_UI_test_fixtures.json",
        "cdi_forms/fixtures/cdi_forms_test_fixtures.json",
    ]

    def test_no_nested_forms_and_delete_posts_the_study_form(self):
        user = User.objects.create_user("markup", password="x-test-only")
        Researcher.objects.get_or_create(user=user)
        study = Study.objects.create(
            researcher=user, name="markup group",
            instrument=Instrument.objects.get(language="English", form="WS"),
        )
        for n in (1, 2):
            Administration.objects.create(
                study=study, subject_id=n, repeat_num=1, url_hash=f"{n:x}".rjust(64, "e"),
                completed=False, due_date=timezone.now() + datetime.timedelta(days=14),
            )
        self.client.force_login(user)
        page = self.client.get(reverse("researcher_ui:console_study", args=[study.pk]))
        parsed = FormNesting()
        parsed.feed(page.content.decode())
        self.assertEqual(parsed.nested, 0)
        self.assertEqual(parsed.button_form.get("delete-selected"), "study-form")

    def test_clinical_report_menu_matches_instrument(self):
        # staging QA: instruments without a report template opened a tab that
        # redirected back with a message; now the menu says so up front
        user = User.objects.create_user("menu", password="x-test-only")
        Researcher.objects.get_or_create(user=user)
        self.client.force_login(user)
        for language, has_report in [("English", True), ("Dutch", False)]:
            with self.subTest(language=language):
                study = Study.objects.create(
                    researcher=user, name=f"menu {language}",
                    instrument=Instrument.objects.get(language=language, form="WS"),
                )
                page = self.client.get(reverse("researcher_ui:console_study", args=[study.pk]))
                self.assertEqual('id="id_select_clinical"' in page.content.decode(), has_report)
                self.assertEqual(
                    "not available for this instrument" in page.content.decode(), not has_report
                )
