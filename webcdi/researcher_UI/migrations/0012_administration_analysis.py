# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("researcher_UI", "0011_administration_page_number"),
    ]

    operations = [
        migrations.AddField(
            model_name="administration",
            name="analysis",
            field=models.BooleanField(
                default=False, verbose_name=b"Can be used for analysis"
            ),
        ),
    ]
