# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("researcher_UI", "0010_auto_20161208_2104"),
    ]

    operations = [
        migrations.AddField(
            model_name="administration",
            name="page_number",
            field=models.IntegerField(default=0, verbose_name=b"Page number"),
        ),
    ]
