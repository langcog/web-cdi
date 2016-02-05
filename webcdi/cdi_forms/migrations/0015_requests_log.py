# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cdi_forms', '0014_auto_20151019_1641'),
    ]

    operations = [
        migrations.CreateModel(
            name='requests_log',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('url_hash', models.CharField(unique=True, max_length=128)),
                ('request_type', models.CharField(max_length=4)),
                ('timestamp', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
