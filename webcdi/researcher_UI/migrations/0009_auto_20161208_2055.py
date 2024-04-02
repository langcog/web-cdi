# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("researcher_UI", "0008_auto_20160205_1132"),
    ]

    operations = [
        migrations.AddField(
            model_name="administration",
            name="created_date",
            field=models.DateTimeField(
                default="1904-01-01", verbose_name=b"Creation date", auto_now_add=True
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="instrument",
            name="form",
            field=models.CharField(max_length=51, blank=True),
        ),
        migrations.AddField(
            model_name="instrument",
            name="language",
            field=models.CharField(max_length=51, blank=True),
        ),
        migrations.AddField(
            model_name="instrument",
            name="max_age",
            field=models.IntegerField(null=True, verbose_name=b"Maximum age"),
        ),
        migrations.AddField(
            model_name="instrument",
            name="min_age",
            field=models.IntegerField(null=True, verbose_name=b"Minimum age"),
        ),
        migrations.AddField(
            model_name="study",
            name="study_group",
            field=models.CharField(max_length=51, blank=True),
        ),
    ]
