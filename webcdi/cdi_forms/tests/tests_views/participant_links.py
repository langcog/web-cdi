import datetime
import json

from django.contrib.auth.models import User
from django.test import TestCase, tag
from django.urls import resolve, reverse
from django.utils import timezone

from cdi_forms.models import BackgroundInfo, Instrument_Forms
from researcher_UI.models import (Administration, Demographic, Instrument,
                                  Study, administration_data)
from researcher_UI.utils.random_url_generator import random_url_generator

UNKNOWN_HASH = "0" * 64
ANSWER = "seeded answer text"


def background_payload(**extra):
    dob = (datetime.datetime.now() - datetime.timedelta(days=500)).strftime("%m/%d/%Y")
    return {
        "form_filler": "father",
        "child_dob": dob,
        "sex": "M",
        "birth_weight_lb": "3.5",
        "birth_order": 1,
        "born_on_due_date": 0,
        "multi_birth_boolean": 0,
        "primary_caregiver": "mother",
        "mother_yob": 1966,
        "mother_education": 18,
        "annual_income": "25000-50000",
        "caregiver_info": "1",
        "other_languages_boolean": 0,
        "ear_infections_boolean": 0,
        "hearing_loss_boolean": 0,
        "vision_problems_boolean": 0,
        "illnesses_boolean": 0,
        "services_boolean": 0,
        "worried_boolean": 0,
        "learning_disability_boolean": 0,
        **extra,
    }


class ParticipantLinkTestCase(TestCase):
    fixtures = [
        "researcher_UI/fixtures/researcher_UI_test_fixtures.json",
        "cdi_forms/fixtures/cdi_forms_test_fixtures.json",
    ]

    def setUp(self):
        self.researcher = User.objects.create_user(
            username="link_test_researcher", password="x-test-only"
        )

    def make_study(self, language="English", form="WS", name="Links", **kwargs):
        kwargs.setdefault(
            "demographic", Demographic.objects.get(name="English_Split.json")
        )
        return Study.objects.create(
            researcher=self.researcher,
            name=name,
            instrument=Instrument.objects.get(language=language, form=form),
            min_age=12,
            max_age=36,
            **kwargs,
        )

    def make_administration(self, study, **kwargs):
        return Administration.objects.create(
            study=study,
            subject_id=1,
            repeat_num=1,
            url_hash=random_url_generator(),
            completed=False,
            due_date=timezone.now() + datetime.timedelta(days=14),
            **kwargs,
        )


