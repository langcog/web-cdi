from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from researcher_UI.forms import *
from researcher_UI.models import administration
import pandas as pd
from django.urls import reverse
from django.contrib.sites.shortcuts import get_current_site

from django.utils.translation import ugettext_lazy as _


@login_required
def download_links(request, study_obj, administrations=None):
    """Download only the associated administration links instead of the whole data spreadsheet"""

    response = HttpResponse(content_type="text/csv")  # Format response as a CSV
    response["Content-Disposition"] = (
        "attachment; filename=" + study_obj.name + "_links.csv" ""
    )  # Name CSV

    if administrations is None:
        administrations = administration.objects.filter(study=study_obj)

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
    admin_data.to_csv(
        response, encoding="utf-8", index=False
    )  # Convert dataframe into a CSV

    # Return CSV
    return response
