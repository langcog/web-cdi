import pandas as pd
from django.db.models import Max
import numpy as np
import re, datetime
from researcher_UI.models import administration, study
from researcher_UI.utils import random_url_generator


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
            if "csv-header" in request.POST:
                ids_df = pd.read_csv(raw_ids_csv)
                if request.POST["subject-ids-column"]:
                    subj_column = request.POST["subject-ids-column"]
                    if subj_column in ids_df.columns:
                        ids_to_add = ids_df[subj_column]
                        ids_type = ids_to_add.dtype
                    else:
                        ids_type = "missing"

                else:
                    ids_to_add = ids_df[ids_df.columns[0]]
                    ids_type = ids_to_add.dtype

            else:
                ids_df = pd.read_csv(raw_ids_csv, header=None)
                ids_to_add = ids_df[ids_df.columns[0]]
                ids_type = ids_to_add.dtype

            if ids_type != "int64":
                validity = False
                if "csv-header" not in request.POST:
                    data[
                        "error_message"
                    ] += "Non integer subject ids. Make sure first row is numeric\n"
                else:
                    if ids_type == "missing":
                        data[
                            "error_message"
                        ] += "Unable to find specified column. Check for any typos."  # Save this error message
                    else:
                        data[
                            "error_message"
                        ] += "Non integer subject ids\n"  # Save this error message

        if params["new_subject_ids"][0] != "":
            subject_ids = re.split("[,;\s\t\n]+", str(params["new_subject_ids"][0]))
            subject_ids = filter(None, subject_ids)
            subject_ids_numbers = all([x.isdigit() for x in subject_ids])
            if not subject_ids_numbers:
                validity = False
                data["error_message"] += "Non integer subject ids\n"

        if params["autogenerate_count"][0] != "":
            autogenerate_count = params["autogenerate_count"][0]
            autogenerate_count_isdigit = autogenerate_count.isdigit()
            if not autogenerate_count_isdigit:
                validity = False
                data[
                    "error_message"
                ] += "Non integer number of IDs to autogenerate\n"  # Save this error message

        if validity:
            test_period = int(study_obj.test_period)
            if raw_ids_csv:

                subject_ids = list(np.unique(ids_to_add.tolist()))

                for sid in subject_ids:
                    new_hash = random_url_generator()
                    old_rep = administration.objects.filter(
                        study=study_obj, subject_id=sid
                    ).count()
                    if not administration.objects.filter(
                        study=study_obj, subject_id=sid, repeat_num=old_rep + 1
                    ).exists():
                        administration.objects.create(
                            study=study_obj,
                            subject_id=sid,
                            repeat_num=old_rep + 1,
                            url_hash=new_hash,
                            completed=False,
                            due_date=datetime.datetime.now()
                            + datetime.timedelta(days=test_period),
                        )

            if params["new_subject_ids"][0] != "":
                subject_ids = re.split("[,;\s\t\n]+", str(params["new_subject_ids"][0]))
                subject_ids = list(filter(None, subject_ids))
                for sid in subject_ids:
                    new_hash = random_url_generator.random_url_generator()
                    old_rep = administration.objects.filter(
                        study=study_obj, subject_id=sid
                    ).count()
                    if not administration.objects.filter(
                        study=study_obj, subject_id=sid, repeat_num=old_rep + 1
                    ).exists():
                        administration.objects.create(
                            study=study_obj,
                            subject_id=sid,
                            repeat_num=old_rep + 1,
                            url_hash=new_hash,
                            completed=False,
                            due_date=datetime.datetime.now()
                            + datetime.timedelta(days=test_period),
                        )

            if params["autogenerate_count"][0] != "":
                autogenerate_count = int(params["autogenerate_count"][0])
                if study_obj.study_group:
                    related_studies = study.objects.filter(
                        researcher=study_obj.researcher,
                        study_group=study_obj.study_group,
                    )
                else:
                    related_studies = study.objects.filter(id=study_obj.id)
                max_subject_id = administration.objects.filter(
                    study__in=related_studies
                ).aggregate(Max("subject_id"))["subject_id__max"]
                if max_subject_id is None:
                    max_subject_id = 0
                for sid in range(
                    max_subject_id + 1, max_subject_id + autogenerate_count + 1
                ):
                    new_hash = random_url_generator.random_url_generator()
                    administration.objects.create(
                        study=study_obj,
                        subject_id=sid,
                        repeat_num=1,
                        url_hash=new_hash,
                        completed=False,
                        due_date=datetime.datetime.now()
                        + datetime.timedelta(days=test_period),
                    )

            data["stat"] = "ok"
            data["redirect_url"] = (
                "/endalk/study/" + study_name + "/?sort=-created_date"
            )
            data["study_name"] = study_name
        else:
            data["stat"] = "error"
    else:
        data["stat"] = "error"
        data["error_message"] = "permission denied"
        data["redirect_url"] = "endalk/"

    return data
