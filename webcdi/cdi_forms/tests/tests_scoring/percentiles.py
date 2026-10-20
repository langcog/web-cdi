from django.contrib.auth.models import User
from django.test import SimpleTestCase, TestCase, tag
from django.utils import timezone

from cdi_forms.cat_forms.models import CatResponse
from cdi_forms.models import BackgroundInfo
from cdi_forms.scores import (NOT_COMPUTED, cat_norms, percentile_of,
                              percentile_thresholds, update_summary_scores)
from researcher_UI.models import (Administration, Benchmark, Instrument,
                                  InstrumentScore, Study, SummaryData)

from .equivalence import BACKGROUND_DEFAULTS

# English L1 short form, "Understands", 16 months, both sexes (published table)
L1_UNDERSTANDS_16 = {
    0: 0, 5: 9, 10: 16, 15: 21, 20: 26, 25: 31, 30: 35, 35: 40, 40: 44, 45: 48,
    50: 52, 55: 55, 60: 59, 65: 63, 70: 67, 75: 70, 80: 74, 85: 78, 90: 81,
    95: 85, 99: 88,
}


@tag("scoring")
class PercentileRulesTest(SimpleTestCase):
    """Virginia Marchman's rules (#686), as golden cases."""

    def test_full_tables_are_used_as_published(self):
        table = {p: 2 * p for p in range(1, 100)}
        self.assertEqual(percentile_thresholds(table), table)

    def test_coarse_tables_are_filled_in_at_one_point_steps(self):
        t = percentile_thresholds(L1_UNDERSTANDS_16)
        self.assertEqual(sorted(t), list(range(1, 100)))
        self.assertAlmostEqual(t[6], 9 + 7 / 5)  # (16 - 9) / 5 per percentile
        self.assertAlmostEqual(t[9], 9 + 4 * 7 / 5)
        self.assertAlmostEqual(t[96], 85 + 3 / 4)  # 95 -> 99 has 4 steps
        self.assertEqual(t[99], 88)

    def test_floor_uses_the_5th_to_10th_slope(self):
        t = percentile_thresholds(L1_UNDERSTANDS_16)
        self.assertAlmostEqual(t[4], 9 - 7 / 5)
        self.assertAlmostEqual(t[1], 9 - 4 * 7 / 5)  # 3.4; the 0 row is ignored

    def test_lookup(self):
        t = percentile_thresholds(L1_UNDERSTANDS_16)
        for score, expected in [
            (0, "<1"), (3, "<1"), (4, "1"), (9, "5"), (10, "5"), (11, "6"),
            (52, "50"), (86, "96"), (88, "99"), (400, "99"),
        ]:
            with self.subTest(score=score):
                self.assertEqual(percentile_of(score, t), expected)

    def test_ties_take_the_highest_percentile(self):
        table = {p: 0 if p <= 10 else p for p in range(1, 100)}
        self.assertEqual(percentile_of(0, percentile_thresholds(table)), "10")

    def test_no_norms(self):
        self.assertEqual(percentile_thresholds({0: -5}), {})  # Spanish CAT, 8-11 months
        self.assertEqual(percentile_thresholds({999: 40}), {})
        self.assertIsNone(percentile_of(3, {}))


def make_norms(instrument, title, table, age=20):
    """table: percentile -> (both, boy, girl)."""
    score = InstrumentScore.objects.create(
        instrument=instrument, title=title, category="word", scoring_measures="produces"
    )
    for percentile, (both, boy, girl) in table.items():
        Benchmark.objects.create(
            instrument=instrument, instrument_score=score, percentile=percentile,
            age=age, raw_score=both, raw_score_boy=boy, raw_score_girl=girl,
        )
    return score


@tag("scoring")
class CatScoringTest(TestCase):
    """CAT is scored from the stored ability estimate, not item responses (#686)."""

    def setUp(self):
        self.instrument = Instrument.objects.create(
            name="Testish_CAT", verbose_name="Testish CAT", language="Testish",
            form="CAT", min_age=12, max_age=36,
        )
        make_norms(self.instrument, "Benchmark Theta", {
            5: (-1.0, -1.2, -0.8), 10: (-0.5, -0.7, -0.3),
            50: (0.0, -0.2, 0.2), 99: (1.0, 0.8, 1.2),
        })
        make_norms(self.instrument, "Total Produced", {
            5: (10, 8, 12), 10: (20, 16, 24), 50: (100, 90, 110), 99: (300, 280, 320),
        })

    def test_cat_norms(self):
        self.assertEqual(
            cat_norms(self.instrument, 20, 0.0, "F"),
            # girls: theta 0.0 sits between 10 (-0.3) and 50 (0.2): 10 + 40 * 0.3 / 0.5 = 34
            {"est_theta_percentile": "50", "raw_score": 100,
             "est_theta_percentile_sex": "34", "raw_score_sex": round(24 + 24 * 86 / 40)},
        )
        low = cat_norms(self.instrument, 20, -2.0, "O")
        self.assertEqual(low["est_theta_percentile"], "<1")
        self.assertEqual(low["raw_score"], 2)  # the 1st, extended below the 5th: 10 - 4 * 10 / 5
        self.assertEqual(low["est_theta_percentile_sex"], NOT_COMPUTED)

    def test_summary_scores_use_theta(self):
        study = Study.objects.create(
            researcher=User.objects.create_user("cat-owner"), name="cat study",
            instrument=self.instrument,
        )
        admin = Administration.objects.create(
            study=study, subject_id=1, repeat_num=1, url_hash="c" * 64,
            completed=True, due_date=timezone.now(),
        )
        BackgroundInfo.objects.create(
            administration=admin, **{**BACKGROUND_DEFAULTS, "age": 20, "sex": "M"}
        )
        CatResponse.objects.create(administration=admin, est_theta=0.0)
        update_summary_scores(admin)
        rows = dict(SummaryData.objects.filter(administration=admin).values_list("title", "value"))
        self.assertEqual(rows["Benchmark Theta"], "0.0")
        self.assertEqual(rows["Benchmark Theta Percentile-both"], "50")
        self.assertEqual(rows["Total Produced"], "100")
        self.assertEqual(rows["Total Produced Percentile-both"], "50")
