# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cdi_forms', '0012_auto_20151019_1640'),
    ]

    operations = [
        migrations.AlterField(
            model_name='english_ws',
            name='gloss',
            field=models.CharField(max_length=101, null=True),
        ),
    ]
