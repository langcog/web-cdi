# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("researcher_UI", "0003_auto_20150910_0915"),
    ]

    operations = [
        migrations.AddField(
            model_name="administration",
            name="completed",
            field=models.BooleanField(default=False),
            preserve_default=False,
        ),
    ]
