from typing import Any

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from django.utils import translation
from django.views.generic import DetailView, FormView

from cdi_forms.forms import ContactForm
from cdi_forms.views.utils import language_map
from researcher_UI.models import Administration


class AdministrationContactView(FormView, DetailView):
    model = Administration
    template_name = "cdi_forms/administration_contact.html"
    form_class = ContactForm

    def get_success_url(self) -> str:
        return reverse("administer_cdi_form", args=[self.object.url_hash])

    def get_object(self, queryset=None):
        self.object = Administration.objects.get(url_hash=self.kwargs["hash_id"])
        return self.object

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        self.get_object()
        language = language_map(self.get_object().study.instrument.language)
        translation.activate(language)
        request.LANGUAGE_CODE = translation.get_language()
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form: Any) -> HttpResponse:
        form.send_email()
        messages.success(self.request, "Form submission successful!")
        return super().form_valid(form)
