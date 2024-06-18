from typing import Any

from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from django.contrib.auth.views import PasswordChangeView
from django.db.models.base import Model as Model
from django.db.models.query import QuerySet
from django.forms import BaseModelForm
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic import UpdateView

from researcher_UI.forms import ProfileForm, ResearcherForm


class ProfileView(UpdateView):
    model = User
    form_class = ProfileForm
    template_name = "researcher_UI/profile.html"
    success_url = reverse_lazy("researcher_ui:console")

    def get_object(self, queryset: QuerySet[Any] | None = ...) -> Model:
        return self.request.user

    def get_context_data(self, **kwargs: Any):
        ctx = super().get_context_data(**kwargs)
        ctx["researcher_form"] = ResearcherForm(instance=self.request.user.researcher)
        return ctx

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        researcher_form = ResearcherForm(
            instance=self.request.user.researcher, data=self.request.POST
        )
        researcher_form.save()
        messages.success(self.request, "Your profile has been updated")
        return super().form_valid(form)


class ChangePasswordView(PasswordChangeView):
    form_class = PasswordChangeForm
    success_url = reverse_lazy("researcher_ui:console")
    template_name = "researcher_UI/change_password.html"

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        messages.success(self.request, "Your password has been updated")
        return super().form_valid(form)
