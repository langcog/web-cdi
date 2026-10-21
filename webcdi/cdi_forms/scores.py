"""Scoring of completed administrations.

Raw scores come from InstrumentScore definitions; percentiles from Benchmark
norm tables. An instrument's scoring configuration is loaded once and
SummaryData is written in bulk: a few queries per administration (#668; the
rewrite matched the original row-by-row scorer exactly on 500 production
administrations before the percentile rules below changed, #687).

Percentile rules (Virginia Marchman, #686), shared by the scorer, the CAT
report and the CAT download via `percentile_thresholds`/`percentile_of`:
- tables with every percentile 1-99 are used as published;
- coarser tables (5, 10, ..., 95, 99) are filled in linearly at 1-point steps;
- below the lowest published percentile (the 5th), the table is extended at
  the slope between the two lowest (5th to 10th) to establish the 1st;
- a score below the 1st percentile is "<1"; the highest percentile is 99;
- ties (several percentiles with the same raw score) take the highest;
- sex-specific results for a child not recorded as M or F are "not computed".

A response whose item_ID is not an item of the instrument is skipped.
"""
import logging
from collections import defaultdict

from django.conf import settings

from researcher_UI.models import (Benchmark, InstrumentScore, Measure,
                                  SummaryData, administration_data)

from .models import BackgroundInfo, Instrument_Forms

logger = logging.getLogger("debug")


NOT_COMPUTED = "not computed"
SEX_COLUMNS = {"M": "raw_score_boy", "F": "raw_score_girl"}


def percentile_thresholds(points):
    """{percentile: raw score} from one norm table -> {1..99: threshold}.

    Percentiles outside 1-99 (0 rows, the 999 "% yes" marker) are ignored.
    Returns {} when the table has no usable rows (no norms).
    """
    known = sorted((p, v) for p, v in points.items() if 1 <= p <= 99)
    if not known:
        return {}
    thresholds = {}
    for (a, ra), (b, rb) in zip(known, known[1:]):
        for p in range(a, b):
            thresholds[p] = ra + (rb - ra) * (p - a) / (b - a)
    top, rtop = known[-1]
    thresholds[top] = rtop
    low, rlow = known[0]
    if low > 1 and len(known) > 1:
        step = (known[1][1] - rlow) / (known[1][0] - low)
        for p in range(1, low):
            thresholds[p] = rlow - (low - p) * step
    return thresholds


def table_thresholds(rows, column="raw_score"):
    """Thresholds for one column (raw_score / raw_score_boy / raw_score_girl) of Benchmark rows."""
    return percentile_thresholds({b.percentile: getattr(b, column) for b in rows})


def percentile_of(score, thresholds):
    """The highest percentile whose threshold `score` reaches, as text.

    "<1" below the 1st percentile; None when there are no norms.
    """
    if not thresholds:
        return None
    result = "<1"
    for p in sorted(thresholds):
        if thresholds[p] <= score:
            result = str(p)
        else:
            break
    return result


def value_at(percentile, thresholds):
    """The raw score at a percentile ("<1" -> the 1st), for estimates like CAT words produced."""
    if not thresholds or percentile is None:
        return None
    p = 1 if percentile == "<1" else int(percentile)
    return thresholds.get(p)


def prematurity_adjustment(background_info):
    """Months to add to the child's age for "adjusted" scores (#726).

    Only when the parent answered "yes" to "Was your child born earlier or
    later than their due date?" (born_on_due_date == 1) and gave early/late and
    the number of weeks: -weeks/4 if early, +weeks/4 if late (whole months).
    Otherwise 0, including leftover early/late values from another answer.
    """
    if background_info.born_on_due_date != 1 or not background_info.due_date_diff:
        return 0
    months = int(background_info.due_date_diff / 4)
    if background_info.early_or_late == "early":
        return -months
    if background_info.early_or_late == "late":
        return months
    return 0


