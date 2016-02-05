# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cdi_forms', '0011_backgroundinfo_born_on_due_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='english_ws',
            name='complexity_category',
            field=models.CharField(max_length=101, null=True),
        ),
    ]
