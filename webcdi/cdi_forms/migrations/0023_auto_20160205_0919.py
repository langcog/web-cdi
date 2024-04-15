# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cdi_forms", "0022_auto_20160205_0746"),
    ]

    operations = [
        migrations.AlterField(
            model_name="english_ws",
            name="choices",
            field=models.CharField(max_length=101, null=True),
        ),
    ]
