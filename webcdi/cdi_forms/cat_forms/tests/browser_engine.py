import datetime
import json

from django.contrib.auth.models import User
from django.test import TestCase, override_settings, tag
from django.urls import reverse
from django.utils import timezone

from cdi_forms.cat_forms.models import CatResponse
from cdi_forms.models import BackgroundInfo
from researcher_UI.models import Administration, Instrument, Study
from researcher_UI.tests.utils import random_password

# Tests for the in-browser (jsCat) CAT flow. Unlike the remote-engine tests
# these make no network calls: item selection happens client-side, so the
# server only renders the page shell and persists answers.


@tag("cat")
@override_settings(CAT_ENGINE="browser")
class BrowserCatTest(TestCase):
    fixtures = [
        "researcher_UI/fixtures/researcher_UI_test_fixtures.json",
        "cdi_forms/fixtures/cdi_forms_test_fixtures.json",
    ]

    def setUp(self):
        self.user = User.objects.create_user(username="test_user", password="secret")
        instrument = Instrument.objects.get(language="English", form="CAT")
        self.study = Study.objects.create(
            researcher=self.user,
            name="Browser CAT Study",
            instrument=instrument,
        )
        self.hash = random_password(size=64)
        self.administration = Administration.objects.create(
            study=self.study,
            subject_id=1,
            repeat_num=1,
            url_hash=self.hash,
            completed=False,
            due_date=timezone.now() + datetime.timedelta(days=31),
            completedBackgroundInfo=True,
        )
        BackgroundInfo.objects.create(administration=self.administration, age=24)
        self.fill_url = reverse(
            "cat_forms:administer_cat_form", kwargs={"hash_id": self.hash}
        )
        self.answer_url = reverse(
            "cat_forms:cat_answer", kwargs={"hash_id": self.hash}
        )

    def answer(self, index, definition, response, est_theta, done=False):
        return self.client.post(
            self.answer_url,
            json.dumps(
                {
                    "index": index,
                    "definition": definition,
                    "response": response,
                    "est_theta": est_theta,
                    "done": done,
                }
            ),
            content_type="application/json",
        )

    def test_get_renders_browser_engine(self):
        response = self.client.get(self.fill_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "webcdi-cat.js")
        self.assertContains(response, "EN.json")

    def test_answer_persists_and_resumes(self):
        response = self.answer(326, "leg", True, 0.6103)
        self.assertEqual(response.status_code, 200)
        response = self.answer(206, "find", False, 0.4303)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 2)

        cat = CatResponse.objects.get(administration=self.administration)
        self.assertEqual(cat.administered_items, [326, 206])
        self.assertEqual(cat.administered_words, ["leg", "find"])
        self.assertEqual(cat.administered_responses, [True, False])
        self.assertAlmostEqual(cat.est_theta, 0.4303)

        # a fresh GET embeds the saved state for the engine to resume from
        response = self.client.get(self.fill_url)
        self.assertContains(response, "[326, 206]")

    def test_done_completes_and_scores(self):
        self.answer(326, "leg", True, 0.6103)
        response = self.answer(206, "find", False, 0.4303, done=True)
        self.assertTrue(response.json()["completed"])

        self.administration.refresh_from_db()
        self.assertTrue(
            self.administration.completed or self.administration.completedSurvey
        )
        self.assertTrue(self.administration.scored)

        # further answers are rejected once closed
        response = self.answer(21, "arm", True, 0.5)
        self.assertEqual(response.status_code, 409)

    def test_bad_payload_rejected(self):
        response = self.client.post(
            self.answer_url, "not json", content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIsNone(
            CatResponse.objects.filter(administration=self.administration)
            .first()
            .administered_items
            if CatResponse.objects.filter(administration=self.administration).exists()
            else None
        )


@tag("cat")
@override_settings(CAT_ENGINE="browser")
class BrowserCatHardestEasiestTest(TestCase):
    """In browser mode the completion page's hardest/easiest word is computed
    locally from the static bank instead of the R API. Verify the view reads
    the right language bank, considers only 'yes' items, and applies the
    easiness rule (max/min of the intercept, d = -a*b)."""

    fixtures = [
        "researcher_UI/fixtures/researcher_UI_test_fixtures.json",
        "cdi_forms/fixtures/cdi_forms_test_fixtures.json",
    ]

    def setUp(self):
        self.user = User.objects.create_user(username="test_user", password="secret")
        instrument = Instrument.objects.get(language="English", form="CAT")
        self.study = Study.objects.create(
            researcher=self.user, name="HE Study", instrument=instrument
        )
        self.administration = Administration.objects.create(
            study=self.study,
            subject_id=1,
            repeat_num=1,
            url_hash=random_password(size=64),
            completed=True,
            scored=True,
            due_date=timezone.now() + datetime.timedelta(days=31),
            completedBackgroundInfo=True,
        )
        BackgroundInfo.objects.create(administration=self.administration, age=24)
        # a mix of yes/no; only the yes items should count
        self.yes_indices = [35, 326, 206]  # ball, leg, find
        self.no_index = 411  # answered "no", must be ignored
        CatResponse.objects.create(
            administration=self.administration,
            administered_items=self.yes_indices + [self.no_index],
            administered_words=["ball", "leg", "find", "pants"],
            administered_responses=[True, True, True, False],
            est_theta=0.5,
        )

    def _bank_expected(self):
        from cdi_forms.cat_forms.views import _cat_bank

        bank = {it["index"]: it for it in _cat_bank("EN")["items"]}
        yes = [bank[i] for i in self.yes_indices]
        easiness = lambda it: -it["a"] * it["b"]
        return (min(yes, key=easiness)["definition"],  # hardest
                max(yes, key=easiness)["definition"])  # easiest

    def test_hardest_easiest_matches_bank(self):
        from cdi_forms.cat_forms.views import AdministerAdministraionView

        view = AdministerAdministraionView()
        view.object = self.administration
        view.language = "en"
        hardest, easiest = view.get_hardest_easiest()

        exp_hardest, exp_easiest = self._bank_expected()
        self.assertEqual(hardest, exp_hardest)
        self.assertEqual(easiest, exp_easiest)
        # the "no" item must not be selected
        self.assertNotEqual(hardest, "pants")
        self.assertNotEqual(easiest, "pants")
