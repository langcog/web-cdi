import json
import re
from django.core.management.base import BaseCommand
from researcher_UI.models import *
import string
from django.conf import settings
import os

# Populates the ItemInfo and ItemMap models with data from instrument definition files.
# Given no arguments, does so for all instruments in 'static/json/instruments.json'.
# Given a language with -l and a form with -f, does so for only their Instrument object.

class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('-l', '--language', type=str)
        parser.add_argument('-f', '--form', type=str)

    def handle(self, *args, **options):
	
        PROJECT_ROOT = settings.BASE_DIR
        instruments = json.load(open(os.path.realpath(PROJECT_ROOT + '/static/json/instruments.json'),encoding='utf8'))
        var_safe = lambda s: ''.join([c for c in '_'.join(s.split()) if c in string.ascii_letters + string.digits + '_'])

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

            instrument_language = curr_instrument['language']
            instrument_form = curr_instrument['form']
            instrument_verbose_name = curr_instrument['verbose_name']

            print ("Updating instrument table for (%s %s)" % (instrument_language, instrument_form))

            instrument_name = var_safe(instrument_language) + '_' + var_safe(instrument_form)

            instrument_min_age = curr_instrument['min_age']
            instrument_max_age = curr_instrument['max_age']

            data_dict = {'language': instrument_language,
                         'form': instrument_form,
                         'verbose_name': instrument_verbose_name,
                         'min_age': instrument_min_age,
                         'max_age': instrument_max_age}

            instrument_obj, created = instrument.objects.update_or_create(name = instrument_name, defaults=data_dict,)

            
            try:
                for demo in curr_instrument['demographics']:
                    demographic, created = Demographic.objects.update_or_create(name=demo, path='/form_data/background_info/' + demo)
                    instrument_obj.demographics.add(demographic)
                    print(f'    Added demographic {demographic}')
            except: 
                print(f'    No demographic selections for {instrument_obj.name}')
