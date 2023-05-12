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
    '''
    This is used to convert Virginia's benching marking data into files which are easier to copy and paste into
    the format we need
    '''

    def add_arguments(self, parser):
        parser.add_argument('-f', '--file', type=str)

    def handle(self, *args, **options):

        path = os.path.realpath(f'{settings.BASE_DIR}/cdi_forms/form_data/scoring_source')
        file_list =  os.listdir(path)
        for item in file_list:
            if not os.path.isfile(f'{path}/{item}'):
                continue
            f = open(f'{path}/output/{item}', 'w')
            writer = csv.writer(f)
            contents = list(unicode_csv_reader(open(f'{path}/{item}', encoding="utf8")))
            col_names = contents[1]
            nrows = len(contents)
            get_row = lambda row: contents[row]
            for row in range(2, nrows):
                row_values = get_row(row)
                for cell in range(1,len(contents[row])):
                    writer.writerow([item, row_values[0], col_names[cell], row_values[cell]])
            f.close()