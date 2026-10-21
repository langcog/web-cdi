from django.contrib.auth.mixins import LoginRequiredMixin
from django.core import serializers
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.views.generic import DetailView

from researcher_UI.models import Instrument


class AjaxDemographicForms(LoginRequiredMixin, DetailView):
    def get(self, request):
        pk = request.GET.get("id")
        if pk is None:
            return HttpResponseBadRequest("Missing parameter: id")
        try:
            data = serializers.serialize(
                "json",
                Instrument.objects.get(name=pk).demographics.all().order_by("pk"),
                fields=("id", "name"),
            )
        except:
            data = []
        return HttpResponse(data, content_type="application/json")


class AjaxChargeStatus(LoginRequiredMixin, DetailView):
    def get(self, request):
        pk = request.GET.get("id")
        if pk is None:
            return HttpResponseBadRequest("Missing parameter: id")
        try:
            instrument = Instrument.objects.get(name=pk)
        except Instrument.DoesNotExist:
            return HttpResponseBadRequest("Unknown instrument")

        data = {"chargeable": instrument.family.chargeable}
        return JsonResponse(data, content_type="application/json")
