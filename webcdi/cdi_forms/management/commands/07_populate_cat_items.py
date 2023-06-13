import json
import re
from django.core.management.base import BaseCommand
from cdi_forms.cat_forms.models import *
from researcher_UI.models import *
import csv, os
from django.apps import apps
from django.conf import settings


# Populates the ItemInfo and ItemMap models with data from instrument definition files.
# Given no arguments, does so for all instruments in 'static/json/instruments.json'.
# Given a language with -l and a form with -f, does so for only their Instrument object.

def unicode_csv_reader(utf8_data, dialect=csv.excel, **kwargs):
    csv_reader = csv.reader(utf8_data, dialect=dialect, **kwargs)
    for row in csv_reader:
        yield [cell for cell in row]
        
class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('-l', '--language', type=str)
        parser.add_argument('-f', '--form', type=str)

    def handle(self, *args, **options):
        instruments = json.load(open(os.path.realpath(settings.BASE_DIR + '/static/json/instruments.json'), encoding="utf8"))
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
            if not curr_instrument['form'] in settings.CAT_FORMS: continue
            instrument_language, instrument_form = curr_instrument['language'], curr_instrument['form']

            instrument_obj = instrument.objects.get(form=instrument_form, language=instrument_language)
            instrument_items = apps.get_model(app_label='cdi_forms', model_name='InstrumentItem')

            print ("    Populating items for", instrument_language, instrument_form)

            ftype = curr_instrument['csv_file'].split('.')[-1]

            if ftype == 'csv':
                contents = list(unicode_csv_reader(open(os.path.realpath(settings.BASE_DIR + '/' + curr_instrument['csv_file']), encoding="utf8")))
                col_names = contents[0]
                nrows = len(contents)
                get_row = lambda row: contents[row]
            else:
                raise IOError("Instrument file must be a CSV.")

            for row in range(1, nrows):
                row_values = get_row(row)
                if len(row_values) > 1:
                    discrimination = float(row_values[col_names.index('discrimination')])
                    difficulty = float(row_values[col_names.index('difficulty')])
                    guessing = float(row_values[col_names.index('guessing')])
                    upper_asymptote = float(row_values[col_names.index('upper_asymptote')])
                    definition = row_values[col_names.index('definition')]
                    
                    data_dict = {'discrimination': discrimination,
                                 'difficulty': difficulty,
                                 'guessing': guessing,
                                 'upper_asymptote': upper_asymptote,
                                }

                    cat_item, created = instrument_items.objects.update_or_create(instrument=instrument_obj, definition=definition, defaults=data_dict,)

            # Now do starting words
            cat_starting_words = apps.get_model(app_label='cdi_forms', model_name='CatStartingWord')
            if 'starting_words' in curr_instrument :
                starting_words_filename = os.path.realpath(settings.BASE_DIR + '/' + curr_instrument['starting_words'])
                
                ftype = starting_words_filename.split('.')[-1]
                if ftype == 'csv':
                    contents = list(unicode_csv_reader(open(starting_words_filename, encoding="utf8")))
                    col_names = contents[0]
                    nrows = len(contents)
                    get_row = lambda row: contents[row]
                else:
                    raise IOError("Starting Words file must be a CSV.")

                for row in range(1, nrows):
                    row_values = get_row(row)
                    if len(row_values) > 1:
                        age = int(row_values[col_names.index('age')])
                        definition = row_values[col_names.index('definition')]

                        instrument_item = instrument_items.objects.get(instrument=instrument_obj,definition=definition)
                        
                        data_dict = {'instrument_item': instrument_item,}

                        age_item, created = cat_starting_words.objects.update_or_create(instrument=instrument_obj, age=age, defaults=data_dict)
                
                print(f'      Processed Starting words for {instrument_obj}')
