import os.path

from django.shortcuts import render, redirect
from django.views.generic import UpdateView
from django.http import Http404
from django.utils import timezone, translation
from django.db.models import Min
from django.conf import settings

from cdi_forms.models import requests_log, BackgroundInfo
from cdi_forms.views import BackgroundInfoView, CreateBackgroundInfoView, BackpageBackgroundInfoView, PROJECT_ROOT, language_map
from researcher_UI.models import administration

from .forms import CatItemForm
from .models import CatResponse
from .utils import string_bool_coerce
from .cdi_cat_api import cdi_cat_api

import logging
# Get an instance of a logger
logger = logging.getLogger("debug")

CAT_LANG_DICT = {
    'en' : 'EN',
    'es' : 'SP',
    'fr' : 'FR',
    'fr-ca' : 'FR',
    'en-ca' : 'EN',
}

# Create your views here.

class CATBackgroundInfoView(BackgroundInfoView):
    pass

class CATCreateBackgroundInfoView(CreateBackgroundInfoView):
    def get(self, request, *args, **kwargs):
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
    max_words = 50
    min_words = 20
    min_error = 0.15
    est_theta = None

    def get_hardest_easiest(self):
        if self.object.catresponse.administered_items :
            hardest = cdi_cat_api(f'hardestWord?items={self.object.catresponse.administered_items}&language={CAT_LANG_DICT[self.language]}')['definition']
            easiest = cdi_cat_api(f'easiestWord?items={self.object.catresponse.administered_items}&language={CAT_LANG_DICT[self.language]}')['definition']
        else : 
            hardest = None
            easiest = None
        return hardest, easiest

    def get_object(self, queryset=None):
        try:
            self.hash_id = self.kwargs['hash_id']
            obj = administration.objects.get(url_hash=self.hash_id)
        except:
            raise Http404("Administration not found")
        return obj

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if 'btn-back' in request.POST:
            return redirect('cat_forms:background-info', pk=self.object.backgroundinfo.id)

        administered_responses = self.object.catresponse.administered_responses or []
        administered_words = self.object.catresponse.administered_words or []
        administered_items = self.object.catresponse.administered_items or []
        
        self.word = {'index': self.request.POST['word_id'], 'definition' : self.request.POST['label']}
        
        administered_words.append(self.word['definition'])
        if 'yes' in self.request.POST:
            administered_responses.append(True)
        else:
            administered_responses.append(False)

        administered_items.append(self.word['index'])
        
        self.object.catresponse.administered_responses = administered_responses
        self.object.catresponse.administered_items = administered_items
        self.object.catresponse.administered_words = administered_words
        self.object.catresponse.save()

        if len(administered_items) > 49 :
            try:
                filename = os.path.realpath(PROJECT_ROOT + self.object.study.demographic.path)
            except Exception:
                filename = 'None'
            if  os.path.isfile(filename):
                self.object.completedSurvey = True
            else :
                self.object.completed = True
            self.object.save()

        self.request.METHOD = 'GET'
        return redirect('cat_forms:administer_cat_form', hash_id=self.hash_id)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['language_code'] = language_map(self.object.study.instrument.language)
        
        if self.word: 
            ctx['form'] = CatItemForm(context={'label':self.word['definition']}, initial={'word_id':self.word['index'], 'label':self.word['definition']})
            try:
                if '*' in self.word['definition']: ctx['footnote'] = True
            except AttributeError:
                pass

        ctx['max_words'] = self.max_words
        try:
            if self.object.catresponse.administered_words:
                ctx['words_shown'] = len(self.object.catresponse.administered_words) + 1
            else:
                ctx['words_shown'] = 1
            ctx['est_theta'] = self.est_theta
            ctx['due_date'] = self.object.due_date.strftime('%b %d, %Y, %I:%M %p')
            ctx['hardest'], ctx['easiest'] = self.get_hardest_easiest()
        except:
            #we get here if the form is expired without being opened
            ctx['words_shown'] = 0
            ctx['est_theta'] = self.est_theta
            ctx['due_date'] = self.object.due_date.strftime('%b %d, %Y, %I:%M %p')
            ctx['hardest'], ctx['easiest'] = None, None
        return ctx

    def get(self, request, *args, **kwargs):

        self.object = self.get_object()
        user_language = language_map(self.object.study.instrument.language)
        self.language=user_language
        translation.activate(user_language)
        if not self.object.completed and self.object.due_date < timezone.now(): 
            logger.debug(f'{self.object} is not completed by can be still')
            response = render (request, 'cdi_forms/expired.html', {}) # Render contact form template   
            response.set_cookie(settings.LANGUAGE_COOKIE_NAME, user_language)
            return response
        requests_log.objects.create(url_hash=self.hash_id, request_type="GET")
        if self.object.completed or self.object.due_date < timezone.now():
            logger.debug(f"Completed for {self.object} is { self.object.completed }")
            logger.debug(f"Due date for {self.object} is { self.object.due_date }")
            logger.debug(f"Administration instance {self.object} COMPLETED")
            response = render(request, 'cdi_forms/cat_forms/cat_completed.html', context=self.get_context_data())
            response.set_cookie(settings.LANGUAGE_COOKIE_NAME, user_language)
            return response
        background_instance, created = BackgroundInfo.objects.get_or_create(administration=self.object) 
        if self.object.completedSurvey:
            logger.debug(f"Administration instance {self.object} BACKPAGE")
            return redirect('backpage-background-info', pk=background_instance.pk)
        elif not self.object.completedBackgroundInfo:
            logger.debug(f"Administration instance {self.object} BACKGROUND INFO")
            return redirect('background-info', pk=background_instance.pk)

        cat_response, created = CatResponse.objects.get_or_create(administration=self.object)
        if created or not cat_response.est_theta:
            cat_response.est_theta = self.est_theta
            cat_response.save()

        administered_responses = self.object.catresponse.administered_responses or []
        administered_items = self.object.catresponse.administered_items or []
        administered_words = self.object.catresponse.administered_words or []
        self.est_theta = self.object.catresponse.est_theta

        
        if len(administered_words) < 1 : # first word might be specified by age
            self.word = cdi_cat_api(f'startItem?age_mos={self.object.backgroundinfo.age}&language={CAT_LANG_DICT[self.language]}')
        else:    
            self.word = cdi_cat_api(f'nextItem?responses={list(map(int,administered_responses))}&items={administered_items}&language={CAT_LANG_DICT[self.language]}')
            if self.word['stop'] == True:
                try:
                    filename = os.path.realpath(PROJECT_ROOT + self.object.study.demographic.path)
                except Exception:
                    filename = 'None'
                if  os.path.isfile(filename):
                    self.object.completedSurvey = True
                else :
                    self.object.completed = True
                self.object.catresponse.est_theta = self.word['curTheta']
                self.object.save()
                self.object.catresponse.save()
                return redirect('cat_forms:administer_cat_form', hash_id=self.hash_id)
            else :
                self.object.catresponse.est_theta = self.word['curTheta']
                self.object.save()
                self.object.catresponse.save()
        return super().get(request, *args, **kwargs) 
