# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("researcher_UI", "0005_auto_20150915_0704"),
    ]

    operations = [
        migrations.AddField(
            model_name="instrument",
            name="verbose_name",
            field=models.CharField(max_length=51, blank=True),
        ),
        migrations.AlterField(
            model_name="administration",
            name="due_date",
            field=models.DateTimeField(verbose_name=b"Expiration date"),
        ),
        migrations.AlterField(
            model_name="administration",
            name="repeat_num",
            field=models.IntegerField(verbose_name=b"Administration number"),
        ),
    ]
