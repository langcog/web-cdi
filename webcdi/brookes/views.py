import datetime

from django.views.generic import FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse

from researcher_UI.models import InstrumentFamily
from brookes.models import BrookesCode
from brookes.forms import BrookesCodeForm

# Create your views here.

class UpdateBrookesCode(LoginRequiredMixin, FormView):
    form_class = BrookesCodeForm
    model = BrookesCode
    template_name = 'brookes/brookescode_form.html'

    def get_success_url(self):
        res = reverse("researcher_ui:console")
        dt = datetime.date.today()
        for chargeable in self.request.user.researcher.allowed_instrument_families.filter(chargeable=True):
            if not BrookesCode.objects.filter(researcher=self.request.user, instrument_family=chargeable, expiry__gte=dt).exists():
                res = reverse("brookes:enter_codes", args=(chargeable.id,))
        
        return res
    
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['form'] = BrookesCodeForm(self.request.POST or None)
        ctx['instrument_family'] = InstrumentFamily.objects.get(id=self.kwargs['instrument_family'])
        return ctx
    
    def form_valid(self, form):
        if 'cancel' in self.request.POST:
            self.request.user.researcher.allowed_instrument_families.remove(InstrumentFamily.objects.get(id=self.kwargs['instrument_family']))
        else: 
            bc = BrookesCode.objects.get(code=self.request.POST['code'])
            bc.researcher = self.request.user
            bc.instrument_family = InstrumentFamily.objects.get(id=self.kwargs['instrument_family'])
            bc.applied = datetime.datetime.now()
            bc.save()
        return super().form_valid(form)