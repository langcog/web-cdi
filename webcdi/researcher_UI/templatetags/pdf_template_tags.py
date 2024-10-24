import logging

from django import template
from django.db.models import Max, Min, Q

from researcher_UI.models import (Administration, Benchmark, SummaryData,
                                  administration_data)

register = template.Library()


logger = logging.getLogger("debug")


@register.simple_tag(takes_context=True)
def get_adjusted_summary_date(context, administration_id, data):
    if "adjusted" in context:
        data += " (adjusted)"
    if SummaryData.objects.filter(
        administration=administration_id, title=data
    ).exists():
        res = SummaryData.objects.get(
            administration=administration_id, title=data
        ).value
        if res == "":
            res = 0
    else:
        res = 0
    return res


@register.simple_tag(takes_context=True)
def get_true_false(context, administration_id, data):
    if get_adjusted_summary_date(context, administration_id, data) in [
        1,
        "1",
        True,
        "true",
        "True",
    ]:
        return "True"
    return "False"


@register.simple_tag(takes_context=True)
def get_cat_benchmark(context, administration_id, data):
    administration = Administration.objects.get(id=int(administration_id))
    row = {
        "est_theta_percentile": 0,
        "est_theta_percentile_sex": 0,
        "raw_score": 0,
        "raw_score_sex": 0,
    }

    if "adjusted" in context:
        age = get_adjusted_benchmark_age(administration_id)
    else:
        age = administration.backgroundinfo.age

    q = Q(
        instrument=administration.study.instrument,
        instrument_score__title="Benchmark Theta",
    )
    res = Benchmark.objects.filter(q).aggregate(Max("age"), Min("age"))
    max = res["age__max"]
    min = res["age__min"]
    if age > max:
        age = max
    if age < min:
        age = min
    row["benchmark_cohort_age"] = age

    q = Q(
        instrument=administration.study.instrument,
        instrument_score__title="Benchmark Theta",
        age=age,
    )
    if Benchmark.objects.filter(
        instrument=administration.study.instrument, age=age
    ).exists():
        benchmarks = Benchmark.objects.filter(q).order_by("percentile")
        for b in benchmarks.filter(age=age):
            if administration.catresponse.est_theta > b.raw_score:
                row["est_theta_percentile"] = b.percentile
            if administration.backgroundinfo.sex == "M":
                if administration.catresponse.est_theta > b.raw_score_boy:
                    row["est_theta_percentile_sex"] = b.percentile
            if administration.backgroundinfo.sex == "F":
                if administration.catresponse.est_theta > b.raw_score_girl:
                    row["est_theta_percentile_sex"] = b.percentile

        q = Q(
            instrument=administration.study.instrument,
            instrument_score__title="Total Produced",
            age=age,
            percentile=row["est_theta_percentile"],
        )
        try:
            row["raw_score"] = int(Benchmark.objects.get(q).raw_score)

        except Exception as e:
            logger.debug(f"Exception {e}")
            pass

        q = Q(
            instrument=administration.study.instrument,
            instrument_score__title="Total Produced",
            age=age,
            percentile=row["est_theta_percentile_sex"],
        )
        try:
            row["raw_score"] = int(Benchmark.objects.get(q).raw_score)
            if administration.backgroundinfo.sex == "M":
                row["raw_score_sex"] = int(Benchmark.objects.get(q).raw_score_boy)
            elif administration.backgroundinfo.sex == "F":
                row["raw_score_sex"] = int(Benchmark.objects.get(q).raw_score_girl)
        except Exception as e:
            logger.debug(f"Exception {e}")
            pass

    return row[data]


@register.filter
def get_adjusted_benchmark_age(administration_id):
    administration = Administration.objects.get(id=int(administration_id))
    age = administration.backgroundinfo.age
    if administration.backgroundinfo.early_or_late == "early":
        age = administration.backgroundinfo.age - int(
            administration.backgroundinfo.due_date_diff / 4
        )
    elif administration.backgroundinfo.early_or_late == "late":
        age = administration.backgroundinfo.age + int(
            administration.backgroundinfo.due_date_diff / 4
        )
    return age


@register.simple_tag(takes_context=True)
def get_benchmark_cohort_age(context, administration_id):
    administration = Administration.objects.get(id=int(administration_id))
    age = administration.backgroundinfo.age
    if "adjusted" in context:
        if context["adjusted"]:
            if administration.backgroundinfo.early_or_late == "early":
                age = administration.backgroundinfo.age - int(
                    administration.backgroundinfo.due_date_diff / 4
                )
            elif administration.backgroundinfo.early_or_late == "late":
                age = administration.backgroundinfo.age + int(
                    administration.backgroundinfo.due_date_diff / 4
                )
    res = Benchmark.objects.filter(
        instrument=administration.study.instrument
    ).aggregate(Max("age"), Min("age"))
    max = res["age__max"]
    min = res["age__min"]
    if age > max:
        age = max
    if age < min:
        age = min
    return age


@register.filter
def get_summary_data(administration_id, data):
    if SummaryData.objects.filter(
        administration=administration_id, title=data
    ).exists():
        res = SummaryData.objects.get(
            administration=administration_id, title=data
        ).value
        if res == "":
            res = 0
    else:
        res = 0
    return res


@register.filter
def get_form_data(administration_id, data):
    try:
        res = administration_data.objects.get(
            administration=administration_id, item_ID=data
        ).value
        if res == "":
            res = "Nil return"
    except Exception:
        res = f"no response provided"
    return res


@register.filter
def get_form_data_endings(administration_id, data):
    try:
        res = administration_data.objects.get(
            administration=administration_id, item_ID=data
        ).value
        if res in ["sometimes", "yes"]:
            res = "Yes"
        else:
            res = "No"
    except Exception:
        res = f"No"
    return res