class ParticipantPagesByLinkTest(ParticipantLinkTestCase):
    """Participant pages are addressed by the administration's url_hash."""

    def setUp(self):
        super().setUp()
        self.study = self.make_study()
        self.administration = self.make_administration(self.study)
        self.hash = self.administration.url_hash
        self.background = BackgroundInfo.objects.create(
            administration=self.administration,
            age=20,
            sex="F",
            form_filler="mother",
            zip_code="941**",
        )
        item = Instrument_Forms.objects.filter(
            instrument=self.study.instrument, choices__isnull=True
        ).first()
        administration_data.objects.create(
            administration=self.administration, item_ID=item.itemID, value=ANSWER
        )

    def background_paths(self, identifier):
        return [
            f"/form/background/{identifier}/",
            f"/form/background/{identifier}/backpage/",
            f"/form/cat/background/{identifier}/",
            f"/form/cat/background-backpage/{identifier}/",
        ]

    def administration_paths(self, identifier):
        return [
            f"/form/administration/{identifier}/pdf/",
            f"/form/administration/{identifier}/view/",
        ]

    def test_background_pages_open_by_link(self):
        for path in self.background_paths(self.hash):
            with self.subTest(path=path.replace(self.hash, "<hash>")):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(
                    response.context["background_form"].instance, self.background
                )

    def test_answer_pages_open_by_link(self):
        response = self.client.get(f"/form/administration/{self.hash}/view/")
        self.assertContains(response, ANSWER)
        response = self.client.get(f"/form/administration/{self.hash}/pdf/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")

    def test_url_names_take_the_link(self):
        for name, expected in [
            ("background-info", f"/form/background/{self.hash}/"),
            ("backpage-background-info", f"/form/background/{self.hash}/backpage/"),
            ("cat_forms:background-info", f"/form/cat/background/{self.hash}/"),
            (
                "cat_forms:backpage-background-info",
                f"/form/cat/background-backpage/{self.hash}/",
            ),
            ("administration-pdf-view", f"/form/administration/{self.hash}/pdf/"),
            ("administration-view", f"/form/administration/{self.hash}/view/"),
        ]:
            with self.subTest(name=name):
                self.assertEqual(reverse(name, kwargs={"hash_id": self.hash}), expected)

    def test_row_ids_do_not_address_pages(self):
        paths = self.background_paths(self.background.pk) + self.administration_paths(
            self.administration.pk
        )
        for path in paths:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 404)

    def test_post_to_row_id_does_not_change_the_row(self):
        for path in self.background_paths(self.background.pk):
            with self.subTest(path=path):
                response = self.client.post(path, background_payload(**{"btn-next": "Finish"}))
                self.assertEqual(response.status_code, 404)
        self.background.refresh_from_db()
        self.administration.refresh_from_db()
        self.assertEqual(self.background.sex, "F")
        self.assertEqual(self.background.form_filler, "mother")
        self.assertFalse(self.administration.completed)

    def test_get_backpage_by_row_id_leaves_completion_alone(self):
        self.study.backpage_boolean = False
        self.study.save()
        response = self.client.get(f"/form/background/{self.background.pk}/backpage/")
        self.assertEqual(response.status_code, 404)
        self.administration.refresh_from_db()
        self.assertFalse(self.administration.completed)

    def test_incorrect_link_is_404(self):
        for path in self.background_paths(UNKNOWN_HASH) + self.administration_paths(
            UNKNOWN_HASH
        ):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 404)
        for path in self.background_paths(UNKNOWN_HASH):
            with self.subTest(path=path, method="POST"):
                self.assertEqual(
                    self.client.post(path, background_payload()).status_code, 404
                )

    def test_post_by_link_saves_to_that_row(self):
        for path in (
            f"/form/background/{self.hash}/",
            f"/form/cat/background/{self.hash}/",
        ):
            BackgroundInfo.objects.filter(pk=self.background.pk).update(
                sex="F", form_filler="mother"
            )
            with self.subTest(path=path.replace(self.hash, "<hash>")):
                response = self.client.post(path, background_payload())
                self.assertEqual(response.status_code, 200)
                self.background.refresh_from_db()
                self.assertEqual(self.background.sex, "M")
                self.assertEqual(self.background.form_filler, "father")

    def test_links_on_other_routes_still_resolve(self):
        for path, url_name in [
            ("/form/background/create/5/bypass/", "create-new-background-info"),
            ("/form/background/create/5/abc/", "create-new-background-info"),
            ("/form/background/create/5/bypass/abc/", "create-new-background-info"),
            ("/form/cat/background-create/5/abc/", "create-new-background-info"),
            (f"/form/administration/{self.hash}/instructions/", "instructions"),
            (f"/form/administration/{self.hash}/first-page/", "update_administration"),
            (f"/form/administration/{self.hash}/3/", "update_administration_section"),
            (
                f"/form/administration/{self.hash}/3/previous/",
                "update_administration_section_previous",
            ),
            (f"/form/administration/{self.hash}/summary/", "administration_summary_view"),
            (f"/form/administration/{self.hash}/contact/", "contact"),
        ]:
            with self.subTest(path=path.replace(self.hash, "<hash>")):
                self.assertEqual(resolve(path).url_name, url_name)

    def test_create_alone_is_not_a_link(self):
        self.assertEqual(self.client.get("/form/background/create/").status_code, 404)

    def test_korean_pdf_redirects_to_view_by_link(self):
        study = self.make_study(language="Korean", name="Korean Links")
        administration = self.make_administration(study)
        response = self.client.get(f"/form/administration/{administration.url_hash}/pdf/")
        self.assertRedirects(
            response, f"/form/administration/{administration.url_hash}/view/"
        )


