# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("supplementtut", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="myregistrationsupplement",
            name="position",
            field=models.CharField(
                default="", max_length=101, verbose_name="Position in Institution"
            ),
            preserve_default=False,
        ),
    ]
