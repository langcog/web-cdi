from django.conf import settings
import pandas as pd
import os, json
from researcher_UI.models import administration, administration_data
from cdi_forms.models import BackgroundInfo
from researcher_UI.utils.try_parsing_date import try_parsing_date_fun
from researcher_UI.utils.processDemos import processDemos_fun
from researcher_UI.utils.random_url_generator import random_url_generator
from django.urls import reverse


def get_default_dict():
    return {
        "annual_income": "Prefer not to disclose",
        "birth_order": 0,
        "birth_weight_kg": None,
        "birth_weight_lb": 0.0,
        "born_on_due_date": 2,
        "caregiver_info": 0,
        "child_ethnicity": [],
        "child_hispanic_latino": None,
        "due_date_diff": None,
        "ear_infections": None,
        "ear_infections_boolean": 2,
        "early_or_late": "",
        "father_education": 0,
        "father_yob": 0,
        "hearing_loss": None,
        "hearing_loss_boolean": 2,
        "illnesses": None,
        "illnesses_boolean": 2,
        "language_days_per_week": None,
        "language_from": None,
        "language_hours_per_day": None,
        "learning_disability": None,
        "learning_disability_boolean": 2,
        "mother_education": 0,
        "mother_yob": 0,
        "multi_birth": None,
        "multi_birth_boolean": 2,
        "other_languages": [],
        "other_languages_boolean": 2,
        "services": None,
        "services_boolean": 2,
        "vision_problems": None,
        "vision_problems_boolean": 2,
        "worried": None,
        "worried_boolean": 2,
        "zip_code": "",
    }


def import_data_fun(request, study_obj):
    data = {}
    PROJECT_ROOT = settings.BASE_DIR
    instruments_json = json.load(
        open(os.path.realpath(PROJECT_ROOT + "/static/json/instruments.json"))
    )
    header_file_path = filter(
        lambda x: x["language"] == study_obj.instrument.language
        and x["form"] == study_obj.instrument.form,
        instruments_json,
    )[0]["fillable_headers"]

    pdf_header_df = pd.read_csv(
        open(os.path.realpath(PROJECT_ROOT + "/" + header_file_path))
    )

    default_dict = get_default_dict()

    csv_file = pd.read_csv(request.FILES["imported_file"])
    demo_list = list(set(default_dict.keys()) & set(csv_file))

    csv_file = processDemos_fun(csv_file, demo_list)
    admin_row = next(csv_file.iterrows())[1]
    error_msg = None
    new_admin_pks = []

    for index, admin_row in csv_file.iterrows():

        raw_sid = str(admin_row["name_of_child"])
        if raw_sid.isdigit():
            sid = int(raw_sid)
        else:
            error_msg = "Subject IDs must be numeric only."
            break

        old_rep = administration.objects.filter(study=study_obj, subject_id=sid).count()

        try:
            due_date = try_parsing_date_fun(admin_row["date_today"])
        except ValueError:
            error_msg = "Invalid date format. Please submit dates as MM-DD-YYYY or YYYY-MM-DD. '/' and '.' delimiters are alsoacceptable."
            break

        new_admin = administration.objects.create(
            study=study_obj,
            subject_id=sid,
            repeat_num=old_rep + 1,
            url_hash=random_url_generator(),
            completed=True,
            completedBackgroundInfo=True,
            due_date=due_date,
            last_modified=due_date,
        )
        new_admin_pks.append(new_admin.pk)

        if admin_row["gender"] == "m":
            sex = "M"
        elif admin_row["gender"] == "f":
            sex = "F"
        else:
            sex = "O"

        dot = due_date

        try:
            dob = try_parsing_date_fun(admin_row["birthdate"])
        except ValueError:
            error_msg = "Invalid date format. Please submit dates as MM-DD-YYYY or YYYY-MM-DD. '/' and '.' delimiters are alsoacceptable."
            break

        raw_age = dot - dob
        age = int(float(raw_age.days) / (365.2425 / 12.0))

        csv_dict = {"sex": sex, "age": age}

        background_dict = default_dict.copy()
        background_dict.update(csv_dict)

        if demo_list:
            background_dict.update(dict(admin_row[demo_list]))

        try:
            BackgroundInfo.objects.get_or_create(
                administration=new_admin, defaults=background_dict
            )
        except:
            error_msg = "Error adding background information."
            break

        fillable_items = pd.DataFrame(
            {"pdf_header": admin_row.index, "value": admin_row.values}
        )
        cdi_responses = []
        cdi_responses_df = pd.merge(
            pdf_header_df, fillable_items, how="left", on="pdf_header"
        )

        yes_list = ["yes", "1"]
        no_list = ["no", "0"]
        graded_list = ["not yet", "sometimes", "often"]

        try:
            for index, response_row in cdi_responses_df.iterrows():
                item_value = None
                raw_value = str(response_row["value"]).lower()
                if study_obj.instrument.form == "WS":
                    if (
                        response_row["item_type"]
                        in ["word", "word_form", "word_ending"]
                        and raw_value in yes_list
                    ):
                        item_value = "produces"
                    elif response_row["item_type"] in [
                        "usage",
                        "ending",
                        "combine",
                    ]:
                        item_value = raw_value
                    elif response_row["item_type"] == "combination_examples":
                        item_value = str(response_row["value"])
                    elif response_row["item_type"] == "complexity":
                        if raw_value in no_list + ["simple"]:
                            item_value = "simple"
                        elif raw_value in yes_list + ["complex"]:
                            item_value = "complex"
                elif study_obj.instrument.form == "WG":
                    if response_row["item_type"] == "first_signs":
                        if raw_value in yes_list + no_list:
                            item_value = "yes" if raw_value in yes_list else "no"
                    elif (
                        response_row["item_type"] == "phrases" and raw_value in yes_list
                    ):
                        item_value = "understands"
                    elif response_row["item_type"] in [
                        "starting_to_talk",
                        "gestures",
                    ]:
                        if raw_value in graded_list:
                            item_value = raw_value
                        elif raw_value in yes_list:
                            item_value = "yes"
                        elif raw_value in no_list:
                            item_value = "no"
                    elif response_row["item_type"] == "word":
                        if raw_value in ["understands", "1"]:
                            item_value = "understands"
                        elif raw_value in [
                            "understands and says",
                            "produces",
                            "2",
                        ]:
                            item_value = "produces"
                if item_value:
                    try:
                        cdi_responses.append(
                            administration_data(
                                administration=new_admin,
                                item_ID=response_row["itemID"],
                                value=item_value,
                            )
                        )
                    except:
                        error_msg = "Error importing item '%s' for subject_id '%s'" % (
                            sid,
                            response_row["itemID"],
                        )
            administration_data.objects.bulk_create(cdi_responses)
        except:
            error_msg = "Error importing administration data. Check that only valid values are in item columns."
            break

    if error_msg is None:
        data["stat"] = "ok"
        data["redirect_url"] = reverse("console", args=[study_obj.name])
    else:
        administration.objects.filter(pk__in=new_admin_pks).delete()
        data["stat"] = "error"
        data["error_message"] = error_msg

    return data