class ParticipantFlowByLinkTest(ParticipantLinkTestCase):
    """The parent's whole path uses the link, from the first redirect to printing."""

    def test_regular_form(self):
        study = self.make_study()
        administration = self.make_administration(study)
        link = administration.url_hash
        fill = f"/form/fill/{link}/"
        background = f"/form/background/{link}/"
        backpage = f"/form/background/{link}/backpage/"
        instructions = f"/form/administration/{link}/instructions/"
        section = f"/form/administration/{link}/1/"
        summary = f"/form/administration/{link}/summary/"
        printable = f"/form/administration/{link}/pdf/"

        self.assertRedirects(self.client.get(fill), background)

        response = self.client.post(background, background_payload(**{"btn-next": "Next"}))
        self.assertRedirects(response, fill, target_status_code=302)
        self.assertRedirects(self.client.get(fill), instructions)
        self.assertContains(self.client.get(instructions), f'href="{background}"')

        response = self.client.post(section, {"btn-back": True})
        self.assertRedirects(response, background)

        response = self.client.post(section, {"btn-submit": True})
        self.assertRedirects(response, backpage)
        self.assertRedirects(self.client.get(fill), backpage)

        response = self.client.post(
            backpage, background_payload(**{"btn-next": "Finish"})
        )
        self.assertRedirects(response, fill, target_status_code=302)
        self.assertRedirects(self.client.get(fill), summary)

        self.assertContains(self.client.get(summary), f'href="{printable}"')
        self.assertEqual(self.client.get(printable).status_code, 200)

    def test_background_next_from_form_posts(self):
        # administer_cdi_form sends these form markers to the background pages
        study = self.make_study()
        administration = self.make_administration(study)
        BackgroundInfo.objects.create(administration=administration, age=20)
        link = administration.url_hash
        fill = f"/form/fill/{link}/"
        self.assertRedirects(
            self.client.post(fill, {"background-info-form": "1"}),
            f"/form/background/{link}/",
        )
        self.assertRedirects(
            self.client.post(fill, {"back-page": "1"}),
            f"/form/background/{link}/backpage/",
        )

    @tag("cat")
    def test_cat_form(self):
        study = self.make_study(form="CAT", name="CAT Links")
        administration = self.make_administration(study)
        link = administration.url_hash
        fill = f"/form/cat/fill/{link}/"
        cat_background = f"/form/cat/background/{link}/"
        cat_backpage = f"/form/cat/background-backpage/{link}/"

        self.assertRedirects(self.client.get(fill), f"/form/background/{link}/")

        response = self.client.post(
            cat_background, background_payload(**{"btn-next": "Next"})
        )
        self.assertRedirects(response, f"/form/fill/{link}/", target_status_code=302)
        self.assertContains(self.client.get(fill), "webcdi-cat.js")

        self.assertRedirects(self.client.post(fill, {"btn-back": "1"}), cat_background)

        response = self.client.post(
            f"/form/cat/answer/{link}/",
            json.dumps(
                {
                    "index": 326,
                    "definition": "leg",
                    "response": True,
                    "est_theta": 0.6,
                    "done": True,
                }
            ),
            content_type="application/json",
        )
        self.assertTrue(response.json()["completed"])
        self.assertRedirects(
            self.client.get(fill), f"/form/background/{link}/backpage/"
        )

        self.assertEqual(self.client.get(cat_backpage).status_code, 200)
        response = self.client.post(
            cat_backpage, background_payload(**{"btn-next": "Finish"})
        )
        self.assertRedirects(response, f"/form/fill/{link}/", target_status_code=302)
        administration.refresh_from_db()
        self.assertTrue(administration.completed)
        self.assertEqual(self.client.get(fill).status_code, 200)
