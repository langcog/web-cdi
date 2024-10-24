import datetime
import logging
from typing import Any

from dateutil.relativedelta import relativedelta
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.views import LoginView
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.utils import translation
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.generic import TemplateView
from django_registration.backends.activation.views import RegistrationView

from brookes.models import BrookesCode
from researcher_UI.models import Researcher
from webcdi.forms import SignUpForm

logger = logging.getLogger("debug")


@method_decorator([never_cache], name="dispatch")
class HomeView(TemplateView):
    template_name = "webcdi/home.html"

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        translation.activate("en")
        request.LANGUAGE_CODE = translation.get_language()
        return super().dispatch(request, *args, **kwargs)


class CustomRegistrationView(RegistrationView):
    form_class = SignUpForm

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        translation.activate("en")
        request.LANGUAGE_CODE = translation.get_language()
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save()
        super().form_valid(form)
        logger.debug(f"User is {user}.  Is Active is {user.is_active}")
        researcher, created = Researcher.objects.get_or_create(user=user)
        researcher.institution = self.request.POST["institution"]
        researcher.position = self.request.POST["position"]
        researcher.save()

        user.is_active = True
        user.save()
        logger.debug(f"User is {user}.  Is Active is {user.is_active}")
        return HttpResponseRedirect(self.get_success_url())


class CustomLoginView(LoginView):
    def get_success_url(self) -> str:
        # We might want to message researchers their licence is about to expire

        from_date = datetime.date.today()
        to_date = datetime.date.today() + relativedelta(months=1)
        codes = BrookesCode.objects.filter(
            researcher=self.request.user, expiry__gte=from_date, expiry__lte=to_date
        )
        for code in codes:
            if BrookesCode.objects.filter(
                researcher=self.request.user,
                expiry__gte=to_date,
                instrument_family=code.instrument_family,
            ).exists():
                codes = codes.exclude(pk=code.pk)
        for code in codes:
            messages.warning(
                self.request,
                f"Your licence for {code.instrument_family} will expire on {code.expiry}",
            )

        return super().get_success_url()

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        translation.activate("en")
        request.LANGUAGE_CODE = translation.get_language()
        return super().dispatch(request, *args, **kwargs)
