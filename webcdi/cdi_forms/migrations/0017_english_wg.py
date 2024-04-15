# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cdi_forms", "0016_auto_20151019_1750"),
    ]

    operations = [
        migrations.CreateModel(
            name="English_WG",
            fields=[
                (
                    "itemID",
                    models.CharField(max_length=101, serialize=False, primary_key=True),
                ),
                ("item", models.CharField(max_length=101)),
                ("item_type", models.CharField(max_length=101)),
                ("category", models.CharField(max_length=101)),
                ("choices", models.CharField(max_length=101)),
                ("uni_lemma", models.CharField(max_length=101)),
                ("definition", models.CharField(max_length=201, null=True)),
                ("gloss", models.CharField(max_length=101, null=True)),
                ("complexity_category", models.CharField(max_length=101, null=True)),
            ],
        ),
    ]
