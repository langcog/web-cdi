from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def nav_active(context):
    """The navbar item the current page belongs to ("" if none: login, profile...)."""
    match = getattr(context.get("request"), "resolver_match", None)
    if match is None:
        return ""
    if match.url_name == "researcher_add_instruments" or match.namespace == "brookes":
        return "instruments"  # code entry is the next step after saving instruments
    if match.url_name in ("documentation", "about"):
        return match.url_name
    if match.namespace == "researcher_ui" and match.url_name not in (
        "profile",
        "change_password",
    ):
        return "home"
    return ""
