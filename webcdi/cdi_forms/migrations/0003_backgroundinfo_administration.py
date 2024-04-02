# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("researcher_UI", "0006_auto_20150921_0719"),
        ("cdi_forms", "0002_backgroundinfo"),
    ]

    operations = [
        migrations.AddField(
            model_name="backgroundinfo",
            name="administration",
            field=models.ForeignKey(
                default=0, to="researcher_UI.administration", on_delete=models.PROTECT
            ),
            preserve_default=False,
        ),
    ]
