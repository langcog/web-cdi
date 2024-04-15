import json
from typing import Any, Dict

from django.http import HttpRequest, HttpResponse
from django.utils import translation
from django.views.generic import DetailView

from cdi_forms.views.utils import PROJECT_ROOT, language_map
from researcher_UI.models import Administration


class InstructionDetailView(DetailView):
    model = Administration
    template_name = "cdi_forms/administration_instructions.html"

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        language = language_map(self.get_object().study.instrument.language)
        translation.activate(language)
        request.LANGUAGE_CODE = translation.get_language()
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        return Administration.objects.get(url_hash=self.kwargs["hash_id"])

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        ctx["language_code"] = language_map(self.object.study.instrument.language)
        with open(
            PROJECT_ROOT
            + "/form_data/"
            + self.object.study.instrument.name
            + "_meta.json",
            "r",
            encoding="utf-8",
        ) as content_file:  # Open associated json file with section ordering and nesting
            # Read json file and store additional variables regarding the instrument, study, and the administration
            data = json.loads(content_file.read())
        ctx["contents"] = data["parts"]
        return ctx
