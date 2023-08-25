from researcher_UI.models import Study, Researcher, Administration
from django.db.models import Max

def max_subject_id(study_obj):
    if study_obj.study_group:
        related_studies = Study.objects.filter(
            researcher=Researcher, study_group=study_obj.study_group
        )
        max_id = Administration.objects.filter(
            study__in=related_studies
        ).aggregate(Max("subject_id"))["subject_id__max"]
    else:
        max_id = Administration.objects.filter(study=study_obj).aggregate(
            Max("subject_id")
        )[
            "subject_id__max"
        ]  # Find the subject ID in this study with the highest number

    if (
        max_id is None
    ):  # If the max subject ID could not be found (e.g., study has 0 participants)
        max_id = 0  # Mark as zero

    return max_id

def max_repeat_num(administration):
    max_id = Administration.objects.filter(study=administration.study, subject_id=administration.subject_id).aggregate(
        Max("repeat_num")
    )[
        "repeat_num__max"
    ]  # Find the subject ID in this study with the highest number

    if (
        max_id is None
    ):  # If the max subject ID could not be found (e.g., study has 0 participants)
        max_id = 0  # Mark as zero

    return max_id