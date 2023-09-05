import pandas as pd
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.http import HttpResponse
from django.urls import reverse
from researcher_UI.models import Administration


@login_required
def download_links(request, study_obj, administrations=None):
    """Download only the associated administration links instead of the whole data spreadsheet"""

    response = HttpResponse(content_type="text/csv")  # Format response as a CSV
    response["Content-Disposition"] = (
        "attachment; filename=" + study_obj.name + "_links.csv" ""
    )  # Name CSV

    if administrations is None:
        administrations = Administration.objects.filter(study=study_obj)

    admin_data = pd.DataFrame.from_records(administrations.values()).rename(
        columns={
            "id": "administration_id",
            "study_id": "study_name",
            "url_hash": "link",
        }
    )  # Grab variables from administration objects
    admin_data = admin_data[
        ["study_name", "subject_id", "repeat_num", "administration_id", "link"]
    ]  # Organize columns

    admin_data[
        "study_name"
    ] = study_obj.name  # Replace study ID number with actual study name

    # Recreate administration links and add them to dataframe
    test_url = "".join(
        [
            "http://",
            get_current_site(request).domain,
            reverse("administer_cdi_form", args=["a" * 64]),
        ]
    ).replace("a" * 64 + "/", "")
    admin_data["link"] = test_url + admin_data["link"]

    if study_obj.instrument.language in ["English"] and study_obj.instrument.form in [
        "WS",
        "WG",
    ]:
        admin_data = admin_data.append(
            {"study_name": "3rd Edition (Marchman et al., 2023)"}, ignore_index=True
        )

    admin_data.to_csv(
        response, encoding="utf-8", index=False
    )  # Convert dataframe into a CSV

    # Return CSV
    return response
