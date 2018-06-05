from django import template
from django.template.defaultfilters import stringfilter
import bleach
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
@stringfilter
def bleach_markdown(text):
    return mark_safe(bleach.clean(markdown.markdown(text), strip = True))