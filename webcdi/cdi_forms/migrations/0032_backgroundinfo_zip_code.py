# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('cdi_forms', '0031_auto_20170201_2315'),
    ]

    operations = [
        migrations.AddField(
            model_name='backgroundinfo',
            name='zip_code',
            field=models.CharField(blank=True, max_length=5, null=True, verbose_name=b'Zip Code (if you live in the U.S.)', validators=[django.core.validators.RegexValidator(regex=b'^\\d{5}$', message=b'Please enter a valid U.S. zip code')]),
        ),
    ]
