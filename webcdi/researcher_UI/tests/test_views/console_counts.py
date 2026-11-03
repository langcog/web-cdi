import html
import re

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from researcher_UI.models import Administration, Instrument, Researcher, Study


def visible_text(fragment):
    text = html.unescape(re.sub(r"<[^>]+>", " ", fragment))
    return re.sub(r"\s+", " ", text).strip()


class ActiveAdministrationCountsTest(TestCase):
    """staging QA: administrations are soft-deleted, and the counts on the
    dashboard card, the group header and the delete-group box included deleted
    ones; the header also counted only completed children, so it disagreed with
    the dashboard. Children = distinct subject_id among active administrations,
    everywhere."""

    fixtures = [
        "researcher_UI/fixtures/researcher_UI_test_fixtures.json",
        "cdi_forms/fixtures/cdi_forms_test_fixtures.json",
    ]

    def setUp(self):
        self.user = User.objects.create_user("counts", password="x-test-only")
        Researcher.objects.get_or_create(user=self.user)
        self.study = Study.objects.create(
            researcher=self.user,
            name="counts group",
            # not chargeable, so re-administering needs no Brookes code
            instrument=Instrument.objects.get(language="Dutch", form="WS"),
        )
        self.group_url = reverse("researcher_ui:console_study", args=[self.study.pk])
        self.client.force_login(self.user)

    def add(self, *subject_ids):
        response = self.client.post(
            reverse("researcher_ui:administer_new", args=[self.study.pk]),
            {
                "new_subject_ids": " ".join(str(s) for s in subject_ids),
                "autogenerate_count": "",
            },
        )
        self.assertEqual(response.json()["stat"], "ok")

    def admin(self, subject_id, repeat_num=1):
        return Administration.objects.get(
            study=self.study, subject_id=subject_id, repeat_num=repeat_num
        )

    def complete(self, *admins):
        Administration.objects.filter(pk__in=[a.pk for a in admins]).update(
            completed=True
        )

    def post_selected(self, action, *admins):
        self.client.post(
            self.group_url, {action: action, "select_col": [str(a.pk) for a in admins]}
        )

    def dashboard(self):
        page = self.client.get(reverse("researcher_ui:console")).content.decode()
        card = re.search(r'wcdi-study-card">(.*?)View group', page, re.S).group(1)
        return visible_text(card)

    def header(self):
        page = self.client.get(self.group_url).content.decode()
        block = re.search(r"</h1>(.*?)<label for=\"study-selector\"", page, re.S).group(1)
        return visible_text(block)

    def delete_box(self):
        page = self.client.get(
            reverse("researcher_ui:rename_study", args=[self.study.pk])
        ).content.decode()
        return (
            visible_text(re.search(r"and all (.*?) in it", page, re.S).group(1)),
            visible_text(
                re.search(r"<strong>([^<]*?administrations?)</strong> in it", page).group(1)
            ),
        )

    def assert_counts(self, completed, total, children):
        admins = "administration" if total == 1 else "administrations"
        kids = "child" if children == 1 else "children"
        summary = f"{completed} of {total} {admins} completed · {children} {kids}"
        with self.subTest("dashboard card", expected=summary):
            self.assertIn(summary, self.dashboard())
        with self.subTest("group header", expected=summary):
            self.assertIn(summary, self.header())
        with self.subTest("delete-group box", expected=total):
            self.assertEqual(self.delete_box(), (f"{total} {admins}", f"{total} {admins}"))

    def test_add_complete_readminister_delete(self):
        self.add(1, 2, 3)
        self.assert_counts(completed=0, total=3, children=3)

        self.complete(self.admin(1), self.admin(2))
        self.assert_counts(completed=2, total=3, children=3)

        # a second administration for the same child
        self.post_selected("administer-selected", self.admin(1))
        self.assert_counts(completed=2, total=4, children=3)

        # one child's only administration: the child goes too
        self.post_selected("delete-selected", self.admin(3))
        self.assert_counts(completed=2, total=3, children=2)

        # one of a child's two administrations: the child stays
        self.post_selected("delete-selected", self.admin(1, 1))
        self.assert_counts(completed=1, total=2, children=2)

        # a completed one, the child's only one
        self.post_selected("delete-selected", self.admin(2))
        self.assert_counts(completed=0, total=1, children=1)

        # adding a deleted child back counts them again
        self.add(3)
        self.assert_counts(completed=0, total=2, children=2)

    def test_everything_deleted(self):
        self.add(1, 2)
        self.post_selected("delete-selected", self.admin(1), self.admin(2))
        self.assertIn("0 of 0 administrations completed · 0 children", self.dashboard())
        self.assertNotIn("completed", self.header())
        self.assertEqual(self.delete_box(), ("0 administrations", "0 administrations"))

    def test_counts_are_per_group(self):
        other = Study.objects.create(
            researcher=self.user, name="another group", instrument=self.study.instrument
        )
        Administration.objects.create(
            study=other, subject_id=9, repeat_num=1, url_hash="c" * 64,
            completed=True, due_date=timezone.now(),
        )
        self.add(1)
        self.assertIn("0 of 1 administration completed · 1 child", self.header())
        self.assertEqual(self.delete_box(), ("1 administration", "1 administration"))
