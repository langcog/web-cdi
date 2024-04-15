# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("researcher_UI", "0006_auto_20150921_0719"),
    ]

    operations = [
        migrations.AddField(
            model_name="administration",
            name="completedBackgroundInfo",
            field=models.BooleanField(default=False),
        ),
    ]
