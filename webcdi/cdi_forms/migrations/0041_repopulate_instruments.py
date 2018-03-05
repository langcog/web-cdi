# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2018-03-05 00:23
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
from django.core.management import call_command

def updateInstruments(apps, schema_editor):
    call_command('populate_instrument')
    call_command('populate_items')

class Migration(migrations.Migration):

    dependencies = [
        ('cdi_forms', '0040_replace_choices_field'),
    ]

    operations = [
        migrations.AlterField(
            model_name='spanish_wg',
            name='choices',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='cdi_forms.Choices'),
        ),
        migrations.AlterField(
            model_name='spanish_wg',
            name='definition',
            field=models.CharField(blank=True, max_length=1001, null=True),
        ),
        migrations.AlterField(
            model_name='spanish_wg',
            name='gloss',
            field=models.CharField(blank=True, max_length=1001, null=True),
        ),
        migrations.AlterField(
            model_name='spanish_ws',
            name='choices',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='cdi_forms.Choices'),
        ),
        migrations.AlterField(
            model_name='spanish_ws',
            name='definition',
            field=models.CharField(blank=True, max_length=1001, null=True),
        ),
        migrations.AlterField(
            model_name='spanish_ws',
            name='gloss',
            field=models.CharField(blank=True, max_length=1001, null=True),
        ),
        migrations.RunPython(updateInstruments)
    ]