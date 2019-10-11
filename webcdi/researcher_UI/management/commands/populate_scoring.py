import json
import re
from django.core.management.base import BaseCommand
from cdi_forms.models import *
from researcher_UI.models import *
import csv, os
from django.apps import apps
from django.conf import settings


# Populates the ItemInfo and ItemMap models with data from instrument definition files.
# Given no arguments, does so for all instruments in 'static/json/instruments.json'.
# Given a language with -l and a form with -f, does so for only their Instrument object.
        
class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('-l', '--language', type=str)
        parser.add_argument('-f', '--form', type=str)

    def handle(self, *args, **options):

        PROJECT_ROOT = settings.BASE_DIR
        instruments = json.load(open(os.path.realpath(PROJECT_ROOT + '/static/json/instruments.json'), encoding="utf8"))
        if options['language'] and options['form']:
            input_language, input_form = options['language'], options['form']
            input_instruments = filter(lambda instrument: instrument['language'] == input_language and
                                                          instrument['form'] == input_form,
                                       instruments)
        elif options['language'] and not options['form']:
            input_language = options['language']
            input_instruments = filter(lambda instrument: instrument['language'] == input_language,
                                       instruments)
        elif not options['language'] and options['form']:
            input_form = options['form']
            input_instruments = filter(lambda instrument: instrument['form'] == input_form,
                                       instruments)
        else:
            input_instruments = instruments

        for curr_instrument in input_instruments:

            instrument_language, instrument_form, instrument_scoring = curr_instrument['language'], curr_instrument['form'], curr_instrument['scoring_json']
            
            instrument_obj = instrument.objects.get(form=instrument_form, language=instrument_language)
            instrument_forms = apps.get_model(app_label='cdi_forms', model_name='Instrument_Forms')

            print ("    Populating Scoring Methodology for", instrument_language, instrument_form)

            scores = json.load(open(os.path.realpath(PROJECT_ROOT + '/' + instrument_scoring), encoding="utf8"))

            for score in scores:
                data_dict = {
                    'category': score['category'],
                    'measure': score['measure'],
                    'order':score['order'],
                    'kind':score['kind'] if 'kind' in score else 'count'
                }
                row, created = InstrumentScore.objects.update_or_create(instrument = instrument_obj, title=score['title'], defaults=data_dict,)