from researcher_UI.models import SummaryData
import pandas as pd


def get_study_scores(administrations):
    scores = SummaryData.objects.values("administration_id", "title", "value").filter(
        administration_id__in=administrations
    )
    if not scores:
        return ""

    melted_scores = pd.DataFrame.from_records(scores).pivot(
        index="administration_id", columns="title", values="value"
    )
    melted_scores.reset_index(level=0, inplace=True)
    return melted_scores
