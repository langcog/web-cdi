from django.http import HttpResponse
from researcher_UI.forms import *
from researcher_UI.models import administration
from cdi_forms.models import BackgroundInfo
import pandas as pd
from django.utils.translation import ugettext_lazy as _
from cdi_forms.cat_forms.models import CatResponse
from researcher_UI.utils.format_admin import format_admin_header, format_admin_data


def download_cat_summary(request, study_obj, administrations=None):
    response = HttpResponse(content_type="text/csv")  # Format response as a CSV
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

    pd_answers = pd.DataFrame.from_dict(rows)

    pd_background_answers = pd.merge(
        pd_background_data, pd_answers, how="outer", on="administration_id"
    )

    combined_data = pd.merge(
        admin_data, pd_background_answers, how="outer", on="administration_id"
    )

    # add footer
    combined_data = combined_data.append({'study_name': '3rd Edition (Marchman et al., 2023)'}, ignore_index=True)

    # Turn pandas dataframe into a CSV
    combined_data.to_csv(response, encoding="utf-8", index=False)

    # Return CSV
    return response