class InstrumentScoring:
    """One instrument's scoring configuration, loaded with a handful of queries.

    Bulk commands build one per instrument and reuse it across administrations.
    """

    def __init__(self, instrument):
        self.instrument = instrument
        self.item_category = {
            item_id: scoring_category or item_type
            for item_id, scoring_category, item_type in Instrument_Forms.objects.filter(
                instrument=instrument
            ).values_list("itemID", "scoring_category", "item_type")
        }
        self.scores = list(InstrumentScore.objects.filter(instrument=instrument))
        self.categories = {f.pk: f.category.split(";") for f in self.scores}
        self.measures = {f.pk: f.scoring_measures.split(";") for f in self.scores}
        self.weights = defaultdict(dict)
        for m in Measure.objects.filter(instrument_score__in=self.scores):
            self.weights[m.instrument_score_id][m.key] = m.value
        # score id -> age -> rows in percentile order (Benchmark.Meta.ordering)
        self.benchmarks = defaultdict(lambda: defaultdict(list))
        ages = []
        for b in Benchmark.objects.filter(instrument=instrument):
            self.benchmarks[b.instrument_score_id][b.age].append(b)
            ages.append(b.age)
        self.min_age = min(ages) if ages else None
        self.max_age = max(ages) if ages else None

    def weight(self, f, key):
        try:
            return self.weights[f.pk][key]
        except KeyError:
            raise Measure.DoesNotExist(f"No measure {key!r} for {f}")

    def rows_near(self, f, age):
        """f's norm rows at `age`, clamped to f's own age range: an
        instrument's scores can have different ranges (English CAT: Total
        Produced 8-36 months, Benchmark Theta 12-36)."""
        ages = self.benchmarks[f.pk]
        if not ages:
            return []
        return self.rows(f, min(max(age, min(ages)), max(ages)))

    def rows(self, f, age):
        return self.benchmarks[f.pk].get(age, [])


def benchmark_scores(values, benchmarks, f, sex, adjusted):
    """Add percentile rows for score `f` to `values`.

    `benchmarks` are f's norm rows at the child's (cohort) age; see the
    module docstring for the rules.
    """
    benchmark = benchmarks[0]
    if benchmark.percentile == 999:
        title = f.title + f" % yes answers at this age and sex{adjusted}"
        if sex in SEX_COLUMNS:
            values[title] = str(getattr(benchmark, SEX_COLUMNS[sex]))
        else:
            values[title] = NOT_COMPUTED
        return

    unisex = table_thresholds(benchmarks)
    if not unisex:  # no norms at this age
        return
    try:
        raw_score = float(values[f.title])
    except (KeyError, ValueError, TypeError):
        raw_score = 0

    sex_title = f"{f.title} Percentile-sex{adjusted}"
    if sex in SEX_COLUMNS:
        sex_score = percentile_of(
            raw_score, table_thresholds(benchmarks, SEX_COLUMNS[sex])
        )
        if sex_score is not None:
            values[sex_title] = sex_score
    else:
        values[sex_title] = NOT_COMPUTED
    values[f"{f.title} Percentile-both{adjusted}"] = percentile_of(raw_score, unisex)


def _compute(administration_instance, scoring, values):
    """Fill `values` (title -> str). Returns True if the administration is fully scored."""
    for f in scoring.scores:
        values.setdefault(f.title, "")
        if f.kind == "count":
            values[f.title] = "0"

    for item_id, value in administration_data.objects.filter(
        administration=administration_instance
    ).values_list("item_ID", "value"):
        scoring_category = scoring.item_category.get(item_id)
        if scoring_category is None:
            logger.error(
                f"Unknown item_ID {item_id} for instrument {scoring.instrument}; not scored"
            )
            continue
        for f in scoring.scores:
            if scoring_category not in scoring.categories[f.pk]:
                continue
            if f.kind == "count":
                if value in scoring.measures[f.pk]:
                    if values[f.title] == "":
                        values[f.title] = str(scoring.weight(f, value))
                    else:
                        values[f.title] = str(
                            int(values[f.title]) + scoring.weight(f, value)
                        )
            else:
                values[f.title] = value

    if scoring.min_age is None:  # instrument has no norms
        return True

    try:
        background_info = BackgroundInfo.objects.get(
            administration=administration_instance
        )
    except Exception:
        return False  # legacy behavior: left unscored, retried by cron

    min_age, max_age = scoring.min_age, scoring.max_age
    try:
        age = background_info.age
        values["benchmark age"] = str(age)
        if age < min_age:
            age = min_age
        if age > max_age:
            age = max_age
    except Exception:
        age = None
    values["benchmark cohort age"] = str(age)

    adjusted_benchmark_age = background_info.age
    if adjusted_benchmark_age is not None:
        adjusted_benchmark_age += prematurity_adjustment(background_info)
    values["adjusted benchmark age"] = str(adjusted_benchmark_age)

    if adjusted_benchmark_age < min_age:
        adjusted_benchmark_age = min_age
    if adjusted_benchmark_age > max_age:
        adjusted_benchmark_age = max_age
    values["adjusted benchmark cohort age"] = str(adjusted_benchmark_age)

    if scoring.instrument.form in settings.CAT_FORMS and not _cat_scores(
        administration_instance, scoring, values, age
    ):
        return True

    for f in scoring.scores:
        if not scoring.benchmarks.get(f.pk):
            continue
        rows = scoring.rows_near(f, age)
        if not rows:
            raise IndexError(f"No benchmark for {f} at age {age}")
        adjusted_rows = scoring.rows_near(f, adjusted_benchmark_age)
        benchmark_scores(values, rows, f, background_info.sex, "")
        benchmark_scores(values, adjusted_rows, f, background_info.sex, " (adjusted)")
    return True


