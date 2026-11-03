import datetime
import json
import random
from unittest import mock

from django.test import TestCase, tag
from django.utils import timezone

from cdi_forms.models import BackgroundInfo, Instrument_Forms
from researcher_UI.models import Administration, administration_data
from researcher_UI.utils.random_url_generator import random_url_generator

from .participant_links import ParticipantLinkTestCase, background_payload

FINISH_TEMPLATE = "cdi_forms/backpage_finish.html"
CLOSED_TEMPLATE = "cdi_forms/single_reusable_link_inactive.html"


class SaveAnswerTest(ParticipantLinkTestCase):
    """save_answer refuses the same states as update_administration_data_item."""

    def setUp(self):
        super().setUp()
        self.study = self.make_study()
        self.administration = self.make_administration(self.study)
        self.item_id = (
            Instrument_Forms.objects.filter(
                instrument=self.study.instrument, choices__isnull=True
            )
            .first()
            .itemID
        )
        self.stored = administration_data.objects.create(
            administration=self.administration, item_ID=self.item_id, value="first"
        )

    def post_answer(self):
        return self.client.post(
            "/form/save_answer/",
            {"hash_id": self.administration.url_hash, self.item_id: "second"},
        )

    def assert_refused(self):
        last_modified = Administration.objects.get(
            pk=self.administration.pk
        ).last_modified
        response = self.post_answer()
        self.assertEqual(response.status_code, 409)
        self.stored.refresh_from_db()
        self.assertEqual(self.stored.value, "first")
        self.assertEqual(
            Administration.objects.get(pk=self.administration.pk).last_modified,
            last_modified,
        )

    def test_open_form_saves(self):
        self.assertEqual(self.post_answer().status_code, 200)
        self.stored.refresh_from_db()
        self.assertEqual(self.stored.value, "second")

    def test_completed_form_is_closed(self):
        self.administration.completed = True
        self.administration.save()
        self.assert_refused()

    def test_expired_form_is_closed(self):
        self.administration.due_date = timezone.now() - datetime.timedelta(minutes=1)
        self.administration.save()
        self.assert_refused()

    def test_unknown_link_is_404(self):
        response = self.client.post("/form/save_answer/", {"hash_id": "0" * 64})
        self.assertEqual(response.status_code, 404)


