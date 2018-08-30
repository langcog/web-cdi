# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

from django.conf import settings
import json, os, string

def populate_instrument(apps, schema_editor):
    PROJECT_ROOT = settings.BASE_DIR
    input_instruments = json.load(open(os.path.realpath(PROJECT_ROOT + '/static/json/instruments.json')))
    var_safe = lambda s: ''.join([c for c in '_'.join(s.split()) if c in string.letters + '_'])
    instrument = apps.get_model('researcher_UI', 'instrument')
    instrument_fields = [f.name for f in instrument._meta.get_fields()]

    for curr_instrument in input_instruments:

        instrument_language = curr_instrument['language']
        instrument_form = curr_instrument['form']
        instrument_verbose_name = curr_instrument['verbose_name']

        instrument_name = var_safe(instrument_language) + '_' + var_safe(instrument_form)

        instrument_min_age = curr_instrument['min_age']
        instrument_max_age = curr_instrument['max_age']

        data_dict = {'language': instrument_language,
                     'form': instrument_form,
                     'verbose_name': instrument_verbose_name,
                     'min_age': instrument_min_age,
                     'max_age': instrument_max_age}

        sub_dict = {k: data_dict.get(k, None) for k in set.intersection(set(data_dict.keys()), set(instrument_fields))}

        instrument_obj, created = instrument.objects.update_or_create(name = instrument_name, defaults=sub_dict,)

class Migration(migrations.Migration):

    dependencies = [
        ('researcher_UI', '0009_auto_20161208_2055'),
    ]

    operations = [
        migrations.AlterField(
            model_name='instrument',
            name='form',
            field=models.CharField(max_length=51),
        ),
        migrations.AlterField(
            model_name='instrument',
            name='language',
            field=models.CharField(max_length=51),
        ),
        migrations.AlterField(
            model_name='instrument',
            name='max_age',
            field=models.IntegerField(default=0, verbose_name=b'Maximum age'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='instrument',
            name='min_age',
            field=models.IntegerField(default=0, verbose_name=b'Minimum age'),
            preserve_default=False,
        ),
        migrations.RunPython(populate_instrument),
        migrations.AlterUniqueTogether(
            name='instrument',
            unique_together=set([('language', 'form')]),
        ),
    ]
