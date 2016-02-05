# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cdi_forms', '0015_requests_log'),
    ]

    operations = [
        migrations.AlterField(
            model_name='requests_log',
            name='url_hash',
            field=models.CharField(max_length=128),
        ),
    ]
