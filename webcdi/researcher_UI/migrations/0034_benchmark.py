# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-06-02 10:30
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("researcher_UI", "0033_auto_20190531_1158"),
    ]

    operations = [
        migrations.CreateModel(
            name="Benchmark",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("percentile", models.IntegerField()),
                ("age", models.IntegerField()),
                ("raw_score", models.IntegerField()),
                ("raw_score_boy", models.IntegerField()),
                ("raw_score_girl", models.IntegerField()),
                (
                    "instrument",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="researcher_UI.instrument",
                    ),
                ),
                (
                    "instrument_score",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="researcher_UI.InstrumentScore",
                    ),
                ),
            ],
        ),
    ]
