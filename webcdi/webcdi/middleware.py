import re

from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponsePermanentRedirect
from django.utils import translation
from django.utils.deprecation import MiddlewareMixin
from django.core.exceptions import MiddlewareNotUsed
from django.utils.http import url_has_allowed_host_and_scheme
from django.urls import resolve

EXEMPT_URLS = [re.compile(settings.LOGIN_URL.lstrip("/"))]
if hasattr(settings, "LOGIN_EXEMPT_URLS"):
    EXEMPT_URLS += [re.compile(url) for url in settings.LOGIN_EXEMPT_URLS]


class LoginRequiredMiddleware(MiddlewareMixin):
    def process_request(self, request):
        assert hasattr(request, "user"), "The Login Required Middleware"
        if not request.user.is_authenticated:
            path = request.path_info.lstrip("/")
            if not any(m.match(path) for m in EXEMPT_URLS):
                redirect_to = settings.LOGIN_URL
                # 'next' variable to support redirection to attempted page after login
                if len(path) > 0 and url_has_allowed_host_and_scheme(
                    url=request.path_info, allowed_hosts=request.get_host()
                ):
                    redirect_to = f"{settings.LOGIN_URL}?next={request.path_info}"

                return HttpResponseRedirect(redirect_to)


class AdminLocaleMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if (
            request.path.startswith("/wcadmin")
            or request.path.startswith("/interface")
            or request.path.startswith("/signup")
        ):
            translation.activate("en")
            request.LANGUAGE_CODE = translation.get_language()

class PrimaryHostRedirectMiddleware:
    """
    Middleware that redirects all requests to PRIMARY_HOST if present.
    """

    def __init__(self, get_response):
        """
        Checks if this plugin has been configured, otherwise have django remove it from the execution queue.
        """
        self.get_response = get_response
        self.primary_host = getattr(settings, "PRIMARY_HOST", None)

        if not self.primary_host:
            raise MiddlewareNotUsed

    def __call__(self, request):
        """
        Checks if the current request matches our primary host settings
        """
        try:
            if "healthcheck" in resolve(request.path_info).url_name:
                return self.get_response(request)
        except Exception:
            pass

        request_schema = "https" if request.is_secure() else "http"
        target_schema = "https" if settings.SECURE_SSL_REDIRECT else request_schema

        # Don't redirect if we are running an internal request e.g. an elb health-check
        if request.get_host() == settings.HOST_IP:
            return self.get_response(request)

        # Check if we can return early and do nothing because the current host matches the PRIMARY_HOST.
        if (request_schema, request.get_host()) == (target_schema, self.primary_host):
            return self.get_response(request)

        # Build our new url with the correct PRIMARY_HOST
        url = "%s://%s%s" % (target_schema, self.primary_host, request.get_full_path())

        return HttpResponsePermanentRedirect(url)