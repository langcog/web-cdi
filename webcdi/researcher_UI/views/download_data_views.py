import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.views.generic import DetailView
from django_weasyprint import WeasyTemplateResponseMixin

from researcher_UI.models import Study
from researcher_UI.utils.clinical_report import clinical_template_name

logger = logging.getLogger("debug")


class PDFAdministrationDetailView(LoginRequiredMixin, WeasyTemplateResponseMixin, DetailView):
    model = Study

    def get_queryset(self):
        # clinical reports contain child data: only the owning researcher
        return Study.objects.filter(researcher=self.request.user)

    def get_template_names(self):
        template_name = clinical_template_name(self.object.instrument)
        return [template_name or "researcher_UI/individual/no_clinical_template.html"]

    def completed_administrations(self):
        """The selected (?id=...) administrations that are completed; reports only cover those."""
        administrations = self.object.administration_set.all().filter(completed=True)
        if "id" in self.request.GET:
            ids = self.request.GET.getlist("id")
            int_ids = []
            for id in ids:
                int_ids.append(int(id))
            administrations = administrations.filter(pk__in=int_ids)
        return administrations

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["administrations"] = self.completed_administrations()
        if "adjusted" in self.kwargs:
            ctx["adjusted"] = True
        return ctx

    def get(self, request, *args, **kwargs) -> HttpResponse:
        self.object = self.get_object()
        if not clinical_template_name(self.object.instrument):
            messages.info(
                self.request,
                mark_safe(
                    f"""
                    <h1>No Clinical Template Available</h1>
                    <p>We do not have a clinical template available for { self.object.instrument } studies.</p>
                    """,
                ),
            )

            return redirect(
                reverse("researcher_ui:console_study", kwargs={"pk": self.object.id})
            )

        if not self.completed_administrations().exists():
            # otherwise the PDF comes out blank
            messages.info(
                self.request,
                "None of the selected administrations has been completed yet, "
                "so there is no clinical report to show.",
            )
            return redirect(
                reverse("researcher_ui:console_study", kwargs={"pk": self.object.id})
            )

        return super().get(request, *args, **kwargs)
