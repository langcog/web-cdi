import datetime
import re
from html.parser import HTMLParser

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from researcher_UI.forms import AddStudyForm
from researcher_UI.models import (Administration, Instrument, InstrumentFamily,
                                  Researcher, Study)


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


class ConsoleSearchTest(TestCase):
    """QA: search must match partially, keep its term and survive the POST redirect."""

    fixtures = ConsoleMarkupTest.fixtures

    def setUp(self):
        self.user = User.objects.create_user("search", password="x-test-only")
        Researcher.objects.get_or_create(user=self.user)
        self.study = Study.objects.create(
            researcher=self.user, name="search group",
            instrument=Instrument.objects.get(language="English", form="WS"),
        )
        for subject_id, lab_id, active in [
            (101, None, True),
            (102, None, True),
            (55, "ABC-7", True),
            (33, "A&B #3", True),
            (100, None, False),  # deleted administrations stay hidden
        ]:
            Administration.objects.create(
                study=self.study, subject_id=subject_id, local_lab_id=lab_id,
                repeat_num=1, url_hash=f"{subject_id:x}".rjust(64, "e"), completed=False,
                is_active=active, due_date=timezone.now() + datetime.timedelta(days=14),
            )
        self.url = reverse("researcher_ui:console_study", args=[self.study.pk])
        self.client.force_login(self.user)

    def found(self, response):
        return sorted(a.subject_id for a in response.context["study_administrations"].data)

    def search(self, term):
        return self.found(self.client.get(self.url, {"search": term}))

    def test_partial_match_on_subject_id(self):
        self.assertEqual(self.search("10"), [101, 102])
        self.assertEqual(self.search("101"), [101])

    def test_partial_case_insensitive_match_on_lab_id(self):
        self.assertEqual(self.search("abc"), [55])
        self.assertEqual(self.search("-7"), [55])

    def test_blank_search_shows_all(self):
        everyone = [33, 55, 101, 102]
        self.assertEqual(self.search(""), everyone)
        self.assertEqual(self.search("   "), everyone)
        self.assertEqual(self.found(self.client.get(self.url)), everyone)

    def test_like_wildcards_are_literal(self):
        self.assertEqual(self.search("%"), [])
        self.assertEqual(self.search("_"), [])

    def test_box_keeps_the_term(self):
        page = self.client.get(self.url, {"search": '10"><b>'})
        self.assertContains(page, 'name="search" value="10&quot;&gt;&lt;b&gt;"')

    def test_search_button_post_keeps_special_characters(self):
        page = self.client.post(self.url, {"search": "A&B #3"}, follow=True)
        self.assertEqual(self.found(page), [33])
        self.assertContains(page, 'name="search" value="A&amp;B #3"')

    def test_table_dates_are_unambiguous(self):
        created = Administration.objects.get(study=self.study, subject_id=101).created_date
        page = self.client.get(self.url).content.decode()
        self.assertIn(f">{created.strftime('%b %-d, %Y')}</time>", page)
        self.assertNotIn(f">{created.strftime('%-m/%-d/%y')}</time>", page)


class NavbarActiveTest(TestCase):
    """QA: the navbar highlighted Home on every page."""

    fixtures = ConsoleMarkupTest.fixtures

    def active_items(self, url):
        page = self.client.get(url)
        self.assertEqual(page.status_code, 200)
        return re.findall(
            r'<li class="nav-item active">\s*<a[^>]*>\s*([\w ]+?)\s*<', page.content.decode()
        )

    def test_active_item_follows_the_page(self):
        user = User.objects.create_user("nav", password="x-test-only")
        researcher, _ = Researcher.objects.get_or_create(user=user)
        study = Study.objects.create(
            researcher=user, name="nav group",
            instrument=Instrument.objects.get(language="English", form="WS"),
        )
        self.client.force_login(user)
        for url, expected in [
            (reverse("researcher_ui:console"), ["Home"]),
            (reverse("researcher_ui:console_study", args=[study.pk]), ["Home"]),
            (reverse("researcher_ui:add_study"), ["Home"]),
            (
                reverse("researcher_ui:researcher_add_instruments", kwargs={"pk": researcher.pk}),
                ["Instruments"],
            ),
            (reverse("documentation"), ["Documentation"]),
            (reverse("about"), ["About"]),
            (reverse("researcher_ui:profile"), []),
        ]:
            with self.subTest(url=url):
                self.assertEqual(self.active_items(url), expected)


class LicenceRequiredLabelTest(TestCase):
    """QA: testers couldn't tell which instruments need a Brookes access code."""

    fixtures = ConsoleMarkupTest.fixtures

    def setUp(self):
        self.user = User.objects.create_user("licence", password="x-test-only")
        self.researcher, _ = Researcher.objects.get_or_create(user=self.user)
        self.paid = Instrument.objects.get(language="English", form="WS")
        self.free = Instrument.objects.get(language="Dutch", form="WS")
        self.paid_family = InstrumentFamily.objects.create(name="Paid forms", chargeable=True)
        self.free_family = InstrumentFamily.objects.create(name="Free forms", chargeable=False)
        Instrument.objects.filter(pk=self.paid.pk).update(family=self.paid_family)
        Instrument.objects.filter(pk=self.free.pk).update(family=self.free_family)
        self.client.force_login(self.user)

    def test_instruments_page_lists_free_and_licensed_families(self):
        page = self.client.get(
            reverse("researcher_ui:researcher_add_instruments", kwargs={"pk": self.researcher.pk})
        )
        self.assertContains(page, "Paid forms (licence required)")
        self.assertContains(page, "Free forms")
        self.assertNotContains(page, "Free forms (licence required)")

    def test_create_group_dropdown_marks_licensed_instruments_only_in_the_label(self):
        self.researcher.allowed_instrument_families.add(self.paid_family, self.free_family)
        field = AddStudyForm(researcher=self.user).fields["instrument"]
        labels = {str(value): label for value, label in field.choices if value}
        self.assertEqual(
            labels,
            {
                str(self.paid.pk): f"{self.paid.verbose_name} (licence required)",
                str(self.free.pk): self.free.verbose_name,
            },
        )
