# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("researcher_UI", "0004_administration_completed"),
    ]

    operations = [
        migrations.AddField(
            model_name="administration",
            name="due_date",
            field=models.DateTimeField(
                default=datetime.datetime(2015, 9, 15, 7, 3, 53, 279039)
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="administration",
            name="last_modified",
            field=models.DateTimeField(
                default=datetime.datetime(2015, 9, 15, 7, 4, 0, 582163), auto_now=True
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="administration",
            name="url_hash",
            field=models.CharField(unique=True, max_length=128),
        ),
    ]
