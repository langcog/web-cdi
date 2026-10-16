"""Scoring of completed administrations.

Raw scores come from InstrumentScore definitions; percentiles from Benchmark
norm tables. Output is identical to the original row-by-row implementation
(frozen in scores_legacy.py, checked by tests and `compare_scoring`), but an
instrument's scoring configuration is loaded once and SummaryData is written
in bulk: a few queries per administration instead of thousands (#668).

Deliberate difference from the legacy code: a response whose item_ID is not
an item of the instrument is skipped (legacy counted it under the previous
response's category, or crashed if it came first).
"""
import logging
from collections import defaultdict

from researcher_UI.models import (Benchmark, InstrumentScore, Measure,
                                  SummaryData, administration_data)

from .models import BackgroundInfo, Instrument_Forms

logger = logging.getLogger("debug")


def calc_benchmark(x1, x2, y1, y2, raw_score):
    if x1 == x2:
        return int((y1 + y2) / 2)
    gradient = float(y2 - y1) / (x2 - x1)
    a = float(y1 - (x1 * gradient))
    return int(a + raw_score * gradient)


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

    def rows(self, f, age):
        return self.benchmarks[f.pk].get(age, [])


def benchmark_scores(values, benchmarks, f, sex, adjusted):
    """Add percentile rows for score `f` to `values`.

    `benchmarks` are f's norm rows at the child's (cohort) age in percentile
    order. Percentile = the highest row whose raw score is <= the child's
    (floor lookup; interpolation via calc_benchmark is disabled since #652).
    Sex-specific percentiles exist only for M/F (#674).
    """
    benchmark = benchmarks[0]
    original_benchmark = benchmark
    if benchmark.percentile == 999:
        title = f.title + f" % yes answers at this age and sex{adjusted}"
        values.setdefault(title, "")
        if sex == "M":
            values[title] = str(benchmark.raw_score_boy)
        elif sex == "F":
            values[title] = str(benchmark.raw_score_girl)
        return

    try:
        raw_score = int(values[f.title])
    except (KeyError, ValueError, TypeError):
        raw_score = 0

    sex_score = 0
    if sex in ("M", "F"):
        column = "raw_score_boy" if sex == "M" else "raw_score_girl"
        sex_score = benchmark.percentile
        for b in benchmarks[1:]:
            if getattr(b, column) <= raw_score:
                benchmark = b
                sex_score = benchmark.percentile
            else:
                break
        values[f"{f.title} Percentile-sex{adjusted}"] = (
            "<1" if sex_score < 1 else str(sex_score)
        )

    if not benchmark.raw_score == 9999:
        benchmark = original_benchmark
        unisex_score = benchmark.percentile
        for b in benchmarks[1:]:
            if b.raw_score <= raw_score:
                benchmark = b
                unisex_score = benchmark.percentile
            else:
                break
        values[f.title + f" Percentile-both{adjusted}"] = (
            "<1" if unisex_score < 1 else str(unisex_score)
        )


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
    if adjusted_benchmark_age is not None and background_info.early_or_late == "early":
        try:
            adjusted_benchmark_age = adjusted_benchmark_age - int(
                background_info.due_date_diff / 4
            )
        except Exception:
            pass
    elif adjusted_benchmark_age is not None and background_info.early_or_late == "late":
        try:
            adjusted_benchmark_age = age + int(background_info.due_date_diff / 4)
        except Exception:
            pass
    values["adjusted benchmark age"] = str(adjusted_benchmark_age)

    if adjusted_benchmark_age < min_age:
        adjusted_benchmark_age = min_age
    if adjusted_benchmark_age > max_age:
        adjusted_benchmark_age = max_age
    values["adjusted benchmark cohort age"] = str(adjusted_benchmark_age)

    for f in scoring.scores:
        if not scoring.benchmarks.get(f.pk):
            continue
        rows = scoring.rows(f, age)
        if not rows:
            raise IndexError(f"No benchmark for {f} at age {age}")
        adjusted_rows = scoring.rows(f, adjusted_benchmark_age)
        if not adjusted_rows:
            # legacy: fall back to the score's youngest age, and keep using it
            # for the remaining scores of this administration
            adjusted_benchmark_age = min(scoring.benchmarks[f.pk])
            adjusted_rows = scoring.rows(f, adjusted_benchmark_age)
        benchmark_scores(values, rows, f, background_info.sex, "")
        benchmark_scores(values, adjusted_rows, f, background_info.sex, " (adjusted)")
    return True


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
