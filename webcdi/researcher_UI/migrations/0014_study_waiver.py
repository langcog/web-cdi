# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("researcher_UI", "0013_auto_20170221_1758"),
    ]

    operations = [
        migrations.AddField(
            model_name="study",
            name="waiver",
            field=models.TextField(blank=True),
        ),
    ]
