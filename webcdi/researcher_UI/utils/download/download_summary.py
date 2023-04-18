from django.http import HttpResponse, HttpResponseServerError
from researcher_UI.models import administration
from cdi_forms.models import BackgroundInfo
import pandas as pd
import numpy as np
from django.urls import reverse
from django.contrib.sites.shortcuts import get_current_site
from researcher_UI.utils.format_admin import format_admin_header, format_admin_data
from researcher_UI.utils.study_score import get_study_scores
from researcher_UI.utils.score_headers import get_score_headers
from researcher_UI.utils.background_header import get_background_header


def download_summary(request, study_obj, administrations=None):
    """
    Create the HttpResponse object with the appropriate CSV header.
    """

    response = HttpResponse(content_type="text/csv")  # Format response as a CSV
    filename = study_obj.name + "_summary.csv"
    response["Content-Disposition"] = (
        'attachment; filename="' + filename + '"'
    )  # Name the CSV response

    administrations = (
        administrations
        if administrations is not None
        else administration.objects.filter(study=study_obj)
    )
    if not administrations.filter(completed=True).exists():
        return HttpResponseServerError("You must select at least 1 completed survery")

    admin_header = format_admin_header(study_obj)

    # Fetch background data variables
    background_header = get_background_header(study_obj)

    # Format background data responses for pandas dataframe and eventual printing
    background_data = BackgroundInfo.objects.values().filter(
        administration__in=administrations
    )

    BI_choices = {}

    fields = BackgroundInfo._meta.get_fields()
    for field in fields:
        if field.choices:
            field_choices = dict(field.choices)
            for k, v in list(field_choices.items()):
                if str(k) == str(v):
                    field_choices.pop(k, None)
            BI_choices[field.name] = {str(k): str(v) for k, v in field_choices.items()}

    new_background = (
        pd.DataFrame.from_records(background_data).astype(str).replace(BI_choices)
    )
    new_background["administration_id"] = new_background["administration_id"].astype(
        "int64"
    )

    # Add scoring
    melted_scores = get_study_scores(administrations)
    if len(melted_scores) < 1:
        return HttpResponseServerError(f"There are no data in the study(ies) to report")

    score_header = get_score_headers(study_obj)
    melted_scores.set_index("administration_id")
    missing_columns = list(set(score_header) - set(melted_scores.columns))
    if missing_columns:
        melted_scores = melted_scores.reindex(
            columns=np.append(melted_scores.columns.values, missing_columns)
        )

    try:
        background_answers = pd.merge(
            new_background, melted_scores, how="outer", on="administration_id"
        )
    except:
        background_answers = pd.DataFrame(
            columns=list(new_background) + list(melted_scores)
        )

    admin_data = format_admin_data(pd, study_obj, administrations, admin_header)

    # Merge administration data into already combined background/CDI form dataframe
    combined_data = pd.merge(
        admin_data, background_answers, how="outer", on="administration_id"
    )

    # Recreate link for administration
    test_url = "".join(
        [
            "http://",
            get_current_site(request).domain,
            reverse("administer_cdi_form", args=["a" * 64]),
        ]
    ).replace("a" * 64 + "/", "")
    combined_data["link"] = test_url + combined_data["link"]

    # Organize columns
    combined_data = combined_data[admin_header + background_header + score_header]
    combined_data = combined_data.replace("nan", "", regex=True)
    combined_data = combined_data.replace("None", "", regex=True)
    combined_data["child_ethnicity"].replace("[]", "", inplace=True)
    combined_data["other_languages"].replace("[]", "", inplace=True)

    # add footer
    combined_data = combined_data.append({'study_name': '3rd Edition (Marchman et al., 2023)'}, ignore_index=True)

    # Turn pandas dataframe into a CSV
    combined_data.to_csv(response, encoding="utf-8", index=False)

    return response
