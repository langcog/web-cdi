# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("researcher_UI", "0015_study_confirm_completion"),
    ]

    operations = [
        migrations.AlterField(
            model_name="administration",
            name="analysis",
            field=models.NullBooleanField(
                default=None, verbose_name=b"Confirmed Age and Completion"
            ),
        ),
    ]
