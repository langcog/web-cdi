# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('cdi_forms', '0026_auto_20161116_1820'),
    ]

    operations = [
        migrations.AlterField(
            model_name='backgroundinfo',
            name='age',
            field=models.IntegerField(default=999, verbose_name=b'Age (in months)', validators=[django.core.validators.MinValueValidator(0)]),
        ),
    ]
