from typing import Any, Dict
import json
from django.http import HttpResponse, HttpRequest
from django.views.generic import DetailView

from django.utils import translation
from researcher_UI.models import administration
from cdi_forms.views.utils import language_map, PROJECT_ROOT

class InstructionDetailView(DetailView):
    model = administration
    template_name = 'cdi_forms/administration_instructions.html'

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        language = language_map(self.get_object().study.instrument.language)
        translation.activate(language)
        request.LANGUAGE_CODE = translation.get_language()
        return super().dispatch(request, *args, **kwargs)
    
    def get_object(self, queryset = None ):
        return administration.objects.get(url_hash=self.kwargs['hash_id'])
        return super().get_object(queryset)
    
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        ctx['language_code'] = language_map(self.object.study.instrument.language)
        with open(
            PROJECT_ROOT + "/form_data/" + self.object.study.instrument.name + "_meta.json",
            "r",
            encoding="utf-8",
        ) as content_file:  # Open associated json file with section ordering and nesting
            # Read json file and store additional variables regarding the instrument, study, and the administration
            data = json.loads(content_file.read())
        ctx['contents'] = data['parts']
        return ctx