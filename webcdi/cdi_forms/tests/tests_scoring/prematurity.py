from django.contrib.auth.models import User
from django.test import TestCase, tag
from django.utils import timezone

from cdi_forms.cat_forms.models import CatResponse
from cdi_forms.models import BackgroundInfo
from cdi_forms.scores import update_summary_scores
from researcher_UI.models import (Administration, Benchmark, Instrument, Study,
                                  SummaryData)
from researcher_UI.templatetags.pdf_template_tags import (
    get_adjusted_benchmark_age, get_benchmark_cohort_age)
from researcher_UI.utils.download.cat_utils import get_pd_norms

from .equivalence import BACKGROUND_DEFAULTS
from .percentiles import make_norms


@tag("scoring")
class PrematurityAdjustmentTest(TestCase):
    """The scorer, the report and the CAT download adjust age for prematurity
    the same way, and only when the parent answered "yes" to "Was your child
    born earlier or later than their due date?" (born_on_due_date == 1) (#726)."""

    def setUp(self):
        instrument = Instrument.objects.create(
            name="Testish_CAT", verbose_name="Testish CAT", language="Testish",
            form="CAT", min_age=12, max_age=36,
        )
        # theta 0.0 is the 50th percentile at 20 months and the 10th at 22
        theta = make_norms(instrument, "Benchmark Theta", {
            10: (-0.5, -0.5, -0.5), 50: (0.0, 0.0, 0.0), 99: (1.0, 1.0, 1.0),
        }, age=20)
        produced = make_norms(instrument, "Total Produced", {
            10: (10, 10, 10), 50: (50, 50, 50), 99: (99, 99, 99),
        }, age=20)
        for score, table in ((theta, {10: 0.0, 50: 0.5, 99: 1.5}),
                             (produced, {10: 20, 50: 60, 99: 120})):
            for percentile, raw in table.items():
                Benchmark.objects.create(
                    instrument=instrument, instrument_score=score,
                    percentile=percentile, age=22,
                    raw_score=raw, raw_score_boy=raw, raw_score_girl=raw,
                )
        self.study = Study.objects.create(
            researcher=User.objects.create_user("cat-owner"), name="cat study",
            instrument=instrument,
        )

    def ages(self, **background):
        """(adjusted age, adjusted cohort age, theta percentile) from each path."""
        Administration.objects.all().delete()
        admin = Administration.objects.create(
            study=self.study, subject_id=1, repeat_num=1, url_hash="c" * 64,
            completed=True, due_date=timezone.now(),
        )
        BackgroundInfo.objects.create(
            administration=admin,
            **{**BACKGROUND_DEFAULTS, "age": 22, "sex": "M", **background},
        )
        CatResponse.objects.create(administration=admin, est_theta=0.0)

        update_summary_scores(admin)
        summary = dict(
            SummaryData.objects.filter(administration=admin).values_list("title", "value")
        )
        download = get_pd_norms(
            self.study, [admin], True,
            [{"administration_id": admin.id, "est_theta": 0.0}],
        ).set_index("administration_id").loc[admin.id]
        return {
            "scorer": (
                int(summary["adjusted benchmark age"]),
                int(summary["adjusted benchmark cohort age"]),
                summary["Benchmark Theta Percentile-both (adjusted)"],
            ),
            "report": (
                get_adjusted_benchmark_age(admin.id),
                get_benchmark_cohort_age({"adjusted": True}, admin.id),
                None,
            ),
            "download": (
                int(download["Adjusted Age"]),
                int(download["Benchmarking Cohort Age"]),
                download["est_theta_percentile"],
            ),
        }

    def assertAllPaths(self, results, age, cohort_age, percentile):
        for path, (got_age, got_cohort, got_percentile) in results.items():
            with self.subTest(path=path):
                self.assertEqual(got_age, age)
                self.assertEqual(got_cohort, cohort_age)
                if got_percentile is not None:
                    self.assertEqual(got_percentile, percentile)

    def test_yes_early_is_adjusted(self):
        self.assertAllPaths(
            self.ages(born_on_due_date=1, early_or_late="early", due_date_diff=8),
            20, 20, "50",
        )

    def test_yes_late_is_adjusted(self):
        # 22 + 1 month, capped at the oldest norms (22)
        self.assertAllPaths(
            self.ages(born_on_due_date=1, early_or_late="late", due_date_diff=4),
            23, 22, "10",
        )

    def test_leftover_early_or_late_without_yes_is_not_adjusted(self):
        # e.g. a parent answered "yes", filled in the weeks, then switched to
        # "no": the hidden fields used to be saved anyway
        for answer in (0, 2, None):
            with self.subTest(born_on_due_date=answer):
                self.assertAllPaths(
                    self.ages(born_on_due_date=answer, early_or_late="early",
                              due_date_diff=8),
                    22, 22, "10",
                )

    def test_missing_weeks_means_no_adjustment(self):
        self.assertAllPaths(
            self.ages(born_on_due_date=1, early_or_late="early", due_date_diff=None),
            22, 22, "10",
        )
