import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import CreateView

from researcher_UI.forms import AddPairedStudyForm
from researcher_UI.models import Study
from researcher_UI.utils import add_paired_study_fun

logger = logging.getLogger("debug")


class AddPairedStudy(LoginRequiredMixin, CreateView):
    model = Study
    form_class = AddPairedStudyForm
    template_name = "researcher_UI/add_paired_study_modal.html"

    def form_valid(self, form):
        add_paired_study_fun(form, self.request.user)
        return redirect(reverse("researcher_ui:console"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        researcher = self.request.user
        context["researcher"] = researcher
        return context

    def get_form_kwargs(self):
        """Passes the request object to the form class.
        This is necessary to only display members that belong to a given user"""

        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs
