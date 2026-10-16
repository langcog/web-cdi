from django.test import TestCase, tag

from cdi_forms.scores import InstrumentScoring, benchmark_scores
from researcher_UI.models import Benchmark, Instrument, InstrumentScore
from researcher_UI.templatetags.pdf_template_tags import (
    get_adjusted_summary_date, get_summary_data)


@tag("scoring")
class SexPercentileTest(TestCase):
    """benchmark_scores must not invent a sex-specific percentile.

    Before #674, a child whose sex was Other, Prefer not to respond or blank
    got "<1" in "<Title> Percentile-sex", because the score started at 0 and
    only M/F updated it.
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
        self.assertEqual(rows["Total Produced Percentile-sex"], "25")
        self.assertEqual(rows["Total Produced Percentile-both"], "50")

    def test_boy_gets_boy_norms(self):
        rows = self.score_with_sex("M")
        self.assertEqual(rows["Total Produced Percentile-sex"], "50")
        self.assertEqual(rows["Total Produced Percentile-both"], "50")

    def test_other_unknown_sex_get_no_sex_percentile(self):
        for sex in ("O", "P", None, ""):
            with self.subTest(sex=sex):
                rows = self.score_with_sex(sex)
                self.assertNotIn("Total Produced Percentile-sex", rows)
                self.assertEqual(rows["Total Produced Percentile-both"], "50")


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
