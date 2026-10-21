from django.template import TemplateDoesNotExist
from django.template.loader import get_template
from django.utils.text import slugify


def clinical_template_name(instrument):
    """The clinical (PDF) report template for an instrument, or None if it has none."""
    name = f"researcher_UI/individual/{slugify(instrument.verbose_name)}.html"
    try:
        get_template(name)
    except TemplateDoesNotExist:
        return None
    return name
