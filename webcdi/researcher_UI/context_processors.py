from django.contrib.sites.shortcuts import get_current_site


def get_site_context(request):
    site_context = {}
    site_context["ENVIRONMENT_NAME"] = get_current_site(request).name
    site_context["ENVIRONMENT_COLOR"] = None

    if site_context["ENVIRONMENT_NAME"] == "Web-CDI":
        site_context["ENVIRONMENT_COLOR"] = "#f44253"
    elif site_context["ENVIRONMENT_NAME"] == "Web-CDI Development":
        site_context["ENVIRONMENT_COLOR"] = "#f48941"
    elif site_context["ENVIRONMENT_NAME"] == "Web-CDI Localhost":
        site_context["ENVIRONMENT_COLOR"] = "#7c7c7c"

    return site_context
