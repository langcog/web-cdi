# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.contrib.postgres.fields


class Migration(migrations.Migration):

    dependencies = [
        ('cdi_forms', '0006_auto_20150921_1706'),
    ]

    operations = [
        migrations.AddField(
            model_name='backgroundinfo',
            name='child_ethnicity',
            field=django.contrib.postgres.fields.ArrayField(size=None, null=True, base_field=models.CharField(max_length=1), blank=True),
        ),
        migrations.AddField(
            model_name='backgroundinfo',
            name='other_languages',
            field=django.contrib.postgres.fields.ArrayField(size=None, null=True, base_field=models.CharField(max_length=101), blank=True),
        ),
    ]
