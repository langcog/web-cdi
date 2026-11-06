import datetime
import re

import numpy as np
import pandas as pd
import pytz
from django.db.models import Max
from django.urls import reverse

from researcher_UI.models import Administration, Study
from researcher_UI.utils.random_url_generator import random_url_generator

ZERO_PADDED_MESSAGE = (
    "Subject ids cannot start with 0 (e.g. 007): ids are stored as numbers, "
    "so the leading zeros would be lost\n"
)
SUBJECT_ID_MAX = 2147483647  # Administration.subject_id is an integer column
OUT_OF_RANGE_MESSAGE = f"Subject ids must be no larger than {SUBJECT_ID_MAX}\n"
NON_INTEGER_CSV_MESSAGE = (
    "Every row in the file's first column must be a whole-number ID (other columns "
    "are ignored). If the file has a header row, tick \"This file has a header row\".\n"
)
NON_INTEGER_COLUMN_MESSAGE = (
    "Every row in the ID column (the first column, unless you named another) must "
    "be a whole-number ID.\n"
)
UNREADABLE_CSV_MESSAGE = (
    "We couldn't read that file as a CSV. Save it as a plain .csv with one column "
    "of IDs.\n"
)
CSV_READ_ERRORS = (
    pd.errors.ParserError,
    pd.errors.EmptyDataError,
    UnicodeDecodeError,
    ValueError,
)


def is_zero_padded(subject_id):
    return re.fullmatch(r"0\d+", str(subject_id).strip()) is not None


def parse_csv_ids(column):
    """Ids are read as text so zero-padding is visible, then made numeric."""
    zero_padded = any(is_zero_padded(x) for x in column.dropna())
    return pd.to_numeric(column, errors="coerce"), zero_padded


