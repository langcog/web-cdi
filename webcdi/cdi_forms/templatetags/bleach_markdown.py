from django import template
from django.template.defaultfilters import stringfilter
import bleach, markdown
from django.utils.safestring import mark_safe
from markdown.extensions.legacy_em import LegacyEmExtension
register = template.Library()

@register.filter
@stringfilter
def bleach_markdown(text):
    return mark_safe(bleach.clean(markdown.markdown(text, extensions=[LegacyEmExtension()]), strip = True))