from django import template

from researcher_UI.models import SummaryData
register = template.Library()

@register.filter
def get_summary_data(administration_id, data):
    try:
        res = SummaryData.objects.get(administration=administration_id, title=data).value
    except:
        res =''
    return res