# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('cdi_forms', '0025_auto_20161021_0137'),
    ]

    operations = [
        migrations.AlterField(
            model_name='backgroundinfo',
            name='age',
            field=models.IntegerField(default=0, verbose_name=b'Age (in months)', validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AlterField(
            model_name='backgroundinfo',
            name='born_on_due_date',
            field=models.BooleanField(verbose_name=b'Was your child born early or late from their due date?'),
        ),
        migrations.AlterField(
            model_name='backgroundinfo',
            name='due_date_diff',
            field=models.IntegerField(blank=True, null=True, verbose_name=b'By how many weeks?<br>(Round to the nearest week)', validators=[django.core.validators.MinValueValidator(1, b'Number of weeks cannot be less than 1')]),
        ),
    ]
