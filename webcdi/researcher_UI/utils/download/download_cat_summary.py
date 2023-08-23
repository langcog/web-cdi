import pandas as pd
from cdi_forms.cat_forms.models import CatResponse
from cdi_forms.models import BackgroundInfo
from django.http import HttpResponse
from researcher_UI.models import Benchmark, Administration
from researcher_UI.utils.format_admin import format_admin_data, format_admin_header


def download_cat_summary(request, study_obj, administrations=None, adjusted=False):
    response = HttpResponse(content_type="text/csv")  # Format response as a CSV
    filename = study_obj.name + "_items.csv"
    response["Content-Disposition"] = (
        'attachment; filename="' + filename + '"'
    )  # Name the CSV response

    administrations = (
        administrations
        if administrations is not None
        else Administration.objects.filter(study=study_obj)
    )

    admin_header = format_admin_header(study_obj)
    admin_data = format_admin_data(pd, study_obj, administrations, admin_header)

    # Fetch background data variables
    background_data = BackgroundInfo.objects.values().filter(
        administration__in=administrations
    )
    pd_background_data = pd.DataFrame.from_records(background_data)

    items = []
    for count in range(670):
        items.append(count + 1)

    answers = CatResponse.objects.values("administration_id", "est_theta").filter(
        administration__in=administrations
    )
    rows = []
    for answer in answers:
        row = {}
        row["administration_id"] = answer["administration_id"]
        row["est_theta"] = answer["est_theta"]

        rows.append(row)

    answer_rows = rows
    pd_answers = pd.DataFrame.from_dict(rows)

    pd_background_answers = pd.merge(
        pd_background_data, pd_answers, how="outer", on="administration_id"
    )

    combined_data = pd.merge(
        admin_data, pd_background_answers, how="outer", on="administration_id"
    )

    # norms
    if Benchmark.objects.filter(instrument=study_obj.instrument).exists():
        benchmarks = Benchmark.objects.filter(instrument=study_obj.instrument).order_by(
            "percentile"
        )
        rows = []
        for obj in administrations:
            row = {}
            row["administration_id"] = obj.id

            age = obj.backgroundinfo.age

            answer = next(
                item for item in answer_rows if item["administration_id"] == obj.id
            )
            for b in benchmarks.filter(age=age):
                if answer["est_theta"]:
                    if answer["est_theta"] > b.raw_score:
                        row["est_theta_percentile"] = b.percentile
                    if obj.backgroundinfo.sex == "M":
                        if answer["est_theta"] > b.raw_score_boy:
                            row["est_theta_percentile_sex"] = b.percentile
                    if obj.backgroundinfo.sex == "F":
                        if answer["est_theta"] > b.raw_score_girl:
                            row["est_theta_percentile_sex"] = b.percentile
            if "est_theta_percentile" in row:
                try:
                    row["raw_score"] = (
                        Benchmark.objects.filter(
                            age=age,
                            instrument_score__title__in=[
                                "Total Produced",
                                "Words Produced",
                                "Palabras que dice",
                            ],
                            instrument__language=obj.study.instrument.language,
                            percentile=row["est_theta_percentile"],
                        )
                        .order_by("-study__instrument__form")[0]
                        .raw_score
                    )
                    if obj.backgroundinfo.sex == "M":
                        row["raw_score_sex"] = (
                            Benchmark.objects.filter(
                                age=age,
                                instrument_score__title__in=[
                                    "Total Produced",
                                    "Words Produced",
                                ],
                                instrument__language=obj.study.instrument.language,
                                percentile=row["est_theta_percentile_sex"],
                            )
                            .order_by("instrument_score__title")[0]
                            .raw_score_boy
                        )
                    elif obj.backgroundinfo.sex == "F":
                        row["raw_score_sex"] = (
                            Benchmark.objects.filter(
                                age=age,
                                instrument_score__title__in=[
                                    "Total Produced",
                                    "Words Produced",
                                ],
                                instrument__language=obj.study.instrument.language,
                                percentile=row["est_theta_percentile_sex"],
                            )
                            .order_by("instrument_score__title")[0]
                            .raw_score_girl
                        )
                except Exception as e:
                    pass
            rows.append(row)
        pd_norms = pd.DataFrame.from_dict(rows)

    combined_data = pd.merge(
        combined_data, pd_norms, how="outer", on="administration_id"
    )
    # Turn pandas dataframe into a CSV
    combined_data.to_csv(response, encoding="utf-8", index=False)

    # Return CSV
    return response
