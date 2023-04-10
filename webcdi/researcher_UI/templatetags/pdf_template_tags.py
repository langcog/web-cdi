from django import template
from researcher_UI.models import SummaryData, administration_data

register = template.Library()


@register.filter
def get_summary_data(administration_id, data):
    try:
        res = SummaryData.objects.get(
            administration=administration_id, title=data
        ).value
        if res == "":
            res = 0
    except Exception as e:
        res = ''
    return res


@register.filter
def get_form_data(administration_id, data):
    try:
        res = administration_data.objects.get(
            administration=administration_id, item_ID=data
        ).value
    except Exception as e:
        res = f"no response provided"
    return res
