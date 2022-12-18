from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from researcher_UI.forms import *
from cdi_forms.views import model_map
import pandas as pd
from django.utils.translation import ugettext_lazy as _
import re


@login_required
def download_dictionary(request, study_obj):
    response = HttpResponse(content_type="text/csv")  # Format the response as a CSV
    response["Content-Disposition"] = (
        "attachment; filename=" + study_obj.instrument.name + "_dictionary.csv" ""
    )  # Name CSV

    raw_item_data = model_map(study_obj.instrument.name).values(
        "itemID", "item_type", "category", "definition", "gloss"
    )  # Grab the relevant variables within the appropriate instrument model
    item_data = pd.DataFrame.from_records(raw_item_data)
    item_data["definition"] = item_data["definition"].apply(
        lambda x: re.sub("__", "", x)
    )
    item_data[["itemID", "item_type", "category", "definition", "gloss"]].to_csv(
        response, encoding="utf-8", index=False
    )  # Convert nested dictionary into a pandas dataframe and then into a CSV

    # Return CSV
    return response
