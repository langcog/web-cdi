import logging

import pandas as pd
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q

from cdi_forms.scores import cat_norms
from researcher_UI.models import Benchmark

logger = logging.getLogger("debug")


def get_pd_norms(study_obj, administrations, adjusted, answer_rows):
    logger.debug(f"get_pd_norms")
    q = Q(instrument=study_obj.instrument, instrument_score__title="Benchmark Theta")
    if Benchmark.objects.filter(q).exists():
        max_age = Benchmark.objects.filter(q).order_by("-age").first().age
        min_age = Benchmark.objects.filter(q).order_by("age").first().age

        rows = []
        for obj in administrations:
            row = {}
            row["administration_id"] = obj.id

            try:
                age = obj.backgroundinfo.age
            except ObjectDoesNotExist:
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

            row["Benchmarking Cohort Age"] = age
            if answer["est_theta"] is not None:
                norms = cat_norms(
                    obj.study.instrument, age, answer["est_theta"], obj.backgroundinfo.sex
                )
                row.update({k: v for k, v in norms.items() if v is not None})
            rows.append(row)
        return pd.DataFrame.from_dict(rows)
