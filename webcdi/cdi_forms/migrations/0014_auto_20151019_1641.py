# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cdi_forms", "0013_auto_20151019_1641"),
    ]

    operations = [
        migrations.AlterField(
            model_name="english_ws",
            name="definition",
            field=models.CharField(max_length=201, null=True),
        ),
    ]
