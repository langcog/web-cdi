from django import template
from researcher_UI.models import SummaryData, administration_data

register = template.Library()


@register.simple_tag(takes_context=True)
def get_adjusted_summary_date(context, administration_id, data):
    if 'adjusted' in context:
        data += ' (adjusted)'
    if SummaryData.objects.filter(
            administration=administration_id, title=data
        ).exists():
        res = SummaryData.objects.get(
            administration=administration_id, title=data
        ).value
        if res == "":
            res = 0
    else:
        res = 0
    return res

@register.simple_tag(takes_context=True)
def get_true_false(context, administration_id, data):
    if get_adjusted_summary_date(context, administration_id, data) in [1, '1', True, 'true', 'True']:
        return 'True'
    return 'False'

@register.filter
def get_summary_data(administration_id, data):
    if SummaryData.objects.filter(
            administration=administration_id, title=data
        ).exists():
        res = SummaryData.objects.get(
            administration=administration_id, title=data
        ).value
        if res == "":
            res = 0
    else:
        res = 0
    '''    
    try:
        res = SummaryData.objects.get(
            administration=administration_id, title=data
        ).value
        if res == "":
            res = 0
    except Exception as e:
        res = f"0"
    '''
    return res


@register.filter
def get_form_data(administration_id, data):
    try:
        res = administration_data.objects.get(
            administration=administration_id, item_ID=data
        ).value
        if res == "":
            res = "Nil return"
    except Exception:
        res = f"no response provided"
    return res

@register.filter
def get_form_data_endings(administration_id, data):
    try:
        res = administration_data.objects.get(
            administration=administration_id, item_ID=data
        ).value
        if res in ['sometimes','yes']:
            res = "Yes"
        else:
            res='No'
    except Exception:
        res = f"No"
    return res