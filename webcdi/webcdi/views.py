import datetime
from typing import Any

from django.http import HttpRequest, HttpResponse
from django.utils import translation
from brookes.models import BrookesCode
from dateutil.relativedelta import relativedelta
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.views.generic import TemplateView
from webcdi.forms import SignUpForm

from django.views.decorators.cache import never_cache

class HomeView(TemplateView):
    template_name = 'webcdi/home.html'

    @never_cache
    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        translation.activate('en')
        request.LANGUAGE_CODE = translation.get_language()
        return super().dispatch(request, *args, **kwargs)
    
def signup(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.refresh_from_db()  # load the profile instance created by the signal
            user.researcher.institution = form.cleaned_data.get("institution")
            user.researcher.position = form.cleaned_data.get("position")
            user.save()
            username = form.cleaned_data.get("username")
            raw_password = form.cleaned_data.get("password1")
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect("researcher_ui:console")
    else:
        form = SignUpForm()
    return render(request, "webcdi/signup.html", {"form": form})


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
        translation.activate('en')
        request.LANGUAGE_CODE = translation.get_language()
        return super().dispatch(request, *args, **kwargs)