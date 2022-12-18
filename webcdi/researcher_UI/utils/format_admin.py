import os
from django.conf import settings


def format_admin_header(study_obj):
    admin_header = [
        "opt_out",
        "study_name",
        "subject_id",
        "local_lab_id",
        "repeat_num",
        "administration_id",
        "link",
        "completed",
        "completedBackgroundInfo",
        "completedSurvey",
        "due_date",
        "last_modified",
        "created_date",
    ]
    filename = os.path.realpath(
        settings.BASE_DIR
        + "/cdi_forms/form_data/background_info/"
        + study_obj.instrument.name
        + "_back.json"
    )

    if not os.path.isfile(filename):
        admin_header.remove("completedSurvey")

    return admin_header


def format_admin_data(pd, study_obj, administrations, admin_header):
    # Try to format administration data for pandas dataframe
    try:
        # exclude completedSurvey if no back background_info page
        filename = os.path.realpath(
            settings.BASE_DIR
            + "/cdi_forms/form_data/background_info/"
            + study_obj.instrument.name
            + "_back.json"
        )
        if not os.path.isfile(filename):
            admin_data = pd.DataFrame.from_records(
                administrations.values(
                    "id",
                    "opt_out",
                    "study__name",
                    "url_hash",
                    "repeat_num",
                    "subject_id",
                    "local_lab_id",
                    "completed",
                    "completedBackgroundInfo",
                    "due_date",
                    "last_modified",
                    "created_date",
                )
            ).rename(
                columns={
                    "id": "administration_id",
                    "study__name": "study_name",
                    "url_hash": "link",
                }
            )
        else:
            admin_data = pd.DataFrame.from_records(
                administrations.values(
                    "id",
                    "opt_out",
                    "study__name",
                    "url_hash",
                    "repeat_num",
                    "subject_id",
                    "local_lab_id",
                    "completed",
                    "completedBackgroundInfo",
                    "completedSurvey",
                    "due_date",
                    "last_modified",
                    "created_date",
                )
            ).rename(
                columns={
                    "id": "administration_id",
                    "study__name": "study_name",
                    "url_hash": "link",
                }
            )
    except:
        admin_data = pd.DataFrame(columns=admin_header)
    return admin_data
