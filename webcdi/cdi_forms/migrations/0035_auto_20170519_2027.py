# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('cdi_forms', '0034_auto_20170515_2147'),
    ]

    operations = [
        migrations.CreateModel(
            name='Zipcode',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('zip_code', models.CharField(max_length=5)),
                ('zip_prefix', models.CharField(max_length=3)),
                ('population', models.IntegerField()),
                ('state', models.CharField(max_length=2)),
            ],
        ),
        migrations.AlterField(
            model_name='backgroundinfo',
            name='zip_code',
            field=models.CharField(blank=True, max_length=5, null=True, verbose_name=b'Zip Code (if you live in the U.S.)', validators=[django.core.validators.RegexValidator(regex=b'^(\\d{3}([*]{2})?)|([A-Z]{2})$', message=b'Please enter a valid U.S. zip code')]),
        ),
    ]
