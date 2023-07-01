from django_weasyprint import WeasyTemplateResponseMixin
from django.shortcuts import redirect
from django.conf import settings
from researcher_UI.models import administration
from django.views.generic import DetailView

from cdi_forms.views.utils import prefilled_cdi_data

class PDFAdministrationDetailView(WeasyTemplateResponseMixin, DetailView):
    model = administration
    template_name = "cdi_forms/pdf_administration.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        prefilled_data = prefilled_cdi_data(self.object)
        for field in prefilled_data:
            context[field] = prefilled_data[field]
        context["language_code"] = settings.LANGUAGE_DICT[
            context["object"].study.instrument.language
        ]
        return context

    def get(self, request, *args, **kwargs):
        if self.get_object().study.instrument.language == "Korean":
            return redirect("administration-view", pk=self.get_object().pk)
        return super().get(request, *args, **kwargs)
