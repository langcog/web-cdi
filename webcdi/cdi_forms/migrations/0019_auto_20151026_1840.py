# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cdi_forms", "0018_auto_20151026_1840"),
    ]

    operations = [
        migrations.AlterField(
            model_name="english_wg",
            name="gloss",
            field=models.CharField(max_length=1001, null=True),
        ),
    ]
