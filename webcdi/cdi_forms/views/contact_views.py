from typing import Any
from django.http import HttpResponse, HttpRequest
from django.views.generic import DetailView, FormView
from django.urls import reverse

from django.utils import translation
from researcher_UI.models import administration

from django.contrib import messages
from cdi_forms.views.utils import language_map
from cdi_forms.forms import ContactForm

class AdministrationContactView(FormView, DetailView):
    model = administration
    template_name = "cdi_forms/administration_contact.html"
    form_class = ContactForm

    def get_success_url(self) -> str:
        return reverse("administer_cdi_form", args=[self.object.url_hash])
    
    def get_object(self, queryset=None):
        self.object = administration.objects.get(url_hash=self.kwargs['hash_id'])
        return self.object

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        self.get_object()
        language = language_map(self.get_object().study.instrument.language)
        translation.activate(language)
        request.LANGUAGE_CODE = translation.get_language()
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form: Any) -> HttpResponse:
        form.send_email()
        messages.success(self.request, 'Form submission successful!')
        return super().form_valid(form)