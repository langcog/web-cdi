from typing import Any, Dict, Optional
from django.db import models
from django.views.generic import DetailView

from django.utils import translation
from researcher_UI.models import administration
from cdi_forms.views.utils import language_map

class InstructionDetailView(DetailView):
    model = administration
    template_name = 'cdi_forms/instructions.html'

    def get_object(self, queryset = None ):
        return administration.objects.get(url_hash=self.kwargs['hash_id'])
        return super().get_object(queryset)
    
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        ctx['language_code'] = language_map(self.object.study.instrument.language)

        return ctx