def _cat_scores(administration_instance, scoring, values, age):
    """CAT ability lives in CatResponse, not in item responses: score theta
    itself, and estimate words produced as the Total Produced norm at the
    child's theta percentile. False if there is no estimate to score."""
    try:
        theta = administration_instance.catresponse.est_theta
    except Exception:
        theta = None
    if theta is None:
        values["Benchmark Theta"] = ""
        values["Total Produced"] = ""
        return False
    values["Benchmark Theta"] = str(theta)
    by_title = {f.title: f for f in scoring.scores}
    theta_rows = scoring.rows_near(by_title["Benchmark Theta"], age)
    produced_rows = scoring.rows_near(by_title["Total Produced"], age)
    estimate = value_at(
        percentile_of(theta, table_thresholds(theta_rows)),
        table_thresholds(produced_rows),
    )
    values["Total Produced"] = "" if estimate is None else str(max(0, round(estimate)))
    return True


def cat_norms(instrument, age, theta, sex):
    """CAT report/download figures at one (cohort) age: theta percentiles and
    estimated words produced (the Total Produced norm at that percentile).
    Values are None where there are no norms (or no theta)."""
    if theta is None:
        return dict.fromkeys(
            ["est_theta_percentile", "raw_score", "est_theta_percentile_sex", "raw_score_sex"]
        )
    rows = defaultdict(list)
    for b in Benchmark.objects.filter(instrument=instrument, age=age).select_related(
        "instrument_score"
    ):
        rows[b.instrument_score.title].append(b)
    theta_rows, produced_rows = rows["Benchmark Theta"], rows["Total Produced"]

    def estimate(percentile, column):
        words = value_at(percentile, table_thresholds(produced_rows, column))
        return None if words is None else max(0, round(words))

    result = {}
    result["est_theta_percentile"] = percentile_of(theta, table_thresholds(theta_rows))
    result["raw_score"] = estimate(result["est_theta_percentile"], "raw_score")
    if sex in SEX_COLUMNS:
        column = SEX_COLUMNS[sex]
        result["est_theta_percentile_sex"] = percentile_of(
            theta, table_thresholds(theta_rows, column)
        )
        result["raw_score_sex"] = estimate(result["est_theta_percentile_sex"], column)
    else:
        result["est_theta_percentile_sex"] = NOT_COMPUTED
        result["raw_score_sex"] = NOT_COMPUTED
    return result


def update_summary_scores(administration_instance, scoring=None):
    """Rebuild an administration's SummaryData. Pass `scoring` to reuse config across calls."""
    if not administration_instance.completed:
        return
    if scoring is None:
        scoring = InstrumentScoring(administration_instance.study.instrument)
    SummaryData.objects.filter(administration=administration_instance).delete()
    values = {}
    try:
        complete = _compute(administration_instance, scoring, values)
    finally:
        # like the legacy code, keep whatever was computed before an error
        SummaryData.objects.bulk_create(
            SummaryData(administration=administration_instance, title=t, value=v)
            for t, v in values.items()
        )
    if complete:
        administration_instance.scored = True
        administration_instance.save()
