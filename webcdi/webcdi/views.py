import datetime

from brookes.models import BrookesCode
from dateutil.relativedelta import relativedelta
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render

from webcdi.forms import SignUpForm


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
        to_date = (
            datetime.date.today() + relativedelta(months=1)
        )
        codes = BrookesCode.objects.filter(
            researcher=self.request.user, expiry__gte=from_date, expiry__lte=to_date
        )
        for code in codes:
            messages.warning(
                self.request,
                f"Your licence for {code.instrument_family} will expire on {code.expiry}",
            )

        return super().get_success_url()
