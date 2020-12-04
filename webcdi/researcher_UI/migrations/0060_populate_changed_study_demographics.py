# Manually written by Henry Mehta on 2020-12-04 09:53

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings
import json, os
from researcher_UI.models import *
import string

def populate_instrument(apps, schema_editor):
        PROJECT_ROOT = settings.BASE_DIR
        input_instruments = json.load(open(os.path.realpath(PROJECT_ROOT + '/static/json/instruments.json'),encoding='utf8'))
        var_safe = lambda s: ''.join([c for c in '_'.join(s.split()) if c in string.ascii_letters + string.digits + '_'])

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
            except: 
                print(f'    No demographic selections for {instrument_obj.name}')

def set_study_demographic(apps, schema_editor):
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

class Migration(migrations.Migration):

    dependencies = [
        ('researcher_UI', '0059_auto_20201204_0953'),
    ]

    operations = [
        migrations.RunPython(populate_instrument),
        migrations.RunPython(set_study_demographic),
    ]