import json

from django.http import HttpResponse
from django.views.generic import UpdateView
from researcher_UI.models import Study
from researcher_UI.forms import ImportDataForm


from researcher_UI.utils import import_data_fun
from django.contrib.auth.mixins import LoginRequiredMixin

class ImportData(LoginRequiredMixin, UpdateView):
    model = Study
    form_class = ImportDataForm
    template_name = "researcher_UI/import_data.html"

    def form_valid(self, form):
        data = import_data_fun(self.request, self.get_object())
        return HttpResponse(json.dumps(data), content_type="application/json")

    def get_context_data(self, **kwargs):
        context = super(ImportData, self).get_context_data(**kwargs)
        study_obj = self.get_object()
        context["form"] = ImportDataForm(researcher=self.request.user, study=study_obj)
        return context
    
