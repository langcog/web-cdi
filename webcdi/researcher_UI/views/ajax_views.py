from django.views.generic import DetailView
from researcher_UI.models import Instrument

from django.http import HttpResponse, JsonResponse
from django.core import serializers

class AjaxDemographicForms(DetailView):
    def get(self, request):
        pk = request.GET["id"]
        try:
            data = serializers.serialize(
                "json",
                Instrument.objects.get(name=pk).demographics.all().order_by("pk"),
                fields=("id", "name"),
            )
        except:
            data = []
        return HttpResponse(data, content_type="application/json")


class AjaxChargeStatus(DetailView):
    def get(self, request):
        pk = request.GET["id"]

        data = {"chargeable": Instrument.objects.get(name=pk).family.chargeable}
        return JsonResponse(data, content_type="application/json")