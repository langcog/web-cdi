# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("researcher_UI", "0016_auto_20170413_2139"),
    ]

    operations = [
        migrations.AddField(
            model_name="study",
            name="anon_collection",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="study",
            name="subject_cap",
            field=models.IntegerField(null=True, blank=True),
        ),
    ]
