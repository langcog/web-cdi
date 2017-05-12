# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('researcher_UI', '0019_auto_20170505_0444'),
    ]

    operations = [
        migrations.AddField(
            model_name='study',
            name='test_period',
            field=models.IntegerField(default=14, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(14)]),
        ),
    ]
