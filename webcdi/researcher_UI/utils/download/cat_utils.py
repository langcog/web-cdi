import logging

import pandas as pd
from django.db.models import Q

from researcher_UI.models import Benchmark

logger = logging.getLogger(__name__)


def get_pd_norms(study_obj, administrations, adjusted, answer_rows):
    q = Q(instrument=study_obj.instrument, instrument_score__title="Benchmark Theta")
    if Benchmark.objects.filter(q).exists():
        benchmarks = Benchmark.objects.filter(q).order_by("percentile")
        max_age = Benchmark.objects.filter(q).order_by("-age").first().age
        min_age = Benchmark.objects.filter(q).order_by("age").first().age

        rows = []
        for obj in administrations:
            row = {}
            row["administration_id"] = obj.id

            try:
                age = obj.backgroundinfo.age
            except:
                continue
            if adjusted:
                logger.debug(f"Born on due date: {obj.backgroundinfo.born_on_due_date}")
                if obj.backgroundinfo.born_on_due_date:
                    if obj.backgroundinfo.early_or_late == "early":
                        age = obj.backgroundinfo.age - int(
                            obj.backgroundinfo.due_date_diff / 4
                        )
                    elif obj.backgroundinfo.early_or_late == "late":
                        age = obj.backgroundinfo.age + int(
                            obj.backgroundinfo.due_date_diff / 4
                        )
                row["Adjusted Age"] = age

                logger.debug(f"Adjusted Age is {age}")

            if age > max_age:
                age = max_age
            if age < min_age:
                age = min_age

            try:
                answer = next(
                    item for item in answer_rows if item["administration_id"] == obj.id
                )
            except Exception as e:
                continue

            for b in benchmarks.filter(age=age):
                row["Benchmarking Cohort Age"] = age
                if answer["est_theta"]:
                    if answer["est_theta"] > b.raw_score:
                        row["est_theta_percentile"] = b.percentile if b.percentile > 0 else '<1'
                    if obj.backgroundinfo.sex == "M":
                        if answer["est_theta"] > b.raw_score_boy:
                            row["est_theta_percentile_sex"] = b.percentile if b.percentile > 0 else '<1'
                    if obj.backgroundinfo.sex == "F":
                        if answer["est_theta"] > b.raw_score_girl:
                            row["est_theta_percentile_sex"] = b.percentile if b.percentile > 0 else '<1'
            if "est_theta_percentile" in row:
                try:
                    q = Q(
                        instrument=study_obj.instrument,
                        instrument_score__title="Total Produced",
                        age=age,
                        percentile=row["est_theta_percentile"],
                    )
                    row["raw_score"] = (
                        Benchmark.objects.filter(q)
                        .order_by("-instrument__form")[0]
                        .raw_score
                    )
                    if obj.backgroundinfo.sex == "M":
                        row["raw_score_sex"] = (
                            Benchmark.objects.filter(q)
                            .order_by("-instrument__form")[0]
                            .raw_score_boy
                        )
                    elif obj.backgroundinfo.sex == "F":
                        row["raw_score_sex"] = (
                            Benchmark.objects.filter(q)
                            .order_by("-instrument__form")[0]
                            .raw_score_girl
                        )
                except Exception as e:
                    logger.debug(e)
                    pass
            rows.append(row)
        return pd.DataFrame.from_dict(rows)
