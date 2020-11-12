from django.template.defaulttags import register

from cdi_forms.models import Choices
from researcher_UI.models import instrument
from django.conf import settings

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def get_item_perc(dictionary, key):
    return str(float(float(dictionary.get(key))/float(dictionary.get('count')))*100)

@register.filter
def translate(choice, instrument_name):
    obj = Choices.objects.get(choice_set_en=choice)
    instrument_obj = instrument.objects.get(name=instrument_name)
    return getattr(obj, 'choice_set_' + settings.LANGUAGE_DICT[instrument_obj.language])

@register.simple_tag
def to_list(*args):
    return args

@register.simple_tag
def set_true():
    return True

@register.simple_tag
def set_false():
    return False