class NoBackpageFlowTest(ParticipantLinkTestCase):
    """On a study with no backpage, the form's submit step finishes the
    administration and viewing a page never does."""

    def regular_administration(self, **kwargs):
        study = self.make_study(backpage_boolean=False)
        administration = self.make_administration(study, **kwargs)
        BackgroundInfo.objects.create(
            administration=administration, age=20, zip_code="941**"
        )
        return administration

    def cat_administration(self, **kwargs):
        study = self.make_study(
            form="CAT", name="CAT no backpage", backpage_boolean=False
        )
        administration = self.make_administration(study, **kwargs)
        BackgroundInfo.objects.create(
            administration=administration, age=20, zip_code="941**"
        )
        return administration

    def test_regular_form_end_to_end(self):
        study = self.make_study(backpage_boolean=False)
        administration = self.make_administration(study)
        link = administration.url_hash
        fill = f"/form/fill/{link}/"
        background = f"/form/background/{link}/"
        section = f"/form/administration/{link}/1/"
        summary = f"/form/administration/{link}/summary/"

        self.assertRedirects(self.client.get(fill), background)
        response = self.client.post(background, background_payload(**{"btn-next": "Next"}))
        self.assertRedirects(response, fill, target_status_code=302)

        response = self.client.post(section, {"btn-submit": True, "item_1": "produces"})
        self.assertRedirects(response, summary)

        administration.refresh_from_db()
        self.assertTrue(administration.completed)
        self.assertTrue(administration.completedSurvey)
        self.assertIsNotNone(administration.completed_date)
        self.assertEqual(
            administration_data.objects.get(
                administration=administration, item_ID="item_1"
            ).value,
            "produces",
        )
        self.assertRedirects(self.client.get(fill), summary)

    @tag("cat")
    def test_cat_form_end_to_end(self):
        study = self.make_study(
            form="CAT", name="CAT no backpage", backpage_boolean=False
        )
        administration = self.make_administration(study)
        link = administration.url_hash
        fill = f"/form/cat/fill/{link}/"
        answer = f"/form/cat/answer/{link}/"

        self.assertRedirects(self.client.get(fill), f"/form/background/{link}/")
        response = self.client.post(
            f"/form/cat/background/{link}/", background_payload(**{"btn-next": "Next"})
        )
        self.assertRedirects(response, f"/form/fill/{link}/", target_status_code=302)
        self.assertContains(self.client.get(fill), "webcdi-cat.js")

        for index, definition, done in [(326, "leg", False), (206, "find", True)]:
            response = self.client.post(
                answer,
                json.dumps(
                    {
                        "index": index,
                        "definition": definition,
                        "response": True,
                        "est_theta": 0.6,
                        "done": done,
                    }
                ),
                content_type="application/json",
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["completed"], done)

        administration.refresh_from_db()
        self.assertTrue(administration.completed)
        self.assertTrue(administration.completedSurvey)
        self.assertTrue(administration.scored)
        response = self.client.get(fill)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "cdi_forms/cat_forms/cat_completed.html")

    def test_viewing_backpage_mid_form_writes_nothing(self):
        for administration, path, destination in [
            (
                self.regular_administration(),
                "/form/background/{}/backpage/",
                "/form/fill/{}/",
            ),
            (
                self.cat_administration(),
                "/form/cat/background-backpage/{}/",
                "/form/cat/fill/{}/",
            ),
        ]:
            with self.subTest(form=administration.study.instrument.form):
                link = administration.url_hash
                response = self.client.get(path.format(link))
                self.assertRedirects(
                    response,
                    destination.format(link),
                    fetch_redirect_response=False,
                )
                administration.refresh_from_db()
                self.assertFalse(administration.completed)
                self.assertFalse(administration.completedSurvey)

    def assert_finishes_by_post(self, administration, fill, backpage):
        """Answers are in but the row is not finished (e.g. the study's backpage
        was switched off while the parent was on it): the page asks for a POST."""
        self.assertRedirects(self.client.get(fill), backpage)
        response = self.client.get(backpage)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, FINISH_TEMPLATE)
        administration.refresh_from_db()
        self.assertFalse(administration.completed)

        response = self.client.post(backpage, {"btn-next": "Finish"})
        self.assertRedirects(response, fill, target_status_code=302)
        administration.refresh_from_db()
        self.assertTrue(administration.completed)
        self.assertIsNotNone(administration.completed_date)

    def test_answers_in_regular_form_finishes_by_post(self):
        administration = self.regular_administration(
            completedBackgroundInfo=True, completedSurvey=True
        )
        link = administration.url_hash
        self.assert_finishes_by_post(
            administration, f"/form/fill/{link}/", f"/form/background/{link}/backpage/"
        )

    @tag("cat")
    def test_answers_in_cat_form_finishes_by_post(self):
        administration = self.cat_administration(
            completedBackgroundInfo=True, completedSurvey=True
        )
        link = administration.url_hash
        self.assertEqual(
            self.client.post(
                f"/form/cat/background-backpage/{link}/", {"btn-next": "Finish"}
            ).status_code,
            302,
        )
        administration.refresh_from_db()
        self.assertTrue(administration.completed)
        self.assertTemplateUsed(
            self.client.get(f"/form/cat/fill/{link}/"),
            "cdi_forms/cat_forms/cat_completed.html",
        )

    @tag("cat")
    def test_cat_form_with_answers_in_reaches_finish_page(self):
        administration = self.cat_administration(
            completedBackgroundInfo=True, completedSurvey=True
        )
        link = administration.url_hash
        response = self.client.get(f"/form/cat/fill/{link}/", follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, FINISH_TEMPLATE)
        administration.refresh_from_db()
        self.assertFalse(administration.completed)

    def test_post_does_not_finish_a_form_still_in_progress(self):
        administration = self.regular_administration(completedBackgroundInfo=True)
        response = self.client.post(
            f"/form/background/{administration.url_hash}/backpage/",
            {"btn-next": "Finish"},
        )
        self.assertEqual(response.status_code, 302)
        administration.refresh_from_db()
        self.assertFalse(administration.completed)

    def test_expired_form_is_not_finished(self):
        administration = self.regular_administration(
            completedBackgroundInfo=True, completedSurvey=True
        )
        administration.due_date = timezone.now() - datetime.timedelta(minutes=1)
        administration.save()
        backpage = f"/form/background/{administration.url_hash}/backpage/"
        self.assertEqual(self.client.get(backpage).status_code, 302)
        self.assertEqual(
            self.client.post(backpage, {"btn-next": "Finish"}).status_code, 302
        )
        administration.refresh_from_db()
        self.assertFalse(administration.completed)

    def test_study_with_backpage_still_shows_it(self):
        study = self.make_study(name="With backpage")
        administration = self.make_administration(
            study, completedBackgroundInfo=True, completedSurvey=True
        )
        BackgroundInfo.objects.create(
            administration=administration, age=20, zip_code="941**"
        )
        response = self.client.get(
            f"/form/background/{administration.url_hash}/backpage/"
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "cdi_forms/backpage_info.html")
        administration.refresh_from_db()
        self.assertFalse(administration.completed)


