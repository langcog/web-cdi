import random

from django.contrib.auth.models import User
from django.db import connection
from django.test import TestCase, tag
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from cdi_forms.models import BackgroundInfo, Instrument_Forms
from cdi_forms.scores import InstrumentScoring, update_summary_scores
from researcher_UI.management.commands.compare_scoring import \
    compare_administration
from researcher_UI.models import (Administration, Benchmark, Instrument,
                                  InstrumentScore, Measure, Study,
                                  SummaryData, administration_data)

BACKGROUND_DEFAULTS = dict(
    birth_order=1,
    multi_birth_boolean=0,
    birth_weight_lb=6.5,
    mother_education=16,
    father_education=16,
    mother_yob=1985,
    father_yob=1985,
    annual_income="50000-75000",
    caregiver_info=2,
    other_languages_boolean=0,
    ear_infections_boolean=0,
    hearing_loss_boolean=0,
    vision_problems_boolean=0,
    illnesses_boolean=0,
    services_boolean=0,
    worried_boolean=0,
    learning_disability_boolean=0,
)


@tag("scoring")
class ScoringEquivalenceTest(TestCase):
    """The bulk scorer must reproduce the legacy scorer exactly (#668).

    Builds administrations for every instrument in the test fixtures that has
    scoring definitions, varying the inputs that drive the scorer's branches
    (sex, prematurity, ages outside the norms, missing background info), and
    compares every SummaryData row, the `scored` flag and any raised error.
    """

    fixtures = [
        "researcher_UI/fixtures/researcher_UI_test_fixtures.json",
        "cdi_forms/fixtures/cdi_forms_test_fixtures.json",
    ]

    @classmethod
    def setUpTestData(cls):
        rng = random.Random(668)
        user = User.objects.create_user(username="equivalence", password="x-test-only")
        cls.admin_ids = []
        cls.instruments = []
        scored_instruments = InstrumentScore.objects.values_list(
            "instrument", flat=True
        ).distinct()
        for instrument in Instrument.objects.filter(pk__in=scored_instruments):
            items = list(
                Instrument_Forms.objects.filter(instrument=instrument).select_related(
                    "choices"
                )
            )
            if not items:
                continue
            cls.instruments.append(instrument.name)
            study = Study.objects.create(
                researcher=user, name=f"eq {instrument.name}", instrument=instrument
            )
            low, high = instrument.min_age, instrument.max_age
            cases = [
                dict(sex="M", age=rng.randint(low, high)),
                dict(sex="F", age=rng.randint(low, high)),
                dict(sex="O", age=rng.randint(low, high)),
                dict(sex="P", age=rng.randint(low, high)),
                dict(sex=None, age=rng.randint(low, high)),
                dict(sex="F", age=low - 3),
                dict(sex="M", age=high + 3),
                dict(sex="M", age=low, early_or_late="early", due_date_diff=10),
                dict(sex="F", age=high, early_or_late="late", due_date_diff=6),
                dict(sex="F", age=rng.randint(low, high), early_or_late="early",
                     due_date_diff=rng.randint(1, 16)),
                None,  # no background info at all
            ]
            for n, case in enumerate(cases):
                admin = Administration.objects.create(
                    study=study,
                    subject_id=n + 1,
                    repeat_num=1,
                    url_hash=f"{instrument.name}-{n}".ljust(64, "x")[:64],
                    completed=True,
                    due_date=timezone.now(),
                )
                if case is not None:
                    BackgroundInfo.objects.create(
                        administration=admin, **BACKGROUND_DEFAULTS, **case
                    )
                responses = []
                for item in items:
                    if rng.random() < 0.3:
                        continue
                    if item.choices_id:
                        options = [o.strip() for o in item.choices.choice_set.split(";")]
                        value = rng.choice(options)
                    else:
                        value = rng.choice(["", "more juice", "daddy go car"])
                    responses.append(
                        administration_data(
                            administration=admin, item_ID=item.itemID, value=value
                        )
                    )
                administration_data.objects.bulk_create(responses)
                cls.admin_ids.append(admin.pk)
        # administrations shipped in the fixtures (real-shaped responses)
        cls.admin_ids += list(
            Administration.objects.filter(completed=True)
            .exclude(pk__in=cls.admin_ids)
            .values_list("pk", flat=True)
        )

    def test_bulk_matches_legacy(self):
        self.assertGreaterEqual(len(self.instruments), 5, self.instruments)
        with_percentiles = 0
        for pk in self.admin_ids:
            legacy, new, differences = compare_administration(pk)
            with self.subTest(administration=pk):
                self.assertEqual(differences, [])
            if any("Percentile" in t for t in new["rows"]):
                with_percentiles += 1
        # guard against a vacuous pass
        self.assertGreater(with_percentiles, 20)

    def test_query_count_is_small(self):
        admin = Administration.objects.get(pk=self.admin_ids[0])
        scoring = InstrumentScoring(admin.study.instrument)
        with CaptureQueriesContext(connection) as queries:
            update_summary_scores(admin, scoring)
        self.assertLess(len(queries), 15)


@tag("scoring")
class UnknownItemTest(TestCase):
    """Responses to items the instrument doesn't have are skipped, not miscounted."""

    def test_unknown_item_is_not_counted(self):
        instrument = Instrument.objects.create(
            name="Tiny_WS", verbose_name="Tiny", language="Tiny", form="WS",
            min_age=16, max_age=30,
        )
        InstrumentScore.objects.create(
            instrument=instrument, title="Words", category="word",
            scoring_measures="produces",
        )
        Instrument_Forms.objects.create(
            instrument=instrument, itemID="item_1", item="ball", item_type="word",
            category="toys", definition="ball", gloss="ball", item_order=1,
        )
        study = Study.objects.create(
            researcher=User.objects.create_user("u", password="x-test-only"),
            name="tiny", instrument=instrument,
        )
        admin = Administration.objects.create(
            study=study, subject_id=1, repeat_num=1, url_hash="t" * 64,
            completed=True, due_date=timezone.now(),
        )
        for item_id in ("item_1", "item_retired"):
            administration_data.objects.create(
                administration=admin, item_ID=item_id, value="produces"
            )
        f = InstrumentScore.objects.get(instrument=instrument)
        Measure.objects.create(instrument_score=f, key="produces", value=1)
        update_summary_scores(admin)
        self.assertEqual(
            SummaryData.objects.get(administration=admin, title="Words").value, "1"
        )
        self.assertFalse(Benchmark.objects.filter(instrument=instrument).exists())
        admin.refresh_from_db()
        self.assertTrue(admin.scored)
