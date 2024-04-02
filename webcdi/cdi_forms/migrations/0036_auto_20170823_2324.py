# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cdi_forms", "0035_auto_20170519_2027"),
    ]

    operations = [
        migrations.CreateModel(
            name="Spanish_WG",
            fields=[
                (
                    "itemID",
                    models.CharField(max_length=101, serialize=False, primary_key=True),
                ),
                ("item", models.CharField(max_length=101)),
                ("item_type", models.CharField(max_length=101)),
                ("category", models.CharField(max_length=101)),
                ("choices", models.CharField(max_length=101, null=True)),
                ("definition", models.CharField(max_length=201, null=True, blank=True)),
                ("uni_lemma", models.CharField(max_length=101, null=True, blank=True)),
                ("gloss", models.CharField(max_length=101, null=True, blank=True)),
                (
                    "complexity_category",
                    models.CharField(max_length=101, null=True, blank=True),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Spanish_WS",
            fields=[
                (
                    "itemID",
                    models.CharField(max_length=101, serialize=False, primary_key=True),
                ),
                ("item", models.CharField(max_length=101)),
                ("item_type", models.CharField(max_length=101)),
                ("category", models.CharField(max_length=101)),
                ("choices", models.CharField(max_length=101, null=True)),
                ("definition", models.CharField(max_length=201, null=True, blank=True)),
                ("uni_lemma", models.CharField(max_length=101, null=True, blank=True)),
                ("gloss", models.CharField(max_length=101, null=True, blank=True)),
                (
                    "complexity_category",
                    models.CharField(max_length=101, null=True, blank=True),
                ),
            ],
        ),
        migrations.AlterField(
            model_name="english_wg",
            name="definition",
            field=models.CharField(max_length=1001, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name="english_ws",
            name="definition",
            field=models.CharField(max_length=1001, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name="english_ws",
            name="gloss",
            field=models.CharField(max_length=1001, null=True, blank=True),
        ),
    ]
