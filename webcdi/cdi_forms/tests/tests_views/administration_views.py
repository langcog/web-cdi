import datetime
import logging
from unittest import mock

from django.contrib.auth.models import User
from django.core import mail
from django.core.management import call_command
from django.db import connection
from django.test import TestCase, tag
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from cdi_forms.cat_forms.models import CatResponse
from cdi_forms.models import BackgroundInfo, Instrument_Forms
from researcher_UI.models import (Administration, Demographic, Instrument,
                                  PaymentCode, Study, administration_data)
from researcher_UI.tests import generate_fake_results
from researcher_UI.utils.random_url_generator import random_url_generator

logger = logging.getLogger("tests")
logger.setLevel(logging.INFO)


class AdministrationSummaryViewTest(TestCase):
    fixtures = [
        "researcher_UI/fixtures/researcher_UI_test_fixtures.json",
        "cdi_forms/fixtures/cdi_forms_test_fixtures.json",
    ]

    def setUp(self):
        self.user = User.objects.create_user(username="test_user", password="secret")

        instrument = Instrument.objects.get(
            language="English",
            form="WS",
        )

        self.study = Study.objects.create(
            researcher=self.user,
            name="Test Study Instance",
            instrument=instrument,
            redirect_url="https://example.com/redirect/{source_id}",
        )

        self.administration = Administration.objects.create(
            study=self.study,
            subject_id=1,
            repeat_num=1,
            url_hash=random_url_generator(),
            completed=False,
            due_date=timezone.now(),
        )

        BackgroundInfo.objects.create(
            administration=self.administration, age=12, source_id="123456"
        )

        self.url = reverse(
            "administration_summary_view",
            kwargs={"hash_id": self.administration.url_hash},
        )

    def test_get(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_completed_get(self):
        self.client.force_login(self.user)
        generate_fake_results(self.study, 1)
        administration = Administration.objects.filter(completed=True)[0]
        url = reverse(
            "administration_summary_view", kwargs={"hash_id": administration.url_hash}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_jquery_loads_before_bootstrap(self):
        # staging QA: "Show Me My Answers" did nothing because Bootstrap's JS
        # (which wires up the collapse toggle) ran before jQuery existed
        generate_fake_results(self.study, 1)
        administration = Administration.objects.filter(completed=True)[0]
        url = reverse(
            "administration_summary_view", kwargs={"hash_id": administration.url_hash}
        )
        page = self.client.get(url).content.decode()
        self.assertIn("Show my answers", page)  # the summary page, not "expired"
        self.assertLess(page.index("jquery-3.7.1.min.js"), page.index("bootstrap/bootstrap.min.js"))

    def complete_with_answers(self):
        """Completes the administration with every item answered with the
        first choice (or "yes" if it has none); returns the summary URL."""
        self.administration.completed = True
        self.administration.save()
        items = Instrument_Forms.objects.filter(
            instrument=self.study.instrument
        ).select_related("choices")
        administration_data.objects.bulk_create(
            administration_data(
                administration=self.administration,
                item_ID=item.itemID,
                value=(
                    item.choices.choice_set_en.split(";")[0].strip()
                    if item.choices
                    else "yes"
                ),
            )
            for item in items
        )
        return self.url

    def test_summary_queries_do_not_grow_with_answers(self):
        # staging QA: 15+ s to open a completed WS link, from one query per
        # answer and one per section (444 queries for ~400 answers)
        url = self.complete_with_answers()
        self.assertGreater(self.administration.administration_data_set.count(), 500)
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(
            len(queries), 15, "\n".join(q["sql"][:120] for q in queries)
        )

    def test_graph_data_counts(self):
        self.administration.completed = True
        self.administration.save()
        items = Instrument_Forms.objects.filter(
            instrument=self.study.instrument, item_type="word", category="sounds"
        ).order_by("item_order")
        answers = {items[0]: "produces", items[1]: "produces", items[2]: "understands"}
        phrase = Instrument_Forms.objects.filter(
            instrument=self.study.instrument
        ).exclude(item_type="word")[0]
        administration_data.objects.bulk_create(
            [
                administration_data(
                    administration=self.administration,
                    item_ID=item.itemID,
                    value=value,
                )
                for item, value in answers.items()
            ]
            # not a word: must not count towards any category
            + [
                administration_data(
                    administration=self.administration,
                    item_ID=phrase.itemID,
                    value="produces",
                ),
            ]
        )
        graph_data = self.client.get(self.url).context["graph_data"]
        self.assertEqual(graph_data["sounds"]["count"], items.count())
        self.assertEqual(graph_data["sounds"]["produces"], 2)
        self.assertEqual(graph_data["sounds"]["understands"], 3)
        self.assertEqual(sum(c["produces"] for c in graph_data.values()), 2)
        self.assertEqual(sum(c["understands"] for c in graph_data.values()), 3)

    def test_toggles_say_they_show_and_hide(self):
        # staging QA: the graph starts open, so "Graph My Data!" closed it;
        # the answers opened out of sight under padding-top:220px
        generate_fake_results(self.study, 1)
        administration = Administration.objects.filter(completed=True)[0]
        url = reverse(
            "administration_summary_view", kwargs={"hash_id": administration.url_hash}
        )
        page = self.client.get(url).content.decode()
        for label in [
            "Hide my graph",
            "Show my graph",
            "Show my answers",
            "Hide my answers",
        ]:
            self.assertIn(label, page)
        # initial states match what is open: graph open, answers closed
        self.assertIn(
            'href="#graph_data" data-toggle="collapse" role="button" aria-expanded="true"',
            page,
        )
        self.assertIn(
            'href="#filled_form" data-toggle="collapse" role="button" aria-expanded="false"',
            page,
        )
        self.assertNotIn("padding-top:220px", page)
        self.assertNotIn("height: 90vh", page)
        self.assertIn("shown.bs.collapse", page)

    def test_toggle_labels_are_translated(self):
        for language, form, label in [
            ("Spanish", "WS", "Ocultar mi gráfico"),
            ("French Quebec", "WS", "Masquer mes réponses"),
            ("Korean", "WS", "내 그래프 숨기기"),
        ]:
            with self.subTest(language=language):
                instrument = Instrument.objects.get(language=language, form=form)
                study = Study.objects.create(
                    researcher=self.user,
                    name=f"{language} Test Study",
                    instrument=instrument,
                    redirect_url="https://example.com/",
                )
                administration = Administration.objects.create(
                    study=study,
                    subject_id=1,
                    repeat_num=1,
                    url_hash=random_url_generator(),
                    completed=True,
                    due_date=timezone.now(),
                )
                BackgroundInfo.objects.create(administration=administration, age=20)
                item = Instrument_Forms.objects.filter(
                    instrument=instrument, choices__isnull=False
                ).first()
                # the answers toggle only appears when there are answers to show
                self.answer(
                    administration,
                    item.itemID,
                    item.choices.choice_set_en.split(";")[0].strip(),
                )
                response = self.client.get(
                    reverse(
                        "administration_summary_view",
                        kwargs={"hash_id": administration.url_hash},
                    )
                )
                self.assertContains(response, label)

    def answers_panel(self, url):
        page = self.client.get(url).content.decode()
        self.assertIn('id="filled_form"', page)
        return page.split('id="filled_form"')[1].split("</form>")[0]

    def completed_administration(self, instrument, **study_fields):
        study = Study.objects.create(
            researcher=self.user,
            name=f"{instrument.name} answers {Study.objects.count()}",
            instrument=instrument,
            redirect_url="https://example.com/",
            **study_fields,
        )
        administration = Administration.objects.create(
            study=study,
            subject_id=1,
            repeat_num=1,
            url_hash=random_url_generator(),
            completed=True,
            due_date=timezone.now(),
        )
        BackgroundInfo.objects.create(administration=administration, age=20)
        return administration

    def summary_url(self, administration):
        return reverse(
            "administration_summary_view", kwargs={"hash_id": administration.url_hash}
        )

    def answer(self, administration, item_id, value):
        administration_data.objects.create(
            administration=administration, item_ID=item_id, value=value
        )

    def test_show_my_answers_shows_the_answers(self):
        # the panel showed the background form, then "Form unavailable. Contact admin."
        # English WS: item_1 "baa baa" and item_2 "choo choo" are checkboxes
        instrument = self.study.instrument
        administration = self.completed_administration(instrument)
        words = Instrument_Forms.objects.filter(
            instrument=instrument, item_type="word"
        ).order_by("item_order")
        self.answer(administration, words[0].itemID, "produces")
        self.answer(administration, "item_760", "often")
        self.answer(administration, "item_example1", "doggy <script>go</script>")
        panel = self.answers_panel(self.summary_url(administration))
        self.assertIn(words[0].definition, panel)
        self.assertNotIn(words[1].definition, panel)  # not answered
        self.assertIn("often", panel)
        self.assertIn("Has your child begun to combine words yet?", panel)
        self.assertIn("doggy &lt;script&gt;go&lt;/script&gt;", panel)
        self.assertNotIn("Form unavailable", panel)

    def test_answers_panel_is_read_only(self):
        url = self.complete_with_answers()
        panel = self.answers_panel(url)
        for control in ["<input", "<select", "<textarea", "<button", "<form"]:
            self.assertNotIn(control, panel)
        # the background form said to enter a date of birth we don't store
        self.assertNotIn("Who is filling in the form?", panel)
        self.assertNotIn("Child DOB", panel)

    def test_answers_panel_off(self):
        url = self.complete_with_answers()
        self.study.show_my_answers_boolen = False
        self.study.save()
        response = self.client.get(url)
        self.assertNotContains(response, 'id="filled_form"')
        self.assertNotContains(response, "Show my answers")
        self.assertIsNone(response.context.get("answers"))

    def test_no_toggle_without_answers(self):
        administration = self.completed_administration(self.study.instrument)
        response = self.client.get(self.summary_url(administration))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Show my answers")
        self.assertNotContains(response, 'id="filled_form"')

    def test_answers_panel_on_every_item_form(self):
        for instrument in Instrument.objects.exclude(form="CAT"):
            with self.subTest(instrument=instrument.name):
                administration = self.completed_administration(instrument)
                items = list(
                    Instrument_Forms.objects.filter(instrument=instrument)
                    .select_related("choices")
                    .order_by("item_order")
                )
                for item in items:
                    self.answer(
                        administration,
                        item.itemID,
                        item.choices.choice_set_en.split(";")[-1].strip()
                        if item.choices
                        else "free text",
                    )
                response = self.client.get(self.summary_url(administration))
                self.assertEqual(response.status_code, 200)
                shown = sum(
                    len(group["words"]) + len(group["answers"])
                    for part in response.context["answers"]
                    for item_type in part["types"]
                    for group in item_type["groups"]
                )
                # a few instruments have items their meta file doesn't place on any page
                self.assertGreater(shown, 0.9 * len(items))
                self.assertLessEqual(shown, len(items))
                panel = self.answers_panel(self.summary_url(administration))
                for control in ["<input", "<select", "<textarea", "<button", "<form"]:
                    self.assertNotIn(control, panel)

    def test_answers_panel_in_a_translated_instrument(self):
        cases = [
            # (instrument, item, stored value, question text, answer the parent sees)
            ("Spanish_WS", "item_1", "produces", "¡am!", None),
            ("Spanish_WS", "item_700", "produces", "com<strong>í</strong>", None),
            ("Spanish_WG", "item_1", "yes", "¿Responde o voltea", "sí"),
            ("Spanish_WG", "item_59", "produces", "guajolote", "comp. y dice"),
            ("Spanish_WG", "item_60", "understands", "hipopótamo", "comprende"),
        ]
        for name, item_id, value, question, answer in cases:
            with self.subTest(item=(name, item_id)):
                instrument = Instrument.objects.get(name=name)
                administration = self.completed_administration(instrument)
                self.answer(administration, item_id, value)
                panel = self.answers_panel(self.summary_url(administration))
                self.assertIn(question, panel)
                if answer:
                    self.assertIn(answer, panel)

    def test_cat_summary_goes_to_the_cat_completion_page(self):
        # A CAT has no item list, so no answers to show; this URL raised an
        # AssertionError (500) from model_map
        cat2 = Instrument.objects.get(name="English_CAT")
        cat2.pk = cat2.name = "English_CAT2"
        cat2.form = "CAT2"
        cat2.save()
        for name in ["English_CAT", "English_CAT2"]:
            with self.subTest(instrument=name):
                instrument = Instrument.objects.get(name=name)
                administration = self.completed_administration(instrument)
                CatResponse.objects.create(administration=administration)
                response = self.client.get(self.summary_url(administration))
                self.assertRedirects(
                    response,
                    reverse(
                        "cat_forms:administer_cat_form",
                        kwargs={"hash_id": administration.url_hash},
                    ),
                    fetch_redirect_response=False,
                )
                completion = self.client.get(response.url)
                self.assertEqual(completion.status_code, 200)
                self.assertTemplateUsed(
                    completion, "cdi_forms/cat_forms/cat_completed.html"
                )
                self.assertNotContains(completion, "Show my answers")

    def test_completed_WG_get(self):
        self.client.force_login(self.user)
        instrument = Instrument.objects.get(
            language="English",
            form="WG",
        )
        study = Study.objects.create(
            researcher=self.user,
            name="WG Test Study Instance",
            instrument=instrument,
            redirect_url="https://redirect_url.com/redirect/{source_id}",
        )
        generate_fake_results(study, 1)
        administration = Administration.objects.filter(completed=True)[0]
        url = reverse(
            "administration_summary_view", kwargs={"hash_id": administration.url_hash}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_redirect_boolean(self):
        self.study.redirect_boolean = True
        self.study.save()
        generate_fake_results(self.study, 1)
        administration = Administration.objects.filter(completed=True)[0]
        url = reverse(
            "administration_summary_view", kwargs={"hash_id": administration.url_hash}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_indirect_redirect_boolean(self):
        self.study.redirect_boolean = True
        self.study.direct_redirect_boolean = False
        self.study.json_redirect = {
            "token": "DD266E7616FE86C190DEBC530CE5E435",
            "content": "surveyLink",
            "format": "json",
            "instrument": "webcdi",
            "event": "v01_arm_1",
            "record": "YISKL0001",
            "returnFormat": "json",
        }
        self.study.save()
        generate_fake_results(self.study, 1)
        administration = Administration.objects.filter(completed=True)[0]
        url = reverse(
            "administration_summary_view", kwargs={"hash_id": administration.url_hash}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_backpage_demographic(self):
        demographic = Demographic.objects.get(name="English_Split.json")
        self.study.demographic = demographic
        self.study.save()
        generate_fake_results(self.study, 1)
        administration = Administration.objects.filter(completed=True)[0]
        url = reverse(
            "administration_summary_view", kwargs={"hash_id": administration.url_hash}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_allow_payment_amazon(self):
        self.study.allow_payment = True
        self.study.save()
        generate_fake_results(self.study, 1)
        # this study's own administration (fixture administrations may already have codes)
        administration = Administration.objects.filter(
            study=self.study, completed=True
        )[0]
        payment_code = PaymentCode(
            study=self.study,
            payment_type="Amazon",
            gift_amount=25.00,
            gift_code="1234567890",
            hash_id=administration.url_hash,
        )
        payment_code.save()
        url = reverse(
            "administration_summary_view", kwargs={"hash_id": administration.url_hash}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_allow_payment_tango(self):
        self.study.allow_payment = True
        self.study.save()
        generate_fake_results(self.study, 1)
        # this study's own administration (fixture administrations may already have codes)
        administration = Administration.objects.filter(
            study=self.study, completed=True
        )[0]
        payment_code = PaymentCode(
            study=self.study,
            payment_type="Tango",
            gift_amount=25.00,
            gift_code="1234567890",
            hash_id=administration.url_hash,
        )
        payment_code.save()
        url = reverse(
            "administration_summary_view", kwargs={"hash_id": administration.url_hash}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_allow_payment_expired(self):
        self.study.allow_payment = True
        self.study.save()
        generate_fake_results(self.study, 1)
        administration = Administration.objects.filter(completed=True)[0]
        url = reverse(
            "administration_summary_view", kwargs={"hash_id": administration.url_hash}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


class AdministrationDetailViewTest(TestCase):
    fixtures = [
        "researcher_UI/fixtures/researcher_UI_test_fixtures.json",
        "cdi_forms/fixtures/cdi_forms_test_fixtures.json",
    ]

    def setUp(self):
        self.user = User.objects.create_user(username="test_user", password="secret")

        instrument = Instrument.objects.get(
            language="English",
            form="WS",
        )

        self.study = Study.objects.create(
            researcher=self.user,
            name="Test Study Instance",
            instrument=instrument,
            redirect_url="https://redirect_url.com/redirect/{source_id}",
        )

    def test_view_get(self):
        self.client.force_login(self.user)
        generate_fake_results(self.study, 1)
        administration = Administration.objects.filter(completed=True)[0]
        url = reverse("administration-view", kwargs={"hash_id": administration.url_hash})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_print_queries_do_not_grow_with_answers(self):
        # the translate filter cost two queries per checkbox word (~1,500 here)
        administration = Administration.objects.create(
            study=self.study,
            subject_id=1,
            repeat_num=1,
            url_hash=random_url_generator(),
            completed=True,
            due_date=timezone.now(),
        )
        BackgroundInfo.objects.create(administration=administration, age=20)
        administration_data.objects.bulk_create(
            administration_data(
                administration=administration,
                item_ID=item.itemID,
                value="produces",
            )
            for item in Instrument_Forms.objects.filter(
                instrument=self.study.instrument, item_type="word"
            )
        )
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(
                reverse("administration-view", kwargs={"pk": administration.pk})
            )
        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(
            len(queries), 15, "\n".join(q["sql"][:120] for q in queries)
        )

    def test_print_shows_the_translated_choice(self):
        instrument = Instrument.objects.get(name="Spanish_WS")
        study = Study.objects.create(
            researcher=self.user,
            name="Spanish print",
            instrument=instrument,
            redirect_url="https://example.com/",
        )
        administration = Administration.objects.create(
            study=study,
            subject_id=1,
            repeat_num=1,
            url_hash=random_url_generator(),
            completed=True,
            due_date=timezone.now(),
        )
        BackgroundInfo.objects.create(administration=administration, age=20)
        administration_data.objects.create(
            administration=administration, item_ID="item_1", value="produces"
        )
        page = self.client.get(
            reverse("administration-view", kwargs={"pk": administration.pk})
        ).content.decode()
        self.assertRegex(page, r"¡am!: </td>\s*<td>produce</td>")


class AdministrationUpdateViewTest(TestCase):
    fixtures = [
        "researcher_UI/fixtures/researcher_UI_test_fixtures.json",
        "cdi_forms/fixtures/cdi_forms_test_fixtures.json",
    ]

    def setUp(self):
        self.user = User.objects.create_user(username="test_user", password="secret")

        instrument = Instrument.objects.get(
            language="English",
            form="WS",
        )

        self.study = Study.objects.create(
            researcher=self.user,
            name="Test Study Instance",
            instrument=instrument,
            redirect_url="https://redirect_url.com/redirect/{source_id}",
        )

        self.administration = Administration.objects.create(
            study=self.study,
            subject_id=1,
            repeat_num=1,
            url_hash="0123456789012345678901234567890123456789012345678901234567890123",
            completed=False,
            due_date=timezone.now() + datetime.timedelta(days=14),
        )

        BackgroundInfo.objects.create(
            administration=self.administration, age=12, source_id="123456"
        )

        self.url = reverse(
            "update_administration", kwargs={"hash_id": self.administration.url_hash}
        )

    def test_get(self):
        self.client.force_login(self.user)
        self.administration.page_number = 1
        self.administration.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_previous_get(self):
        self.client.force_login(self.user)
        self.administration.page_number = 10
        self.administration.save()
        url = reverse(
            "update_administration_section_previous",
            kwargs={
                "hash_id": self.administration.url_hash,
                "section": 1,
                "previous": True,
            },
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_completed_get(self):
        self.client.force_login(self.user)
        self.administration.completed = True
        self.administration.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_completed_post(self):
        self.client.force_login(self.user)
        self.administration.completed = True
        self.administration.save()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)

    def test_expired_post_refused(self):
        # #758: an expired, uncompleted form can't be saved or submitted
        self.study.allow_payment = True
        self.study.save()
        PaymentCode.objects.create(
            study=self.study,
            payment_type="Amazon",
            gift_amount=5.00,
            gift_code="1234567890",
        )
        self.administration.due_date = timezone.now() - datetime.timedelta(minutes=1)
        self.administration.page_number = 2
        self.administration.save()
        last_modified = Administration.objects.get(
            pk=self.administration.pk
        ).last_modified
        summary_url = reverse(
            "administration_summary_view", args=(self.administration.url_hash,)
        )
        for button, payload in [
            ("save", {"btn-save": True}),
            ("next", {"btn-next": True, "next": 5}),
            ("previous", {"btn-previous": True, "previous": 1}),
            ("submit", {"btn-submit": True}),
        ]:
            with self.subTest(button=button):
                payload["item_1"] = "produces"
                response = self.client.post(self.section_url(3), payload)
                self.assertRedirects(
                    response, summary_url, fetch_redirect_response=False
                )
                self.assertTemplateUsed(
                    self.client.get(summary_url),
                    "cdi_forms/administration_expired.html",
                )
                administration = Administration.objects.get(pk=self.administration.pk)
                self.assertFalse(administration.completed)
                self.assertFalse(administration.completedSurvey)
                self.assertEqual(administration.page_number, 2)
                self.assertEqual(administration.last_modified, last_modified)
                self.assertFalse(
                    administration_data.objects.filter(
                        administration=self.administration
                    ).exists()
                )
                self.assertIsNone(
                    PaymentCode.objects.get(gift_code="1234567890").hash_id
                )

    def test_btn_save_post(self):
        self.client.force_login(self.user)
        payload = {"btn-save": True}
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 302)

    def test_btn_previous_post(self):
        self.client.force_login(self.user)

        payload = {"btn-previous": True, "previous": 10}
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 302)

    def test_btn_next_post(self):
        self.client.force_login(self.user)

        payload = {"btn-next": True, "next": 12}
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 302)

    def test_post_enabler_blank(self):
        self.client.force_login(self.user)

        payload = {"btn-next": True, "next": 30}
        url = reverse(
            "update_administration_section",
            kwargs={"hash_id": self.administration.url_hash, "section": 29},
        )
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, 302)
        redirect_url = reverse(
            "update_administration_section",
            kwargs={"hash_id": self.administration.url_hash, "section": 30},
        )
        self.assertRedirects(
            response,
            redirect_url,
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        response = self.client.get(redirect_url, payload)
        self.assertContains(response, "Thank you for completing!")

    def test_post_enabler_negative(self):
        self.client.force_login(self.user)

        payload = {"btn-next": True, "next": 30, "item_760": "not yet"}
        url = reverse(
            "update_administration_section",
            kwargs={"hash_id": self.administration.url_hash, "section": 29},
        )
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, 302)
        redirect_url = reverse(
            "update_administration_section",
            kwargs={"hash_id": self.administration.url_hash, "section": 30},
        )
        self.assertRedirects(
            response,
            redirect_url,
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        response = self.client.get(redirect_url, payload)
        self.assertContains(response, "Thank you for completing!")

    def test_post_enabler_sometimes(self):
        self.client.force_login(self.user)

        payload = {"btn-next": True, "next": 30, "item_760": "sometimes"}
        url = reverse(
            "update_administration_section",
            kwargs={"hash_id": self.administration.url_hash, "section": 29},
        )
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, 302)
        redirect_url = reverse(
            "update_administration_section",
            kwargs={"hash_id": self.administration.url_hash, "section": 30},
        )
        self.assertRedirects(
            response,
            redirect_url,
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        response = self.client.get(redirect_url, payload)
        self.assertNotContains(response, "Thank you for completing!")

    def test_post_enabler_often(self):
        self.client.force_login(self.user)

        payload = {"btn-next": True, "next": 30, "item_760": "often"}
        url = reverse(
            "update_administration_section",
            kwargs={"hash_id": self.administration.url_hash, "section": 29},
        )
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, 302)
        redirect_url = reverse(
            "update_administration_section",
            kwargs={"hash_id": self.administration.url_hash, "section": 30},
        )
        self.assertRedirects(
            response,
            redirect_url,
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        response = self.client.get(redirect_url, payload)
        self.assertNotContains(response, "Thank you for completing!")

    def test_btn_back_post(self):
        self.client.force_login(self.user)
        payload = {"btn-back": True}
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 302)

    def test_back_to_background_returns_to_same_section(self):
        # "Go back to Background Info" from section 3, then "Next" on the
        # background page, should land the parent on section 3 again (not 4).
        self.study.min_age = 12
        self.study.max_age = 36
        self.study.save()
        self.administration.due_date = timezone.now() + datetime.timedelta(days=14)
        self.administration.completedBackgroundInfo = True
        self.administration.save()
        section_url = reverse(
            "update_administration_section",
            kwargs={"hash_id": self.administration.url_hash, "section": 3},
        )

        response = self.client.post(section_url, {"btn-back": True})
        self.assertEqual(response.status_code, 302)
        background_url = response.url
        self.assertTrue(
            background_url.startswith(
                reverse(
                    "background-info",
                    args=(self.administration.url_hash,),
                )
            )
        )

        dob = (datetime.datetime.now() - datetime.timedelta(days=500)).strftime(
            "%m/%d/%Y"
        )
        payload = {
            "btn-next": "Next",
            "form_filler": "mother",
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
        }
        response = self.client.post(background_url, payload, follow=True)
        self.assertEqual(response.redirect_chain[-1][0], section_url)

    def resume_url(self):
        """Where reopening the parent's link sends them."""
        response = self.client.get(
            reverse("administer_cdi_form", args=(self.administration.url_hash,))
        )
        return response.url

    def section_url(self, section):
        return reverse(
            "update_administration_section",
            kwargs={"hash_id": self.administration.url_hash, "section": section},
        )

    def test_resume_where_the_parent_was_sent(self):
        self.administration.due_date = timezone.now() + datetime.timedelta(days=14)
        self.administration.completedBackgroundInfo = True
        self.administration.save()
        for button, payload, resume_at in [
            ("save", {"btn-save": True}, 4),
            ("next", {"btn-next": True, "next": 5}, 5),
            ("previous", {"btn-previous": True, "previous": 3}, 3),
        ]:
            with self.subTest(button=button):
                self.client.post(self.section_url(4), payload)
                self.assertEqual(self.resume_url(), self.section_url(resume_at))

    def test_section_queries_do_not_grow_with_enablers(self):
        # the last English WS section's items are shown depending on item_760;
        # each one's dependency used to be looked up in the database (91 queries)
        administration_data.objects.create(
            administration=self.administration, item_ID="item_760", value="often"
        )
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(self.section_url(31))
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.context["data"]["objects"]), 30)
        self.assertLessEqual(
            len(queries), 10, "\n".join(q["sql"][:120] for q in queries)
        )

    def test_enabled_items_depend_on_the_enabler_answer(self):
        items = Instrument_Forms.objects.filter(
            instrument=self.study.instrument, enabler="item_760"
        )
        self.assertGreater(items.count(), 0)
        complexity = set(items.filter(category="complexity").values_list("itemID", flat=True))
        self.assertGreater(len(complexity), 30)

        def shown():
            data = self.client.get(self.section_url(31)).context["data"]
            return {i["itemID"] for i in data["objects"]}

        self.assertEqual(shown() & complexity, set())  # not answered
        for value, expected in [
            ("often", complexity),
            ("sometimes", complexity),
            ("not yet", set()),
        ]:
            with self.subTest(item_760=value):
                administration_data.objects.update_or_create(
                    administration=self.administration,
                    item_ID="item_760",
                    defaults={"value": value},
                )
                self.assertEqual(shown() & complexity, expected)

    def test_saving_a_section_is_one_write(self):
        # "Next" re-posts the whole page; each item used to cost ~7-9 queries
        items = list(
            Instrument_Forms.objects.filter(
                instrument=self.study.instrument, item_type="word"
            ).order_by("item_order")[:40]
        )
        saved, changed, new = items[0], items[1], items[2:]
        for item, value in [(saved, "produces"), (changed, "understands")]:
            administration_data.objects.create(
                administration=self.administration, item_ID=item.itemID, value=value
            )
        payload = {
            "btn-next": True,
            "next": 3,
            saved.itemID: "produces",
            changed.itemID: "produces",
        }
        payload.update({item.itemID: "produces" for item in new})
        with CaptureQueriesContext(connection) as queries:
            response = self.client.post(self.section_url(2), payload)
        self.assertEqual(response.status_code, 302)
        self.assertLessEqual(
            len(queries), 10, "\n".join(q["sql"][:120] for q in queries)
        )
        self.assertEqual(
            dict(
                administration_data.objects.filter(
                    administration=self.administration
                ).values_list("item_ID", "value")
            ),
            {item.itemID: "produces" for item in items},
        )

    def test_post_ignores_values_outside_the_item_choices(self):
        word = Instrument_Forms.objects.filter(
            instrument=self.study.instrument, item_type="word"
        ).first()
        administration_data.objects.create(
            administration=self.administration, item_ID=word.itemID, value="produces"
        )
        textbox = Instrument_Forms.objects.filter(
            instrument=self.study.instrument, choices__isnull=True
        ).first()
        response = self.client.post(
            self.section_url(2),
            {
                "btn-save": True,
                word.itemID: "not a choice",
                textbox.itemID: "",
                "not_an_item": "produces",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            list(
                administration_data.objects.filter(
                    administration=self.administration
                ).values_list("item_ID", "value")
            ),
            [(word.itemID, "produces")],
        )

    def test_section_past_the_end_shows_the_last_section(self):
        # English WS has sections 1-31
        last = self.client.get(self.section_url(31)).context["data"]["menu"]
        response = self.client.get(self.section_url(99))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["data"]["menu"], last)

    def test_page_without_section_resumes_from_page_number(self):
        self.administration.page_number = 6
        self.administration.save()
        self.assertEqual(self.client.get(self.url).context["data"]["menu"], 6)
        self.administration.page_number = 0
        self.administration.save()
        self.assertEqual(self.client.get(self.url).context["data"]["menu"], 1)

    def test_migration_keeps_in_progress_parents_where_they_were(self):
        import importlib

        from django.apps import apps

        migration = importlib.import_module(
            "researcher_UI.migrations.0108_page_number_is_resume_section"
        )
        self.administration.page_number = 4  # old meaning: last posted from 4
        self.administration.save()
        done = Administration.objects.create(
            study=self.study, subject_id=2, repeat_num=1, url_hash="d" * 64,
            completed=True, due_date=timezone.now(), page_number=4,
        )
        migration.forwards(apps, None)
        self.administration.refresh_from_db()
        done.refresh_from_db()
        self.assertEqual(self.administration.page_number, 5)  # old code resumed at 4 + 1
        self.assertEqual(done.page_number, 4)

    def test_btn_submit_post(self):
        self.client.force_login(self.user)
        payload = {"btn-submit": True}
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 302)

    def test_btn_submit_allow_payment_post(self):
        self.client.force_login(self.user)
        self.study.allow_payment = True
        self.study.save()
        payload = {"btn-submit": True}
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 302)

    def test_btn_submit_with_payment_post(self):
        payment_code = PaymentCode(
            study=self.study,
            payment_type="Amazon",
            gift_amount=25.00,
            gift_code="1234567890",
        )
        payment_code.save()
        self.client.force_login(self.user)
        self.study.allow_payment = True
        self.study.name = "Wordful Study (Official)"
        self.study.save()
        self.administration.repeat_num = 2
        self.administration.save()
        payload = {"btn-submit": True}
        response = self.client.post(self.url, payload)
        pc = PaymentCode.objects.get(gift_code="1234567890")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(pc.hash_id, self.administration.url_hash)

    def test_backpage_post(self):
        demographic = Demographic.objects.get(name="English_Split.json")
        self.study.demographic = demographic
        self.study.save()
        payload = {"btn-submit": True}
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 302)

    def test_page_in_item_type_post(self):
        for instrument in Instrument.objects.exclude(form="CAT"):
            study = Study(
                researcher=self.user,
                name=f"{instrument.name} Test Study Instance",
                instrument=instrument,
                redirect_url="https://redirect_url.com/redirect/{source_id}",
            )
            study.save()
            administration = Administration.objects.create(
                study=study,
                subject_id=1,
                repeat_num=1,
                url_hash=random_url_generator(),
                completed=False,
                due_date=timezone.now() + datetime.timedelta(days=14),
            )
            administration.save()

            payload = {"btn-next": True, "next": 12}
            url = reverse(
                "update_administration", kwargs={"hash_id": administration.url_hash}
            )

            response = self.client.post(url, payload)
            self.assertEqual(response.status_code, 302)

    def test_completion_data(self):
        self.study.no_demographic_boolean = True
        self.study.completion_data = {
            "record_id": "{{source_id}}",
            "redcap_event_name": "{{event_id}}",
            "webcdi_completion_status": "1",
        }
        self.study.send_completion_flag_url = "https://example.com"
        self.study.save()
        payload = {"btn-submit": True}
        post = mock.Mock(return_value=mock.Mock(status_code=200))
        with mock.patch(
            "researcher_UI.utils.completion_notice.requests.post", post
        ), self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 302)
        # one completion notice (#723), with the placeholders filled in
        post.assert_called_once()
        self.assertEqual(post.call_args.args, ("https://example.com",))
        self.assertEqual(post.call_args.kwargs["data"]["webcdi_completion_status"], "1")
        self.administration.refresh_from_db()
        self.assertEqual(self.administration.send_completion_flag_url_response, 200)

    def test_post_data(self):
        payload = {
            "btn-submit": True,
            "item_1": "produces",
            "item_2": "produces",
            "item_5": "no",
            "item_6": "no",
            "item_example1": "Example",
        }
        response = self.client.post(self.url, payload)
        administration_datas = administration_data.objects.filter(
            administration=self.administration
        ).count()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(3, administration_datas)
        example = administration_datas = administration_data.objects.get(
            administration=self.administration, item_ID="item_example1"
        )
        self.assertEqual(example.value, "Example")


