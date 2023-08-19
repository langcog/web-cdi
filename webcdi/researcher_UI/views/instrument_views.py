from researcher_UI.forms import AddInstrumentForm
from researcher_UI.models import researcher
from brookes.models import BrookesCode
from django.views.generic import UpdateView
import datetime

from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse

class AddInstruments(LoginRequiredMixin, UpdateView):
    model = researcher
    form_class = AddInstrumentForm
    template_name = "researcher_UI/researcher_form.html"

    def get_success_url(self):
        res = reverse("researcher_ui:console")
        dt = datetime.date.today()
        for chargeable in self.object.allowed_instrument_families.filter(
            chargeable=True
        ):
            if not BrookesCode.objects.filter(
                researcher=self.request.user,
                instrument_family=chargeable,
                expiry__gte=dt,
            ).exists():
                res = reverse("brookes:enter_codes", args=(chargeable.id,))

        return res

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        return ctx
