from django.test import TestCase, tag

from cdi_forms.scores import NOT_COMPUTED, InstrumentScoring, benchmark_scores
from researcher_UI.models import Benchmark, Instrument, InstrumentScore
from researcher_UI.templatetags.pdf_template_tags import (
    get_adjusted_summary_date, get_summary_data)


@tag("scoring")
class SexPercentileTest(TestCase):
    """Sex-specific percentiles use the child's sex's norms; for a child not
    recorded as M or F they are "not computed" (#674, #686).

    The table is coarse (1, 25, 50, 75), so values are filled in linearly
    between published rows; a raw score of 55 falls between rows.
    """

    def setUp(self):
        instrument = Instrument.objects.create(
            name="Test_WS",
            verbose_name="Test WS",
            language="Test",
            form="WS",
            min_age=16,
            max_age=30,
        )
        self.score = InstrumentScore.objects.create(
            instrument=instrument,
            title="Total Produced",
            category="word",
            scoring_measures="produces",
        )
        # percentile -> (unisex, boy, girl) raw-score thresholds at age 20
        for percentile, (both, boy, girl) in {
            1: (0, 0, 0),
            25: (20, 15, 25),
            50: (50, 40, 60),
            75: (100, 90, 110),
        }.items():
            Benchmark.objects.create(
                instrument=instrument,
                instrument_score=self.score,
                percentile=percentile,
                age=20,
                raw_score=both,
                raw_score_boy=boy,
                raw_score_girl=girl,
            )

    def score_with_sex(self, sex):
        scoring = InstrumentScoring(self.score.instrument)
        values = {"Total Produced": "55"}
        benchmark_scores(values, scoring.rows(self.score, 20), self.score, sex, "")
        return values

    def test_girl_gets_girl_norms(self):
        rows = self.score_with_sex("F")
        # girls: 25 + 1.4 per percentile from the 25th (25) -> 55 reached at 46
        self.assertEqual(rows["Total Produced Percentile-sex"], "46")
        self.assertEqual(rows["Total Produced Percentile-both"], "52")

    def test_boy_gets_boy_norms(self):
        rows = self.score_with_sex("M")
        # boys: 40 + 2 per percentile from the 50th -> 55 reached at 57
        self.assertEqual(rows["Total Produced Percentile-sex"], "57")
        self.assertEqual(rows["Total Produced Percentile-both"], "52")

    def test_other_unknown_sex_get_not_computed(self):
        for sex in ("O", "P", None, ""):
            with self.subTest(sex=sex):
                rows = self.score_with_sex(sex)
                self.assertEqual(rows["Total Produced Percentile-sex"], NOT_COMPUTED)
                self.assertEqual(rows["Total Produced Percentile-both"], "52")


@tag("scoring")
class MissingPercentileReportTest(TestCase):
    """The clinical report renders a missing percentile blank, a missing count as 0."""

    def test_missing_rows(self):
        self.assertEqual(get_summary_data(999999, "Total Produced Percentile-sex"), "")
        self.assertEqual(get_summary_data(999999, "Total Produced"), 0)
        self.assertEqual(
            get_adjusted_summary_date({}, 999999, "Total Produced Percentile-sex"), ""
        )
        self.assertEqual(get_adjusted_summary_date({}, 999999, "Total Produced"), 0)