class NoBackpageCompletionSignalsTest(ParticipantLinkTestCase):
    """Finishing on a study with no backpage scores the administration and sends
    one completion notice, with signals running as they do outside tests."""

    NOTICE_URL = "https://example.com/notify"

    def setUp(self):
        super().setUp()
        self.post = mock.Mock(return_value=mock.Mock(status_code=200))

    def make_administration_for(self, form="WS", **kwargs):
        study = self.make_study(
            form=form,
            name=f"Signals {form}",
            backpage_boolean=False,
            send_completion_flag_url=self.NOTICE_URL,
            completion_data={"record_id": "{{source_id}}"},
        )
        administration = self.make_administration(
            study, completedBackgroundInfo=True, **kwargs
        )
        BackgroundInfo.objects.create(
            administration=administration,
            age=20,
            sex="F",
            zip_code="941**",
            source_id="abc",
        )
        return administration

    def run_with_signals(self, request):
        with mock.patch(
            "researcher_UI.utils.completion_notice.requests.post", self.post
        ), mock.patch(
            "researcher_UI.signals.TESTING", False
        ), self.captureOnCommitCallbacks(
            execute=True
        ):
            return request()

    def assert_finished(self, administration, completed_date=True):
        administration.refresh_from_db()
        self.assertTrue(administration.completed)
        self.assertTrue(administration.scored)
        if completed_date:
            self.assertIsNotNone(administration.completed_date)
        self.assert_one_notice(administration)

    def assert_one_notice(self, administration):
        self.post.assert_called_once()
        self.assertEqual(self.post.call_args.args[0], self.NOTICE_URL)
        self.assertEqual(self.post.call_args.kwargs["data"], {"record_id": "abc"})
        administration.refresh_from_db()
        self.assertEqual(administration.completion_notice_attempts, 1)
        self.assertEqual(administration.send_completion_flag_url_response, 200)

    def assert_no_notice_from_viewing_backpage(self, administration, path):
        response = self.run_with_signals(lambda: self.client.get(path))
        self.assertEqual(response.status_code, 302)
        self.assert_one_notice(administration)

    def test_regular_submit_step(self):
        administration = self.make_administration_for()
        link = administration.url_hash
        response = self.run_with_signals(
            lambda: self.client.post(
                f"/form/administration/{link}/1/",
                {"btn-submit": True, "item_1": "produces"},
            )
        )
        self.assertRedirects(
            response,
            f"/form/administration/{link}/summary/",
            fetch_redirect_response=False,
        )
        self.assert_finished(administration)
        self.assert_no_notice_from_viewing_backpage(
            administration, f"/form/background/{link}/backpage/"
        )

    def test_finish_page_post(self):
        administration = self.make_administration_for(completedSurvey=True)
        link = administration.url_hash
        backpage = f"/form/background/{link}/backpage/"
        response = self.run_with_signals(
            lambda: self.client.post(backpage, {"btn-next": "Finish"})
        )
        self.assertEqual(response.status_code, 302)
        self.assert_finished(administration)
        self.assert_no_notice_from_viewing_backpage(administration, backpage)

    @tag("cat")
    def test_cat_final_answer(self):
        administration = self.make_administration_for(form="CAT")
        link = administration.url_hash
        response = self.run_with_signals(
            lambda: self.client.post(
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
        )
        self.assertTrue(response.json()["completed"])
        # CAT's final answer has never recorded completed_date
        self.assert_finished(administration, completed_date=False)
        self.assert_no_notice_from_viewing_backpage(
            administration, f"/form/cat/background-backpage/{link}/"
        )


class ReusableLinkSettingTest(ParticipantLinkTestCase):
    """The create routes follow single_reusable_link_active, as new_parent does."""

    def create_paths(self, study):
        return [
            f"/form/background/create/{study.pk}/bypass/",
            f"/form/background/create/{study.pk}/bypass/abc/",
            f"/form/background/create/{study.pk}/abc/",
            f"/form/cat/background-create/{study.pk}/bypass/abc/",
            f"/form/cat/background-create/{study.pk}/abc/",
        ]

    def test_setting_off_closes_create_routes(self):
        study = self.make_study(single_reusable_link_active=False)
        for path in self.create_paths(study):
            with self.subTest(path=path, method="GET"):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, CLOSED_TEMPLATE)
            with self.subTest(path=path, method="POST"):
                response = self.client.post(path, background_payload())
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, CLOSED_TEMPLATE)
        self.assertFalse(Administration.objects.filter(study=study).exists())

    def test_setting_on_keeps_create_routes(self):
        study = self.make_study()
        for path in self.create_paths(study):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, "cdi_forms/background_info.html")
        response = self.client.post(self.create_paths(study)[0], background_payload())
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Administration.objects.filter(study=study).count(), 1)

    def new_parent_url(self, study):
        return f"/interface/{study.researcher.username}/{study.name}/new_parent/"

    def test_new_parent_link_reaches_create_page(self):
        study = self.make_study()
        response = self.client.get(self.new_parent_url(study), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "cdi_forms/background_info.html")

    def test_new_parent_source_id_link_reaches_create_page(self):
        study = self.make_study()
        response = self.client.get(
            self.new_parent_url(study) + "?source_id=abc", follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "cdi_forms/background_info.html")

    @tag("cat")
    def test_new_parent_link_reaches_cat_create_page(self):
        study = self.make_study(form="CAT", name="CAT reusable")
        response = self.client.get(self.new_parent_url(study), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "cdi_forms/background_info.html")

    def test_individual_links_stay_open_when_setting_off(self):
        study = self.make_study(single_reusable_link_active=False)
        administration = self.make_administration(study)
        link = administration.url_hash
        self.assertRedirects(
            self.client.get(f"/form/fill/{link}/"), f"/form/background/{link}/"
        )

    def test_unknown_study_is_404(self):
        self.assertEqual(
            self.client.get("/form/background/create/99999999/bypass/").status_code,
            404,
        )


class RandomUrlGeneratorTest(TestCase):
    def test_does_not_depend_on_random_module_state(self):
        random.seed(1234)
        first = random_url_generator()
        random.seed(1234)
        self.assertNotEqual(first, random_url_generator())

    def test_length_and_alphabet_are_unchanged(self):
        value = random_url_generator()
        self.assertEqual(len(value), 64)
        self.assertLessEqual(set(value), set("0123456789abcdef"))

    def test_arguments_are_honoured(self):
        self.assertEqual(random_url_generator(size=5, chars="x"), "xxxxx")