def admin_new_fun(request, permitted, study_name, study_obj):
    data = {}
    if permitted:
        params = dict(request.POST)
        validity = True
        data["error_message"] = ""
        raw_ids_csv = (
            request.FILES["subject-ids-csv"]
            if "subject-ids-csv" in request.FILES
            else None
        )
        if (
            params["new_subject_ids"][0] == ""
            and params["autogenerate_count"][0] == ""
            and raw_ids_csv is None
        ):
            validity = False
            data["error_message"] += "Form is empty\n"

        if raw_ids_csv:
            try:
                ids_df = pd.read_csv(
                    raw_ids_csv,
                    header="infer" if "csv-header" in request.POST else None,
                    dtype=str,
                )
            except CSV_READ_ERRORS:
                ids_df = pd.DataFrame()

            if ids_df.empty:
                ids_type = "unreadable"
            elif "csv-header" in request.POST:
                if request.POST["subject-ids-column"]:
                    subj_column = request.POST["subject-ids-column"]
                    if subj_column in ids_df.columns:
                        ids_to_add, zero_padded = parse_csv_ids(ids_df[subj_column])
                        ids_type = ids_to_add.dtype
                    else:
                        ids_type = "missing"

                else:
                    ids_to_add, zero_padded = parse_csv_ids(ids_df[ids_df.columns[0]])
                    ids_type = ids_to_add.dtype

            else:
                ids_to_add, zero_padded = parse_csv_ids(ids_df[ids_df.columns[0]])
                ids_type = ids_to_add.dtype

            if ids_type != "int64":
                validity = False
                if ids_type == "unreadable":
                    data["error_message"] += UNREADABLE_CSV_MESSAGE
                elif "csv-header" not in request.POST:
                    data["error_message"] += NON_INTEGER_CSV_MESSAGE
                else:
                    if ids_type == "missing":
                        data[
                            "error_message"
                        ] += "Unable to find specified column. Check for any typos."  # Save this error message
                    else:
                        data["error_message"] += NON_INTEGER_COLUMN_MESSAGE
            elif zero_padded:
                validity = False
                data["error_message"] += ZERO_PADDED_MESSAGE
            elif ids_to_add.abs().max() > SUBJECT_ID_MAX:
                validity = False
                data["error_message"] += OUT_OF_RANGE_MESSAGE

        if params["new_subject_ids"][0] != "":
            subject_ids = re.split("[,;\s\t\n]+", str(params["new_subject_ids"][0]))
            subject_ids = list(filter(None, subject_ids))
            subject_ids_numbers = all([x.isdigit() for x in subject_ids])
            if not subject_ids_numbers:
                validity = False
                data["error_message"] += "Non integer subject ids\n"
            elif any(is_zero_padded(x) for x in subject_ids):
                validity = False
                data["error_message"] += ZERO_PADDED_MESSAGE
            elif any(int(x) > SUBJECT_ID_MAX for x in subject_ids):
                validity = False
                data["error_message"] += OUT_OF_RANGE_MESSAGE

        if params["autogenerate_count"][0] != "":
            autogenerate_count = params["autogenerate_count"][0]
            autogenerate_count_isdigit = autogenerate_count.isdigit()
            if not autogenerate_count_isdigit:
                validity = False
                data[
                    "error_message"
                ] += "Non integer number of IDs to autogenerate\n"  # Save this error message
            elif int(autogenerate_count) > 100:
                validity = False
                data[
                    "error_message"
                ] += "Maximum autogenerated administrations is 100\n"  # Save this error message

        if validity:
            test_period = int(study_obj.test_period)
            if raw_ids_csv:
                subject_ids = list(np.unique(ids_to_add.tolist()))

                for sid in subject_ids:
                    new_hash = random_url_generator()
                    old_rep = Administration.objects.filter(
                        study=study_obj, subject_id=sid
                    ).count()
                    if not Administration.objects.filter(
                        study=study_obj, subject_id=sid, repeat_num=old_rep + 1
                    ).exists():
                        Administration.objects.create(
                            study=study_obj,
                            subject_id=sid,
                            repeat_num=old_rep + 1,
                            url_hash=new_hash,
                            completed=False,
                            due_date=pytz.utc.localize(
                                datetime.datetime.now()
                                + datetime.timedelta(days=test_period)
                            ),
                        )

            if params["new_subject_ids"][0] != "":
                subject_ids = re.split("[,;\s\t\n]+", str(params["new_subject_ids"][0]))
                subject_ids = list(filter(None, subject_ids))
                for sid in subject_ids:
                    new_hash = random_url_generator()
                    old_rep = Administration.objects.filter(
                        study=study_obj, subject_id=sid
                    ).count()
                    if not Administration.objects.filter(
                        study=study_obj, subject_id=sid, repeat_num=old_rep + 1
                    ).exists():
                        Administration.objects.create(
                            study=study_obj,
                            subject_id=sid,
                            repeat_num=old_rep + 1,
                            url_hash=new_hash,
                            completed=False,
                            due_date=pytz.utc.localize(
                                datetime.datetime.now()
                                + datetime.timedelta(days=test_period)
                            ),
                        )

            if params["autogenerate_count"][0] != "":
                autogenerate_count = int(params["autogenerate_count"][0])
                if study_obj.study_group:
                    related_studies = Study.objects.filter(
                        researcher=study_obj.researcher,
                        study_group=study_obj.study_group,
                    )
                else:
                    related_studies = Study.objects.filter(id=study_obj.id)
                max_subject_id = Administration.objects.filter(
                    study__in=related_studies
                ).aggregate(Max("subject_id"))["subject_id__max"]
                if max_subject_id is None:
                    max_subject_id = 0
                for sid in range(
                    max_subject_id + 1, max_subject_id + autogenerate_count + 1
                ):
                    new_hash = random_url_generator()
                    Administration.objects.create(
                        study=study_obj,
                        subject_id=sid,
                        repeat_num=1,
                        url_hash=new_hash,
                        completed=False,
                        due_date=pytz.utc.localize(
                            datetime.datetime.now()
                            + datetime.timedelta(days=test_period)
                        ),
                    )

            data["stat"] = "ok"

            data["redirect_url"] = (
                reverse("researcher_ui:console_study", args=[study_obj.pk])
                + "?sort=-created_date"
            )
            data["study_name"] = study_name
        else:
            data["stat"] = "error"
    else:
        data["stat"] = "error"
        data["error_message"] = "permission denied"

    return data
