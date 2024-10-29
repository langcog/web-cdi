import logging

import pandas as pd
from django.db.models import Q
from django.http import HttpResponse

from cdi_forms.cat_forms.models import CatResponse
from cdi_forms.models import BackgroundInfo
from researcher_UI.models import Administration
from researcher_UI.utils.format_admin import (format_admin_data,
                                              format_admin_header)

from .cat_utils import get_pd_norms

# Get an instance of a logger
logger = logging.getLogger("debug")


def download_cat_data(
    request, study_obj, administrations=None, adjusted=False, summary=False
):
    response = HttpResponse(content_type="text/csv")
    filename = study_obj.name + "_items.csv"
    response["Content-Disposition"] = (
        'attachment; filename="' + filename + '"'
    )  # Name the CSV response

    administrations = (
        administrations
        if administrations is not None
        else Administration.objects.filter(study=study_obj, is_active=True)
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

    if summary:
        answers = CatResponse.objects.values("administration_id", "est_theta").filter(
            administration__in=administrations
        )
    else:
        answers = CatResponse.objects.values(
            "administration_id",
            "est_theta",
            "administered_words",
            "administered_responses",
        ).filter(administration__in=administrations)
    rows = []
    for answer in answers:
        row = {}
        row["administration_id"] = answer["administration_id"]
        row["est_theta"] = answer["est_theta"]

        if not summary and answer["administered_words"]:
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

    # Get PD Norms
    pd_norms = get_pd_norms(study_obj, administrations, adjusted, answer_rows)

    combined_data = pd.merge(
        combined_data, pd_norms, how="outer", on="administration_id"
    )

    if study_obj.instrument.language in [
        "French French"
    ] and study_obj.instrument.form in [
        "CAT",
    ]:
        pd.concat(
            [
                combined_data,
                pd.DataFrame(
                    [
                        {
                            "study_name": "NOTE:  The Ns for the by sex norms are small (some are <5)."
                        }
                    ]
                ),
            ],
            ignore_index=True,
        )

    # Turn pandas dataframe into a CSV
    combined_data.to_csv(response, encoding="utf-8", index=False)

    # Return CSV
    return response
