# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cdi_forms", "0010_remove_backgroundinfo_born_on_due_date"),
    ]

    operations = [
        migrations.AddField(
            model_name="backgroundinfo",
            name="born_on_due_date",
            field=models.BooleanField(
                default=False, verbose_name=b"Was your child born early or late?"
            ),
            preserve_default=False,
        ),
    ]
