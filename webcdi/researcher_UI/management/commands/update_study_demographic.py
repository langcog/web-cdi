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

from researcher_UI.models import study, Demographic, instrument
        
class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('-l', '--language', type=str)
        parser.add_argument('-f', '--form', type=str)

    def handle(self, *args, **options):

        studies = study.objects.all()
        for obj in studies:
            if obj.instrument.language == 'Dutch' : 
                obj.demographic = Demographic.objects.get(name="Dutch_Split.json")
            if obj.instrument.language == 'Hebrew' : 
                obj.demographic = Demographic.objects.get(name="Hebrew_Split.json")
            if obj.instrument.name == "English_WS2":
                obj.instrument = instrument.objects.get(name="English_WS")
                obj.demographic = Demographic.objects.get(name="English_Split.json")
            if obj.instrument.name == "English_WG2":
                obj.instrument = instrument.objects.get(name="English_WG")
                obj.demographic = Demographic.objects.get(name="English_Split.json")
            if obj.instrument.name == "English_CAT2":
                obj.instrument = instrument.objects.get(name="English_CAT")
                obj.demographic = Demographic.objects.get(name="English_Split.json")
            if obj.instrument.name == "Canadian_English_WS2":
                obj.instrument = instrument.objects.get(name="Canadian_English_WS")
                obj.demographic = Demographic.objects.get(name="Canadian_English_Split.json")
            if obj.instrument.name == "Canadian_English_WG2":
                obj.instrument = instrument.objects.get(name="Canadian_English_WG")
                obj.demographic = Demographic.objects.get(name="Canadian_English_Split.json")
            if obj.instrument.name == "English_CDI3B":
                obj.instrument = instrument.objects.get(name="English_CDI3")
                obj.demographic = Demographic.objects.get(name="English_Split.json")
            if obj.instrument.name == "English_L1B":
                obj.instrument = instrument.objects.get(name="English_L1")
                obj.demographic = Demographic.objects.get(name="English_Split.json")
            if obj.instrument.name == "English_L2AB":
                obj.instrument = instrument.objects.get(name="English_L2A")
                obj.demographic = Demographic.objects.get(name="English_Split.json")
            if obj.instrument.name == "English_L2BB":
                obj.instrument = instrument.objects.get(name="English_L2B")
                obj.demographic = Demographic.objects.get(name="English_Split.json")
            if obj.instrument.name == "French_Quebec_WG2":
                obj.instrument = instrument.objects.get(name="French_Quebec_WG")
                obj.demographic = Demographic.objects.get(name="French_Quebec_Split.json")
            if obj.instrument.name == "French_Quebec_WS2":
                obj.instrument = instrument.objects.get(name="French_Quebec_WS")
                obj.demographic = Demographic.objects.get(name="French_Quebec_Split.json")
            if obj.instrument.name == "Spanish_WG2":
                obj.instrument = instrument.objects.get(name="Spanish_WG")
                obj.demographic = Demographic.objects.get(name="Spanish_Split.json")
            if obj.instrument.name == "Spanish_WS2":
                obj.instrument = instrument.objects.get(name="Spanish_WS")
                obj.demographic = Demographic.objects.get(name="Spanish_Split.json")
            if obj.demographic:
                print(f'    Saving {obj.name} with instrument {obj.instrument.name} and demographic {obj.demographic}')
            obj.save()