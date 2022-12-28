from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from researcher_UI.forms import *
from researcher_UI.models import (
    administration,
    administration_data,
)
from cdi_forms.views import get_model_header
from cdi_forms.models import BackgroundInfo
import pandas as pd
import numpy as np
from django.utils.translation import ugettext_lazy as _
from io import BytesIO
import re, zipfile
from researcher_UI.utils.write_to_zip import write_to_zip


def download_cdi_format(request, study_obj, administrations=None):
    outfile = BytesIO()

    if administrations is not None:
        completed_admins = administrations.filter(completed=True)
    else:
        completed_admins = administration.objects.filter(
            study=study_obj, completed=True
        )

    r = re.compile("item_[0-9]{1,3}")
    model_header = list(filter(r.match, get_model_header(study_obj.instrument.name)))
    admin_header = [
        "study_name",
        "subject_id",
        "repeat_num",
        "completed",
        "last_modified",
    ]
    background_header = [
        "age",
        "sex",
        "zip_code",
        "birth_order",
        "birth_weight_lb",
        "birth_weight_kg",
        "multi_birth_boolean",
        "multi_birth",
        "born_on_due_date",
        "early_or_late",
        "due_date_diff",
        "mother_yob",
        "mother_education",
        "father_yob",
        "father_education",
        "annual_income",
        "child_hispanic_latino",
        "child_ethnicity",
        "caregiver_info",
        "other_languages_boolean",
        "language_days_per_week",
        "language_hours_per_day",
        "ear_infections_boolean",
        "hearing_loss_boolean",
        "vision_problems_boolean",
        "illnesses_boolean",
        "services_boolean",
        "worried_boolean",
        "learning_disability_boolean",
    ]

    # study not completed if "completed_admins" is null; should throw useful error
    answers = administration_data.objects.values(
        "administration_id", "item_ID", "value"
    ).filter(administration_id__in=completed_admins)
    melted_answers = pd.DataFrame.from_records(answers).pivot(
        index="administration_id", columns="item_ID", values="value"
    )
    melted_answers.reset_index(level=0, inplace=True)

    missing_columns = [x for x in model_header if x not in melted_answers.columns]

    if missing_columns:
        melted_answers = melted_answers.reindex(
            columns=np.append(melted_answers.columns.values, missing_columns)
        )

    new_answers = melted_answers

    def my_fun(arg):
        if isinstance(arg, str):
            return arg.encode("utf-8")
        else:
            return str(arg)

    new_answers.loc[:, 1:] = new_answers.iloc[:, 1:].applymap(my_fun)

    if study_obj.instrument.form == "WG":
        for c in new_answers.columns[1:]:
            new_answers = new_answers.replace(
                {
                    c: {
                        "nan": 0,
                        "none": 0,
                        "None": 0,
                        "understands": 1,
                        "produces": 2,
                        "simple": 1,
                        "complex": 2,
                        "no": 0,
                        "yes": 1,
                        "not yet": 0,
                        "sometimes": 1,
                        "often": 2,
                        "never": 0,
                    }
                }
            )
    elif study_obj.instrument.form == "WS":
        for c in new_answers.columns[1:]:
            new_answers = new_answers.replace(
                {
                    c: {
                        "nan": 0,
                        "none": 0,
                        "None": 0,
                        "produces": 1,
                        "simple": 1,
                        "complex": 2,
                        "no": 0,
                        "yes": 1,
                        "not yet": 0,
                        "sometimes": 1,
                        "often": 2,
                        "never": 0,
                    }
                }
            )

    background_data = BackgroundInfo.objects.values().filter(
        administration__in=completed_admins
    )
    new_background = pd.DataFrame.from_records(background_data)

    admin_data = pd.DataFrame.from_records(completed_admins.values()).rename(
        columns={
            "id": "administration_id",
            "study_id": "study_name",
            "url_hash": "link",
        }
    )
    admin_data["study_name"] = study_obj.name
    background_answers = pd.merge(
        new_background, new_answers, how="outer", on="administration_id"
    )
    combined_data = pd.merge(
        admin_data, background_answers, how="outer", on="administration_id"
    )
    combined_data = combined_data[admin_header + background_header + model_header]
    combined_data["last_modified"] = combined_data["last_modified"].dt.strftime(
        "%Y-%m-%d %H:%M %Z"
    )
    combined_data["annual_income"] = combined_data["annual_income"].apply(
        lambda x: 0 if x == "Prefer not to disclose" else x
    )
    vocab_start = combined_data.columns.values.tolist().index("item_1")

    with zipfile.ZipFile(outfile, "w") as zf:
        combined_data.apply(lambda x: write_to_zip(x, zf, vocab_start), axis=1)
    zf.close()
    response = HttpResponse(outfile.getvalue(), content_type="application/octet-stream")
    response["Content-Disposition"] = "attachment; filename=%s.zip" % study_obj.name
    return response
