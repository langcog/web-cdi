import json
import logging

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from cdi_forms.models import Instrument_Forms
from cdi_forms.views import get_model_header
from researcher_UI.models import (Administration, Instrument, Study,
                                  administration_data)
from researcher_UI.tests import generate_fake_results

logger = logging.getLogger("selenium")
logger.setLevel(logging.INFO)


class StudyAPIViewTest(TestCase):
    fixtures = [
        "researcher_UI/fixtures/researcher_UI_test_fixtures.json",
        "cdi_forms/fixtures/cdi_forms_test_fixtures.json",
    ]

    def setUp(self):
        self.user = User.objects.create_user(
            username="PaulMcCartney", password="PaulMcCartney"
        )
        self.invalid_user = User.objects.create_user(
            username="JohnLennon", password="JohnLennon"
        )

        instrument = Instrument.objects.filter(form__in=["WS", "WG"]).order_by("?")[0]
        self.study = Study.objects.create(
            researcher=self.user, name="Test Study Instance", instrument=instrument
        )

        self.url = reverse("api:study_api", kwargs={"pk": self.study.id})

        self.empty_study = Study.objects.create(
            researcher=self.user,
            name="Empty Test Study Instance",
            instrument=instrument,
        )
        self.empty_url = reverse("api:study_api", kwargs={"pk": self.empty_study.id})

        english_instrument = Instrument.objects.filter(
            language="English", form__in=["WS", "WG"]
        ).order_by("?")[0]
        self.english_study = Study.objects.create(
            researcher=self.user,
            name="English Test Study Instance",
            instrument=english_instrument,
        )
        self.english_url = reverse(
            "api:study_api", kwargs={"pk": self.english_study.id}
        )

        self.payload = {"username": "PaulMcCartney", "password": "PaulMcCartney"}

        self.invalid_payload = {"username": "JohnLennon", "password": "JohnLennon"}

        self.invalid_user_payload = {
            "username": "JohnLennon",
            "password": "PaulMcCartney",
        }

        generate_fake_results(self.study, 10)
        generate_fake_results(self.english_study, 10)

    def test_study_api(self):
        response = self.client.generic("POST", self.url, json.dumps(self.payload))
        self.assertEqual(response.status_code, 200)

    def test_repeated_item_labels(self):
        # #640: some forms list the same word twice (e.g. as a noun and as a
        # verb); the export keys items by label, which made duplicate keys
        # and a 500 on pandas 3. Each item keeps its own value, and repeats
        # are suffixed _1, _2, ... in form order.
        for name in ["Dutch_WS", "Argentine_Spanish_WS"]:
            with self.subTest(instrument=name):
                instrument = Instrument.objects.get(name=name)
                study = Study.objects.create(
                    researcher=self.user, name=f"{name} labels", instrument=instrument
                )
                generate_fake_results(study, 2)
                labels = {}
                for item_id, label in Instrument_Forms.objects.filter(
                    instrument=instrument
                ).values_list("itemID", "item"):
                    labels.setdefault(label, []).append(item_id)
                label, item_ids = next(
                    (k, v) for k, v in sorted(labels.items()) if len(v) > 1
                )
                administration = Administration.objects.filter(
                    study=study, completed=True
                ).first()
                values = {}
                for n, item_id in enumerate(item_ids):
                    values[item_id] = f"value {n}"
                    administration_data.objects.update_or_create(
                        administration=administration,
                        item_ID=item_id,
                        defaults={"value": values[item_id]},
                    )

                response = self.client.generic(
                    "POST",
                    reverse("api:study_api", kwargs={"pk": study.id}),
                    json.dumps(self.payload),
                )
                self.assertEqual(response.status_code, 200)
                record = next(
                    r
                    for r in response.json().values()
                    if r["administration_id"] == administration.pk
                )
                form_order = get_model_header(name)
                ordered = sorted(item_ids, key=form_order.index)
                keys = [label] + [f"{label}_{n}" for n in range(1, len(ordered))]
                self.assertEqual(
                    [record[k] for k in keys], [values[i] for i in ordered]
                )

    def test_count_scores_and_empty_lists(self):
        # #756: pandas-3 in-place replaces were no-ops, so a count score with
        # no stored value came out blank (not 0) and empty lists as "[]"
        from cdi_forms.models import BackgroundInfo
        from researcher_UI.models import InstrumentScore, SummaryData

        instrument = Instrument.objects.get(name="English_WS")
        study = Study.objects.create(
            researcher=self.user, name="cleanup English_WS", instrument=instrument
        )
        generate_fake_results(study, 2)
        administration = Administration.objects.filter(study=study).first()
        BackgroundInfo.objects.filter(administration=administration).update(
            child_ethnicity=[], other_languages=[]
        )
        count_title = (
            InstrumentScore.objects.filter(instrument=instrument, kind="count")
            .first()
            .title
        )
        SummaryData.objects.filter(
            administration__study=study, title=count_title
        ).delete()

        response = self.client.generic(
            "POST",
            reverse("api:study_api", kwargs={"pk": study.id}),
            json.dumps(self.payload),
        )
        self.assertEqual(response.status_code, 200)
        record = next(
            r
            for r in response.json().values()
            if r["administration_id"] == administration.pk
        )
        # counts are stored as strings ("0", "12"), like the scorer writes them
        self.assertEqual(record[count_title], "0")
        self.assertEqual(record["child_ethnicity"], "")
        self.assertEqual(record["other_languages"], "")

    def test_english_study_api(self):
        response = self.client.generic(
            "POST", self.english_url, json.dumps(self.payload)
        )
        self.assertEqual(response.status_code, 200)

    def test_api_permission_denied(self):
        response = self.client.generic(
            "POST", self.url, json.dumps(self.invalid_payload)
        )
        self.assertEqual(response.status_code, 403)

    def test_api_invalid_user(self):
        response = self.client.generic(
            "POST", self.url, json.dumps(self.invalid_user_payload)
        )
        self.assertEqual(response.status_code, 401)

    def test_api_no_completed_administrations(self):
        response = self.client.generic("POST", self.empty_url, json.dumps(self.payload))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["Error"], "You must select at least 1 completed survey"
        )
