import numpy

from django.shortcuts import render, redirect
from django.views.generic import UpdateView
from django.http import Http404
from django.utils import timezone

# simulation package contains the Simulator and all abstract classes
from catsim.simulation import *
# initialization package contains different initial proficiency estimation strategies
from catsim.initialization import *
# selection package contains different item selection strategies
from catsim.selection import *
# estimation package contains different proficiency estimation methods
from catsim.estimation import *
# stopping package contains different stopping criteria for the CAT
from catsim.stopping import *

from cdi_forms.models import requests_log, BackgroundInfo

from cdi_forms.views import BackgroundInfoView, CreateBackgroundInfoView, BackpageBackgroundInfoView
from researcher_UI.models import administration

from .forms import CatItemForm
from .models import InstrumentItem, CatResponse
from .utils import string_bool_coerce
# Create your views here.

class CATBackgroundInfoView(BackgroundInfoView):
    pass

class CATCreateBackgroundInfoView(CreateBackgroundInfoView):
    def get(self, request, *args, **kwargs):
        print("CAT Create backgroun")
        return super().get(request, *args, **kwargs)

class CATBackpageBackgroundInfoView(BackpageBackgroundInfoView):
    pass

class AdministerAdministraionView(UpdateView):
    model = administration
    refresh = False
    hash_id = None
    form_class = CatItemForm
    template_name = 'cdi_forms/cat_forms/cat_form.html'
    word=None
    instrument_items = None

    def get_object(self, queryset=None):
        try:
            self.hash_id = self.kwargs['hash_id']
            obj = administration.objects.get(url_hash=self.hash_id)
        except:
            raise Http404("Administration not found")
        return obj

    def get_items(self):
        self.instrument_items = InstrumentItem.objects.filter(instrument=self.object.study.instrument)
        items = []
        for instrument_item in self.instrument_items:
            items.append([instrument_item.discrimination, instrument_item.difficulty, instrument_item.guessing, instrument_item.upper_asymptote])
        
        return numpy.asarray(items, dtype=numpy.float32)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if 'btn-back' in request.POST:
            print("We're here")
            return redirect('cat_forms:background-info', pk=self.object.backgroundinfo.id)

        administered_responses = self.object.catresponse.administered_responses or []
        administered_words = self.object.catresponse.administered_words or []
        administered_items = self.object.catresponse.administered_items or []
        
        instrument_item = InstrumentItem.objects.get(id=int(self.request.POST['word']))
        administered_words.append(instrument_item.definition)
        administered_responses.append(string_bool_coerce(self.request.POST['item']))
        items = self.get_items()
        for index, item in enumerate(self.instrument_items):
            print(index)
            if item == instrument_item:
                administered_items.append(index)
                break

        estimator = HillClimbingEstimator()
        new_theta = estimator.estimate(items=items, administered_items=administered_items, response_vector=administered_responses, est_theta=self.object.catresponse.est_theta)

        self.object.catresponse.administered_responses=administered_responses
        self.object.catresponse.administered_items=administered_items
        self.object.catresponse.administered_words = administered_words
        self.object.catresponse.est_theta = new_theta

        stopper = MaxItemStopper(20)
        if stopper.stop(administered_items=items[administered_items], theta=self.object.catresponse.est_theta):
            self.object.completed = True
            self.object.save()

        self.object.catresponse.save()

        self.request.METHOD = 'GET'
        return redirect('cat_forms:administer_cat_form', hash_id=self.hash_id)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['form'] = CatItemForm(context={'word':self.word}, initial={'word':self.word})
        return ctx

    def get(self, request, *args, **kwargs):
        print("GET 2")
        self.object = self.get_object()
        requests_log.objects.create(url_hash=self.hash_id, request_type="GET")
        if self.object.completed or self.object.due_date < timezone.now():
            return render(request, 'cdi_forms/cat_forms/cat_completed.html', context=self.get_context_data())
        background_instance, created = BackgroundInfo.objects.get_or_create(administration=self.object) 
        if self.object.completedSurvey:
            return redirect('backpage-background-info', pk=background_instance.pk)
        elif not self.object.completedBackgroundInfo:
            return redirect('background-info', pk=background_instance.pk)

        items = self.get_items()

        initializer = RandomInitializer()
        selector = MaxInfoSelector()
        est_theta = initializer.initialize()

        cat_response, created = CatResponse.objects.get_or_create(administration=self.object)
        if created or not cat_response.est_theta:
            cat_response.est_theta = est_theta
            cat_response.save()

        administered_responses = self.object.catresponse.administered_responses or []
        administered_items = self.object.catresponse.administered_items or []
        administered_words = self.object.catresponse.administered_words or []
        est_theta = self.object.catresponse.est_theta

        item_index = selector.select(items=items, administered_items=administered_items, est_theta=est_theta)

        self.word = self.instrument_items[int(item_index)]

        return super().get(request, *args, **kwargs) 
