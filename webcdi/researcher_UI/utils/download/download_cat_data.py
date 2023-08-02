import pandas as pd
from cdi_forms.cat_forms.models import CatResponse
from cdi_forms.models import BackgroundInfo
from django.http import HttpResponse
from researcher_UI.models import Benchmark, administration
from researcher_UI.utils.format_admin import format_admin_data, format_admin_header


def download_cat_data(request, study_obj, administrations=None, adjusted=False):
    response = HttpResponse(content_type="text/csv")
    filename = study_obj.name + "_items.csv"
    response["Content-Disposition"] = (
        'attachment; filename="' + filename + '"'
    )  # Name the CSV response

    administrations = (
        administrations
        if administrations is not None
        else administration.objects.filter(study=study_obj)
    )

    admin_header = format_admin_header(study_obj)
    admin_data = format_admin_data(pd, study_obj, administrations, admin_header)

    # Fetch background data variables
    background_data = BackgroundInfo.objects.values().filter(
        administration__in=administrations
    )
    pd_background_data = pd.DataFrame.from_records(background_data)

    items = []
    for count in range(678):
        items.append(count + 1)

    answers = CatResponse.objects.values(
        "administration_id", "est_theta", "administered_words", "administered_responses"
    ).filter(administration__in=administrations)
    rows = []
    for answer in answers:
        row = {}
        row["administration_id"] = answer["administration_id"]
        row["est_theta"] = answer["est_theta"]

        if answer["administered_words"]:
            count = 0
            for word in answer["administered_words"]:
                row[word] = answer["administered_responses"][count]
                count += 1

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
        benchmarks = Benchmark.objects.filter(instrument=study_obj.instrument).order_by('percentile')
        rows = []
        for obj in administrations:
            row = {}
            row["administration_id"] = obj.id
            
            age = obj.backgroundinfo.age
            if adjusted and not obj.backgroundinfo.born_on_due_date:
                if obj.backgroundinfo.early_or_late == 'early':
                    age = obj.backgroundinfo.age + obj.backgroundinfo.due_date_diff
                elif obj.backgroundinfo.early_or_late == 'late':
                    age = obj.backgroundinfo.age - obj.backgroundinfo.due_date_diff
                row['adjusted age'] = age
                
            answer = next(item for item in answer_rows if item["administration_id"] == obj.id)
            for b in benchmarks.filter(age=age):
                if answer['est_theta']:
                    if answer['est_theta'] < b.raw_score:
                        row['est_theta_percentile'] = b.percentile
                    if obj.backgroundinfo.sex == 'M':
                        if answer['est_theta'] < b.raw_score_boy:
                            row['est_theta_percentile_sex'] = b.percentile
                    if obj.backgroundinfo.sex == 'F':
                        if answer['est_theta'] < b.raw_score_girl:
                            row['est_theta_percentile_sex'] = b.percentile
            rows.append(row)
        pd_norms = pd.DataFrame.from_dict(rows)

    combined_data = pd.merge(
        combined_data, pd_norms, how="outer", on="administration_id"
    )

    # Turn pandas dataframe into a CSV
    combined_data.to_csv(response, encoding="utf-8", index=False)

    # Return CSV
    return response
