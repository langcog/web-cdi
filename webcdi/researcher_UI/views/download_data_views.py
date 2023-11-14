from django.views.generic import DetailView
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils.safestring import mark_safe
from django.template.loader import get_template
from django.utils.text import slugify
from django_weasyprint import WeasyTemplateResponseMixin

from researcher_UI.models import Study


class PDFAdministrationDetailView(WeasyTemplateResponseMixin, DetailView):
    model = Study

    def get_template_names(self):
        name = slugify(f"{self.object.instrument.verbose_name}")
        template_name = f"researcher_UI/individual/{name}.html"
        try:
            get_template(template_name)
            return [template_name]
        except:
            return ["researcher_UI/individual/no_clinical_template.html"]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["administrations"] = self.object.administration_set.all().filter(
            completed=True
        )
        if "id" in self.request.GET:
            ids = self.request.GET.getlist("id")
            int_ids = []
            for id in ids:
                int_ids.append(int(id))
            ctx["administrations"] = ctx["administrations"].filter(pk__in=int_ids)
        if 'adjusted' in self.kwargs:
            ctx['adjusted'] = True
        return ctx

    def get(self, request, *args, **kwargs) -> HttpResponse:
        self.object = self.get_object()
        name = slugify(f"{self.object.instrument.verbose_name}")
        template_name = f"researcher_UI/individual/{name}.html"
        try:
            get_template(template_name)
        except Exception as e:
            messages.info(
                self.request,
                mark_safe(
                    f"""
                    <h1>No Clinical Template Available</h1>
                    <p>We do not have a clinical template available for { self.object.instrument } studies.</p>
                    """,
                ),
            )

            return redirect(request.META.get("HTTP_REFERER"))

        return super().get(request, *args, **kwargs)
