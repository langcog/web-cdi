from django.conf import settings
import pandas as pd
from researcher_UI.utils.make_str import make_str_fun
import codecs
import json
import datetime
import re
from cdi_forms.models import BackgroundInfo, Zipcode
import pandas as pd
from django.conf import settings


def processDemos_fun(csv_file, demo_list=None):
    recoded_df = csv_file.where((pd.notnull(csv_file)), None)
    PROJECT_ROOT = settings.BASE_DIR

    if demo_list:
        for col in demo_list:
            if "boolean" in col or col == "born_on_due_date":
                recoded_df[col] = recoded_df[col].apply(
                    lambda x: int(x) if x in [0, 1] else 2
                )
            elif col == "child_hispanic_latino":
                recoded_df[col] = recoded_df[col].apply(
                    lambda x: bool(x) if x in [0, 1] else None
                )
            elif col == "birth_order":
                recoded_df[col] = (
                    recoded_df[col]
                    .apply(lambda x: int(x) if x in range(1, 10) else 0)
                    .astype("int")
                )
            elif col in [
                "ear_infections",
                "hearing_loss",
                "illnesses",
                "learning_disability",
                "multi_birth",
                "services",
                "vision_problems",
                "worried",
            ]:
                recoded_df[col] = recoded_df[col].apply(
                    lambda x: make_str_fun(x) if x and len(x) <= 1000 else None
                )
            elif col == "language_from":
                recoded_df[col] = recoded_df[col].apply(
                    lambda x: make_str_fun(x) if x and len(x) <= 50 else None
                )
            elif "yob" in col:
                recoded_df[col] = (
                    recoded_df[col]
                    .apply(
                        lambda x: int(x)
                        if x in range(1950, datetime.datetime.today().year + 1)
                        else 0
                    )
                    .astype("int")
                )
            elif "education" in col:
                recoded_df[col] = (
                    recoded_df[col]
                    .apply(lambda x: int(x) if x in range(1, 24) else 0)
                    .astype("int")
                )
            elif col == "early_or_late":
                recoded_df[col] = recoded_df[col].apply(
                    lambda x: make_str_fun(x.lower())
                    if x and x.lower() in ["early", "late"]
                    else None
                )
            elif col == "zip_code":

                def parse_zipcode(c):
                    if c and re.match("(\d{3}([*]{2})?)", c):
                        if Zipcode.objects.filter(zip_prefix=c).exists():
                            return Zipcode.objects.filter(zip_prefix=c).first().state
                        else:
                            return c + "**"
                    elif c and re.match("([A-Z]{2})", c):
                        return make_str_fun(c)
                    else:
                        return ""

                recoded_df[col] = recoded_df[col].str[:3].apply(parse_zipcode)
            elif col == "language_days_per_week":
                recoded_df[col] = recoded_df[col].apply(
                    lambda x: int(x) if x in range(1, 8) else None
                )
            elif col == "language_hours_per_day":
                recoded_df[col] = recoded_df[col].apply(
                    lambda x: int(x) if x in range(1, 25) else None
                )
            elif col == "due_date_diff":
                recoded_df[col] = recoded_df[col].apply(
                    lambda x: int(x) if x >= 1 else None
                )
            elif col == "caregiver_info":
                recoded_df[col] = recoded_df[col].apply(
                    lambda x: int(x) if x in range(0, 5) else 0
                )
            elif col == "birth_weight_lb":

                def round_lb(c):
                    c = int(c * 2) / 2.0
                    c = 1.0 if c < 3.0 else c
                    c = 10.0 if c > 10.0 else c
                    return c

                recoded_df[col] = recoded_df[col].apply(round_lb)
            elif col == "birth_weight_kg":

                def round_kg(c):
                    c = int(c * 4) / 4.0
                    c = 1.0 if c < 1.5 else c
                    c = 5.0 if c > 5.0 else c
                    return c

                recoded_df[col] = recoded_df[col].apply(round_kg)
            elif col == "annual_income":
                recoded_df[col] = recoded_df[col].apply(
                    lambda x: make_str_fun(x)
                    if x
                    and x in dict(BackgroundInfo._meta.get_field(col).choices).keys()
                    else "Prefer not to disclose"
                )
            elif col == "child_ethnicity":
                recoded_df[col] = recoded_df[col].apply(
                    lambda x: list(
                        set(make_str_fun(x).upper().split("/"))
                        & set(["N", "H", "W", "B", "A", "O"])
                    )
                    if x
                    else []
                )
            elif col == "other_languages":
                lang_choices = [
                    make_str_fun(v["name"])
                    for k, v in json.load(
                        codecs.open(PROJECT_ROOT + "/languages.json", "r", "utf-8")
                    ).iteritems()
                ]
                recoded_df[col] = recoded_df[col].apply(
                    lambda x: list(
                        set([y.strip() for y in make_str_fun(x).split("/")])
                        & set(lang_choices)
                    )
                    if x
                    else []
                )

    recoded_df = recoded_df.where((pd.notnull(recoded_df)), None)
    return recoded_df
