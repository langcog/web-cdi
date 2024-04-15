# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("researcher_UI", "0019_auto_20170505_0444"),
    ]

    operations = [
        migrations.AddField(
            model_name="study",
            name="test_period",
            field=models.IntegerField(
                default=14,
                validators=[
                    django.core.validators.MinValueValidator(1),
                    django.core.validators.MaxValueValidator(14),
                ],
            ),
        ),
    ]
