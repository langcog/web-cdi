# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("researcher_UI", "0012_administration_analysis"),
    ]

    operations = [
        migrations.AlterField(
            model_name="administration",
            name="analysis",
            field=models.NullBooleanField(
                default=None, verbose_name=b"Can be used for analysis"
            ),
        ),
    ]