class UpdateAdministrationDataItemTest(TestCase):
    fixtures = [
        "researcher_UI/fixtures/researcher_UI_test_fixtures.json",
        "cdi_forms/fixtures/cdi_forms_test_fixtures.json",
    ]

    def setUp(self):
        self.user = User.objects.create_user(username="test_user", password="secret")

        instrument = Instrument.objects.get(
            language="English",
            form="WS",
        )

        self.study = Study.objects.create(
            researcher=self.user,
            name="Test Study Instance",
            instrument=instrument,
            redirect_url="https://redirect_url.com/redirect/{source_id}",
        )

        self.administration = Administration.objects.create(
            study=self.study,
            subject_id=1,
            repeat_num=1,
            url_hash="0123456789012345678901234567890123456789012345678901234567890123",
            completed=False,
            due_date=timezone.now() + datetime.timedelta(days=14),
        )

        BackgroundInfo.objects.create(
            administration=self.administration, age=12, source_id="123456"
        )

        self.url = reverse("update-administration-data-item")

    def test_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    def test_missing_params(self):
        # #630: used to raise MultiValueDictKeyError (500)
        base = {"hash_id": self.administration.url_hash}
        for payload in [
            {**base, "item": "item_1", "value": "produces"},  # no check
            {**base, "check": "true", "value": "produces"},  # no item
            {**base, "check": "true", "item": "item_1"},  # no value
        ]:
            response = self.client.post(self.url, payload)
            self.assertEqual(response.status_code, 400, payload)
        self.assertFalse(
            administration_data.objects.filter(
                administration=self.administration
            ).exists()
        )

    def test_upload_data(self):
        payload = {
            "hash_id": self.administration.url_hash,
            "check": "true",
            "item": "item_1",
            "value": "produces",
        }
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 200)

        item = administration_data.objects.get(
            administration=self.administration, item_ID="item_1"
        )
        self.assertEqual(item.value, "produces")

    def test_upload_data_removal(self):
        payload = {
            "hash_id": self.administration.url_hash,
            "check": "true",
            "item": "item_1",
            "value": "produces",
        }
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 200)

        item = administration_data.objects.get(
            administration=self.administration, item_ID="item_1"
        )
        self.assertEqual(item.value, "produces")

        payload = {
            "hash_id": self.administration.url_hash,
            "check": "true",
            "item": "item_1",
            "value": "",
        }
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 200)

        item = administration_data.objects.filter(
            administration=self.administration, item_ID="item_1"
        ).exists()
        self.assertEqual(item, False)

    def test_upload_data_change(self):
        payload = {
            "hash_id": self.administration.url_hash,
            "check": "true",
            "item": "item_761",
            "value": "simple",
        }
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 200)

        item = administration_data.objects.get(
            administration=self.administration, item_ID="item_761"
        )
        self.assertEqual(item.value, "simple")

        payload = {
            "hash_id": self.administration.url_hash,
            "check": "true",
            "item": "item_761",
            "value": "complex",
        }
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 200)

        item = administration_data.objects.get(
            administration=self.administration, item_ID="item_761"
        )
        self.assertEqual(item.value, "complex")

    def assert_refused(self, administration):
        # #739: no item changes once the administration is completed or expired
        administration_data.objects.create(
            administration=administration, item_ID="item_2", value="produces"
        )
        last_modified = Administration.objects.get(pk=administration.pk).last_modified
        for payload in [
            {"check": "true", "item": "item_1", "value": "produces"},  # add
            {"check": "true", "item": "item_2", "value": "understands"},  # change
            {"check": "false", "item": "item_2"},  # remove
        ]:
            payload["hash_id"] = administration.url_hash
            response = self.client.post(self.url, payload)
            self.assertEqual(response.status_code, 409, payload)
        self.assertEqual(
            list(
                administration_data.objects.filter(
                    administration=administration
                ).values_list("item_ID", "value")
            ),
            [("item_2", "produces")],
        )
        self.assertEqual(
            Administration.objects.get(pk=administration.pk).last_modified,
            last_modified,
        )

    def test_completed_administration_refused(self):
        self.administration.completed = True
        self.administration.save()
        self.assert_refused(self.administration)

    def test_expired_administration_refused(self):
        self.administration.due_date = timezone.now() - datetime.timedelta(minutes=1)
        self.administration.save()
        self.assert_refused(self.administration)

    def test_open_administration_accepted(self):
        payload = {
            "hash_id": self.administration.url_hash,
            "check": "true",
            "item": "item_1",
            "value": "produces",
        }
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 200)
        payload = {"hash_id": self.administration.url_hash, "check": "false", "item": "item_1"}
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            administration_data.objects.filter(
                administration=self.administration
            ).exists()
        )


class UpdateSummaryViewTest(TestCase):
    fixtures = [
        "researcher_UI/fixtures/researcher_UI_test_fixtures.json",
        "cdi_forms/fixtures/cdi_forms_test_fixtures.json",
    ]

    def setUp(self):
        self.user = User.objects.create_user(username="test_user", password="secret")

        instrument = Instrument.objects.get(
            language="English",
            form="WS",
        )

        self.study = Study.objects.create(
            researcher=self.user,
            name="Test Study Instance",
            instrument=instrument,
            redirect_url="https://example.com/redirect/{source_id}",
        )

    def test_completed_get(self):
        self.client.force_login(self.user)
        generate_fake_results(self.study, 10)
        args = []
        opts = {}
        call_command("update_summary_data", *args, **opts)
        self.assertEquals(
            10, Administration.objects.filter(study=self.study, scored=True).count()
        )
        # progress goes to the log, not to anyone's inbox
        self.assertEqual(len(mail.outbox), 0)
