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

def unicode_csv_reader(utf8_data, dialect=csv.excel, **kwargs):
    csv_reader = csv.reader(utf8_data, dialect=dialect, **kwargs)
    for row in csv_reader:
        yield [unicode(cell, 'utf-8') for cell in row]
        
class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('-l', '--language', type=str)
        parser.add_argument('-f', '--form', type=str)

    def handle(self, *args, **options):

        PROJECT_ROOT = settings.BASE_DIR
        instruments = json.load(open(os.path.realpath(PROJECT_ROOT + '/static/json/instruments.json')))
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
            instrument_language, instrument_form = curr_instrument['language'], curr_instrument['form']

            if not 'benchmark' in curr_instrument:
                print "    No Benchmark data for", instrument_language, instrument_form
                continue
            
            print "    Populating Benchmark data for", instrument_language, instrument_form
            
            instrument_obj = instrument.objects.get(form=instrument_form, language=instrument_language)

            ftype = curr_instrument['csv_file'].split('.')[-1]

            if ftype == 'csv':

                contents = list(unicode_csv_reader(open(os.path.realpath(PROJECT_ROOT + '/' + curr_instrument['benchmark']))))
                col_names = contents[0]
                nrows = len(contents)
                get_row = lambda row: contents[row]
            else:
                raise IOError("Instrument file must be a CSV.")


            for row in xrange(1, nrows):
                row_values = get_row(row)
                if len(row_values) > 1:
                    title = row_values[col_names.index('title')]
                    scoring_obj = InstrumentScore.objects.get(title=title, instrument=instrument_obj)
                    percentile = row_values[col_names.index('percentile')]
                    age = row_values[col_names.index('age')]
                    raw_score = row_values[col_names.index('raw_score')]
                    percentile_boy = row_values[col_names.index('percentile_boy')]
                    percentile_girl = row_values[col_names.index('percentile_girl')]
                    data_dict = {'raw_score': raw_score,
                                 'percentile_boy': percentile_boy,
                                 'percentile_girl': percentile_boy}

                    cdi_item, created = Benchmark.objects.update_or_create(instrument=instrument_obj, instrument_score=scoring_obj, percentile = percentile, age=age, defaults=data_dict,)

